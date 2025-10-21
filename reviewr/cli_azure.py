"""
Azure DevOps CLI commands for reviewr.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional
import click
from rich.console import Console

from .integrations.azure_devops import (
    AzureDevOpsIntegration,
    AzureDevOpsComment,
    AzureDevOpsVote,
    review_pull_request
)
from .config import ConfigLoader
from .providers import ReviewType

console = Console()


@click.group(name='azure')
def azure_cli():
    """Azure DevOps integration commands."""
    pass


@azure_cli.command(name='review')
@click.option('--pr-id', type=int, help='Pull request ID (auto-detected from Azure Pipelines if not provided)')
@click.option('--pat', help='Personal Access Token (defaults to AZURE_DEVOPS_PAT env var)')
@click.option('--organization', help='Organization name (auto-detected from git if not provided)')
@click.option('--project', help='Project name (auto-detected from git if not provided)')
@click.option('--repository', help='Repository name (auto-detected from git if not provided)')
@click.option('--auto-approve', is_flag=True, help='Automatically approve PR if no critical/high issues')
@click.option('--no-inline-comments', is_flag=True, help='Skip posting inline comments')
@click.option('--work-item', type=int, help='Link work item to PR')
@click.argument('path', type=click.Path(exists=True), default='.')
def review_command(
    pr_id: Optional[int],
    pat: Optional[str],
    organization: Optional[str],
    project: Optional[str],
    repository: Optional[str],
    auto_approve: bool,
    no_inline_comments: bool,
    work_item: Optional[int],
    path: str
):
    """
    Review a pull request and post results to Azure DevOps.
    
    This command runs a code review and posts the findings as comments on the PR.
    
    Examples:
        # Review current PR (auto-detected from Azure Pipelines)
        reviewr azure review
        
        # Review specific PR
        reviewr azure review --pr-id 123
        
        # Review with auto-approval
        reviewr azure review --auto-approve
        
        # Link work item
        reviewr azure review --work-item 456
    """
    try:
        # Initialize integration
        integration = AzureDevOpsIntegration(
            pat=pat,
            organization=organization,
            project=project,
            repository=repository
        )
        
        # Get PR ID
        if pr_id is None:
            pr_id = integration.get_pr_id()
            if pr_id is None:
                console.print("[red]Error:[/red] Could not detect PR ID. Provide --pr-id or run in Azure Pipelines.")
                sys.exit(1)
        
        console.print(f"[cyan]Reviewing PR #{pr_id}...[/cyan]")
        
        # Run review
        from .cli import _run_review
        from .config import ReviewrConfig
        
        config = ReviewrConfig()
        
        # Run the review
        result = asyncio.run(_run_review(
            config=config,
            path=path,
            review_types=[ReviewType.SECURITY, ReviewType.CORRECTNESS, ReviewType.MAINTAINABILITY],
            language=None,
            include_patterns=[],
            exclude_patterns=[],
            verbose=1,
            use_cache=True,
            use_local_analysis=True,
            local_only=False
        ))
        
        console.print(f"[green]✓[/green] Review complete: {len(result.findings)} findings")
        
        # Post to Azure DevOps
        console.print("[cyan]Posting results to Azure DevOps...[/cyan]")
        
        summary = review_pull_request(
            pr_id=pr_id,
            findings=result.findings,
            auto_approve=auto_approve,
            post_inline=not no_inline_comments,
            pat=pat,
            organization=organization,
            project=project,
            repository=repository
        )
        
        console.print(f"[green]✓[/green] Posted summary comment")
        if summary['inline_comments'] > 0:
            console.print(f"[green]✓[/green] Posted {summary['inline_comments']} inline comments")
        if summary['vote_set']:
            console.print(f"[green]✓[/green] Approved PR (no critical/high issues)")
        
        # Link work item if requested
        if work_item:
            console.print(f"[cyan]Linking work item #{work_item}...[/cyan]")
            integration.link_work_item(pr_id, work_item)
            console.print(f"[green]✓[/green] Linked work item #{work_item}")
        
        # Update build status
        commit_id = result.provider_stats.get('commit_id')
        if commit_id:
            has_critical = any(f.get('severity', '').lower() in ['critical', 'high'] for f in result.findings)
            state = 'failed' if has_critical else 'succeeded'
            description = f"reviewr: {len(result.findings)} findings"
            
            integration.update_build_status(commit_id, state, description)
            console.print(f"[green]✓[/green] Updated build status: {state}")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@azure_cli.command(name='setup')
@click.option('--pat', help='Personal Access Token')
@click.option('--organization', help='Organization name')
@click.option('--project', help='Project name')
@click.option('--repository', help='Repository name')
def setup_command(
    pat: Optional[str],
    organization: Optional[str],
    project: Optional[str],
    repository: Optional[str]
):
    """
    Set up Azure DevOps integration.
    
    Configure Azure DevOps credentials and test the connection.
    
    Examples:
        reviewr azure setup --pat YOUR_PAT --organization myorg --project myproject --repository myrepo
    """
    console.print("[bold cyan]Azure DevOps Integration Setup[/bold cyan]\n")
    
    if not pat:
        console.print("[red]Error:[/red] --pat is required")
        console.print("\nTo create a Personal Access Token:")
        console.print("1. Go to https://dev.azure.com/{organization}/_usersSettings/tokens")
        console.print("2. Click 'New Token'")
        console.print("3. Select scopes:")
        console.print("   - Code (Read & Write)")
        console.print("   - Pull Request Threads (Read & Write)")
        console.print("   - Build (Read & Execute)")
        console.print("4. Copy the token")
        sys.exit(1)
    
    try:
        # Test connection
        console.print("[cyan]Testing Azure DevOps connection...[/cyan]")
        
        integration = AzureDevOpsIntegration(
            pat=pat,
            organization=organization,
            project=project,
            repository=repository
        )
        
        console.print("[green]✓[/green] Connection successful!")
        console.print(f"\nConfiguration:")
        console.print(f"  Organization: {integration.organization}")
        console.print(f"  Project: {integration.project}")
        console.print(f"  Repository: {integration.repository}")
        console.print(f"  Server: {integration.server_url}")
        
        console.print("\n[bold]Environment Variables:[/bold]")
        console.print(f"  export AZURE_DEVOPS_PAT='{pat}'")
        console.print(f"  export AZURE_DEVOPS_ORG='{integration.organization}'")
        console.print(f"  export AZURE_DEVOPS_PROJECT='{integration.project}'")
        console.print(f"  export AZURE_DEVOPS_REPO='{integration.repository}'")
        
        console.print("\n[bold]Azure Pipelines YAML:[/bold]")
        console.print("""
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.9'
  
  - script: |
      pip install reviewr
    displayName: 'Install reviewr'
  
  - script: |
      reviewr azure review --auto-approve
    displayName: 'Code Review'
    env:
      AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
