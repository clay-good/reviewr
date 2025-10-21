import sys
import asyncio
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from .config import ConfigLoader, ReviewrConfig
from .config.defaults import DEFAULT_CONFIG_TEMPLATE_YAML, DEFAULT_CONFIG_TEMPLATE_TOML
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .utils.formatters import TerminalFormatter, MarkdownFormatter

console = Console()


@click.command()
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--security', is_flag=True, help='Security review: vulnerabilities, injections, auth issues')
@click.option('--performance', is_flag=True, help='Performance review: inefficient algorithms, bottlenecks')
@click.option('--correctness', is_flag=True, help='Correctness review: logic errors, edge cases')
@click.option('--maintainability', is_flag=True, help='Maintainability review: clarity, documentation')
@click.option('--architecture', is_flag=True, help='Architecture review: design patterns, SOLID principles')
@click.option('--standards', is_flag=True, help='Standards review: idioms, conventions, style')
@click.option('--explain', is_flag=True, help='Explain: comprehensive code explanation and overview')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types (except explain)')
@click.option('--output-format', type=click.Choice(['sarif', 'markdown', 'html', 'junit']),
              help='Output format (required for review)')
@click.option('--preset', help='Use a configuration preset (security, performance, quick, comprehensive, etc.)')
@click.option('--custom-presets-dir', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory containing custom preset files')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--no-local-analysis', is_flag=True, help='Disable local analysis (AST, complexity, etc.)')
@click.option('--local-only', is_flag=True, help='Use only local analysis, skip AI review')
@click.option('--rules', type=click.Path(exists=True), help='Path to custom rules file (YAML/JSON)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode: review findings one by one')
@click.option('--language', '-l', help='Explicitly specify language (auto-detected if not provided)')
@click.option('--include', multiple=True, help='File patterns to include')
@click.option('--exclude', multiple=True, help='File patterns to exclude')
@click.option('--init', is_flag=True, help='Initialize a new configuration file')
@click.option('--init-format', type=click.Choice(['yaml', 'toml']), default='yaml',
              help='Configuration file format for --init (default: yaml)')
# Advanced analyzer control flags
@click.option('--enable-security-analysis', is_flag=True, default=True, help='Enable security vulnerability detection (default: enabled)')
@click.option('--disable-security-analysis', is_flag=True, help='Disable security analysis')
@click.option('--enable-dataflow-analysis', is_flag=True, default=True, help='Enable data flow/taint tracking (default: enabled)')
@click.option('--disable-dataflow-analysis', is_flag=True, help='Disable data flow analysis')
@click.option('--enable-complexity-analysis', is_flag=True, default=True, help='Enable complexity metrics (default: enabled)')
@click.option('--disable-complexity-analysis', is_flag=True, help='Disable complexity analysis')
@click.option('--enable-type-analysis', is_flag=True, default=True, help='Enable type safety checks (default: enabled)')
@click.option('--disable-type-analysis', is_flag=True, help='Disable type safety analysis')
@click.option('--enable-performance-analysis', is_flag=True, default=True, help='Enable performance pattern detection (default: enabled)')
@click.option('--disable-performance-analysis', is_flag=True, help='Disable performance analysis')
@click.option('--enable-semantic-analysis', is_flag=True, default=True, help='Enable semantic code understanding (default: enabled)')
@click.option('--disable-semantic-analysis', is_flag=True, help='Disable semantic analysis')
@click.option('--min-severity', type=click.Choice(['info', 'low', 'medium', 'high', 'critical']),
              default='info', help='Minimum severity level to report (default: info)')
