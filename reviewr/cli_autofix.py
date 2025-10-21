"""Enhanced CLI commands for AI-powered auto-fix functionality."""

import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

from .config import ConfigLoader
from .providers import ProviderFactory
from .autofix import (
    FixApplicator,
    AIFixGenerator,
    BatchFixProcessor,
    BatchResult,
    Fix,
    FixStatus
)

console = Console()


@click.group(name='autofix')
def autofix_cli():
    """AI-powered auto-fix for code issues."""
    pass


@autofix_cli.command('generate')
@click.argument('findings_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for generated fixes (JSON)')
@click.option('--language', '-l', help='Programming language (auto-detected if not specified)')
@click.option('--min-confidence', type=float, default=0.7,
              help='Minimum confidence threshold (0.0-1.0, default: 0.7)')
@click.option('--max-fixes', type=int, help='Maximum number of fixes to generate')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def generate_fixes(
    findings_file: str,
    output: Optional[str],
    language: Optional[str],
    min_confidence: float,
    max_fixes: Optional[int],
    config: Optional[str],
    provider: Optional[str],
    verbose: bool
) -> None:
    """
    Generate AI-powered fix suggestions from review findings.
    
    Examples:
        reviewr autofix generate results.json --output fixes.json
        reviewr autofix generate results.json --provider claude --min-confidence 0.8
        reviewr autofix generate results.json --language python --max-fixes 10
    """
    try:
        # Load configuration
        cfg = ConfigLoader.load_config(config)
        if provider:
            cfg.provider.name = provider
        if verbose:
            cfg.verbose = True
        
        # Load findings
        with open(findings_file, 'r') as f:
            findings_data = json.load(f)
        
        findings = findings_data.get('findings', [])
        
        if not findings:
            console.print("[yellow]No findings found in file[/yellow]")
            return
        
        console.print(f"[cyan]Loaded {len(findings)} findings from {findings_file}[/cyan]")
        
        # Auto-detect language if not specified
        if not language:
            language = _detect_language(findings)
            console.print(f"[cyan]Detected language: {language}[/cyan]")
        
        # Create AI fix generator
        provider_factory = ProviderFactory()
        ai_generator = AIFixGenerator(
            language=language,
            provider_factory=provider_factory,
            config=cfg
        )
        
        # Load file contents
        file_contents = _load_file_contents(findings)
        
        # Generate fixes
        console.print("[cyan]Generating AI-powered fixes...[/cyan]")
        
        # Convert findings to objects
        from types import SimpleNamespace
        finding_objects = [SimpleNamespace(**f) for f in findings]
        
        # Generate fixes
        fixes = ai_generator.generate_fixes(finding_objects, file_contents)
        
        # Filter by confidence
        fixes = [f for f in fixes if f.confidence >= min_confidence]
        
        # Limit number of fixes
        if max_fixes:
            fixes = fixes[:max_fixes]
        
        if not fixes:
            console.print("[yellow]No fixes generated[/yellow]")
            return
        
        # Display fixes
        _display_fixes(fixes)
        
        # Save to file if requested
        if output:
            fixes_data = {
                "fixes": [f.to_dict() for f in fixes],
                "total": len(fixes),
                "language": language,
                "min_confidence": min_confidence
            }
            
            with open(output, 'w') as f:
                json.dump(fixes_data, f, indent=2)
            
            console.print(f"\n[green]✓ Fixes saved to {output}[/green]")
        
        console.print(f"\n[green]✓ Generated {len(fixes)} fixes[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@autofix_cli.command('apply')
@click.argument('fixes_file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without applying changes')
@click.option('--interactive', '-i', is_flag=True, help='Ask for confirmation before each fix')
@click.option('--safe-only', is_flag=True, help='Only apply fixes marked as safe')
@click.option('--min-confidence', type=float, default=0.8,
              help='Minimum confidence threshold (0.0-1.0, default: 0.8)')
@click.option('--backup-dir', type=click.Path(), default='.reviewr_backups',
              help='Directory for backups (default: .reviewr_backups)')
@click.option('--no-validation', is_flag=True, help='Skip syntax validation after applying fixes')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def apply_fixes(
    fixes_file: str,
    dry_run: bool,
    interactive: bool,
    safe_only: bool,
    min_confidence: float,
    backup_dir: str,
    no_validation: bool,
    verbose: bool
) -> None:
    """
    Apply generated fixes to code files.
    
    Examples:
        reviewr autofix apply fixes.json --dry-run
        reviewr autofix apply fixes.json --interactive --safe-only
        reviewr autofix apply fixes.json --min-confidence 0.9
    """
    try:
        # Load fixes
        with open(fixes_file, 'r') as f:
            fixes_data = json.load(f)
        
        fixes_list = fixes_data.get('fixes', [])
        
        if not fixes_list:
            console.print("[yellow]No fixes found in file[/yellow]")
            return
        
        console.print(f"[cyan]Loaded {len(fixes_list)} fixes from {fixes_file}[/cyan]")
        
        # Convert to Fix objects
        from .autofix.base import FixCategory
        fixes = []
        for fix_data in fixes_list:
            fix = Fix(
                fix_id=fix_data['fix_id'],
                category=FixCategory(fix_data['category']),
                file_path=fix_data['file_path'],
                line_start=fix_data['line_start'],
                line_end=fix_data['line_end'],
                description=fix_data['description'],
                old_code=fix_data['old_code'],
                new_code=fix_data['new_code'],
                confidence=fix_data['confidence'],
                safe=fix_data['safe'],
                requires_validation=fix_data.get('requires_validation', True),
                finding_message=fix_data.get('finding_message'),
                explanation=fix_data.get('explanation')
            )
            fixes.append(fix)
        
        # Create applicator
        applicator = FixApplicator(
            backup_dir=backup_dir,
            dry_run=dry_run,
            validate_syntax=not no_validation,
            verbose=verbose
        )
        
        # Create batch processor
        confirmation_callback = _create_confirmation_callback() if interactive else None
        processor = BatchFixProcessor(
            applicator=applicator,
            interactive=interactive,
            confirmation_callback=confirmation_callback
        )
        
        # Process fixes
        console.print("[cyan]Applying fixes...[/cyan]")
        
        result = processor.process_fixes(
            fixes=fixes,
            safe_only=safe_only,
            min_confidence=min_confidence
        )
        
        # Display results
        _display_batch_result(result, dry_run)
        
        if result.successful > 0:
            console.print(f"\n[green]✓ Successfully applied {result.successful} fixes[/green]")
        
        if result.failed > 0:
            console.print(f"[red]✗ Failed to apply {result.failed} fixes[/red]")
        
        if result.skipped > 0:
            console.print(f"[yellow]⊘ Skipped {result.skipped} fixes[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@autofix_cli.command('review')
@click.argument('fixes_file', type=click.Path(exists=True))
@click.option('--show-diff', is_flag=True, help='Show diff for each fix')
@click.option('--filter-category', multiple=True, help='Filter by category')
@click.option('--min-confidence', type=float, default=0.0,
              help='Minimum confidence threshold (0.0-1.0)')
def review_fixes(
    fixes_file: str,
    show_diff: bool,
    filter_category: tuple,
    min_confidence: float
) -> None:
    """
    Review generated fixes interactively.
    
    Examples:
        reviewr autofix review fixes.json
        reviewr autofix review fixes.json --show-diff
        reviewr autofix review fixes.json --filter-category security --min-confidence 0.8
    """
    try:
        # Load fixes
        with open(fixes_file, 'r') as f:
            fixes_data = json.load(f)
        
        fixes_list = fixes_data.get('fixes', [])
        
        if not fixes_list:
            console.print("[yellow]No fixes found in file[/yellow]")
            return
        
        # Filter fixes
        filtered_fixes = []
        for fix in fixes_list:
            if fix['confidence'] < min_confidence:
                continue
            if filter_category and fix['category'] not in filter_category:
                continue
            filtered_fixes.append(fix)
        
        if not filtered_fixes:
            console.print("[yellow]No fixes match the filter criteria[/yellow]")
            return
        
        console.print(f"[cyan]Reviewing {len(filtered_fixes)} fixes[/cyan]\n")
        
        # Review each fix
        for i, fix in enumerate(filtered_fixes, 1):
            console.print(f"\n[bold cyan]Fix {i}/{len(filtered_fixes)}[/bold cyan]")
            console.print(f"File: {fix['file_path']}")
            console.print(f"Lines: {fix['line_start']}-{fix['line_end']}")
            console.print(f"Category: {fix['category']}")
            console.print(f"Confidence: {fix['confidence']:.2f}")
            console.print(f"Safe: {'Yes' if fix['safe'] else 'No'}")
            console.print(f"\nDescription: {fix['description']}")
            
            if fix.get('explanation'):
                console.print(f"Explanation: {fix['explanation']}")
            
            if show_diff:
                console.print("\n[bold]Old Code:[/bold]")
                syntax = Syntax(fix['old_code'], "python", theme="monokai", line_numbers=True)
                console.print(syntax)
                
                console.print("\n[bold]New Code:[/bold]")
                syntax = Syntax(fix['new_code'], "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            
            console.print("\n" + "─" * 80)
        
        console.print(f"\n[green]✓ Reviewed {len(filtered_fixes)} fixes[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _detect_language(findings: List[dict]) -> str:
    """Detect programming language from findings."""
    if not findings:
        return "python"
    
    # Check file extensions
    extensions = {}
    for finding in findings:
        file_path = finding.get('file_path', '')
        ext = Path(file_path).suffix.lower()
        extensions[ext] = extensions.get(ext, 0) + 1
    
    # Map extensions to languages
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
    }
    
    # Find most common extension
    if extensions:
        most_common_ext = max(extensions, key=extensions.get)
        return ext_map.get(most_common_ext, 'python')
    
    return 'python'


def _load_file_contents(findings: List[dict]) -> dict:
    """Load file contents for all findings."""
    file_contents = {}
    
    for finding in findings:
        file_path = finding.get('file_path', '')
        if file_path and file_path not in file_contents:
            try:
                with open(file_path, 'r') as f:
                    file_contents[file_path] = f.read()
            except Exception:
                pass
    
    return file_contents


def _display_fixes(fixes: List[Fix]) -> None:
    """Display generated fixes in a table."""
    table = Table(title="Generated Fixes")
    table.add_column("ID", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Lines", style="yellow")
    table.add_column("Category", style="magenta")
    table.add_column("Confidence", style="blue")
    table.add_column("Safe", style="red")
    
    for fix in fixes:
        table.add_row(
            fix.fix_id[:8],
            Path(fix.file_path).name,
            f"{fix.line_start}-{fix.line_end}",
            fix.category.value,
            f"{fix.confidence:.2f}",
            "✓" if fix.safe else "✗"
        )
    
    console.print(table)


def _display_batch_result(result: BatchResult, dry_run: bool) -> None:
    """Display batch processing results."""
    mode = "Dry Run" if dry_run else "Applied Fixes"
    
    table = Table(title=mode)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Fixes", str(result.total_fixes))
    table.add_row("Successful", str(result.successful))
    table.add_row("Failed", str(result.failed))
    table.add_row("Skipped", str(result.skipped))
    table.add_row("Success Rate", f"{result.success_rate:.1%}")
    
    console.print(table)


def _create_confirmation_callback():
    """Create a callback for interactive confirmation."""
    def confirm(fix: Fix) -> bool:
        console.print(f"\n[bold]Fix: {fix.description}[/bold]")
        console.print(f"File: {fix.file_path}")
        console.print(f"Lines: {fix.line_start}-{fix.line_end}")
        console.print(f"Confidence: {fix.confidence:.2f}")
        
        return Confirm.ask("Apply this fix?")
    
    return confirm

