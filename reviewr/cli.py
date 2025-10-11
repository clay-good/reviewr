"""Main CLI interface for reviewr."""

import sys
import asyncio
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from .config import ConfigLoader, ReviewrConfig
from .config.defaults import DEFAULT_CONFIG_TEMPLATE
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .utils.formatters import TerminalFormatter, MarkdownFormatter

console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']), 
              help='LLM provider to use')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--output', '-o', type=click.Choice(['sarif', 'markdown', 'both']),
              default='both', help='Output format (default: both sarif and markdown files)')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], provider: Optional[str], 
        verbose: int, no_cache: bool, output: str) -> None:
    """reviewr - AI-powered code review CLI tool."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['provider_override'] = provider
    ctx.obj['verbose'] = verbose
    ctx.obj['no_cache'] = no_cache
    ctx.obj['output_format'] = output


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--security', is_flag=True, help='Security review: vulnerabilities, injections, auth issues')
@click.option('--performance', is_flag=True, help='Performance review: inefficient algorithms, bottlenecks')
@click.option('--correctness', is_flag=True, help='Correctness review: logic errors, edge cases')
@click.option('--maintainability', is_flag=True, help='Maintainability review: clarity, documentation')
@click.option('--architecture', is_flag=True, help='Architecture review: design patterns, SOLID principles')
@click.option('--standards', is_flag=True, help='Standards review: idioms, conventions, style')
@click.option('--explain', is_flag=True, help='Explain: comprehensive code explanation and overview')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types (except explain)')
@click.option('--language', '-l', help='Explicitly specify language (auto-detected if not provided)')
@click.option('--include', multiple=True, help='File patterns to include')
@click.option('--exclude', multiple=True, help='File patterns to exclude')
@click.pass_context
def review(ctx: click.Context, path: str, security: bool, performance: bool,
           correctness: bool, maintainability: bool, architecture: bool,
           standards: bool, explain: bool, all_types: bool, language: Optional[str],
           include: tuple, exclude: tuple) -> None:
    """Review code at the specified path."""
    try:
        # Load configuration
        loader = ConfigLoader()
        cli_overrides = {}
        
        if ctx.obj['provider_override']:
            cli_overrides['default_provider'] = ctx.obj['provider_override']
        
        if ctx.obj['no_cache']:
            cli_overrides['cache'] = {'enabled': False}
        
        config = loader.load(
            config_path=ctx.obj['config_path'],
            cli_overrides=cli_overrides
        )
        
        # Determine review types
        review_types = []
        if all_types:
            # All types except explain (explain is opt-in only)
            review_types = [rt for rt in ReviewType if rt != ReviewType.EXPLAIN]
        else:
            if security:
                review_types.append(ReviewType.SECURITY)
            if performance:
                review_types.append(ReviewType.PERFORMANCE)
            if correctness:
                review_types.append(ReviewType.CORRECTNESS)
            if maintainability:
                review_types.append(ReviewType.MAINTAINABILITY)
            if architecture:
                review_types.append(ReviewType.ARCHITECTURE)
            if standards:
                review_types.append(ReviewType.STANDARDS)
            if explain:
                review_types.append(ReviewType.EXPLAIN)
        
        # Use default review types if none specified
        if not review_types:
            review_types = [ReviewType(rt) for rt in config.review.default_types]
        
        if ctx.obj['verbose']:
            console.print(f"[blue]Review types:[/blue] {', '.join(rt.value for rt in review_types)}")
            console.print(f"[blue]Provider:[/blue] {config.default_provider}")
        
        # Run review
        result = asyncio.run(_run_review(
            config=config,
            path=path,
            review_types=review_types,
            language=language,
            include_patterns=list(include),
            exclude_patterns=list(exclude),
            verbose=ctx.obj['verbose']
        ))
        
        # Generate and save output files
        output_format = ctx.obj['output_format']

        # Always generate both SARIF and Markdown unless specifically limited
        if output_format in ['both', 'sarif']:
            # Generate SARIF output
            from .utils.formatters import SarifFormatter
            sarif_formatter = SarifFormatter()
            sarif_output = sarif_formatter.format_result(result)

            # Save SARIF file
            sarif_path = Path.cwd() / "reviewr-report.sarif"
            with open(sarif_path, 'w') as f:
                f.write(sarif_output)
            console.print(f"[green]✓[/green] SARIF report saved to: {sarif_path}")

        if output_format in ['both', 'markdown']:
            # Generate Markdown output
            markdown_formatter = MarkdownFormatter()
            markdown_output = markdown_formatter.format_result(result)

            # Save Markdown file
            markdown_path = Path.cwd() / "reviewr-report.md"
            with open(markdown_path, 'w') as f:
                f.write(markdown_output)
            console.print(f"[green]✓[/green] Markdown report saved to: {markdown_path}")

        # Show summary in terminal
        console.print(f"\n[bold cyan]Review Summary:[/bold cyan]")
        console.print(f"Files reviewed: {result.files_reviewed}")
        console.print(f"Total findings: {len(result.findings)}")

        # Show findings by severity
        by_severity = result.get_findings_by_severity()
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                console.print(f"{severity.title()}: {count}")

        if result.provider_stats:
            console.print(f"API requests: {result.provider_stats.get('request_count', 0)}")
            console.print(f"Tokens used: {result.provider_stats.get('total_input_tokens', 0) + result.provider_stats.get('total_output_tokens', 0)}")
        
        # Exit with error code if critical or high severity issues found
        if result.has_critical_issues():
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if ctx.obj['verbose'] > 1:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new configuration file."""
    config_path = Path.cwd() / ".reviewr.yml"
    
    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return
    
    try:
        with open(config_path, 'w') as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)
        
        console.print(f"[green]✓[/green] Created configuration file: {config_path}")
        console.print("\n[blue]Next steps:[/blue]")
        console.print("1. Set your API keys as environment variables:")
        console.print("   - ANTHROPIC_API_KEY for Claude")
        console.print("   - OPENAI_API_KEY for OpenAI")
        console.print("   - GOOGLE_API_KEY for Gemini")
        console.print("2. Edit .reviewr.yml to customize settings")
        console.print("3. Run: reviewr review <path>")
        
    except Exception as e:
        console.print(f"[red]Error creating config file:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def show_config(ctx: click.Context) -> None:
    """Show current configuration."""
    try:
        loader = ConfigLoader()
        config = loader.load(config_path=ctx.obj['config_path'])
        
        table = Table(title="reviewr Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Default Provider", config.default_provider)
        table.add_row("Review Types", ", ".join(config.review.default_types))
        table.add_row("Severity Threshold", config.review.severity_threshold.value)
        table.add_row("Cache Enabled", str(config.cache.enabled))
        table.add_row("Cache Directory", config.cache.directory)
        table.add_row("Chunking Strategy", config.chunking.strategy.value)
        table.add_row("Max Chunk Size", str(config.chunking.max_chunk_size))
        
        console.print(table)
        
        # Show configured providers
        console.print("\n[bold]Configured Providers:[/bold]")
        for name, provider_config in config.providers.items():
            has_key = "✓" if provider_config.api_key else "✗"
            console.print(f"  {has_key} {name}: {provider_config.model}")
        
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        sys.exit(1)


async def _run_review(
    config: ReviewrConfig,
    path: str,
    review_types: List[ReviewType],
    language: Optional[str],
    include_patterns: List[str],
    exclude_patterns: List[str],
    verbose: int
) -> 'ReviewResult':
    """Run the review process."""
    from .review.orchestrator import ReviewOrchestrator
    
    # Create provider
    provider_name = config.default_provider
    provider_config = config.providers.get(provider_name)
    
    if not provider_config:
        raise ValueError(f"Provider '{provider_name}' not configured")
    
    provider = ProviderFactory.create_provider(provider_name, provider_config)
    
    # Create orchestrator
    orchestrator = ReviewOrchestrator(
        provider=provider,
        config=config,
        verbose=verbose
    )
    
    # Run review
    result = await orchestrator.review_path(
        path=path,
        review_types=review_types,
        language=language,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )
    
    return result


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()

