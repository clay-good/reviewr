"""
Microsoft Teams CLI commands for reviewr.
"""

import click
import json
import os
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from reviewr.integrations.teams import (
    TeamsConfig,
    TeamsClient,
    AdaptiveCardBuilder,
    create_review_summary_card,
    create_critical_alert_card,
    send_review_summary,
    send_critical_alert
)

console = Console()


@click.group(name='teams')
def teams_cli():
    """Microsoft Teams integration commands."""
    pass


@teams_cli.command(name='send')
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--webhook-url', help='Teams webhook URL (or set TEAMS_WEBHOOK_URL env var)')
@click.option('--bot-token', help='Teams bot token (or set TEAMS_BOT_TOKEN env var)')
@click.option('--channel-id', help='Teams channel ID (or set TEAMS_CHANNEL_ID env var)')
@click.option('--team-id', help='Teams team ID (or set TEAMS_TEAM_ID env var)')
@click.option('--project-name', default='Code Review', help='Project name for the message')
@click.option('--repository-url', help='Repository URL to include in the message')
@click.option('--critical-only', is_flag=True, help='Only send critical findings')
def send_command(
    results_file: str,
    webhook_url: Optional[str],
    bot_token: Optional[str],
    channel_id: Optional[str],
    team_id: Optional[str],
    project_name: str,
    repository_url: Optional[str],
    critical_only: bool
):
    """Send review results to Microsoft Teams channel."""
    console.print("\n[bold blue]📤 Sending review results to Microsoft Teams...[/bold blue]\n")
    
    # Load results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to load results file: {e}[/bold red]")
        raise click.Abort()
    
    # Extract findings
    findings = results.get('findings', [])
    
    if not findings:
        console.print("[yellow]⚠️  No findings to send[/yellow]")
        return
    
    # Filter critical findings if requested
    if critical_only:
        findings = [f for f in findings if f.get('severity', '').lower() == 'critical']
        if not findings:
            console.print("[yellow]⚠️  No critical findings to send[/yellow]")
            return
    
    # Get configuration
    webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
    bot_token = bot_token or os.getenv('TEAMS_BOT_TOKEN')
    channel_id = channel_id or os.getenv('TEAMS_CHANNEL_ID')
    team_id = team_id or os.getenv('TEAMS_TEAM_ID')
    
    if not webhook_url and not bot_token:
        console.print("[bold red]❌ Either --webhook-url or --bot-token must be provided[/bold red]")
        console.print("\nSet TEAMS_WEBHOOK_URL or TEAMS_BOT_TOKEN environment variable, or use the --webhook-url or --bot-token option")
        raise click.Abort()
    
    # Send to Teams
    try:
        if critical_only and len(findings) == 1:
            # Send as critical alert
            response = send_critical_alert(
                finding=findings[0],
                webhook_url=webhook_url,
                bot_token=bot_token,
                channel_id=channel_id,
                team_id=team_id,
                project_name=project_name,
                file_url=repository_url
            )
        else:
            # Send as summary
            response = send_review_summary(
                findings=findings,
                webhook_url=webhook_url,
                bot_token=bot_token,
                channel_id=channel_id,
                team_id=team_id,
                project_name=project_name,
                repository_url=repository_url
            )
        
        console.print("[bold green]✅ Successfully sent to Microsoft Teams![/bold green]")
        
        # Display summary
        table = Table(title="Message Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Findings Sent", str(len(findings)))
        table.add_row("Project", project_name)
        
        if webhook_url:
            table.add_row("Method", "Webhook")
        else:
            table.add_row("Method", "Bot API")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]❌ Failed to send to Teams: {e}[/bold red]")
        raise click.Abort()