@click.option('--cyclomatic-threshold', type=int, default=10, help='Cyclomatic complexity threshold (default: 10)')
@click.option('--cognitive-threshold', type=int, default=15, help='Cognitive complexity threshold (default: 15)')
# Incremental/diff-based analysis options
@click.option('--diff', is_flag=True, help='Only review changed code (incremental analysis)')
@click.option('--diff-base', default='HEAD', help='Base reference for diff (default: HEAD)')
@click.option('--diff-target', help='Target reference for diff (default: working directory)')
@click.option('--diff-context', type=int, default=5, help='Lines of context around changes (default: 5)')
# Advanced security scanning options
@click.option('--security-scan', is_flag=True, help='Enable advanced security scanning (CVE, SAST, license)')
@click.option('--scan-vulnerabilities', is_flag=True, help='Scan dependencies for known vulnerabilities (CVE/OSV)')
@click.option('--scan-sast', is_flag=True, help='Run SAST (Static Application Security Testing) rules')
@click.option('--scan-licenses', is_flag=True, help='Check license compliance')
@click.option('--license-policy', type=click.Choice(['permissive', 'copyleft-friendly']),
              default='permissive', help='License policy to enforce (default: permissive)')
# Code metrics options
@click.option('--metrics', is_flag=True, help='Enable code metrics analysis (complexity, duplication, debt)')
@click.option('--metrics-complexity', is_flag=True, help='Analyze code complexity metrics')
@click.option('--metrics-duplication', is_flag=True, help='Detect code duplication')
@click.option('--metrics-debt', is_flag=True, help='Estimate technical debt')
@click.option('--min-duplicate-lines', type=int, default=6, help='Minimum lines for duplicate detection (default: 6)')
# Slack integration options
@click.option('--slack', is_flag=True, help='Post review summary to Slack')
@click.option('--slack-channel', help='Slack channel to post to (overrides env var)')
@click.option('--slack-critical-only', is_flag=True, help='Only post to Slack if critical issues found')
def cli(path: Optional[str], security: bool, performance: bool,
        correctness: bool, maintainability: bool, architecture: bool,
        standards: bool, explain: bool, all_types: bool, output_format: Optional[str],
        preset: Optional[str], custom_presets_dir: Optional[Path],
        config: Optional[str], provider: Optional[str], verbose: int, no_cache: bool,
        no_local_analysis: bool, local_only: bool, rules: Optional[str], interactive: bool, language: Optional[str],
        include: tuple, exclude: tuple, init: bool, init_format: str,
        enable_security_analysis: bool, disable_security_analysis: bool,
        enable_dataflow_analysis: bool, disable_dataflow_analysis: bool,
        enable_complexity_analysis: bool, disable_complexity_analysis: bool,
        enable_type_analysis: bool, disable_type_analysis: bool,
        enable_performance_analysis: bool, disable_performance_analysis: bool,
        enable_semantic_analysis: bool, disable_semantic_analysis: bool,
        min_severity: str, cyclomatic_threshold: int, cognitive_threshold: int,
        diff: bool, diff_base: str, diff_target: Optional[str], diff_context: int,
        security_scan: bool, scan_vulnerabilities: bool, scan_sast: bool,
        scan_licenses: bool, license_policy: str,
        metrics: bool, metrics_complexity: bool, metrics_duplication: bool,
        metrics_debt: bool, min_duplicate_lines: int,
        slack: bool, slack_channel: Optional[str], slack_critical_only: bool) -> None:
    """reviewr - AI-powered code review CLI tool.

    Review code at PATH with specified review types and output format.
    You must specify at least one review type (or --all) and an output format.

    Examples:
        reviewr /path/to/file.py --all --output-format sarif
        reviewr /path/to/file.py --security --performance --output-format markdown
        reviewr /path/to/project --explain --output-format html
        reviewr --init                    # Initialize config file
        reviewr --init --init-format toml # Initialize TOML config
    """
    # Handle init command
    if init:
        _handle_init_command(init_format)
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

    try:
        # Load configuration
        loader = ConfigLoader()
        cli_overrides = {}

        # Apply preset if specified
        if preset:
            from reviewr.config.presets import get_preset_manager
            manager = get_preset_manager(custom_presets_dir)
            preset_config = manager.get_preset(preset)

            if not preset_config:
                console.print(f"[red]Error:[/red] Unknown preset '{preset}'")
                console.print(f"\n💡 Use: [cyan]reviewr preset list[/cyan] to see available presets")
                sys.exit(1)

            console.print(f"[cyan]📋 Using preset:[/cyan] {preset} - {preset_config.description}")

            # Apply preset to cli_overrides
            preset_dict = manager.apply_preset(preset, {})

            # Map preset values to CLI overrides
            if not all_types and not any([security, performance, correctness, maintainability, architecture, standards, explain]):
                # Only apply preset review types if no explicit types specified
                preset_review_types = preset_dict.get('review_types', [])
                if 'security' in preset_review_types:
                    security = True
                if 'performance' in preset_review_types:
                    performance = True
                if 'correctness' in preset_review_types:
                    correctness = True
                if 'maintainability' in preset_review_types:
                    maintainability = True
                if 'architecture' in preset_review_types:
                    architecture = True
                if 'standards' in preset_review_types:
                    standards = True

            if not output_format:
                output_format = preset_dict.get('output_format', 'markdown')

            if 'min_severity' in preset_dict:
                min_severity = preset_dict['min_severity']

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

        # Create analyzer configuration from CLI flags
        from .analysis import AnalyzerConfig
        analyzer_config = AnalyzerConfig(
            enable_security=not disable_security_analysis,
            enable_dataflow=not disable_dataflow_analysis,
            enable_complexity=not disable_complexity_analysis,
            enable_type_safety=not disable_type_analysis,
            enable_performance=not disable_performance_analysis,
            enable_semantic=not disable_semantic_analysis,
            min_severity=min_severity,
            cyclomatic_threshold=cyclomatic_threshold,
            cognitive_threshold=cognitive_threshold
        )

        if verbose:
            enabled_analyzers = []
            if analyzer_config.enable_security:
                enabled_analyzers.append('security')
            if analyzer_config.enable_dataflow:
                enabled_analyzers.append('dataflow')
            if analyzer_config.enable_complexity:
                enabled_analyzers.append('complexity')
            if analyzer_config.enable_type_safety:
                enabled_analyzers.append('type')
            if analyzer_config.enable_performance:
                enabled_analyzers.append('performance')
            if analyzer_config.enable_semantic:
                enabled_analyzers.append('semantic')
            console.print(f"[blue]Local analyzers:[/blue] {', '.join(enabled_analyzers)}")
            console.print(f"[blue]Min severity:[/blue] {min_severity}")

        # Run review
        result = asyncio.run(_run_review(
            config=cfg,
            path=path,
            review_types=review_types,
            language=language,
            include_patterns=list(include),
            exclude_patterns=list(exclude),
            verbose=verbose,
            use_cache=not no_cache,
            use_local_analysis=not no_local_analysis,
            local_only=local_only,
            rules_engine=rules_engine,
            analyzer_config=analyzer_config,
            use_diff=diff,
            diff_base=diff_base,
            diff_target=diff_target,
            diff_context=diff_context,
            security_scan=security_scan,
            scan_vulnerabilities=scan_vulnerabilities,
            scan_sast=scan_sast,
            scan_licenses=scan_licenses,
            license_policy=license_policy,
            metrics=metrics,
            metrics_complexity=metrics_complexity,
            metrics_duplication=metrics_duplication,
            metrics_debt=metrics_debt,
            min_duplicate_lines=min_duplicate_lines
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

        # Post to Slack if requested
        if slack:
            try:
                from .integrations.slack import SlackConfig, post_review_summary, post_critical_alert

                console.print(f"\n[cyan]Posting to Slack...[/cyan]")

                config = SlackConfig.from_env()
                if slack_channel:
                    config.channel = slack_channel

                # Check for critical issues
                critical_findings = [f for f in result.findings if f.get('severity', '').lower() == 'critical']

                # Post critical alert if needed
                if critical_findings:
                    post_critical_alert(critical_findings, config)
                    console.print(f"[green]✓[/green] Posted critical alert to {config.channel}")

                # Post summary unless critical-only mode and no critical issues
                if not slack_critical_only or critical_findings:
                    post_review_summary(result, config)
                    console.print(f"[green]✓[/green] Posted review summary to {config.channel}")
                elif slack_critical_only:
                    console.print(f"[yellow]No critical issues, skipping Slack post[/yellow]")

            except ValueError as e:
                console.print(f"[yellow]Warning:[/yellow] Slack not configured: {e}")
                console.print("Run 'reviewr slack setup' to configure Slack integration")
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to post to Slack: {e}")

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
    verbose: int,
    use_cache: bool = True,
    use_local_analysis: bool = True,
    local_only: bool = False,
    rules_engine = None,
    analyzer_config = None,
    use_diff: bool = False,
    diff_base: str = "HEAD",
    diff_target: Optional[str] = None,
    diff_context: int = 5,
    security_scan: bool = False,
    scan_vulnerabilities: bool = False,
    scan_sast: bool = False,
    scan_licenses: bool = False,
    license_policy: str = "permissive",
    metrics: bool = False,
    metrics_complexity: bool = False,
    metrics_duplication: bool = False,
    metrics_debt: bool = False,
    min_duplicate_lines: int = 6
) -> 'ReviewResult':
    """Run the review process."""
    from .review.orchestrator import ReviewOrchestrator

    # Create provider (skip if local_only mode)
    provider = None
    if not local_only:
        provider_name = config.default_provider
        provider_config = config.providers.get(provider_name)

        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not configured")

        provider = ProviderFactory.create_provider(provider_name, provider_config)

    # Create diff analyzer if needed
    diff_analyzer = None
    if use_diff:
        from .analysis.diff_analyzer import DiffAnalyzer
        diff_analyzer = DiffAnalyzer(context_lines=diff_context)

    # Run advanced security scanning if requested
    security_findings = []
    if security_scan or scan_vulnerabilities or scan_sast or scan_licenses:
        security_findings = await _run_security_scan(
            path=path,
            scan_vulnerabilities=security_scan or scan_vulnerabilities,
            scan_sast=security_scan or scan_sast,
            scan_licenses=security_scan or scan_licenses,
            license_policy=license_policy,
            verbose=verbose
        )

    # Run code metrics analysis if requested
    metrics_findings = []
    if metrics or metrics_complexity or metrics_duplication or metrics_debt:
        metrics_findings = await _run_metrics_analysis(
            path=path,
            analyze_complexity=metrics or metrics_complexity,
            analyze_duplication=metrics or metrics_duplication,
            analyze_debt=metrics or metrics_debt,
            min_duplicate_lines=min_duplicate_lines,
            security_findings=security_findings,
            verbose=verbose
        )

    # Create orchestrator
    orchestrator = ReviewOrchestrator(
        provider=provider,
        config=config,
        verbose=verbose,
        use_cache=use_cache,
        use_local_analysis=use_local_analysis,
        rules_engine=rules_engine,
        analyzer_config=analyzer_config,
        diff_analyzer=diff_analyzer,
        diff_base=diff_base if use_diff else None,
        diff_target=diff_target if use_diff else None
    )

    # Run review
    result = await orchestrator.review_path(
        path=path,
        review_types=review_types,
        language=language,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )

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

    # Add security scan findings to result
    if security_findings:
        result.findings.extend(security_findings)
        result.provider_stats['security_scan_stats'] = {
            'findings': len(security_findings),
            'vulnerabilities': sum(1 for f in security_findings if f.get('type') == 'vulnerability'),
            'sast_issues': sum(1 for f in security_findings if f.get('type') == 'sast'),
            'license_issues': sum(1 for f in security_findings if f.get('type') == 'license')
        }

    # Add metrics findings to result
    if metrics_findings:
        result.findings.extend(metrics_findings)
        result.provider_stats['metrics_stats'] = {
            'findings': len(metrics_findings),
            'complexity_issues': sum(1 for f in metrics_findings if f.get('type') == 'complexity'),
            'duplication_issues': sum(1 for f in metrics_findings if f.get('type') == 'duplication'),
            'debt_issues': sum(1 for f in metrics_findings if f.get('type') == 'debt')
        }

    return result


def _handle_init_command(format: str) -> None:
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


async def _run_security_scan(
    path: Path,
    scan_vulnerabilities: bool,
    scan_sast: bool,
    scan_licenses: bool,
    license_policy: str,
    verbose: int
) -> List[dict]:
    """Run advanced security scanning."""
    from .security.vulnerability_scanner import VulnerabilityScanner
    from .security.dependency_checker import DependencyChecker
    from .security.license_checker import LicenseChecker
    from .security.sast_engine import SASTEngine

    findings = []

    if verbose:
        console.print("[cyan]Running advanced security scanning...[/cyan]")

    # Scan for vulnerabilities
    if scan_vulnerabilities:
        if verbose:
            console.print("  [cyan]→[/cyan] Scanning dependencies for vulnerabilities...")

        try:
            scanner = VulnerabilityScanner()

            # Check for dependency files
            for dep_file in ['requirements.txt', 'package.json', 'go.mod', 'Cargo.toml']:
                dep_path = path / dep_file if path.is_dir() else path.parent / dep_file
                if dep_path.exists():
                    if dep_file == 'requirements.txt':
                        vulns = scanner.scan_requirements_txt(dep_path)
                    elif dep_file == 'package.json':
                        vulns = scanner.scan_package_json(dep_path)
                    elif dep_file == 'go.mod':
                        vulns = scanner.scan_go_mod(dep_path)
                    elif dep_file == 'Cargo.toml':
                        vulns = scanner.scan_cargo_toml(dep_path)
                    else:
                        continue

                    for vuln in vulns:
                        findings.append({
                            'type': 'vulnerability',
                            'severity': vuln.severity.value,
                            'message': f"{vuln.id}: {vuln.summary}",
                            'details': vuln.details,
                            'package': vuln.package,
                            'version': vuln.version,
                            'fix': vuln.get_remediation(),
                            'file': str(dep_path),
                            'line': 1
                        })

            if verbose:
                console.print(f"    [green]✓[/green] Found {len([f for f in findings if f['type'] == 'vulnerability'])} vulnerabilities")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] Vulnerability scanning failed: {e}")

    # Run SAST
    if scan_sast:
        if verbose:
            console.print("  [cyan]→[/cyan] Running SAST (Static Application Security Testing)...")

        try:
            engine = SASTEngine()

            # Scan all code files
            code_files = []
            if path.is_file():
                code_files = [path]
            else:
                for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.php']:
                    code_files.extend(path.rglob(f'*{ext}'))

            for code_file in code_files:
                try:
                    code = code_file.read_text()
                    language = code_file.suffix[1:]  # Remove dot

                    sast_findings = engine.scan_code(code, language, code_file)

                    for finding in sast_findings:
                        findings.append({
                            'type': 'sast',
                            'severity': finding['severity'],
                            'message': f"{finding['rule_name']}: {finding['description']}",
                            'details': finding['fix_guidance'],
                            'cwe_id': finding['cwe_id'],
                            'cwe_url': finding['cwe_url'],
                            'owasp_category': finding['owasp_category'],
                            'file': finding['file'],
                            'line': finding['line']
                        })

                except Exception as e:
                    if verbose > 1:
                        console.print(f"    [yellow]⚠[/yellow] Failed to scan {code_file}: {e}")

            if verbose:
                console.print(f"    [green]✓[/green] Found {len([f for f in findings if f['type'] == 'sast'])} SAST issues")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] SAST scanning failed: {e}")

    # Check licenses
    if scan_licenses:
        if verbose:
            console.print("  [cyan]→[/cyan] Checking license compliance...")

        try:
            policy = LicenseChecker.PERMISSIVE_POLICY if license_policy == 'permissive' else LicenseChecker.COPYLEFT_FRIENDLY_POLICY
            checker = LicenseChecker(policy)

            # For now, just report that license checking is available
            # Full implementation would require querying package registries
            if verbose:
                console.print(f"    [green]✓[/green] License policy: {policy.name}")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] License checking failed: {e}")

    return findings


