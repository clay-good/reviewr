import sys
import asyncio
import os
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console

from .config import ConfigLoader
from .providers import ReviewType, ProviderFactory
from .review.orchestrator import ReviewOrchestrator
from .integrations.github import GitHubIntegration, GitHubReviewStatus

console = Console()


@click.command(name='github-pr')
@click.option('--pr-number', type=int, help='Pull request number (auto-detected if not provided)')
@click.option('--security', is_flag=True, help='Security review')
@click.option('--performance', is_flag=True, help='Performance review')
@click.option('--correctness', is_flag=True, help='Correctness review')
@click.option('--maintainability', is_flag=True, help='Maintainability review')
@click.option('--architecture', is_flag=True, help='Architecture review')
@click.option('--standards', is_flag=True, help='Standards review')
@click.option('--all', 'all_types', is_flag=True, help='Run all review types')
@click.option('--provider', '-p', type=click.Choice(['claude', 'openai', 'gemini']),
              help='LLM provider to use')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--no-local-analysis', is_flag=True, help='Disable local analysis')
@click.option('--approve-if-no-issues', is_flag=True, help='Approve PR if no critical/high issues found')
@click.option('--request-changes-on-critical', is_flag=True, help='Request changes if critical/high issues found')
@click.option('--comment-only', is_flag=True, help='Only post comments, do not approve/request changes')
@click.option('--repo', help='Repository in format owner/repo (auto-detected if not provided)')
@click.option('--token', help='GitHub token (defaults to GITHUB_TOKEN env var)')
def github_pr(
    pr_number: Optional[int],
    security: bool,
    performance: bool,
    correctness: bool,
    maintainability: bool,
    architecture: bool,
    standards: bool,
    all_types: bool,
    provider: Optional[str],
    config: Optional[str],
    verbose: int,
    no_cache: bool,
    no_local_analysis: bool,
    approve_if_no_issues: bool,
    request_changes_on_critical: bool,
    comment_only: bool,
    repo: Optional[str],
    token: Optional[str]
) -> None:
    """Review a GitHub Pull Request and post inline comments.
    
    This command reviews all files changed in a PR and posts inline comments
    for each finding. It can optionally approve the PR or request changes.
    
    Examples:
        # Review PR #123 with all review types
        reviewr github-pr --pr-number 123 --all
        
        # Review current PR (auto-detected) with security only
        reviewr github-pr --security
        
        # Review and approve if no issues
        reviewr github-pr --all --approve-if-no-issues
        
        # Review and request changes on critical issues
        reviewr github-pr --all --request-changes-on-critical
    """
    try:
        # Initialize GitHub integration
        gh = GitHubIntegration(token=token, repo=repo)
        
        # Get PR number
        if not pr_number:
            pr_number = gh.get_pr_number()
            if not pr_number:
                console.print("[red]Error:[/red] Could not detect PR number. Use --pr-number option.")
                sys.exit(1)
        
        console.print(f"[cyan]Reviewing PR #{pr_number} in {gh.repo}[/cyan]")
        
        # Get changed files
        pr_files = gh.get_pr_files(pr_number)
        changed_files = [f['filename'] for f in pr_files if f['status'] != 'removed']
        
        if not changed_files:
            console.print("[yellow]No files to review in this PR.[/yellow]")
            return
        
        console.print(f"[cyan]Found {len(changed_files)} changed file(s)[/cyan]")
        if verbose:
            for file in changed_files:
                console.print(f"  - {file}")
        
        # Determine review types
        review_types = []
        if all_types:
            review_types = [
                ReviewType.SECURITY,
                ReviewType.PERFORMANCE,
                ReviewType.CORRECTNESS,
                ReviewType.MAINTAINABILITY,
                ReviewType.ARCHITECTURE,
                ReviewType.STANDARDS
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
            if architecture:
                review_types.append(ReviewType.ARCHITECTURE)
            if standards:
                review_types.append(ReviewType.STANDARDS)
        
        if not review_types:
            console.print("[red]Error:[/red] No review types specified. Use --all or specify individual types.")
            sys.exit(1)
        
        # Load configuration
        config_loader = ConfigLoader()
        if config:
            cfg = config_loader.load_from_file(Path(config))
        else:
            cfg = config_loader.load_from_defaults()
        
        # Override provider if specified
        if provider:
            cfg.default_provider = provider
        
        # Create provider
        provider_instance = ProviderFactory.create_provider(
            cfg.default_provider,
            cfg.providers.get(cfg.default_provider)
        )
        
        # Create orchestrator
        orchestrator = ReviewOrchestrator(
            provider=provider_instance,
            verbose=verbose,
            use_cache=not no_cache,
            use_local_analysis=not no_local_analysis
        )
        
        # Review only changed files
        console.print(f"\n[bold]Running review...[/bold]")
        
        # Filter to only existing files
        files_to_review = []
        for file in changed_files:
            file_path = Path(file)
            if file_path.exists():
                files_to_review.append(file_path)
            elif verbose:
                console.print(f"[yellow]Skipping {file} (not found locally)[/yellow]")
        
        if not files_to_review:
            console.print("[yellow]No files found locally to review.[/yellow]")
            return
        
        # Run review
        result = asyncio.run(orchestrator.review_files(files_to_review, review_types))
        
        # Display summary
        console.print(f"\n[bold]Review Complete![/bold]")
        console.print(f"Files reviewed: {result.files_reviewed}")
        console.print(f"Total findings: {len(result.findings)}")
        
        # Show findings by severity
        by_severity = result.get_findings_by_severity()
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                color = {
                    'critical': 'red',
                    'high': 'orange1',
                    'medium': 'yellow',
                    'low': 'blue',
                    'info': 'cyan'
                }.get(severity, 'white')
                console.print(f"  [{color}]{severity.upper()}[/{color}]: {count}")
        
        # Post to GitHub
        if result.findings:
            console.print(f"\n[cyan]Posting {len(result.findings)} finding(s) to GitHub...[/cyan]")
            
            # Get commit SHA
            commit_sha = gh.get_commit_sha(pr_number)
            
            # Convert findings to comments
            comments = gh.format_findings_as_comments(result.findings, changed_files)
            
            if not comments:
                console.print("[yellow]No findings match changed files. Posting summary only.[/yellow]")
                summary = gh.format_summary(result)
                gh.create_issue_comment(pr_number, summary)
            else:
                # Determine review status
                if comment_only:
                    event = GitHubReviewStatus.COMMENT
                elif request_changes_on_critical and result.has_critical_issues():
                    event = GitHubReviewStatus.REQUEST_CHANGES
                elif approve_if_no_issues and not result.has_critical_issues():
                    event = GitHubReviewStatus.APPROVE
                else:
                    event = GitHubReviewStatus.COMMENT
                
                # Create review with comments
                summary = gh.format_summary(result)
                gh.create_review_comment(
                    pr_number=pr_number,
                    commit_id=commit_sha,
                    comments=comments,
                    body=summary,
                    event=event
                )
                
                console.print(f"[green]✓[/green] Posted review with {len(comments)} inline comment(s)")
                console.print(f"[green]✓[/green] Review status: {event.value}")
        else:
            console.print("\n[green]✓ No issues found![/green]")
            
            # Post summary
            summary = gh.format_summary(result)
            gh.create_issue_comment(pr_number, summary)
            
            # Approve if requested
            if approve_if_no_issues:
                commit_sha = gh.get_commit_sha(pr_number)
                gh.create_review_comment(
                    pr_number=pr_number,
                    commit_id=commit_sha,
                    comments=[],
                    body=summary,
                    event=GitHubReviewStatus.APPROVE
                )
                console.print("[green]✓ PR approved![/green]")
        
        console.print(f"\n[green]✓ GitHub review complete![/green]")
        console.print(f"View at: https://github.com/{gh.repo}/pull/{pr_number}")
        
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[yellow]Install requests: pip install requests[/yellow]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    github_pr()

