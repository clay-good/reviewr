"""
CircleCI CLI commands for reviewr.
"""

import os
import sys
import json
import click
from pathlib import Path
from typing import Optional

from reviewr.integrations.circleci import (
    CircleCIIntegration,
    CircleCIConfig,
    review_workflow
)


@click.group(name='circleci')
def circleci_cli():
    """CircleCI integration commands."""
    pass


@circleci_cli.command(name='review')
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--api-token', help='CircleCI API token (defaults to CIRCLE_TOKEN env var)')
@click.option('--project-slug', help='Project slug (format: vcs-slug/org-name/repo-name)')
@click.option('--workflow-id', help='Workflow ID (defaults to CIRCLE_WORKFLOW_ID env var)')
@click.option('--output', help='Output file for review report (JSON)')
@click.option('--preset', type=click.Choice(['balanced', 'strict', 'quick', 'security-focused']), 
              default='balanced', help='Review preset')
@click.option('--review-type', multiple=True, 
              type=click.Choice(['security', 'performance', 'correctness', 'maintainability', 'architecture', 'standards']),
              help='Review types to perform')
@click.option('--security-scan', is_flag=True, help='Run security scanning')
@click.option('--code-metrics', is_flag=True, help='Calculate code metrics')
def review_command(
    path: str,
    api_token: Optional[str],
    project_slug: Optional[str],
    workflow_id: Optional[str],
    output: Optional[str],
    preset: str,
    review_type: tuple,
    security_scan: bool,
    code_metrics: bool
):
    """
    Review code in CircleCI workflow.
    
    This command runs a code review and stores results as CircleCI artifacts.
    
    Examples:
        # Review current workflow (auto-detected from CircleCI environment)
        reviewr circleci review
        
        # Review specific workflow
        reviewr circleci review --workflow-id abc123
        
        # Review and save report
        reviewr circleci review --output review-report.json
        
        # Security-focused review
        reviewr circleci review --preset security-focused --security-scan
    """
    from reviewr.orchestrator import ReviewOrchestrator
    
    click.echo("🔍 Starting CircleCI code review...")
    click.echo()
    
    # Initialize orchestrator
    orchestrator = ReviewOrchestrator()
    
    # Build review options
    review_options = {
        'preset': preset,
        'security_scan': security_scan,
        'code_metrics': code_metrics
    }
    
    if review_type:
        review_options['review_types'] = list(review_type)
    
    # Run review
    click.echo(f"📂 Reviewing: {path}")
    click.echo(f"⚙️  Preset: {preset}")
    if review_type:
        click.echo(f"🎯 Review types: {', '.join(review_type)}")
    click.echo()
    
    try:
        # Run the review
        findings = orchestrator.review(path, **review_options)
        
        # Store results in CircleCI
        result = review_workflow(
            findings=findings,
            output_file=output or 'circleci-review-report.json',
            api_token=api_token,
            project_slug=project_slug,
            workflow_id=workflow_id
        )
        
        # Display summary
        click.echo("=" * 80)
        click.echo(result['summary'])
        click.echo("=" * 80)
        click.echo()
        
        if result['artifact_stored']:
            click.echo(f"✅ Report saved: {result['output_file']}")
            click.echo("   (Will be uploaded as CircleCI artifact)")
        
        click.echo()
        click.echo(f"Workflow ID: {result['workflow_id']}")
        
        # Exit with error if critical or high issues found
        critical_count = sum(1 for f in findings if f.get('severity') == 'critical')
        high_count = sum(1 for f in findings if f.get('severity') == 'high')
        
        if critical_count > 0 or high_count > 0:
            click.echo()
            click.echo("❌ Review failed - critical or high priority issues found")
            sys.exit(1)
        else:
            click.echo()
            click.echo("✅ Review passed!")
            sys.exit(0)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@circleci_cli.command(name='setup')
