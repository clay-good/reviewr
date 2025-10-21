"""
Email reporting module for reviewr.

Supports SMTP, SendGrid, and AWS SES for sending code review reports via email.
"""

import os
import smtplib
import json
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path


class EmailProvider(Enum):
    """Email provider types."""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"


class ReportType(Enum):
    """Email report types."""
    SUMMARY = "summary"
    CRITICAL_ALERT = "critical_alert"
    DIGEST = "digest"
    CUSTOM = "custom"


@dataclass
class EmailConfig:
    """Email configuration."""
    provider: EmailProvider
    from_email: str
    from_name: Optional[str] = None
    
    # SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # SendGrid settings
    sendgrid_api_key: Optional[str] = None
    
    # AWS SES settings
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Create config from environment variables."""
        provider_str = os.getenv('EMAIL_PROVIDER', 'smtp')
        provider = EmailProvider(provider_str)
        
        return cls(
            provider=provider,
            from_email=os.getenv('EMAIL_FROM', ''),
            from_name=os.getenv('EMAIL_FROM_NAME'),
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            sendgrid_api_key=os.getenv('SENDGRID_API_KEY'),
            aws_region=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )


class EmailClient:
    """Email client for sending code review reports."""
    
    def __init__(self, config: EmailConfig):
        """Initialize email client."""
        self.config = config
        
        if not config.from_email:
            raise ValueError("from_email is required")
        
        # Validate provider-specific settings
        if config.provider == EmailProvider.SMTP:
            if not config.smtp_host or not config.smtp_port:
                raise ValueError("SMTP host and port are required for SMTP provider")
        elif config.provider == EmailProvider.SENDGRID:
            if not config.sendgrid_api_key:
                raise ValueError("SendGrid API key is required for SendGrid provider")
        elif config.provider == EmailProvider.AWS_SES:
            if not config.aws_access_key_id or not config.aws_secret_access_key:
                raise ValueError("AWS credentials are required for AWS SES provider")
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            attachments: List of attachments with 'filename' and 'content' keys
        
        Returns:
            Response dictionary with status and message
        """
        if self.config.provider == EmailProvider.SMTP:
            return self._send_smtp(to, subject, html_body, text_body, cc, bcc, attachments)
        elif self.config.provider == EmailProvider.SENDGRID:
            return self._send_sendgrid(to, subject, html_body, text_body, cc, bcc, attachments)
        elif self.config.provider == EmailProvider.AWS_SES:
            return self._send_ses(to, subject, html_body, text_body, cc, bcc, attachments)
        else:
            raise ValueError(f"Unsupported email provider: {self.config.provider}")
    
    def _send_smtp(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>" if self.config.from_name else self.config.from_email
            msg['To'] = ', '.join(to)
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Add text and HTML parts
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(attachment['content'])
                    part.add_header('Content-Disposition', 'attachment', filename=attachment['filename'])
                    msg.attach(part)
            
            # Send email
            all_recipients = to + (cc or []) + (bcc or [])
            
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg, self.config.from_email, all_recipients)
            
            return {
                'success': True,
                'message': f'Email sent successfully to {len(all_recipients)} recipient(s)',
                'provider': 'smtp'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to send email via SMTP: {str(e)}',
                'provider': 'smtp'
            }
    
    def _send_sendgrid(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content, Cc, Bcc, Attachment
            import base64
            
            sg = sendgrid.SendGridAPIClient(api_key=self.config.sendgrid_api_key)
            
            # Create message
            from_email = Email(self.config.from_email, self.config.from_name)
            to_emails = [To(email) for email in to]
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                html_content=Content("text/html", html_body)
            )
            
            if text_body:
                mail.add_content(Content("text/plain", text_body))
            
            # Add CC
            if cc:
                for email in cc:
                    mail.add_cc(Cc(email))
            
            # Add BCC
            if bcc:
                for email in bcc:
                    mail.add_bcc(Bcc(email))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    encoded = base64.b64encode(attachment['content']).decode()
                    att = Attachment()
                    att.file_content = encoded
                    att.file_name = attachment['filename']
                    mail.add_attachment(att)
            
            # Send email
            response = sg.send(mail)
            
            return {
                'success': True,
                'message': f'Email sent successfully via SendGrid',
                'provider': 'sendgrid',
                'status_code': response.status_code
            }
        
        except ImportError:
            return {
                'success': False,
                'message': 'SendGrid library not installed. Install with: pip install sendgrid',
                'provider': 'sendgrid'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to send email via SendGrid: {str(e)}',
                'provider': 'sendgrid'
            }
    
    def _send_ses(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send email via AWS SES."""
        try:
            import boto3
            
            ses = boto3.client(
                'ses',
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key
            )
            
            # Build destination
            destination = {'ToAddresses': to}
            if cc:
                destination['CcAddresses'] = cc
            if bcc:
                destination['BccAddresses'] = bcc
            
            # Build message
            message = {
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_body}}
            }
            
            if text_body:
                message['Body']['Text'] = {'Data': text_body}
            
            # Send email (note: SES doesn't support attachments via send_email, need send_raw_email)
            if attachments:
                # Use raw email for attachments
                msg = MIMEMultipart('mixed')
                msg['Subject'] = subject
                msg['From'] = self.config.from_email
                msg['To'] = ', '.join(to)
                
                msg_body = MIMEMultipart('alternative')
                if text_body:
                    msg_body.attach(MIMEText(text_body, 'plain'))
                msg_body.attach(MIMEText(html_body, 'html'))
                msg.attach(msg_body)
                
                for attachment in attachments:
                    part = MIMEApplication(attachment['content'])
                    part.add_header('Content-Disposition', 'attachment', filename=attachment['filename'])
                    msg.attach(part)
                
                response = ses.send_raw_email(
                    Source=self.config.from_email,
                    Destinations=to + (cc or []) + (bcc or []),
                    RawMessage={'Data': msg.as_string()}
                )
            else:
                response = ses.send_email(
                    Source=self.config.from_email,
                    Destination=destination,
                    Message=message
                )
            
            return {
                'success': True,
                'message': f'Email sent successfully via AWS SES',
                'provider': 'aws_ses',
                'message_id': response['MessageId']
            }
        
        except ImportError:
            return {
                'success': False,
                'message': 'boto3 library not installed. Install with: pip install boto3',
                'provider': 'aws_ses'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to send email via AWS SES: {str(e)}',
                'provider': 'aws_ses'
            }
    
    def test_connection(self) -> bool:
        """Test email connection."""
        try:
            result = self.send_email(
                to=[self.config.from_email],
                subject="reviewr Email Test",
                html_body="<p>This is a test email from reviewr.</p>",
                text_body="This is a test email from reviewr."
            )
            return result['success']
        except Exception:
            return False


def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        'critical': '#dc3545',  # Red
        'high': '#fd7e14',      # Orange
        'medium': '#ffc107',    # Yellow
        'low': '#28a745',       # Green
        'info': '#17a2b8'       # Blue
    }
    return colors.get(severity.lower(), '#6c757d')


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity level."""
    emojis = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'info': '🔵'
    }
    return emojis.get(severity.lower(), '⚪')


