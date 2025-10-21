"""
CLI commands for email reporting.
"""

import click
import json
import os
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from reviewr.reporting.email import (
    EmailConfig,
    EmailClient,
    EmailProvider,
    send_review_summary,
    send_critical_alert
)

console = Console()


@click.group(name='email')
def email_cli():
    """Email reporting commands."""
    pass


@email_cli.command(name='send')
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--to', multiple=True, required=True, help='Recipient email address(es)')
@click.option('--from-email', help='Sender email address (or use EMAIL_FROM env var)')
@click.option('--provider', type=click.Choice(['smtp', 'sendgrid', 'aws_ses']), default='smtp', help='Email provider')
@click.option('--smtp-host', help='SMTP server host')
@click.option('--smtp-port', type=int, default=587, help='SMTP server port')
@click.option('--smtp-username', help='SMTP username')
@click.option('--smtp-password', help='SMTP password')
@click.option('--sendgrid-api-key', help='SendGrid API key')
@click.option('--aws-region', default='us-east-1', help='AWS region for SES')
@click.option('--project-name', default='Code Review', help='Project name for the email')
@click.option('--repository-url', help='Repository URL to include in the email')
@click.option('--cc', multiple=True, help='CC email address(es)')
@click.option('--bcc', multiple=True, help='BCC email address(es)')
@click.option('--critical-only', is_flag=True, help='Only send critical findings')
@click.option('--attach-json', is_flag=True, help='Attach JSON results file')
def send_command(
    results_file: str,
    to: tuple,
    from_email: Optional[str],
    provider: str,
    smtp_host: Optional[str],
    smtp_port: int,
    smtp_username: Optional[str],
    smtp_password: Optional[str],
    sendgrid_api_key: Optional[str],
    aws_region: str,
    project_name: str,
    repository_url: Optional[str],
    cc: tuple,
    bcc: tuple,
    critical_only: bool,
    attach_json: bool
):
    """Send review results via email."""
    console.print(f"\n[bold cyan]📧 Sending Email Report[/bold cyan]\n")
    
    # Load results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading results file: {e}[/red]")
        return
    
    findings = results.get('findings', [])
    
    # Filter critical findings if requested
    if critical_only:
        findings = [f for f in findings if f.get('severity', '').lower() == 'critical']
        console.print(f"[yellow]Filtering to {len(findings)} critical finding(s)[/yellow]")
    
    if not findings and critical_only:
        console.print("[green]No critical findings to send[/green]")
        return
    
    # Prepare attachments
    attachments = None
    if attach_json:
        with open(results_file, 'rb') as f:
            attachments = [{
                'filename': Path(results_file).name,
                'content': f.read()
            }]
    
    # Get from_email from env if not provided
    if not from_email:
        from_email = os.getenv('EMAIL_FROM')
    
    if not from_email:
        console.print("[red]Error: from_email is required (use --from-email or EMAIL_FROM env var)[/red]")
        return
    
    # Send email
    try:
        result = send_review_summary(
            findings=findings,
            to=list(to),
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            sendgrid_api_key=sendgrid_api_key,
            aws_region=aws_region if provider == 'aws_ses' else None,
            project_name=project_name,
            repository_url=repository_url,
            cc=list(cc) if cc else None,
            bcc=list(bcc) if bcc else None,
            attachments=attachments
        )
        
        if result['success']:
            console.print(f"[green]✓ {result['message']}[/green]")
            
            # Display summary
            table = Table(title="Email Summary")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("To", ', '.join(to))
            if cc:
                table.add_row("CC", ', '.join(cc))
            if bcc:
                table.add_row("BCC", ', '.join(bcc))
            table.add_row("Provider", result['provider'])
            table.add_row("Findings", str(len(findings)))
            if attach_json:
                table.add_row("Attachments", Path(results_file).name)
            
            console.print(table)
        else:
            console.print(f"[red]✗ {result['message']}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error sending email: {e}[/red]")


