import sys
import asyncio
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from .config import ConfigLoader, ReviewrConfig
<<<<<<< HEAD
from .config.defaults import DEFAULT_CONFIG_TEMPLATE_YAML, DEFAULT_CONFIG_TEMPLATE_TOML
=======
from .config.defaults import DEFAULT_CONFIG_TEMPLATE
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .utils.formatters import TerminalFormatter, MarkdownFormatter

console = Console()


@click.command()
<<<<<<< HEAD
@click.argument('path', type=click.Path(exists=True), required=False)
=======
@click.argument('path', type=click.Path(exists=True))
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
@click.option('--security', is_flag=True, help='Security review: vulnerabilities, injections, auth issues')
@click.option('--performance', is_flag=True, help='Performance review: inefficient algorithms, bottlenecks')
@click.option('--correctness', is_flag=True, help='Correctness review: logic errors, edge cases')
@click.option('--maintainability', is_flag=True, help='Maintainability review: clarity, documentation')
@click.option('--architecture', is_flag=True, help='Architecture review: design patterns, SOLID principles')
@click.option('--standards', is_flag=True, help='Standards review: idioms, conventions, style')
@click.option('--explain', is_flag=True, help='Explain: comprehensive code explanation and overview')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types (except explain)')
@click.option('--output-format', type=click.Choice(['sarif', 'markdown', 'html', 'junit']),
<<<<<<< HEAD
              help='Output format (required for review)')
=======
              required=True, help='Output format (required)')
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--no-cache', is_flag=True, help='Disable caching')
<<<<<<< HEAD
@click.option('--no-local-analysis', is_flag=True, help='Disable local analysis (AST, complexity, etc.)')
@click.option('--rules', type=click.Path(exists=True), help='Path to custom rules file (YAML/JSON)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode: review findings one by one')
@click.option('--language', '-l', help='Explicitly specify language (auto-detected if not provided)')
@click.option('--include', multiple=True, help='File patterns to include')
@click.option('--exclude', multiple=True, help='File patterns to exclude')
@click.option('--init', is_flag=True, help='Initialize a new configuration file')
@click.option('--init-format', type=click.Choice(['yaml', 'toml']), default='yaml',
              help='Configuration file format for --init (default: yaml)')
def cli(path: Optional[str], security: bool, performance: bool,
        correctness: bool, maintainability: bool, architecture: bool,
        standards: bool, explain: bool, all_types: bool, output_format: Optional[str],
        config: Optional[str], provider: Optional[str], verbose: int, no_cache: bool,
        no_local_analysis: bool, rules: Optional[str], interactive: bool, language: Optional[str],
        include: tuple, exclude: tuple, init: bool, init_format: str) -> None:
=======
@click.option('--language', '-l', help='Explicitly specify language (auto-detected if not provided)')
@click.option('--include', multiple=True, help='File patterns to include')
@click.option('--exclude', multiple=True, help='File patterns to exclude')
def cli(path: str, security: bool, performance: bool,
        correctness: bool, maintainability: bool, architecture: bool,
        standards: bool, explain: bool, all_types: bool, output_format: str,
        config: Optional[str], provider: Optional[str], verbose: int, no_cache: bool,
        language: Optional[str], include: tuple, exclude: tuple) -> None:
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
    """reviewr - AI-powered code review CLI tool.

    Review code at PATH with specified review types and output format.
    You must specify at least one review type (or --all) and an output format.

    Examples:
        reviewr /path/to/file.py --all --output-format sarif
        reviewr /path/to/file.py --security --performance --output-format markdown
        reviewr /path/to/project --explain --output-format html
<<<<<<< HEAD
        reviewr --init                    # Initialize config file
        reviewr --init --init-format toml # Initialize TOML config
    """
    # Handle init command
    if init:
        _handle_init(init_format)
        return

    # Require path for review
    if not path:
        console.print("[red]Error:[/red] PATH argument is required (or use --init to create config)")
        console.print("\nUsage: reviewr <path> --all --output-format sarif")
        console.print("   or: reviewr --init")
        sys.exit(1)

    # Require output format for review
    if not output_format:
        console.print("[red]Error:[/red] --output-format is required")
        console.print("\nAvailable formats: sarif, markdown, html, junit")
        sys.exit(1)
