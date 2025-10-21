"""GitLab CLI integration for reviewr."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

from .config.loader import load_config
from .providers.factory import create_provider
from .providers.base import ReviewType
from .review.orchestrator import ReviewOrchestrator
from .integrations.gitlab import GitLabIntegration, GitLabReviewStatus


@click.command(name='gitlab-mr')
@click.option('--mr-iid', type=int, help='Merge request IID (auto-detected if not provided)')
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
@click.option('--post-comments', is_flag=True, default=True, help='Post inline comments (default: True)')
@click.option('--post-summary', is_flag=True, default=True, help='Post summary comment (default: True)')
@click.option('--approve-if-clean', is_flag=True, help='Approve MR if no critical/high issues found')
@click.option('--project-id', help='GitLab project ID (auto-detected if not provided)')
@click.option('--api-url', help='GitLab API URL (defaults to https://gitlab.com/api/v4)')
def gitlab_mr(
    mr_iid: Optional[int],
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
    post_comments: bool,
    post_summary: bool,
    approve_if_clean: bool,
    project_id: Optional[str],
    api_url: Optional[str]
):
    """
    Review a GitLab merge request and post findings as comments.
    
    This command reviews all files changed in a merge request and posts
    the findings as inline comments and a summary comment.
    
    Examples:
    
        # Review current MR (auto-detected in GitLab CI)
        reviewr-gitlab review --all
        
        # Review specific MR
        reviewr-gitlab review --mr-iid 123 --all
        
        # Review with specific types
        reviewr-gitlab review --mr-iid 123 --security --performance
        
        # Review and approve if clean
        reviewr-gitlab review --all --approve-if-clean
    """
    console = Console()
    
    # Validate review types
    if not any([security, performance, correctness, maintainability, architecture, standards, all_types]):
        console.print("[red]Error: Must specify at least one review type or --all[/red]")
        sys.exit(1)
    
    # Build review types list
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
    
    try:
        # Initialize GitLab integration
        gitlab = GitLabIntegration(project_id=project_id, api_url=api_url)
        
        # Get MR number
        if mr_iid is None:
            mr_iid = gitlab.get_mr_number()
            if mr_iid is None:
                console.print("[red]Error: Could not detect MR IID. Provide --mr-iid or run in GitLab CI.[/red]")
                sys.exit(1)
        
        console.print(f"[cyan]Reviewing GitLab MR #{mr_iid}...[/cyan]")
        
        # Get changed files
        mr_files = gitlab.get_mr_files(mr_iid)
        changed_files = [f['new_path'] for f in mr_files if f.get('new_path')]
        
        if not changed_files:
            console.print("[yellow]No files to review in this MR.[/yellow]")
            sys.exit(0)
        
        console.print(f"[cyan]Found {len(changed_files)} changed file(s)[/cyan]")
        
        # Load config
        reviewr_config = load_config(config)
        
        # Override provider if specified
        if provider:
            reviewr_config.provider.name = provider
        
        # Create provider
        llm_provider = create_provider(reviewr_config.provider)
        
        # Create orchestrator
        orchestrator = ReviewOrchestrator(
            provider=llm_provider,
            config=reviewr_config,
            verbose=verbose
        )
        
        # Review all changed files
        console.print("[cyan]Running code review...[/cyan]")
        
        async def review_files():
            all_findings = []
            files_reviewed = 0
            
            for file_path in changed_files:
                # Check if file exists (might be deleted)
                if not Path(file_path).exists():
                    if verbose:
                        console.print(f"[yellow]Skipping deleted file: {file_path}[/yellow]")
                    continue
                
                if verbose:
                    console.print(f"[cyan]Reviewing {file_path}...[/cyan]")
                
                findings = await orchestrator.review_file(
                    file_path=file_path,
                    review_types=review_types
                )
                
                all_findings.extend(findings)
                files_reviewed += 1
            
            # Create result object
            from .review.orchestrator import ReviewResult
            result = ReviewResult(
                findings=all_findings,
                files_reviewed=files_reviewed,
                total_chunks=0,
                provider_stats={}
            )
            
            return result
        
        # Run async review
        result = asyncio.run(review_files())
        
        console.print(f"[green]Review complete! Found {len(result.findings)} finding(s)[/green]")
        
        # Post comments if requested
        if post_comments and result.findings:
            console.print("[cyan]Posting inline comments...[/cyan]")
            comments = gitlab.format_findings_as_comments(result.findings, changed_files)
            
            if comments:
                try:
                    gitlab.create_discussion(mr_iid, comments)
                    console.print(f"[green]Posted {len(comments)} inline comment(s)[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to post some comments: {e}[/yellow]")
        
        # Post summary if requested
        if post_summary:
            console.print("[cyan]Posting summary comment...[/cyan]")
            summary = gitlab.format_summary(result)
            
            try:
                gitlab.create_mr_note(mr_iid, summary)
                console.print("[green]Posted summary comment[/green]")
            except Exception as e:
                console.print(f"[red]Error posting summary: {e}[/red]")
        
        # Approve if requested and no critical issues
        if approve_if_clean:
            if not result.has_critical_issues():
                console.print("[cyan]No critical/high issues found. Approving MR...[/cyan]")
                try:
                    gitlab.approve_mr(mr_iid)
                    console.print("[green]MR approved ✓[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to approve MR: {e}[/yellow]")
            else:
                console.print("[yellow]Critical/high issues found. Not approving MR.[/yellow]")
        
        # Exit with error code if critical issues found
        if result.has_critical_issues():
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for reviewr-gitlab command."""
    gitlab_mr()


if __name__ == '__main__':
    main()