async def _run_metrics_analysis(
    path: Path,
    analyze_complexity: bool,
    analyze_duplication: bool,
    analyze_debt: bool,
    min_duplicate_lines: int,
    security_findings: List[dict],
    verbose: int
) -> List[dict]:
    """Run code metrics analysis."""
    from .metrics.complexity import ComplexityAnalyzer
    from .metrics.duplication import DuplicationDetector
    from .metrics.debt import TechnicalDebtEstimator

    findings = []

    if verbose:
        console.print("[cyan]Running code metrics analysis...[/cyan]")

    # Analyze complexity
    complexity_metrics = []
    if analyze_complexity:
        if verbose:
            console.print("  [cyan]→[/cyan] Analyzing code complexity...")

        try:
            analyzer = ComplexityAnalyzer()

            # Find all Python files
            if path.is_dir():
                python_files = list(path.rglob("*.py"))
            else:
                python_files = [path]

            # Analyze each file
            for file_path in python_files:
                if any(part.startswith(('test_', '__pycache__', '.'))
                      for part in file_path.parts):
                    continue

                metrics = analyzer.analyze_file(file_path)
                complexity_metrics.extend(metrics)

                # Create findings for complex functions
                for metric in metrics:
                    if metric.is_complex:
                        severity = 'high' if metric.cyclomatic > 20 else 'medium'
                        findings.append({
                            'type': 'complexity',
                            'severity': severity,
                            'title': f'High complexity in function {metric.name}',
                            'description': f'Cyclomatic: {metric.cyclomatic}, Cognitive: {metric.cognitive}',
                            'file': str(file_path),
                            'line': metric.line_start,
                            'recommendation': 'Refactor to reduce complexity'
                        })

                    if not metric.is_maintainable:
                        findings.append({
                            'type': 'complexity',
                            'severity': 'medium',
                            'title': f'Low maintainability in function {metric.name}',
                            'description': f'Maintainability index: {metric.maintainability_index:.1f}',
                            'file': str(file_path),
                            'line': metric.line_start,
                            'recommendation': 'Improve code quality and structure'
                        })

            if verbose and complexity_metrics:
                summary = analyzer.get_summary()
                console.print(f"    [green]✓[/green] Analyzed {summary['total_functions']} functions")
                console.print(f"      Complex functions: {summary['complex_functions']}")
                console.print(f"      Avg cyclomatic: {summary['avg_cyclomatic']:.1f}")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] Complexity analysis failed: {e}")

    # Detect duplication
    duplication_report = None
    if analyze_duplication:
        if verbose:
            console.print("  [cyan]→[/cyan] Detecting code duplication...")

        try:
            detector = DuplicationDetector(min_lines=min_duplicate_lines)

            if path.is_dir():
                duplication_report = detector.analyze_project(path)

                # Create findings for duplicates
                for duplicate in duplication_report.significant_duplicates:
                    severity = 'high' if duplicate.lines > 50 else 'medium'
                    findings.append({
                        'type': 'duplication',
                        'severity': severity,
                        'title': f'Code duplication detected ({duplicate.lines} lines)',
                        'description': f'Duplicate code between {duplicate.file1}:{duplicate.line1_start} and {duplicate.file2}:{duplicate.line2_start}',
                        'file': duplicate.file1,
                        'line': duplicate.line1_start,
                        'recommendation': 'Extract common code into reusable function'
                    })

                if verbose:
                    console.print(f"    [green]✓[/green] Duplication: {duplication_report.duplication_percentage:.1f}%")
                    console.print(f"      Significant duplicates: {len(duplication_report.significant_duplicates)}")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] Duplication detection failed: {e}")

    # Estimate technical debt
    if analyze_debt:
        if verbose:
            console.print("  [cyan]→[/cyan] Estimating technical debt...")

        try:
            estimator = TechnicalDebtEstimator()

            # Calculate total LOC
            total_loc = 0
            if path.is_dir():
                for py_file in path.rglob("*.py"):
                    if not any(part.startswith(('test_', '__pycache__', '.'))
                              for part in py_file.parts):
                        try:
                            total_loc += len(py_file.read_text().splitlines())
                        except:
                            pass

            debt_report = estimator.estimate_from_metrics(
                complexity_metrics=complexity_metrics,
                duplication_report=duplication_report,
                security_findings=security_findings,
                total_loc=total_loc
            )

            # Create findings for critical debt items
            for item in debt_report.critical_items:
                findings.append({
                    'type': 'debt',
                    'severity': 'critical',
                    'title': item.description,
                    'description': f'{item.impact}. Estimated remediation: {item.remediation_hours:.1f} hours',
                    'file': item.file_path,
                    'line': item.line_number,
                    'recommendation': item.recommendation
                })

            if verbose:
                console.print(f"    [green]✓[/green] Technical debt: {debt_report.total_debt_days:.1f} days")
                console.print(f"      SQALE rating: {debt_report.sqale_rating}")
                console.print(f"      Critical items: {len(debt_report.critical_items)}")

        except Exception as e:
            if verbose:
                console.print(f"    [yellow]⚠[/yellow] Debt estimation failed: {e}")

    return findings


