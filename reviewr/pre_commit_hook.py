
import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Optional
from rich.console import Console

from .config import ConfigLoader
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .utils.secrets_scanner import SecretsScanner

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='reviewr pre-commit hook')
    parser.add_argument('filenames', nargs='*', help='Files to review')
    parser.add_argument('--security-only', action='store_true', help='Only run security review')
    parser.add_argument('--secrets-only', action='store_true', help='Only scan for secrets')
    parser.add_argument('--fail-on', choices=['critical', 'high', 'medium', 'low'], 
                       default='high', help='Fail on this severity level or higher')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return parser.parse_args()


async def run_review(
    files: List[str],
    review_types: List[ReviewType],
    config_path: Optional[str],
    verbose: bool
) -> int:
    """Run review on files."""
    if not files:
        return 0
    
    try:
        # Load configuration
        loader = ConfigLoader()
        config = loader.load(config_path=config_path)
        
        # Create provider
        provider_name = config.default_provider
        provider_config = config.providers.get(provider_name)
        
        if not provider_config:
            console.print(f"[red]Error:[/red] Provider '{provider_name}' not configured")
            return 1
        
        if not provider_config.api_key:
            console.print(f"[yellow]Warning:[/yellow] No API key configured for {provider_name}")
            console.print("Set the appropriate environment variable:")
            console.print(f"  - ANTHROPIC_API_KEY for Claude")
            console.print(f"  - OPENAI_API_KEY for OpenAI")
            console.print(f"  - GOOGLE_API_KEY for Gemini")
            return 0  # Don't fail if no API key
        
        provider = ProviderFactory.create_provider(provider_name, provider_config)
        
        # Create orchestrator
        orchestrator = ReviewOrchestrator(
            provider=provider,
            config=config,
            verbose=1 if verbose else 0
        )
        
        # Review each file
        all_findings = []
        for file_path in files:
            if verbose:
                console.print(f"Reviewing {file_path}...")
            
            try:
                findings = await orchestrator._review_file(
                    Path(file_path),
                    review_types,
                    None
                )
                all_findings.extend(findings)
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]Warning:[/yellow] Error reviewing {file_path}: {e}")
        
        return len(all_findings)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1


def run_secrets_scan(files: List[str], verbose: bool) -> int:
    """Run secrets scan on files."""
    if not files:
        return 0
    
    scanner = SecretsScanner()
    total_secrets = 0
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = scanner.scan_content(content, file_path)
            
            if matches:
                console.print(f"\n[red]⚠️  Secrets detected in {file_path}:[/red]")
                for match in matches:
                    console.print(f"  Line {match.line_number}: {match.type.replace('_', ' ')} - {match.matched_text}")
                    if verbose:
                        console.print(f"    Context: {match.context}")
                total_secrets += len(matches)
        
        except Exception as e:
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] Error scanning {file_path}: {e}")
    
    if total_secrets > 0:
        console.print(f"\n[red]❌ Found {total_secrets} potential secret(s)[/red]")
        console.print("[yellow]Remove hardcoded secrets and use environment variables or a secrets management system.[/yellow]")
    
    return total_secrets


def main() -> int:
    """Main entry point for pre-commit hook."""
    args = parse_args()
    
    # Secrets-only mode
    if args.secrets_only:
        return 1 if run_secrets_scan(args.filenames, args.verbose) > 0 else 0
    
    # Determine review types
    if args.security_only:
        review_types = [ReviewType.SECURITY]
    else:
        # Default: security and correctness for pre-commit
        review_types = [ReviewType.SECURITY, ReviewType.CORRECTNESS]
    
    # Run review
    findings_count = asyncio.run(run_review(
        args.filenames,
        review_types,
        args.config,
        args.verbose
    ))
    
    if findings_count > 0:
        console.print(f"\n[yellow]⚠️  Found {findings_count} issue(s) in staged files[/yellow]")
        console.print("Review the findings and fix them before committing.")
        console.print("Or use 'git commit --no-verify' to skip this check.")
        return 1
    
    if args.verbose:
        console.print("[green]✓ No issues found[/green]")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