@email_cli.command(name='setup')
@click.option('--provider', type=click.Choice(['smtp', 'sendgrid', 'aws_ses']), default='smtp', help='Email provider')
@click.option('--from-email', help='Sender email address')
@click.option('--smtp-host', help='SMTP server host')
@click.option('--smtp-port', type=int, default=587, help='SMTP server port')
@click.option('--smtp-username', help='SMTP username')
@click.option('--smtp-password', help='SMTP password')
@click.option('--sendgrid-api-key', help='SendGrid API key')
@click.option('--aws-region', default='us-east-1', help='AWS region for SES')
def setup_command(
    provider: str,
    from_email: Optional[str],
    smtp_host: Optional[str],
    smtp_port: int,
    smtp_username: Optional[str],
    smtp_password: Optional[str],
    sendgrid_api_key: Optional[str],
    aws_region: str
):
    """Set up email integration and test connection."""
    console.print(f"\n[bold cyan]📧 Email Integration Setup[/bold cyan]\n")
    
    # Display current configuration
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Provider", provider)
    table.add_row("From Email", from_email or os.getenv('EMAIL_FROM', '[not set]'))
    
    if provider == 'smtp':
        table.add_row("SMTP Host", smtp_host or os.getenv('SMTP_HOST', '[not set]'))
        table.add_row("SMTP Port", str(smtp_port))
        table.add_row("SMTP Username", smtp_username or os.getenv('SMTP_USERNAME', '[not set]'))
        table.add_row("SMTP Password", '***' if smtp_password or os.getenv('SMTP_PASSWORD') else '[not set]')
    elif provider == 'sendgrid':
        table.add_row("SendGrid API Key", '***' if sendgrid_api_key or os.getenv('SENDGRID_API_KEY') else '[not set]')
    elif provider == 'aws_ses':
        table.add_row("AWS Region", aws_region)
        table.add_row("AWS Access Key ID", '***' if os.getenv('AWS_ACCESS_KEY_ID') else '[not set]')
        table.add_row("AWS Secret Access Key", '***' if os.getenv('AWS_SECRET_ACCESS_KEY') else '[not set]')
    
    console.print(table)
    
    # Test connection if credentials provided
    try:
        provider_enum = EmailProvider(provider)
        config = EmailConfig(
            provider=provider_enum,
            from_email=from_email or os.getenv('EMAIL_FROM', ''),
            smtp_host=smtp_host or os.getenv('SMTP_HOST'),
            smtp_port=smtp_port,
            smtp_username=smtp_username or os.getenv('SMTP_USERNAME'),
            smtp_password=smtp_password or os.getenv('SMTP_PASSWORD'),
            sendgrid_api_key=sendgrid_api_key or os.getenv('SENDGRID_API_KEY'),
            aws_region=aws_region
        )
        
        client = EmailClient(config)
        
        console.print("\n[yellow]Testing connection...[/yellow]")
        if client.test_connection():
            console.print("[green]✓ Connection test successful![/green]")
        else:
            console.print("[red]✗ Connection test failed[/red]")
    
    except ValueError as e:
        console.print(f"\n[yellow]⚠ Cannot test connection: {e}[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Connection test failed: {e}[/red]")
    
    # Display setup instructions
    console.print("\n[bold]Setup Instructions:[/bold]\n")
    
    if provider == 'smtp':
        console.print("1. Set environment variables:")
        console.print("   export EMAIL_FROM='your-email@example.com'")
        console.print("   export SMTP_HOST='smtp.gmail.com'")
        console.print("   export SMTP_PORT='587'")
        console.print("   export SMTP_USERNAME='your-email@example.com'")
        console.print("   export SMTP_PASSWORD='your-password'")
        console.print("\n2. For Gmail, use an App Password:")
        console.print("   https://support.google.com/accounts/answer/185833")
    
    elif provider == 'sendgrid':
        console.print("1. Create a SendGrid account:")
        console.print("   https://signup.sendgrid.com/")
        console.print("\n2. Create an API key:")
        console.print("   https://app.sendgrid.com/settings/api_keys")
        console.print("\n3. Set environment variables:")
        console.print("   export EMAIL_FROM='your-email@example.com'")
        console.print("   export SENDGRID_API_KEY='your-api-key'")
    
    elif provider == 'aws_ses':
        console.print("1. Set up AWS SES:")
        console.print("   https://console.aws.amazon.com/ses/")
        console.print("\n2. Verify your email address or domain")
        console.print("\n3. Set environment variables:")
        console.print("   export EMAIL_FROM='your-email@example.com'")
        console.print("   export AWS_REGION='us-east-1'")
        console.print("   export AWS_ACCESS_KEY_ID='your-access-key'")
        console.print("   export AWS_SECRET_ACCESS_KEY='your-secret-key'")


@email_cli.command(name='test')
@click.option('--to', required=True, help='Test recipient email address')
@click.option('--from-email', help='Sender email address (or use EMAIL_FROM env var)')
@click.option('--provider', type=click.Choice(['smtp', 'sendgrid', 'aws_ses']), default='smtp', help='Email provider')
@click.option('--smtp-host', help='SMTP server host')
@click.option('--smtp-port', type=int, default=587, help='SMTP server port')
@click.option('--smtp-username', help='SMTP username')
@click.option('--smtp-password', help='SMTP password')
@click.option('--sendgrid-api-key', help='SendGrid API key')
@click.option('--aws-region', default='us-east-1', help='AWS region for SES')
def test_command(
    to: str,
    from_email: Optional[str],
    provider: str,
    smtp_host: Optional[str],
    smtp_port: int,
    smtp_username: Optional[str],
    smtp_password: Optional[str],
    sendgrid_api_key: Optional[str],
    aws_region: str
):
    """Test email configuration."""
    console.print(f"\n[bold cyan]📧 Testing Email Configuration[/bold cyan]\n")
    
    # Get from_email from env if not provided
    if not from_email:
        from_email = os.getenv('EMAIL_FROM')
    
    if not from_email:
        console.print("[red]Error: from_email is required (use --from-email or EMAIL_FROM env var)[/red]")
        return
    
    try:
        provider_enum = EmailProvider(provider)
        config = EmailConfig(
            provider=provider_enum,
            from_email=from_email,
            smtp_host=smtp_host or os.getenv('SMTP_HOST'),
            smtp_port=smtp_port,
            smtp_username=smtp_username or os.getenv('SMTP_USERNAME'),
            smtp_password=smtp_password or os.getenv('SMTP_PASSWORD'),
            sendgrid_api_key=sendgrid_api_key or os.getenv('SENDGRID_API_KEY'),
            aws_region=aws_region
        )
        
        client = EmailClient(config)
        
        console.print(f"[yellow]Sending test email to {to}...[/yellow]")
        
        result = client.send_email(
            to=[to],
            subject="reviewr Email Test",
            html_body="<h1>Test Successful!</h1><p>This is a test email from reviewr.</p>",
            text_body="Test Successful! This is a test email from reviewr."
        )
        
        if result['success']:
            console.print(f"[green]✓ {result['message']}[/green]")
            console.print(f"\n[bold]Check {to} for the test email[/bold]")
        else:
            console.print(f"[red]✗ {result['message']}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    email_cli()