""")
        
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Add the environment variables to your shell profile")
        console.print("2. Add AZURE_DEVOPS_PAT as a secret variable in Azure Pipelines")
        console.print("3. Add the YAML configuration to azure-pipelines.yml")
        console.print("4. Test with: reviewr azure review --pr-id <PR_ID>")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        sys.exit(1)


@azure_cli.command(name='status')
@click.option('--commit-id', required=True, help='Commit SHA')
@click.option('--state', type=click.Choice(['succeeded', 'failed', 'pending', 'error']),
              required=True, help='Build status')
@click.option('--description', required=True, help='Status description')
@click.option('--context', default='reviewr', help='Status context (default: reviewr)')
@click.option('--pat', help='Personal Access Token (defaults to AZURE_DEVOPS_PAT env var)')
@click.option('--organization', help='Organization name')
@click.option('--project', help='Project name')
@click.option('--repository', help='Repository name')
def status_command(
    commit_id: str,
    state: str,
    description: str,
    context: str,
    pat: Optional[str],
    organization: Optional[str],
    project: Optional[str],
    repository: Optional[str]
):
    """
    Update build status for a commit.
    
    Examples:
        reviewr azure status --commit-id abc123 --state succeeded --description "Review passed"
        reviewr azure status --commit-id abc123 --state failed --description "Critical issues found"
    """
    try:
        integration = AzureDevOpsIntegration(
            pat=pat,
            organization=organization,
            project=project,
            repository=repository
        )
        
        console.print(f"[cyan]Updating build status for {commit_id[:8]}...[/cyan]")
        
        integration.update_build_status(commit_id, state, description, context)
        
        console.print(f"[green]✓[/green] Build status updated: {state}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@azure_cli.command(name='link-work-item')
@click.option('--pr-id', type=int, required=True, help='Pull request ID')
@click.option('--work-item-id', type=int, required=True, help='Work item ID')
@click.option('--pat', help='Personal Access Token (defaults to AZURE_DEVOPS_PAT env var)')
@click.option('--organization', help='Organization name')
@click.option('--project', help='Project name')
@click.option('--repository', help='Repository name')
def link_work_item_command(
    pr_id: int,
    work_item_id: int,
    pat: Optional[str],
    organization: Optional[str],
    project: Optional[str],
    repository: Optional[str]
):
    """
    Link a work item to a pull request.
    
    Examples:
        reviewr azure link-work-item --pr-id 123 --work-item-id 456
    """
    try:
        integration = AzureDevOpsIntegration(
            pat=pat,
            organization=organization,
            project=project,
            repository=repository
        )
        
        console.print(f"[cyan]Linking work item #{work_item_id} to PR #{pr_id}...[/cyan]")
        
        integration.link_work_item(pr_id, work_item_id)
        
        console.print(f"[green]✓[/green] Work item linked successfully")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    azure_cli()

