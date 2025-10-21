"""
Jenkins CLI commands for reviewr.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional
import click
from rich.console import Console

from .integrations.jenkins import (
    JenkinsIntegration,
    JenkinsConfig,
    JenkinsBuildStatus,
    review_build
)
from .config import ConfigLoader
from .providers import ReviewType

console = Console()


@click.group(name='jenkins')
def jenkins_cli():
    """Jenkins integration commands."""
    pass


@jenkins_cli.command(name='review')
@click.option('--url', help='Jenkins URL (defaults to JENKINS_URL env var)')
@click.option('--username', help='Jenkins username (defaults to JENKINS_USERNAME env var)')
@click.option('--api-token', help='Jenkins API token (defaults to JENKINS_API_TOKEN env var)')
@click.option('--job-name', help='Job name (defaults to JOB_NAME env var)')
@click.option('--build-number', type=int, help='Build number (defaults to BUILD_NUMBER env var)')
@click.option('--output', help='Output file for review report (JSON)')
@click.option('--no-description', is_flag=True, help='Skip setting build description')
@click.option('--no-badge', is_flag=True, help='Skip adding badge')
@click.argument('path', type=click.Path(exists=True), default='.')
def review_command(
    url: Optional[str],
    username: Optional[str],
    api_token: Optional[str],
    job_name: Optional[str],
    build_number: Optional[int],
    output: Optional[str],
    no_description: bool,
    no_badge: bool,
    path: str
):
    """
    Review code and update Jenkins build.
    
    This command runs a code review and updates the Jenkins build with results.
    
    Examples:
        # Review current build (auto-detected from Jenkins environment)
        reviewr jenkins review
        
        # Review specific build
        reviewr jenkins review --job-name my-job --build-number 123
        
        # Review and save report
        reviewr jenkins review --output review-report.json
    """
    try:
        # Initialize integration
        integration = JenkinsIntegration(
            url=url,
            username=username,
            api_token=api_token,
            job_name=job_name,
            build_number=build_number
        )
        
        console.print(f"[cyan]Reviewing code for Jenkins build...[/cyan]")
        if integration.job_name and integration.build_number:
            console.print(f"[cyan]Job: {integration.job_name} #{integration.build_number}[/cyan]")
        
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
        
        # Update Jenkins
        console.print("[cyan]Updating Jenkins build...[/cyan]")
        
        summary = review_build(
            findings=result.findings,
            output_file=output,
            set_description=not no_description,
            add_badge=not no_badge,
            url=url,
            username=username,
            api_token=api_token,
            job_name=job_name,
            build_number=build_number
        )
        
        if summary['description_set']:
            console.print(f"[green]✓[/green] Updated build description")
        if summary['badge_added']:
            console.print(f"[green]✓[/green] Added build badge")
        if summary['output_file']:
            console.print(f"[green]✓[/green] Saved report to {summary['output_file']}")
        
        # Exit with error if critical/high issues found
        has_critical = any(f.get('severity', '').lower() in ['critical', 'high'] for f in result.findings)
        if has_critical:
            console.print("[red]✗[/red] Critical or high severity issues found")
            sys.exit(1)
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@jenkins_cli.command(name='setup')
@click.option('--url', help='Jenkins URL')
@click.option('--username', help='Jenkins username')
@click.option('--api-token', help='Jenkins API token')
def setup_command(
    url: Optional[str],
    username: Optional[str],
    api_token: Optional[str]
):
    """
    Set up Jenkins integration.
    
    Configure Jenkins credentials and test the connection.
    
    Examples:
        reviewr jenkins setup --url https://jenkins.example.com --username admin --api-token YOUR_TOKEN
    """
    console.print("[bold cyan]Jenkins Integration Setup[/bold cyan]\n")
    
    if not url:
        console.print("[red]Error:[/red] --url is required")
        console.print("\nProvide your Jenkins URL:")
        console.print("  Example: https://jenkins.example.com")
        sys.exit(1)
    
    if not username or not api_token:
        console.print("[red]Error:[/red] --username and --api-token are required")
        console.print("\nTo create an API token:")
        console.print("1. Go to {url}/user/{username}/configure")
        console.print("2. Click 'Add new Token' under 'API Token'")
        console.print("3. Give it a name (e.g., 'reviewr')")
        console.print("4. Click 'Generate'")
        console.print("5. Copy the token")
        sys.exit(1)
    
    try:
        # Test connection
        console.print("[cyan]Testing Jenkins connection...[/cyan]")
        
        integration = JenkinsIntegration(
            url=url,
            username=username,
            api_token=api_token
        )
        
        # Try to get Jenkins version
        response = integration.headers
        console.print("[green]✓[/green] Connection successful!")
        console.print(f"\nConfiguration:")
        console.print(f"  URL: {integration.url}")
        console.print(f"  Username: {integration.username}")
        
        console.print("\n[bold]Environment Variables:[/bold]")
        console.print(f"  export JENKINS_URL='{url}'")
        console.print(f"  export JENKINS_USERNAME='{username}'")
        console.print(f"  export JENKINS_API_TOKEN='{api_token}'")
        
        console.print("\n[bold]Jenkinsfile (Declarative Pipeline):[/bold]")
        console.print("""
