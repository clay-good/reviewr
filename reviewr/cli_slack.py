"""
Slack CLI commands for reviewr.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional
import click
from rich.console import Console

from .integrations.slack import (
    SlackClient,
    SlackConfig,
    SlackFormatter,
    post_review_summary,
    post_critical_alert
)
from .config import ConfigLoader
from .providers import ReviewType

console = Console()


@click.group(name='slack')
def slack_cli():
    """Slack integration commands."""
    pass


@slack_cli.command(name='setup')
@click.option('--webhook-url', help='Slack webhook URL')
@click.option('--bot-token', help='Slack bot token')
@click.option('--channel', default='#code-reviews', help='Default channel (default: #code-reviews)')
@click.option('--username', default='reviewr', help='Bot username (default: reviewr)')
@click.option('--icon-emoji', default=':robot_face:', help='Bot icon emoji (default: :robot_face:)')
def setup_command(
    webhook_url: Optional[str],
    bot_token: Optional[str],
    channel: str,
    username: str,
    icon_emoji: str
):
    """
    Set up Slack integration.
    
    Configure Slack webhook or bot token for posting review results.
    
    Examples:
        # Using webhook (simpler, recommended)
        reviewr slack setup --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL
        
        # Using bot token (more features)
        reviewr slack setup --bot-token xoxb-your-bot-token --channel #code-reviews
    """
    console.print("[bold cyan]Slack Integration Setup[/bold cyan]\n")
    
    if not webhook_url and not bot_token:
        console.print("[red]Error:[/red] Either --webhook-url or --bot-token must be provided")
        console.print("\nTo get a webhook URL:")
        console.print("1. Go to https://api.slack.com/apps")
        console.print("2. Create a new app or select existing")
        console.print("3. Enable 'Incoming Webhooks'")
        console.print("4. Add webhook to workspace")
        console.print("5. Copy the webhook URL")
        sys.exit(1)
    
    # Create config
    config = SlackConfig(
        webhook_url=webhook_url,
        bot_token=bot_token,
        channel=channel,
        username=username,
        icon_emoji=icon_emoji
    )
    
    # Test connection
    try:
        console.print("[cyan]Testing Slack connection...[/cyan]")
        
        client = SlackClient(config)
        response = client.post_message(
            text="reviewr Slack integration test",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":white_check_mark: *reviewr Slack integration is working!*\n\nYou're all set to receive code review notifications."
                    }
                }
            ]
        )
        
        console.print("[green]✓[/green] Slack connection successful!")
        console.print(f"\nConfiguration:")
        console.print(f"  Channel: {channel}")
        console.print(f"  Username: {username}")
        console.print(f"  Icon: {icon_emoji}")
        
        console.print("\n[bold]Environment Variables:[/bold]")
        if webhook_url:
            console.print(f"  export SLACK_WEBHOOK_URL='{webhook_url}'")
        if bot_token:
            console.print(f"  export SLACK_BOT_TOKEN='{bot_token}'")
        console.print(f"  export SLACK_CHANNEL='{channel}'")
        console.print(f"  export SLACK_USERNAME='{username}'")
        console.print(f"  export SLACK_ICON_EMOJI='{icon_emoji}'")
        
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Add the environment variables to your shell profile")
        console.print("2. Run a review with --slack flag:")
        console.print("   reviewr /path/to/code --all --output-format sarif --slack")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Slack connection failed: {e}")
        sys.exit(1)


@slack_cli.command(name='test')
@click.option('--channel', help='Channel to post to (overrides env var)')
def test_command(channel: Optional[str]):
    """
    Test Slack integration.
    
    Send a test message to verify configuration.
    
    Examples:
        reviewr slack test
        reviewr slack test --channel #test-channel
    """
    try:
        config = SlackConfig.from_env()
        
        if channel:
            config.channel = channel
        
        console.print(f"[cyan]Sending test message to {config.channel}...[/cyan]")
        
        client = SlackClient(config)
        response = client.post_message(
            text="reviewr test message",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":white_check_mark: Test Message"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "This is a test message from *reviewr*.\n\nIf you can see this, your Slack integration is working correctly!"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Channel: {config.channel} | Username: {config.username}"
                        }
                    ]
                }
            ]
        )
        
        console.print("[green]✓[/green] Test message sent successfully!")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun 'reviewr slack setup' to configure Slack integration")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@slack_cli.command(name='post')
@click.argument('report_file', type=click.Path(exists=True))
@click.option('--channel', help='Channel to post to (overrides env var)')
@click.option('--critical-only', is_flag=True, help='Only post if critical issues found')
def post_command(
    report_file: str,
    channel: Optional[str],
    critical_only: bool
):
    """
    Post a review report to Slack.
    
    Read a SARIF report file and post summary to Slack.
    
    Examples:
        reviewr slack post reviewr-report.sarif
        reviewr slack post reviewr-report.sarif --channel #security
        reviewr slack post reviewr-report.sarif --critical-only
    """
    import json
    
    try:
        config = SlackConfig.from_env()
        
        if channel:
            config.channel = channel
        
        # Read report file
        console.print(f"[cyan]Reading report from {report_file}...[/cyan]")
        
        with open(report_file, 'r') as f:
            if report_file.endswith('.sarif'):
                sarif_data = json.load(f)
                # Extract findings from SARIF
                findings = []
                for run in sarif_data.get('runs', []):
                    for result in run.get('results', []):
                        findings.append({
                            'title': result.get('message', {}).get('text', 'Unknown'),
                            'severity': result.get('level', 'warning'),
                            'file': result.get('locations', [{}])[0].get('physicalLocation', {}).get('artifactLocation', {}).get('uri', 'unknown'),
                            'line': result.get('locations', [{}])[0].get('physicalLocation', {}).get('region', {}).get('startLine', 0)
                        })
                
                # Create mock result object
                class MockResult:
                    def __init__(self, findings):
                        self.findings = findings
                        self.files_reviewed = len(set(f['file'] for f in findings))
                        self.provider_stats = {'total_time': 'N/A'}
                
                result = MockResult(findings)
            else:
                console.print("[red]Error:[/red] Only SARIF format is supported")
                sys.exit(1)
        
        # Check if we should post
        critical_findings = [f for f in findings if f.get('severity', '').lower() == 'critical']
        
        if critical_only and not critical_findings:
            console.print("[yellow]No critical issues found, skipping post[/yellow]")
            return
        
        # Post to Slack
        console.print(f"[cyan]Posting to {config.channel}...[/cyan]")
        
        if critical_findings:
            post_critical_alert(critical_findings, config)
            console.print(f"[green]✓[/green] Posted critical alert ({len(critical_findings)} issues)")
        
        post_review_summary(result, config)
        console.print(f"[green]✓[/green] Posted review summary ({len(findings)} findings)")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun 'reviewr slack setup' to configure Slack integration")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@slack_cli.command(name='notify')
@click.argument('message')
@click.option('--channel', help='Channel to post to (overrides env var)')
@click.option('--severity', type=click.Choice(['info', 'warning', 'error']), default='info',
              help='Message severity (default: info)')
def notify_command(
    message: str,
    channel: Optional[str],
    severity: str
):
    """
    Send a custom notification to Slack.
    
    Examples:
        reviewr slack notify "Deployment started"
        reviewr slack notify "Build failed" --severity error
        reviewr slack notify "Tests passed" --channel #ci-cd
    """
    try:
        config = SlackConfig.from_env()
        
        if channel:
            config.channel = channel
        
        # Choose emoji based on severity
        emoji_map = {
            'info': ':information_source:',
            'warning': ':warning:',
            'error': ':x:'
        }
        emoji = emoji_map.get(severity, ':information_source:')
        
        console.print(f"[cyan]Sending notification to {config.channel}...[/cyan]")
        
        client = SlackClient(config)
        response = client.post_message(
            text=f"{emoji} {message}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{message}*"
                    }
                }
            ]
        )
        
        console.print("[green]✓[/green] Notification sent successfully!")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun 'reviewr slack setup' to configure Slack integration")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    slack_cli()

