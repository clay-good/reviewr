"""
CLI commands for Bitbucket integration.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console

from .config import ConfigLoader
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .integrations.bitbucket import BitbucketIntegration, BitbucketReviewStatus

console = Console()


@click.group(name='bitbucket')
def bitbucket_cli():
    """Bitbucket integration commands."""
    pass


@bitbucket_cli.command(name='review')
@click.option('--pr', type=int, help='Pull request number (auto-detected if not provided)')
@click.option('--workspace', help='Bitbucket workspace (auto-detected if not provided)')
@click.option('--repo-slug', help='Repository slug (auto-detected if not provided)')
@click.option('--username', help='Bitbucket username (defaults to BITBUCKET_USERNAME env var)')
@click.option('--app-password', help='Bitbucket app password (defaults to BITBUCKET_APP_PASSWORD env var)')
@click.option('--is-server', is_flag=True, help='Use Bitbucket Server/Data Center instead of Cloud')
@click.option('--server-url', help='Bitbucket Server URL (required if --is-server)')
@click.option('--security', is_flag=True, help='Security review')
@click.option('--performance', is_flag=True, help='Performance review')
@click.option('--correctness', is_flag=True, help='Correctness review')
@click.option('--maintainability', is_flag=True, help='Maintainability review')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types')
@click.option('--auto-approve', is_flag=True, help='Auto-approve PR if no critical issues')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']), help='LLM provider')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--diff', is_flag=True, help='Only review changed code (incremental analysis)')
@click.option('--diff-base', default='HEAD', help='Base reference for diff (default: HEAD)')
def review(
    pr: Optional[int],
    workspace: Optional[str],
    repo_slug: Optional[str],
    username: Optional[str],
    app_password: Optional[str],
    is_server: bool,
    server_url: Optional[str],
    security: bool,
    performance: bool,
    correctness: bool,
    maintainability: bool,
    all_types: bool,
    auto_approve: bool,
    config: Optional[str],
    provider: Optional[str],
    verbose: int,
    diff: bool,
    diff_base: str
):
    """Review a Bitbucket pull request."""
    try:
        # Initialize Bitbucket integration
        bb = BitbucketIntegration(
            username=username,
            app_password=app_password,
            workspace=workspace,
            repo_slug=repo_slug,
            is_server=is_server,
            server_url=server_url
        )
        
        # Get PR number
        pr_number = pr or bb.get_pr_number()
        if not pr_number:
            console.print("[red]Error: Could not determine PR number. Provide --pr option or run in Bitbucket Pipelines.[/red]")
            sys.exit(1)
        
        console.print(f"[blue]Reviewing Bitbucket PR #{pr_number}[/blue]")
        
        # Get PR files
        pr_files = bb.get_pr_files(pr_number)
        if not pr_files:
            console.print("[yellow]Warning: No files found in PR[/yellow]")
        else:
            console.print(f"[blue]Found {len(pr_files)} file(s) in PR[/blue]")
        
        # Determine review types
        review_types = []
        if all_types:
            review_types = [
                ReviewType.SECURITY,
                ReviewType.PERFORMANCE,
                ReviewType.CORRECTNESS,
                ReviewType.MAINTAINABILITY
            ]
        else:
            if security:
                review_types.append(ReviewType.SECURITY)
            if performance:
                review_types.append(ReviewType.PERFORMANCE)
            if correctness:
                review_types.append(ReviewType.CORRECTNESS)
            if maintainability:
                review_types.append(ReviewType.MAINTAINABILITY)
        
        if not review_types:
            review_types = [ReviewType.SECURITY, ReviewType.PERFORMANCE]
        
        # Load config
        loader = ConfigLoader()
        cfg = loader.load(config_path=config)
        
        # Override provider if specified
        if provider:
            cfg.default_provider = provider
        
        # Create provider
        provider_name = cfg.default_provider
        provider_config = cfg.providers.get(provider_name)
        
        if not provider_config:
            console.print(f"[red]Error: Provider '{provider_name}' not configured[/red]")
            sys.exit(1)
        
        llm_provider = ProviderFactory.create_provider(provider_name, provider_config)
        
        # Create diff analyzer if needed
        diff_analyzer = None
        if diff:
            from .analysis.diff_analyzer import DiffAnalyzer
            diff_analyzer = DiffAnalyzer(context_lines=5)
        
        # Create orchestrator
        orchestrator = ReviewOrchestrator(
            provider=llm_provider,
            config=cfg,
            verbose=verbose,
            use_cache=True,
            use_local_analysis=True,
            diff_analyzer=diff_analyzer,
            diff_base=diff_base if diff else None,
            diff_target=None
        )
        
        # Run review
        console.print("[blue]Running code review...[/blue]")
        result = asyncio.run(orchestrator.review_path(
            path='.',
            review_types=review_types,
            language=None
        ))
        
        console.print(f"[green]Review complete![/green]")
        console.print(f"Files reviewed: {result.files_reviewed}")
        console.print(f"Total findings: {len(result.findings)}")
        
        # Filter findings to only PR files
        if pr_files:
            filtered_findings = [f for f in result.findings if f.file in pr_files]
            console.print(f"Findings in PR files: {len(filtered_findings)}")
        else:
            filtered_findings = result.findings
        
        # Post review to Bitbucket
        if filtered_findings or auto_approve:
            console.print("[blue]Posting review to Bitbucket...[/blue]")
            
            # Create build status
            commit_sha = bb.get_commit_sha()
            if commit_sha:
                bb.create_build_status(
                    commit_sha=commit_sha,
                    state="INPROGRESS",
                    description="Running code review..."
                )
            
            # Post review
            success = bb.post_review(
                pr_number=pr_number,
                findings=filtered_findings,
                auto_approve=auto_approve
            )
            
            if success:
                console.print("[green]✓ Review posted successfully![/green]")
                
                # Update build status
                if commit_sha:
                    has_critical = any(f.severity in ('critical', 'high') for f in filtered_findings)
                    bb.create_build_status(
                        commit_sha=commit_sha,
                        state="FAILED" if has_critical else "SUCCESSFUL",
                        description=f"Found {len(filtered_findings)} issue(s)"
                    )
            else:
                console.print("[red]✗ Failed to post review[/red]")
                sys.exit(1)
        else:
            console.print("[green]✓ No issues found![/green]")
            
            # Update build status
            commit_sha = bb.get_commit_sha()
            if commit_sha:
                bb.create_build_status(
                    commit_sha=commit_sha,
                    state="SUCCESSFUL",
                    description="No issues found"
                )
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose > 1:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@bitbucket_cli.command(name='setup')
def setup():
    """Setup Bitbucket integration."""
    console.print("[bold]Bitbucket Integration Setup[/bold]\n")
    
    console.print("1. Create a Bitbucket App Password:")
    console.print("   - Go to https://bitbucket.org/account/settings/app-passwords/")
    console.print("   - Click 'Create app password'")
    console.print("   - Give it a label (e.g., 'reviewr')")
    console.print("   - Select permissions: Pull requests (Read, Write), Repositories (Read)")
    console.print("   - Click 'Create'\n")
    
    console.print("2. Set environment variables:")
    console.print("   export BITBUCKET_USERNAME='your-username'")
    console.print("   export BITBUCKET_APP_PASSWORD='your-app-password'\n")
    
    console.print("3. For Bitbucket Pipelines, add to bitbucket-pipelines.yml:")
    console.print("""
pipelines:
  pull-requests:
    '**':
      - step:
          name: Code Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --all --auto-approve
""")
    
    console.print("\n[green]Setup complete! Run 'reviewr bitbucket review --help' for usage.[/green]")


if __name__ == '__main__':
    bitbucket_cli()