@teams_cli.command(name='setup')
@click.option('--webhook-url', help='Teams webhook URL to test')
@click.option('--bot-token', help='Teams bot token to test')
@click.option('--channel-id', help='Teams channel ID')
@click.option('--team-id', help='Teams team ID')
def setup_command(
    webhook_url: Optional[str],
    bot_token: Optional[str],
    channel_id: Optional[str],
    team_id: Optional[str]
):
    """Set up Microsoft Teams integration and test connection."""
    console.print("\n[bold blue]🔧 Microsoft Teams Integration Setup[/bold blue]\n")
    
    # Get configuration
    webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
    bot_token = bot_token or os.getenv('TEAMS_BOT_TOKEN')
    channel_id = channel_id or os.getenv('TEAMS_CHANNEL_ID')
    team_id = team_id or os.getenv('TEAMS_TEAM_ID')
    
    # Display current configuration
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")
    
    if webhook_url:
        table.add_row("Webhook URL", webhook_url[:50] + "...", "Configured ✅")
    else:
        table.add_row("Webhook URL", "Not set", "❌")
    
    if bot_token:
        table.add_row("Bot Token", bot_token[:20] + "...", "Configured ✅")
    else:
        table.add_row("Bot Token", "Not set", "❌")
    
    if channel_id:
        table.add_row("Channel ID", channel_id, "Configured ✅")
    else:
        table.add_row("Channel ID", "Not set", "❌")
    
    if team_id:
        table.add_row("Team ID", team_id, "Configured ✅")
    else:
        table.add_row("Team ID", "Not set", "❌")
    
    console.print(table)
    
    # Test connection if credentials provided
    if webhook_url or bot_token:
        console.print("\n[bold blue]🔍 Testing connection...[/bold blue]\n")
        
        try:
            config = TeamsConfig(
                webhook_url=webhook_url,
                bot_token=bot_token,
                channel_id=channel_id,
                team_id=team_id
            )
            client = TeamsClient(config)
            
            if client.test_connection():
                console.print("[bold green]✅ Connection successful![/bold green]")
            else:
                console.print("[bold red]❌ Connection failed[/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Connection test failed: {e}[/bold red]")
    else:
        console.print("\n[yellow]⚠️  No credentials provided. Cannot test connection.[/yellow]")
    
    # Display setup instructions
    console.print("\n[bold]Setup Instructions:[/bold]\n")
    console.print("1. [bold]Webhook Integration (Simple):[/bold]")
    console.print("   - Go to your Teams channel")
    console.print("   - Click '...' → Connectors → Incoming Webhook")
    console.print("   - Configure and copy the webhook URL")
    console.print("   - Set TEAMS_WEBHOOK_URL environment variable\n")
    
    console.print("2. [bold]Bot Integration (Advanced):[/bold]")
    console.print("   - Register a bot in Azure Bot Service")
    console.print("   - Add bot to your Teams team")
    console.print("   - Get bot token, channel ID, and team ID")
    console.print("   - Set TEAMS_BOT_TOKEN, TEAMS_CHANNEL_ID, TEAMS_TEAM_ID environment variables\n")
    
    console.print("[bold]Environment Variables:[/bold]")
    console.print("  export TEAMS_WEBHOOK_URL='https://outlook.office.com/webhook/...'")
    console.print("  export TEAMS_BOT_TOKEN='your-bot-token'")
    console.print("  export TEAMS_CHANNEL_ID='19:...'")
    console.print("  export TEAMS_TEAM_ID='your-team-id'\n")


@teams_cli.command(name='test')
@click.option('--webhook-url', help='Teams webhook URL to test')
@click.option('--bot-token', help='Teams bot token to test')
@click.option('--channel-id', help='Teams channel ID')
@click.option('--team-id', help='Teams team ID')
@click.option('--message', default='Test message from reviewr', help='Test message to send')
def test_command(
    webhook_url: Optional[str],
    bot_token: Optional[str],
    channel_id: Optional[str],
    team_id: Optional[str],
    message: str
):
    """Test Microsoft Teams webhook or bot configuration."""
    console.print("\n[bold blue]🧪 Testing Microsoft Teams integration...[/bold blue]\n")
    
    # Get configuration
    webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
    bot_token = bot_token or os.getenv('TEAMS_BOT_TOKEN')
    channel_id = channel_id or os.getenv('TEAMS_CHANNEL_ID')
    team_id = team_id or os.getenv('TEAMS_TEAM_ID')
    
    if not webhook_url and not bot_token:
        console.print("[bold red]❌ Either --webhook-url or --bot-token must be provided[/bold red]")
        raise click.Abort()
    
    try:
        config = TeamsConfig(
            webhook_url=webhook_url,
            bot_token=bot_token,
            channel_id=channel_id,
            team_id=team_id
        )
        client = TeamsClient(config)
        
        # Create test card
        builder = AdaptiveCardBuilder()
        builder.add_header("🧪 reviewr Test Message", "Connection test successful!")
        builder.add_text(message)
        builder.add_fact_set([
            {"title": "Status", "value": "✅ Working"},
            {"title": "Method", "value": "Webhook" if webhook_url else "Bot API"}
        ])
        
        card = builder.build()
        
        # Send test message
        response = client.send_message(text=message, card=card)
        
        console.print("[bold green]✅ Test message sent successfully![/bold green]")
        console.print(f"\nResponse: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Test failed: {e}[/bold red]")
        raise click.Abort()


if __name__ == '__main__':
    teams_cli()