pipeline {
    agent any
    
    environment {
        JENKINS_URL = credentials('jenkins-url')
        JENKINS_USERNAME = credentials('jenkins-username')
        JENKINS_API_TOKEN = credentials('jenkins-api-token')
    }
    
    stages {
        stage('Code Review') {
            steps {
                sh 'pip install reviewr'
                sh 'reviewr jenkins review'
            }
        }
    }
}
""")
        
        console.print("\n[bold]Jenkinsfile (Scripted Pipeline):[/bold]")
        console.print("""
node {
    stage('Code Review') {
        sh 'pip install reviewr'
        sh 'reviewr jenkins review'
    }
}
""")
        
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Add the environment variables to your Jenkins credentials")
        console.print("2. Add the Jenkinsfile to your repository")
        console.print("3. Create a Jenkins pipeline job")
        console.print("4. Test with: reviewr jenkins review")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        sys.exit(1)


@jenkins_cli.command(name='set-description')
@click.option('--url', help='Jenkins URL (defaults to JENKINS_URL env var)')
@click.option('--username', help='Jenkins username (defaults to JENKINS_USERNAME env var)')
@click.option('--api-token', help='Jenkins API token (defaults to JENKINS_API_TOKEN env var)')
@click.option('--job-name', help='Job name (defaults to JOB_NAME env var)')
@click.option('--build-number', type=int, help='Build number (defaults to BUILD_NUMBER env var)')
@click.argument('description')
def set_description_command(
    url: Optional[str],
    username: Optional[str],
    api_token: Optional[str],
    job_name: Optional[str],
    build_number: Optional[int],
    description: str
):
    """
    Set build description.
    
    Examples:
        reviewr jenkins set-description "Code review passed"
        reviewr jenkins set-description "<strong>Review:</strong> 5 issues found"
    """
    try:
        integration = JenkinsIntegration(
            url=url,
            username=username,
            api_token=api_token,
            job_name=job_name,
            build_number=build_number
        )
        
        console.print(f"[cyan]Setting build description...[/cyan]")
        
        integration.set_build_description(description)
        
        console.print(f"[green]✓[/green] Build description updated")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@jenkins_cli.command(name='add-badge')
@click.option('--url', help='Jenkins URL (defaults to JENKINS_URL env var)')
@click.option('--username', help='Jenkins username (defaults to JENKINS_USERNAME env var)')
@click.option('--api-token', help='Jenkins API token (defaults to JENKINS_API_TOKEN env var)')
@click.option('--job-name', help='Job name (defaults to JOB_NAME env var)')
@click.option('--build-number', type=int, help='Build number (defaults to BUILD_NUMBER env var)')
@click.option('--color', type=click.Choice(['blue', 'green', 'yellow', 'red']), default='blue', help='Badge color')
@click.argument('text')
def add_badge_command(
    url: Optional[str],
    username: Optional[str],
    api_token: Optional[str],
    job_name: Optional[str],
    build_number: Optional[int],
    color: str,
    text: str
):
    """
    Add a badge to the build.
    
    Examples:
        reviewr jenkins add-badge "Review: Passed" --color green
        reviewr jenkins add-badge "Review: Issues Found" --color red
    """
    try:
        integration = JenkinsIntegration(
            url=url,
            username=username,
            api_token=api_token,
            job_name=job_name,
            build_number=build_number
        )
        
        console.print(f"[cyan]Adding badge to build...[/cyan]")
        
        integration.add_badge(text, color)
        
        console.print(f"[green]✓[/green] Badge added: {text}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    jenkins_cli()