def render_summary_template(
    findings: List[Dict[str, Any]],
    project_name: str = "Code Review",
    repository_url: Optional[str] = None,
    review_date: Optional[str] = None
) -> str:
    """Render HTML template for review summary."""
    from datetime import datetime

    if review_date is None:
        review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count findings by severity
    severity_counts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'info': 0
    }

    for finding in findings:
        severity = finding.get('severity', 'info').lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    total_issues = len(findings)

    # Determine overall status
    if severity_counts['critical'] > 0:
        status = "Critical Issues Found"
        status_color = "#dc3545"
        status_emoji = "🔴"
    elif severity_counts['high'] > 0:
        status = "High Priority Issues Found"
        status_color = "#fd7e14"
        status_emoji = "🟠"
    elif severity_counts['medium'] > 0:
        status = "Issues Found"
        status_color = "#ffc107"
        status_emoji = "🟡"
    elif severity_counts['low'] > 0:
        status = "Minor Issues Found"
        status_color = "#28a745"
        status_emoji = "🟢"
    else:
        status = "No Issues Found"
        status_color = "#28a745"
        status_emoji = "✅"

    # Build findings HTML
    findings_html = ""
    for finding in findings[:20]:  # Limit to 20 findings in email
        severity = finding.get('severity', 'info').lower()
        color = get_severity_color(severity)
        emoji = get_severity_emoji(severity)

        findings_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">
                <span style="color: {color}; font-weight: bold;">{emoji} {severity.upper()}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">
                <strong>{finding.get('title', 'Untitled')}</strong><br>
                <small style="color: #6c757d;">{finding.get('file', 'Unknown file')}:{finding.get('line', '?')}</small>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">
                {finding.get('type', 'unknown')}
            </td>
        </tr>
        """

    if len(findings) > 20:
        findings_html += f"""
        <tr>
            <td colspan="3" style="padding: 12px; text-align: center; color: #6c757d;">
                ... and {len(findings) - 20} more issues
            </td>
        </tr>
        """

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{project_name} - Code Review Report</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; margin: 0; padding: 0; background-color: #f8f9fa;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">📊 Code Review Report</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{project_name}</p>
            </div>

            <!-- Status Card -->
            <div style="background-color: white; padding: 30px; border-left: 4px solid {status_color};">
                <h2 style="margin: 0 0 10px 0; color: {status_color};">{status_emoji} {status}</h2>
                <p style="margin: 0; color: #6c757d;">Review Date: {review_date}</p>
            </div>

            <!-- Summary Stats -->
            <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0;">Summary</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;"><strong>Total Issues:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right;">{total_issues}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🔴 Critical:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #dc3545; font-weight: bold;">{severity_counts['critical']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟠 High:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #fd7e14; font-weight: bold;">{severity_counts['high']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟡 Medium:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #ffc107; font-weight: bold;">{severity_counts['medium']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟢 Low:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #28a745;">{severity_counts['low']}</td>
                    </tr>
                </table>
            </div>

            <!-- Findings -->
            {f'''
            <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0;">Findings</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Severity</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Issue</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {findings_html}
                    </tbody>
                </table>
            </div>
            ''' if findings else ''}

            <!-- Repository Link -->
            {f'''
            <div style="text-align: center; margin-top: 30px;">
                <a href="{repository_url}" style="display: inline-block; background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Repository</a>
            </div>
            ''' if repository_url else ''}

            <!-- Footer -->
            <div style="text-align: center; margin-top: 30px; padding: 20px; color: #6c757d; font-size: 14px;">
                <p>Generated by <strong>reviewr</strong> - AI-Powered Code Review</p>
                <p style="margin: 5px 0 0 0;">This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def render_critical_alert_template(
    finding: Dict[str, Any],
    project_name: str = "Code Review",
    file_url: Optional[str] = None
) -> str:
    """Render HTML template for critical alert."""
    severity = finding.get('severity', 'critical').lower()
    color = get_severity_color(severity)
    emoji = get_severity_emoji(severity)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Critical Issue Alert - {project_name}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; margin: 0; padding: 0; background-color: #f8f9fa;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Alert Header -->
            <div style="background-color: {color}; color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 32px;">🚨</h1>
                <h2 style="margin: 10px 0 0 0; font-size: 24px;">Critical Issue Detected</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{project_name}</p>
            </div>

            <!-- Issue Details -->
            <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0; color: {color};">{emoji} {finding.get('title', 'Untitled Issue')}</h3>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Severity:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; color: {color}; font-weight: bold;">{emoji} {severity.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Type:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{finding.get('type', 'unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">File:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;"><code>{finding.get('file', 'Unknown')}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; font-weight: bold;">Line:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{finding.get('line', '?')}</td>
                    </tr>
                </table>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0;">Description:</h4>
                    <p style="margin: 0;">{finding.get('description', 'No description available')}</p>
                </div>

                {f'''
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
                    <h4 style="margin: 0 0 10px 0; color: #856404;">Recommendation:</h4>
                    <p style="margin: 0; color: #856404;">{finding.get('recommendation', 'No recommendation available')}</p>
                </div>
                ''' if finding.get('recommendation') else ''}

                {f'''
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{file_url}" style="display: inline-block; background-color: {color}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">View File</a>
                </div>
                ''' if file_url else ''}
            </div>

            <!-- Footer -->
            <div style="text-align: center; margin-top: 30px; padding: 20px; color: #6c757d; font-size: 14px;">
                <p>Generated by <strong>reviewr</strong> - AI-Powered Code Review</p>
                <p style="margin: 5px 0 0 0;">This is an automated alert. Please address this issue immediately.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def render_digest_template(
    reviews: List[Dict[str, Any]],
    period: str = "Daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """Render HTML template for digest report."""
    from datetime import datetime

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Calculate aggregate stats
    total_reviews = len(reviews)
    total_issues = sum(len(review.get('findings', [])) for review in reviews)

    severity_counts = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }

    for review in reviews:
        for finding in review.get('findings', []):
            severity = finding.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

    # Build reviews HTML
    reviews_html = ""
    for review in reviews:
        project_name = review.get('project_name', 'Unknown Project')
        findings_count = len(review.get('findings', []))
        review_date = review.get('date', 'Unknown date')

        reviews_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6;"><strong>{project_name}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{review_date}</td>
            <td style="padding: 12px; border-bottom: 1px solid #dee2e6; text-align: right;">{findings_count}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{period} Code Review Digest</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; margin: 0; padding: 0; background-color: #f8f9fa;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">📈 {period} Code Review Digest</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{start_date or ''} - {end_date}</p>
            </div>

            <!-- Summary Stats -->
            <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0;">Summary</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 6px;">
                        <div style="font-size: 36px; font-weight: bold; color: #667eea;">{total_reviews}</div>
                        <div style="color: #6c757d; margin-top: 5px;">Reviews</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 6px;">
                        <div style="font-size: 36px; font-weight: bold; color: #667eea;">{total_issues}</div>
                        <div style="color: #6c757d; margin-top: 5px;">Total Issues</div>
                    </div>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🔴 Critical:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #dc3545; font-weight: bold;">{severity_counts['critical']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟠 High:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #fd7e14; font-weight: bold;">{severity_counts['high']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟡 Medium:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #ffc107; font-weight: bold;">{severity_counts['medium']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">🟢 Low:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; color: #28a745;">{severity_counts['low']}</td>
                    </tr>
                </table>
            </div>

            <!-- Reviews List -->
            <div style="background-color: white; padding: 30px; margin-top: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0;">Reviews</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Project</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Date</th>
                            <th style="padding: 12px; text-align: right; border-bottom: 2px solid #dee2e6;">Issues</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reviews_html}
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="text-align: center; margin-top: 30px; padding: 20px; color: #6c757d; font-size: 14px;">
                <p>Generated by <strong>reviewr</strong> - AI-Powered Code Review</p>
                <p style="margin: 5px 0 0 0;">This is an automated digest. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_review_summary(
    findings: List[Dict[str, Any]],
    to: List[str],
    from_email: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    sendgrid_api_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    project_name: str = "Code Review",
    repository_url: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Send review summary email."""
    # Determine provider
    if sendgrid_api_key:
        provider = EmailProvider.SENDGRID
    elif aws_region:
        provider = EmailProvider.AWS_SES
    else:
        provider = EmailProvider.SMTP

    # Create config
    config = EmailConfig(
        provider=provider,
        from_email=from_email or os.getenv('EMAIL_FROM', ''),
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        sendgrid_api_key=sendgrid_api_key,
        aws_region=aws_region
    )

    # Create client
    client = EmailClient(config)

    # Render template
    html_body = render_summary_template(findings, project_name, repository_url)

    # Determine subject
    critical_count = sum(1 for f in findings if f.get('severity', '').lower() == 'critical')
    if critical_count > 0:
        subject = f"🔴 {project_name} - {critical_count} Critical Issue(s) Found"
    elif findings:
        subject = f"📊 {project_name} - Code Review Report ({len(findings)} issue(s))"
    else:
        subject = f"✅ {project_name} - Code Review Report (No Issues)"

    # Send email
    return client.send_email(
        to=to,
        subject=subject,
        html_body=html_body,
        cc=cc,
        bcc=bcc,
        attachments=attachments
    )


def send_critical_alert(
    finding: Dict[str, Any],
    to: List[str],
    from_email: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    sendgrid_api_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    project_name: str = "Code Review",
    file_url: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send critical alert email."""
    # Determine provider
    if sendgrid_api_key:
        provider = EmailProvider.SENDGRID
    elif aws_region:
        provider = EmailProvider.AWS_SES
    else:
        provider = EmailProvider.SMTP

    # Create config
    config = EmailConfig(
        provider=provider,
        from_email=from_email or os.getenv('EMAIL_FROM', ''),
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        sendgrid_api_key=sendgrid_api_key,
        aws_region=aws_region
    )

    # Create client
    client = EmailClient(config)

    # Render template
    html_body = render_critical_alert_template(finding, project_name, file_url)

    # Send email
    subject = f"🚨 CRITICAL: {finding.get('title', 'Security Issue')} - {project_name}"

    return client.send_email(
        to=to,
        subject=subject,
        html_body=html_body,
        cc=cc,
        bcc=bcc
    )