@click.group(invoke_without_command=True)
@click.pass_context
def main_group(ctx):
    """reviewr - AI-powered code review CLI tool."""
    # If no subcommand is provided, run the main CLI
    if ctx.invoked_subcommand is None:
        ctx.invoke(cli, **{k: v for k, v in ctx.params.items() if k != 'help'})


# Add preset subcommand
from reviewr.cli_presets import preset_cli
main_group.add_command(preset_cli)

# Add policy subcommand
from reviewr.cli_policy import policy_group
main_group.add_command(policy_group)

# Add fix subcommand
try:
    from reviewr.cli_fix import fix_cli
    main_group.add_command(fix_cli)
except ImportError:
    pass

# Add dashboard subcommand
try:
    from reviewr.cli_dashboard import dashboard_cli
    main_group.add_command(dashboard_cli)
except ImportError:
    pass

# Add learning subcommand
try:
    from reviewr.cli_learning import learning_cli
    main_group.add_command(learning_cli)
except ImportError:
    pass

# Add bitbucket subcommand
try:
    from reviewr.cli_bitbucket import bitbucket_cli
    main_group.add_command(bitbucket_cli)
except ImportError:
    pass

# Add slack subcommand
try:
    from reviewr.cli_slack import slack_cli
    main_group.add_command(slack_cli)
