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


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--security', is_flag=True, help='Security review: vulnerabilities, injections, auth issues')
@click.option('--performance', is_flag=True, help='Performance review: inefficient algorithms, bottlenecks')
@click.option('--correctness', is_flag=True, help='Correctness review: logic errors, edge cases')
@click.option('--maintainability', is_flag=True, help='Maintainability review: clarity, documentation')
@click.option('--architecture', is_flag=True, help='Architecture review: design patterns, SOLID principles')
@click.option('--standards', is_flag=True, help='Standards review: idioms, conventions, style')
@click.option('--explain', is_flag=True, help='Explain: comprehensive code explanation and overview')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types (except explain)')
@click.option('--output-format', type=click.Choice(['sarif', 'markdown', 'html', 'junit']),
              required=True, help='Output format (required)')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--language', '-l', help='Explicitly specify language (auto-detected if not provided)')
@click.option('--include', multiple=True, help='File patterns to include')
@click.option('--exclude', multiple=True, help='File patterns to exclude')
def cli(path: str, security: bool, performance: bool,
        correctness: bool, maintainability: bool, architecture: bool,
        standards: bool, explain: bool, all_types: bool, output_format: str,
        config: Optional[str], provider: Optional[str], verbose: int, no_cache: bool,
        language: Optional[str], include: tuple, exclude: tuple) -> None:
    """reviewr - AI-powered code review CLI tool.

    Review code at PATH with specified review types and output format.
    You must specify at least one review type (or --all) and an output format.

    Examples:
        reviewr /path/to/file.py --all --output-format sarif
        reviewr /path/to/file.py --security --performance --output-format markdown
        reviewr /path/to/project --explain --output-format html
    """
    try:
        # Load configuration
        loader = ConfigLoader()
        cli_overrides = {}

        if provider:
            cli_overrides['default_provider'] = provider

        if no_cache:
            cli_overrides['cache'] = {'enabled': False}

        cfg = loader.load(
            config_path=config,
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

        # Require at least one review type
        if not review_types:
            console.print("[red]Error:[/red] You must specify at least one review type (or use --all)")
            console.print("\nAvailable review types:")
            console.print("  --security        Security vulnerabilities")
            console.print("  --performance     Performance issues")
            console.print("  --correctness     Logic errors and bugs")
            console.print("  --maintainability Code maintainability")
            console.print("  --architecture    Architecture and design")
            console.print("  --standards       Coding standards")
            console.print("  --explain         Code explanation")
            console.print("  --all             All review types (except explain)")
            sys.exit(1)

        if verbose:
            console.print(f"[blue]Review types:[/blue] {', '.join(rt.value for rt in review_types)}")
            console.print(f"[blue]Provider:[/blue] {cfg.default_provider}")
            console.print(f"[blue]Output format:[/blue] {output_format}")

        # Run review
        result = asyncio.run(_run_review(
            config=cfg,
            path=path,
            review_types=review_types,
            language=language,
            include_patterns=list(include),
            exclude_patterns=list(exclude),
            verbose=verbose
        ))

        # Generate and save output file based on format
        if output_format == 'sarif':
            from .utils.formatters import SarifFormatter
            formatter = SarifFormatter()
            output = formatter.format_result(result)
            output_path = Path.cwd() / "reviewr-report.sarif"
            with open(output_path, 'w') as f:
                f.write(output)
            console.print(f"[green]✓[/green] SARIF report saved to: {output_path}")

        elif output_format == 'markdown':
            markdown_formatter = MarkdownFormatter()
            output = markdown_formatter.format_result(result)
            output_path = Path.cwd() / "reviewr-report.md"
            with open(output_path, 'w') as f:
                f.write(output)
            console.print(f"[green]✓[/green] Markdown report saved to: {output_path}")

        elif output_format == 'html':
            from .utils.formatters import HtmlFormatter
            formatter = HtmlFormatter()
            output = formatter.format_result(result)
            output_path = Path.cwd() / "reviewr-report.html"
            with open(output_path, 'w') as f:
                f.write(output)
            console.print(f"[green]✓[/green] HTML report saved to: {output_path}")

        elif output_format == 'junit':
            from .utils.formatters import JunitFormatter
            formatter = JunitFormatter()
            output = formatter.format_result(result)
            output_path = Path.cwd() / "reviewr-report.xml"
            with open(output_path, 'w') as f:
                f.write(output)
            console.print(f"[green]✓[/green] JUnit XML report saved to: {output_path}")

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
        if verbose > 1:
            import traceback
            console.print(traceback.format_exc())
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
    cli()


if __name__ == '__main__':
    main()