@click.option('--api-token', help='CircleCI API token')
@click.option('--project-slug', help='Project slug (format: vcs-slug/org-name/repo-name)')
def setup_command(api_token: Optional[str], project_slug: Optional[str]):
    """
    Set up CircleCI integration.
    
    This command helps configure and test the CircleCI integration.
    
    Examples:
        # Test connection with environment variables
        reviewr circleci setup
        
        # Test connection with explicit credentials
        reviewr circleci setup --api-token YOUR_TOKEN --project-slug gh/org/repo
    """
    click.echo("🔧 CircleCI Integration Setup")
    click.echo("=" * 80)
    click.echo()
    
    try:
        # Initialize integration
        integration = CircleCIIntegration(
            api_token=api_token,
            project_slug=project_slug
        )
        
        click.echo("✅ Configuration:")
        click.echo(f"   API Token: {'*' * 8}{integration.api_token[-4:] if integration.api_token else 'Not set'}")
        click.echo(f"   Project Slug: {integration.project_slug or 'Not set'}")
        click.echo(f"   Workflow ID: {integration.workflow_id or 'Not set'}")
        click.echo(f"   Job Number: {integration.job_number or 'Not set'}")
        click.echo()
        
        # Test API connection if workflow ID is available
        if integration.workflow_id:
            click.echo("🔍 Testing API connection...")
            workflow_info = integration.get_workflow_info()
            click.echo(f"✅ Connected to workflow: {workflow_info.get('name', 'Unknown')}")
            click.echo(f"   Status: {workflow_info.get('status', 'Unknown')}")
            click.echo()
        
        # Show environment variables
        click.echo("📋 CircleCI Environment Variables:")
        env_vars = [
            'CIRCLE_TOKEN',
            'CIRCLE_PROJECT_USERNAME',
            'CIRCLE_PROJECT_REPONAME',
            'CIRCLE_WORKFLOW_ID',
            'CIRCLE_BUILD_NUM',
            'CIRCLE_REPOSITORY_URL'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'TOKEN' in var:
                    display_value = f"{'*' * 8}{value[-4:]}"
                else:
                    display_value = value
                click.echo(f"   {var}: {display_value}")
            else:
                click.echo(f"   {var}: Not set")
        
        click.echo()
        click.echo("=" * 80)
        click.echo()
        click.echo("📚 Next Steps:")
        click.echo()
        click.echo("1. Add reviewr orb to your .circleci/config.yml:")
        click.echo("   orbs:")
        click.echo("     reviewr: reviewr/reviewr@1.0.0")
        click.echo()
        click.echo("2. Use the code-review job in your workflow:")
        click.echo("   workflows:")
        click.echo("     version: 2")
        click.echo("     review:")
        click.echo("       jobs:")
        click.echo("         - reviewr/code-review")
        click.echo()
        click.echo("3. Or use the review command directly:")
        click.echo("   - run:")
        click.echo("       name: Code Review")
        click.echo("       command: reviewr circleci review")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@circleci_cli.command(name='publish')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--api-token', help='CircleCI API token')
@click.option('--project-slug', help='Project slug')
def publish_command(file_path: str, api_token: Optional[str], project_slug: Optional[str]):
    """
    Publish results as CircleCI artifact.
    
    This command documents an artifact for CircleCI upload.
    Actual upload happens via the store_artifacts step in config.yml.
    
    Examples:
        # Document artifact
        reviewr circleci publish review-report.json
    """
    click.echo(f"📦 Publishing artifact: {file_path}")
    click.echo()
    
    try:
        integration = CircleCIIntegration(
            api_token=api_token,
            project_slug=project_slug
        )
        
        artifact_info = integration.store_artifact(file_path)
        
        click.echo("✅ Artifact documented:")
        click.echo(f"   Name: {artifact_info['name']}")
        click.echo(f"   Path: {artifact_info['path']}")
        click.echo(f"   Size: {artifact_info['size']} bytes")
        click.echo(f"   Destination: {artifact_info['destination']}")
        click.echo()
        click.echo("💡 To upload this artifact, add to your .circleci/config.yml:")
        click.echo("   - store_artifacts:")
        click.echo(f"       path: {artifact_info['path']}")
        click.echo(f"       destination: {artifact_info['destination']}")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@circleci_cli.command(name='workflow-info')
@click.option('--api-token', help='CircleCI API token')
@click.option('--workflow-id', help='Workflow ID')
def workflow_info_command(api_token: Optional[str], workflow_id: Optional[str]):
    """
    Get workflow information.
    
    Examples:
        # Get current workflow info
        reviewr circleci workflow-info
        
        # Get specific workflow info
        reviewr circleci workflow-info --workflow-id abc123
    """
    try:
        integration = CircleCIIntegration(api_token=api_token, workflow_id=workflow_id)
        
        click.echo("🔍 Fetching workflow information...")
        click.echo()
        
        workflow_info = integration.get_workflow_info()
        
        click.echo("📋 Workflow Information:")
        click.echo(f"   ID: {workflow_info.get('id')}")
        click.echo(f"   Name: {workflow_info.get('name')}")
        click.echo(f"   Status: {workflow_info.get('status')}")
        click.echo(f"   Created: {workflow_info.get('created_at')}")
        click.echo()
        
        # Get jobs
        click.echo("🔧 Jobs:")
        jobs = integration.get_workflow_jobs()
        for job in jobs:
            click.echo(f"   - {job.get('name')}: {job.get('status')}")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    circleci_cli()