except ImportError:
    pass

# Add azure subcommand
try:
    from reviewr.cli_azure import azure_cli
    main_group.add_command(azure_cli)
except ImportError:
    pass

# Add jenkins subcommand
try:
    from reviewr.cli_jenkins import jenkins_cli
    main_group.add_command(jenkins_cli)
except ImportError:
    pass

# Add circleci subcommand
try:
    from reviewr.cli_circleci import circleci_cli
    main_group.add_command(circleci_cli)
except ImportError:
    pass

# Add teams subcommand
try:
    from reviewr.cli_teams import teams_cli
    main_group.add_command(teams_cli)
except ImportError:
    pass

# Add email subcommand
try:
    from reviewr.cli_email import email_cli
    main_group.add_command(email_cli)
except ImportError:
    pass

# Add autofix subcommand
try:
    from reviewr.cli_autofix import autofix_cli
    main_group.add_command(autofix_cli)
except ImportError:
    pass


def main() -> None:
    """Main entry point."""
    # For backward compatibility, if called directly, run the review CLI
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ['preset', 'policy', 'fix', 'dashboard', 'learn', 'bitbucket', 'slack', 'azure', 'jenkins', 'circleci', 'teams', 'email', 'autofix']:
        main_group()
    else:
        cli()


if __name__ == '__main__':
    main()

