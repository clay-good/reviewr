"""CLI commands for auto-fix functionality."""

import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, List, Dict
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .config import ConfigLoader
from .providers import ProviderFactory, ReviewType
from .review.orchestrator import ReviewOrchestrator
from .autofix import (
    FixApplicator,
    PythonFixGenerator,
    JavaScriptFixGenerator,
    CompositeFixGenerator,
    FixStatus
)

console = Console()


@click.group()
def fix():
    """Auto-fix code issues detected by reviewr."""
    pass


@fix.command('apply')
@click.argument('path', type=click.Path(exists=True))
@click.option('--findings-file', '-f', type=click.Path(exists=True),
              help='JSON file with findings from previous review')
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without applying changes')
@click.option('--interactive', '-i', is_flag=True, help='Ask for confirmation before each fix')
@click.option('--safe-only', is_flag=True, help='Only apply fixes marked as safe')
@click.option('--category', multiple=True,
              type=click.Choice(['formatting', 'imports', 'type_hints', 'security', 'performance', 'correctness', 'style']),
              help='Only apply fixes in these categories')
@click.option('--min-confidence', type=float, default=0.8,
              help='Minimum confidence threshold (0.0-1.0, default: 0.8)')
@click.option('--backup-dir', type=click.Path(), default='.reviewr_backups',
              help='Directory for backups (default: .reviewr_backups)')
@click.option('--no-validation', is_flag=True, help='Skip syntax validation after applying fixes')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use for analysis')
def apply_fixes(
    path: str,
    findings_file: Optional[str],
    dry_run: bool,
    interactive: bool,
    safe_only: bool,
    category: tuple,
    min_confidence: float,
    backup_dir: str,
    no_validation: bool,
    verbose: bool,
    config: Optional[str],
    provider: Optional[str]
) -> None:
    """
    Apply auto-fixes to code issues.
    
    Can either:
    1. Use findings from a previous review (--findings-file)
    2. Run a new review and apply fixes immediately
    
    Examples:
        reviewr fix apply src/ --dry-run
        reviewr fix apply src/ --interactive --safe-only
        reviewr fix apply src/ --findings-file results.json
        reviewr fix apply src/ --category imports --category style
    """
    try:
        # Load configuration
        cfg = ConfigLoader.load_config(config)
        
        # Override provider if specified
        if provider:
            cfg.provider.name = provider
        
        # Run the fix process
        asyncio.run(_apply_fixes_async(
            path=path,
            findings_file=findings_file,
            dry_run=dry_run,
            interactive=interactive,
            safe_only=safe_only,
            categories=list(category) if category else None,
            min_confidence=min_confidence,
            backup_dir=backup_dir,
            validate_syntax=not no_validation,
            verbose=verbose,
            config=cfg
        ))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


async def _apply_fixes_async(
    path: str,
    findings_file: Optional[str],
    dry_run: bool,
    interactive: bool,
    safe_only: bool,
    categories: Optional[List[str]],
    min_confidence: float,
    backup_dir: str,
    validate_syntax: bool,
    verbose: bool,
    config
) -> None:
    """Async implementation of apply fixes."""
    
    # Get findings
    if findings_file:
        console.print(f"📂 Loading findings from {findings_file}...")
        with open(findings_file, 'r') as f:
            findings_data = json.load(f)
            # Convert to ReviewFinding objects
            from .providers.base import ReviewFinding, ReviewType
            findings = [
                ReviewFinding(
                    type=ReviewType(f['type']),
                    severity=f['severity'],
                    file_path=f['file_path'],
                    line_start=f['line_start'],
                    line_end=f['line_end'],
                    message=f['message'],
                    suggestion=f.get('suggestion'),
                    code_snippet=f.get('code_snippet'),
                    confidence=f.get('confidence', 1.0)
                )
                for f in findings_data.get('findings', [])
            ]
    else:
        console.print(f"🔍 Analyzing code at {path}...")
        
        # Run review
        provider = ProviderFactory.create_provider(config)
        orchestrator = ReviewOrchestrator(provider, config, verbose=verbose)
        
        review_types = [
            ReviewType.SECURITY,
            ReviewType.PERFORMANCE,
            ReviewType.CORRECTNESS,
            ReviewType.MAINTAINABILITY,
            ReviewType.STANDARDS
        ]
        
        result = await orchestrator.review_path(
            path,
            review_types=review_types,
            include_patterns=list(config.file_discovery.include_patterns),
            exclude_patterns=list(config.file_discovery.exclude_patterns)
        )
        
        findings = result.findings
        console.print(f"✓ Found {len(findings)} issues")
    
    if not findings:
        console.print("[green]✓[/green] No issues found!")
        return
    
    # Load file contents
    console.print("📖 Loading file contents...")
    file_contents = _load_file_contents(findings)
    
    # Generate fixes
    console.print("🔧 Generating fixes...")
    composite_generator = CompositeFixGenerator()
    composite_generator.add_generator(PythonFixGenerator())
    composite_generator.add_generator(JavaScriptFixGenerator())
    
    all_fixes = composite_generator.generate_fixes(findings, file_contents)
    
    # Filter fixes
    filtered_fixes = _filter_fixes(
        all_fixes,
        safe_only=safe_only,
        categories=categories,
        min_confidence=min_confidence
    )
    
    if not filtered_fixes:
        console.print("[yellow]⚠[/yellow] No fixable issues found with current filters")
        return
    
    console.print(f"✓ Generated {len(filtered_fixes)} fixes")
    
    # Show summary
    _show_fix_summary(filtered_fixes)
    
    if dry_run:
        console.print("\n[cyan]Dry run mode - no changes will be made[/cyan]")
        _show_fix_details(filtered_fixes)
        return
    
    # Apply fixes
    console.print(f"\n{'🤔 Interactive mode' if interactive else '⚡ Applying fixes'}...")
    
    applicator = FixApplicator(
        backup_dir=backup_dir,
        dry_run=False,
        validate_syntax=validate_syntax,
        verbose=verbose
    )
    
    results = applicator.apply_fixes(
        filtered_fixes,
        interactive=interactive
    )
    
    # Show results
    _show_results(results)
    
    # Show backup location
    if any(r.status == FixStatus.SUCCESS for r in results):
        console.print(f"\n💾 Backups saved to: {backup_dir}")
        console.print(f"   To rollback: reviewr fix rollback --backup-dir {backup_dir}")


