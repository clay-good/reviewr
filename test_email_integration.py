"""
Tests for email integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from reviewr.reporting.email import (
    EmailConfig,
    EmailClient,
    EmailProvider,
    get_severity_color,
    get_severity_emoji,
    render_summary_template,
    render_critical_alert_template,
    render_digest_template,
    send_review_summary,
    send_critical_alert
)


class TestEmailConfig:
    """Test EmailConfig."""
    
    def test_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv('EMAIL_PROVIDER', 'smtp')
        monkeypatch.setenv('EMAIL_FROM', 'test@example.com')
        monkeypatch.setenv('SMTP_HOST', 'smtp.example.com')
        monkeypatch.setenv('SMTP_PORT', '587')
        monkeypatch.setenv('SMTP_USERNAME', 'user')
        monkeypatch.setenv('SMTP_PASSWORD', 'pass')
        
        config = EmailConfig.from_env()
        
        assert config.provider == EmailProvider.SMTP
        assert config.from_email == 'test@example.com'
        assert config.smtp_host == 'smtp.example.com'
        assert config.smtp_port == 587
        assert config.smtp_username == 'user'
        assert config.smtp_password == 'pass'
    
    def test_from_env_defaults(self, monkeypatch):
        """Test creating config with defaults."""
        monkeypatch.delenv('EMAIL_FROM', raising=False)
        
        config = EmailConfig.from_env()
        
        assert config.provider == EmailProvider.SMTP
        assert config.from_email == ''
        assert config.smtp_port == 587


class TestEmailClient:
    """Test EmailClient."""
    
    def test_init_no_from_email(self):
        """Test initialization without from_email."""
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='',
            smtp_host='smtp.example.com',
            smtp_port=587
        )
        
        with pytest.raises(ValueError, match="from_email is required"):
            EmailClient(config)
    
    def test_init_smtp_no_host(self):
        """Test initialization with SMTP but no host."""
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='test@example.com'
        )
        
        with pytest.raises(ValueError, match="SMTP host and port are required"):
            EmailClient(config)
    
    def test_init_sendgrid_no_api_key(self):
        """Test initialization with SendGrid but no API key."""
        config = EmailConfig(
            provider=EmailProvider.SENDGRID,
            from_email='test@example.com'
        )
        
        with pytest.raises(ValueError, match="SendGrid API key is required"):
            EmailClient(config)
    
    def test_init_aws_ses_no_credentials(self):
        """Test initialization with AWS SES but no credentials."""
        config = EmailConfig(
            provider=EmailProvider.AWS_SES,
            from_email='test@example.com'
        )
        
        with pytest.raises(ValueError, match="AWS credentials are required"):
            EmailClient(config)
    
    @patch('smtplib.SMTP')
    def test_send_smtp_success(self, mock_smtp):
        """Test sending email via SMTP."""
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='test@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587,
            smtp_username='user',
            smtp_password='pass'
        )
        
        client = EmailClient(config)
        
        result = client.send_email(
            to=['recipient@example.com'],
            subject='Test',
            html_body='<p>Test</p>'
        )
        
        assert result['success'] is True
        assert 'smtp' in result['provider']
        mock_smtp.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_smtp_with_attachments(self, mock_smtp):
        """Test sending email via SMTP with attachments."""
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='test@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587
        )
        
        client = EmailClient(config)
        
        result = client.send_email(
            to=['recipient@example.com'],
            subject='Test',
            html_body='<p>Test</p>',
            attachments=[{
                'filename': 'test.json',
                'content': b'{"test": true}'
            }]
        )
        
        assert result['success'] is True
    
    @patch('smtplib.SMTP')
    def test_send_smtp_error(self, mock_smtp):
        """Test SMTP error handling."""
        mock_smtp.side_effect = Exception("Connection failed")
        
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='test@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587
        )
        
        client = EmailClient(config)
        
        result = client.send_email(
            to=['recipient@example.com'],
            subject='Test',
            html_body='<p>Test</p>'
        )
        
        assert result['success'] is False
        assert 'Connection failed' in result['message']
    
    @patch('smtplib.SMTP')
    def test_test_connection(self, mock_smtp):
        """Test connection testing."""
        config = EmailConfig(
            provider=EmailProvider.SMTP,
            from_email='test@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587
        )
        
        client = EmailClient(config)
        
        assert client.test_connection() is True


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_get_severity_color(self):
        """Test getting severity color."""
        assert get_severity_color('critical') == '#dc3545'
        assert get_severity_color('high') == '#fd7e14'
        assert get_severity_color('medium') == '#ffc107'
        assert get_severity_color('low') == '#28a745'
        assert get_severity_color('info') == '#17a2b8'
        assert get_severity_color('unknown') == '#6c757d'
    
    def test_get_severity_emoji(self):
        """Test getting severity emoji."""
        assert get_severity_emoji('critical') == '🔴'
        assert get_severity_emoji('high') == '🟠'
        assert get_severity_emoji('medium') == '🟡'
        assert get_severity_emoji('low') == '🟢'
        assert get_severity_emoji('info') == '🔵'
        assert get_severity_emoji('unknown') == '⚪'


class TestTemplateRendering:
    """Test template rendering."""
    
    def test_render_summary_no_issues(self):
        """Test rendering summary with no issues."""
        html = render_summary_template([], "Test Project")

        assert "Test Project" in html
        assert "No Issues Found" in html
        assert "Total Issues:" in html
        assert ">0<" in html  # Check for 0 count in table cell
    
    def test_render_summary_with_critical(self):
        """Test rendering summary with critical issues."""
        findings = [
            {
                'severity': 'critical',
                'title': 'SQL Injection',
                'file': 'app.py',
                'line': 42,
                'type': 'security',
                'description': 'Potential SQL injection'
            }
        ]
        
        html = render_summary_template(findings, "Test Project")
        
        assert "Test Project" in html
        assert "Critical Issues Found" in html
        assert "SQL Injection" in html
        assert "app.py:42" in html
    
    def test_render_summary_with_url(self):
        """Test rendering summary with repository URL."""
        html = render_summary_template(
            [],
            "Test Project",
            repository_url="https://github.com/test/repo"
        )
        
        assert "https://github.com/test/repo" in html
        assert "View Repository" in html
    
    def test_render_critical_alert(self):
        """Test rendering critical alert."""
        finding = {
            'severity': 'critical',
            'title': 'SQL Injection',
            'file': 'app.py',
            'line': 42,
            'type': 'security',
            'description': 'Potential SQL injection',
            'recommendation': 'Use parameterized queries'
        }
        
        html = render_critical_alert_template(finding, "Test Project")
        
        assert "Test Project" in html
        assert "Critical Issue Detected" in html
        assert "SQL Injection" in html
        assert "app.py" in html
        assert "Use parameterized queries" in html
    
    def test_render_digest(self):
        """Test rendering digest."""
        reviews = [
            {
                'project_name': 'Project 1',
                'date': '2024-01-01',
                'findings': [
                    {'severity': 'critical', 'title': 'Issue 1'},
                    {'severity': 'high', 'title': 'Issue 2'}
                ]
            },
            {
                'project_name': 'Project 2',
                'date': '2024-01-02',
                'findings': [
                    {'severity': 'medium', 'title': 'Issue 3'}
                ]
            }
        ]
        
        html = render_digest_template(reviews, "Daily", "2024-01-01", "2024-01-02")
        
        assert "Daily Code Review Digest" in html
        assert "Project 1" in html
        assert "Project 2" in html
        assert "2024-01-01" in html
        assert "2024-01-02" in html


class TestHighLevelFunctions:
    """Test high-level functions."""
    
    @patch('reviewr.reporting.email.EmailClient')
    def test_send_review_summary(self, mock_client_class):
        """Test sending review summary."""
        mock_client = Mock()
        mock_client.send_email.return_value = {'success': True, 'message': 'Sent'}
        mock_client_class.return_value = mock_client
        
        findings = [
            {'severity': 'high', 'title': 'Issue 1', 'file': 'test.py', 'line': 1, 'type': 'security'}
        ]
        
        result = send_review_summary(
            findings=findings,
            to=['test@example.com'],
            from_email='sender@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587,
            project_name='Test Project'
        )
        
        assert result['success'] is True
        mock_client.send_email.assert_called_once()
    
    @patch('reviewr.reporting.email.EmailClient')
    def test_send_critical_alert(self, mock_client_class):
        """Test sending critical alert."""
        mock_client = Mock()
        mock_client.send_email.return_value = {'success': True, 'message': 'Sent'}
        mock_client_class.return_value = mock_client
        
        finding = {
            'severity': 'critical',
            'title': 'SQL Injection',
            'file': 'app.py',
            'line': 42,
            'type': 'security',
            'description': 'Potential SQL injection'
        }
        
        result = send_critical_alert(
            finding=finding,
            to=['test@example.com'],
            from_email='sender@example.com',
            smtp_host='smtp.example.com',
            smtp_port=587,
            project_name='Test Project'
        )
        
        assert result['success'] is True
        mock_client.send_email.assert_called_once()