=======
    """
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
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

<<<<<<< HEAD
        # Load custom rules if provided
        rules_engine = None
        if rules:
            from .rules import RulesLoader
            try:
                rules_engine = RulesLoader.create_engine_from_file(rules)
                if verbose:
                    stats = rules_engine.get_statistics()
                    console.print(f"[blue]Custom rules:[/blue] {stats['enabled_rules']} enabled")
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to load custom rules: {e}")

=======
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
        # Run review
        result = asyncio.run(_run_review(
            config=cfg,
            path=path,
            review_types=review_types,
            language=language,
            include_patterns=list(include),
            exclude_patterns=list(exclude),
<<<<<<< HEAD
            verbose=verbose,
            use_cache=not no_cache,
            use_local_analysis=not no_local_analysis,
            rules_engine=rules_engine
        ))

        # Interactive mode: review findings one by one
        if interactive and result.findings:
            from .interactive import InteractiveReviewer, filter_findings_by_decisions

            reviewer = InteractiveReviewer(console)
            decisions = reviewer.review_findings(result.findings, show_code=True)

            # Filter findings based on decisions
            accepted_findings = reviewer.get_accepted_findings()
            result.findings = accepted_findings

            # Export decisions if requested
            decisions_path = Path.cwd() / "reviewr-decisions.json"
            reviewer.export_decisions(str(decisions_path))

=======
            verbose=verbose
        ))

>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
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
<<<<<<< HEAD

            # Show cache stats if available
            cache_stats = result.provider_stats.get('cache_stats')
            if cache_stats and not no_cache:
                console.print(f"\n[bold cyan]Cache Performance:[/bold cyan]")
                console.print(f"Cache hits: {cache_stats['hits']}")
                console.print(f"Cache misses: {cache_stats['misses']}")
                console.print(f"Hit rate: {cache_stats['hit_rate']}")

            # Show local analysis stats if available
            local_stats = result.provider_stats.get('local_analysis_stats')
            if local_stats and not no_local_analysis:
                console.print(f"\n[bold cyan]Local Analysis:[/bold cyan]")
                console.print(f"Files analyzed: {local_stats['files_analyzed']}")
                console.print(f"Issues found: {local_stats['findings']}")
                console.print(f"[dim]No API calls required for local analysis[/dim]")

            # Show custom rules stats if available
            custom_rules_stats = result.provider_stats.get('custom_rules_stats')
            if custom_rules_stats and rules:
                console.print(f"\n[bold cyan]Custom Rules:[/bold cyan]")
                console.print(f"Files analyzed: {custom_rules_stats['files_analyzed']}")
                console.print(f"Issues found: {custom_rules_stats['findings']}")
                console.print(f"[dim]No API calls required for custom rules[/dim]")

=======
        
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
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
<<<<<<< HEAD
    verbose: int,
    use_cache: bool = True,
    use_local_analysis: bool = True,
    rules_engine = None
) -> 'ReviewResult':
    """Run the review process."""
    from .review.orchestrator import ReviewOrchestrator

    # Create provider
    provider_name = config.default_provider
    provider_config = config.providers.get(provider_name)

    if not provider_config:
        raise ValueError(f"Provider '{provider_name}' not configured")

    provider = ProviderFactory.create_provider(provider_name, provider_config)

=======
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
    
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
    # Create orchestrator
    orchestrator = ReviewOrchestrator(
        provider=provider,
        config=config,
<<<<<<< HEAD
        verbose=verbose,
        use_cache=use_cache,
        use_local_analysis=use_local_analysis,
        rules_engine=rules_engine
    )

=======
        verbose=verbose
    )
    
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
    # Run review
    result = await orchestrator.review_path(
        path=path,
        review_types=review_types,
        language=language,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )
<<<<<<< HEAD

    # Add cache stats to result
    cache_stats = orchestrator.get_cache_stats()
    if cache_stats:
        result.provider_stats['cache_stats'] = cache_stats

    # Add local analysis stats to result
    local_stats = orchestrator.get_local_analysis_stats()
    if local_stats and local_stats['findings'] > 0:
        result.provider_stats['local_analysis_stats'] = local_stats

    # Add custom rules stats to result
    custom_rules_stats = orchestrator.get_custom_rules_stats()
    if custom_rules_stats and custom_rules_stats['findings'] > 0:
        result.provider_stats['custom_rules_stats'] = custom_rules_stats

    return result


def _handle_init(format: str) -> None:
    """Handle the init command."""
    if format == 'yaml':
        config_file = Path.cwd() / '.reviewr.yml'
        template = DEFAULT_CONFIG_TEMPLATE_YAML
    else:
        config_file = Path.cwd() / '.reviewr.toml'
        template = DEFAULT_CONFIG_TEMPLATE_TOML

    if config_file.exists():
        console.print(f"[yellow]Warning:[/yellow] {config_file.name} already exists")
        console.print("Remove it first or choose a different format")
        sys.exit(1)

    try:
        with open(config_file, 'w') as f:
            f.write(template)

        console.print(f"[green]✓[/green] Created {config_file.name}")
        console.print("\nNext steps:")
        console.print("1. Edit the configuration file to set your preferences")
        console.print("2. Set your API key environment variable:")
        console.print("   export ANTHROPIC_API_KEY='your-key'")
        console.print("3. Run a review:")
        console.print(f"   reviewr <path> --all --output-format sarif")

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to create config file: {e}")
        sys.exit(1)


=======
    
    return result


>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
def main() -> None:
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()