@fix.command('rollback')
@click.option('--backup-dir', type=click.Path(exists=True), default='.reviewr_backups',
              help='Directory containing backups (default: .reviewr_backups)')
def rollback_fixes(backup_dir: str) -> None:
    """
    Rollback all applied fixes by restoring from backups.
    
    Example:
        reviewr fix rollback
        reviewr fix rollback --backup-dir custom_backups/
    """
    try:
        applicator = FixApplicator(backup_dir=backup_dir)
        count = applicator.rollback_all()
        
        if count > 0:
            console.print(f"[green]✓[/green] Rolled back {count} file(s)")
        else:
            console.print("[yellow]⚠[/yellow] No backups found to rollback")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _load_file_contents(findings) -> Dict[str, str]:
    """Load contents of all files mentioned in findings."""
    file_contents = {}
    
    unique_files = set(f.file_path for f in findings)
    
    for file_path in unique_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_contents[file_path] = f.read()
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read {file_path}: {e}")
    
    return file_contents


def _filter_fixes(fixes, safe_only: bool, categories: Optional[List[str]], min_confidence: float):
    """Filter fixes based on criteria."""
    filtered = fixes
    
    if safe_only:
        filtered = [f for f in filtered if f.safe]
    
    if categories:
        filtered = [f for f in filtered if f.category.value in categories]
    
    filtered = [f for f in filtered if f.confidence >= min_confidence]
    
    return filtered


def _show_fix_summary(fixes):
    """Show summary table of fixes."""
    table = Table(title="Fix Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Safe", justify="right", style="yellow")
    table.add_column("Avg Confidence", justify="right", style="blue")
    
    # Group by category
    by_category = {}
    for fix in fixes:
        cat = fix.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(fix)
    
    for category, cat_fixes in sorted(by_category.items()):
        safe_count = sum(1 for f in cat_fixes if f.safe)
        avg_conf = sum(f.confidence for f in cat_fixes) / len(cat_fixes)
        
        table.add_row(
            category,
            str(len(cat_fixes)),
            str(safe_count),
            f"{avg_conf:.0%}"
        )
    
    console.print(table)


def _show_fix_details(fixes):
    """Show detailed information about each fix."""
    for i, fix in enumerate(fixes, 1):
        console.print(f"\n[bold cyan]Fix {i}/{len(fixes)}:[/bold cyan]")
        console.print(f"  File: {fix.file_path}:{fix.line_start}")
        console.print(f"  Category: {fix.category.value}")
        console.print(f"  Description: {fix.description}")
        console.print(f"  Confidence: {fix.confidence:.0%}")
        console.print(f"  Safe: {'✓' if fix.safe else '✗'}")
        
        if fix.explanation:
            console.print(f"  Explanation: {fix.explanation}")


def _show_results(results):
    """Show results of applying fixes."""
    success_count = sum(1 for r in results if r.status == FixStatus.SUCCESS)
    failed_count = sum(1 for r in results if r.status == FixStatus.FAILED)
    skipped_count = sum(1 for r in results if r.status == FixStatus.SKIPPED)
    
    console.print(f"\n{'='*80}")
    console.print(f"[bold]Results:[/bold]")
    console.print(f"  [green]✓ Success:[/green] {success_count}")
    console.print(f"  [red]✗ Failed:[/red] {failed_count}")
    console.print(f"  [yellow]⏭ Skipped:[/yellow] {skipped_count}")
    console.print(f"{'='*80}")
    
    # Show failed fixes
    if failed_count > 0:
        console.print("\n[red]Failed fixes:[/red]")
        for result in results:
            if result.status == FixStatus.FAILED:
                console.print(f"  • {result.fix.description}: {result.message}")


def main():
    """Main entry point for fix CLI."""
    fix()


# Alias for import in main CLI
fix_cli = fix


if __name__ == '__main__':
    main()

