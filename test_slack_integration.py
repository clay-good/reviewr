"""
Tests for Slack integration.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from reviewr.integrations.slack import (
    SlackClient,
    SlackConfig,
    SlackFormatter,
    SlackMessageType,
    post_review_summary,
    post_critical_alert
)


class TestSlackConfig:
    """Test SlackConfig."""
    
    def test_from_env_webhook(self, monkeypatch):
        """Test creating config from environment variables with webhook."""
        monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/test')
        monkeypatch.setenv('SLACK_CHANNEL', '#test')
        
        config = SlackConfig.from_env()
        
        assert config.webhook_url == 'https://hooks.slack.com/test'
        assert config.channel == '#test'
        assert config.username == 'reviewr'
    
    def test_from_env_bot_token(self, monkeypatch):
        """Test creating config from environment variables with bot token."""
        monkeypatch.setenv('SLACK_BOT_TOKEN', 'xoxb-test-token')
        monkeypatch.setenv('SLACK_CHANNEL', '#code-reviews')
        
        config = SlackConfig.from_env()
        
        assert config.bot_token == 'xoxb-test-token'
        assert config.channel == '#code-reviews'
    
    def test_from_env_defaults(self, monkeypatch):
        """Test default values."""
        monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/test')
        
        config = SlackConfig.from_env()
        
        assert config.channel == '#code-reviews'
        assert config.username == 'reviewr'
        assert config.icon_emoji == ':robot_face:'


class TestSlackClient:
    """Test SlackClient."""
    
    def test_init_no_credentials(self):
        """Test initialization without credentials."""
        config = SlackConfig()
        
        with pytest.raises(ValueError, match="Either webhook_url or bot_token must be provided"):
            SlackClient(config)
    
    def test_init_with_webhook(self):
        """Test initialization with webhook."""
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        client = SlackClient(config)
        
        assert client.config.webhook_url == 'https://hooks.slack.com/test'
    
    def test_init_with_bot_token(self):
        """Test initialization with bot token."""
        config = SlackConfig(bot_token='xoxb-test')
        client = SlackClient(config)
        
        assert client.config.bot_token == 'xoxb-test'
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_post_webhook(self, mock_post):
        """Test posting message via webhook."""
        mock_post.return_value.status_code = 200
        
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        client = SlackClient(config)
        
        result = client.post_message("Test message")
        
        assert result['ok'] is True
        assert result['webhook'] is True
        mock_post.assert_called_once()
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_post_webhook_with_blocks(self, mock_post):
        """Test posting message with blocks via webhook."""
        mock_post.return_value.status_code = 200
        
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        client = SlackClient(config)
        
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]
        result = client.post_message("Test message", blocks=blocks)
        
        assert result['ok'] is True
        call_args = mock_post.call_args
        assert 'blocks' in call_args[1]['json']
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_post_api(self, mock_post):
        """Test posting message via API."""
        mock_post.return_value.json.return_value = {'ok': True, 'ts': '1234567890.123456'}
        
        config = SlackConfig(bot_token='xoxb-test', channel='#test')
        client = SlackClient(config)
        
        result = client.post_message("Test message")
        
        assert result['ok'] is True
        assert 'ts' in result
        mock_post.assert_called_once()
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_post_api_with_thread(self, mock_post):
        """Test posting message to thread via API."""
        mock_post.return_value.json.return_value = {'ok': True, 'ts': '1234567890.123456'}
        
        config = SlackConfig(bot_token='xoxb-test', channel='#test')
        client = SlackClient(config)
        
        result = client.post_message("Test reply", thread_ts='1234567890.123456')
        
        assert result['ok'] is True
        call_args = mock_post.call_args
        assert call_args[1]['json']['thread_ts'] == '1234567890.123456'
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_update_message(self, mock_post):
        """Test updating a message."""
        mock_post.return_value.json.return_value = {'ok': True}
        
        config = SlackConfig(bot_token='xoxb-test')
        client = SlackClient(config)
        
        result = client.update_message('#test', '1234567890.123456', "Updated message")
        
        assert result['ok'] is True
        mock_post.assert_called_once()
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_add_reaction(self, mock_post):
        """Test adding a reaction."""
        mock_post.return_value.json.return_value = {'ok': True}
        
        config = SlackConfig(bot_token='xoxb-test')
        client = SlackClient(config)
        
        result = client.add_reaction('#test', '1234567890.123456', 'thumbsup')
        
        assert result['ok'] is True
        call_args = mock_post.call_args
        assert 'reactions.add' in call_args[0][0]
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_webhook_error(self, mock_post):
        """Test webhook error handling."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Invalid webhook'
        
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        client = SlackClient(config)
        
        with pytest.raises(Exception, match="Slack webhook failed"):
            client.post_message("Test message")
    
    @patch('reviewr.integrations.slack.requests.post')
    def test_api_error(self, mock_post):
        """Test API error handling."""
        mock_post.return_value.json.return_value = {'ok': False, 'error': 'channel_not_found'}
        
        config = SlackConfig(bot_token='xoxb-test', channel='#test')
        client = SlackClient(config)
        
        with pytest.raises(Exception, match="Slack API failed"):
            client.post_message("Test message")


class TestSlackFormatter:
    """Test SlackFormatter."""
    
    def test_format_summary_no_findings(self):
        """Test formatting summary with no findings."""
        result = Mock()
        result.findings = []
        result.files_reviewed = 5
        result.provider_stats = {'total_time': '10s'}
        
        formatter = SlackFormatter()
        message = formatter.format_summary(result)
        
        assert 'text' in message
        assert 'blocks' in message
        assert ':white_check_mark:' in message['text']
    
    def test_format_summary_with_critical(self):
        """Test formatting summary with critical findings."""
        result = Mock()
        result.findings = [
            {'severity': 'critical', 'title': 'SQL Injection'},
            {'severity': 'high', 'title': 'XSS'},
            {'severity': 'medium', 'title': 'Unused variable'}
        ]
        result.files_reviewed = 5
        result.provider_stats = {'total_time': '10s'}
        
        formatter = SlackFormatter()
        message = formatter.format_summary(result)
        
        assert ':red_circle:' in message['text']
        assert 'Critical Issues Found' in str(message['blocks'])
    
    def test_format_summary_with_high(self):
        """Test formatting summary with high severity findings."""
        result = Mock()
        result.findings = [
            {'severity': 'high', 'title': 'XSS'},
            {'severity': 'medium', 'title': 'Unused variable'}
        ]
        result.files_reviewed = 5
        result.provider_stats = {'total_time': '10s'}
        
        formatter = SlackFormatter()
        message = formatter.format_summary(result)
        
        assert ':large_orange_diamond:' in message['text']
        assert 'High Priority Issues Found' in str(message['blocks'])
    
    def test_format_summary_severity_breakdown(self):
        """Test severity breakdown in summary."""
        result = Mock()
        result.findings = [
            {'severity': 'critical', 'title': 'Issue 1'},
            {'severity': 'critical', 'title': 'Issue 2'},
            {'severity': 'high', 'title': 'Issue 3'},
            {'severity': 'medium', 'title': 'Issue 4'},
            {'severity': 'low', 'title': 'Issue 5'},
            {'severity': 'info', 'title': 'Issue 6'}
        ]
        result.files_reviewed = 5
        result.provider_stats = {'total_time': '10s'}
        
        formatter = SlackFormatter()
        message = formatter.format_summary(result)
        
        blocks_str = str(message['blocks'])
        assert 'Critical: 2' in blocks_str
        assert 'High: 1' in blocks_str
        assert 'Medium: 1' in blocks_str
    
    def test_format_critical_alert(self):
        """Test formatting critical alert."""
        findings = [
            {
                'title': 'SQL Injection',
                'file': 'app.py',
                'line': 42,
                'severity': 'critical'
            },
            {
                'title': 'Command Injection',
                'file': 'utils.py',
                'line': 100,
                'severity': 'critical'
            }
        ]
        
        formatter = SlackFormatter()
        message = formatter.format_critical_alert(findings)
        
        assert ':rotating_light:' in message['text']
        assert 'Critical Issues Detected' in str(message['blocks'])
        assert 'SQL Injection' in str(message['blocks'])
    
    def test_format_critical_alert_many_findings(self):
        """Test formatting critical alert with many findings."""
        findings = [
            {'title': f'Issue {i}', 'file': 'test.py', 'line': i, 'severity': 'critical'}
            for i in range(10)
        ]
        
        formatter = SlackFormatter()
        message = formatter.format_critical_alert(findings)
        
        # Should limit to 5 findings
        blocks_str = str(message['blocks'])
        assert 'Issue 0' in blocks_str
        assert 'Issue 4' in blocks_str
        assert '...and 5 more critical issues' in blocks_str


class TestSlackIntegration:
    """Test high-level Slack integration functions."""
    
    @patch('reviewr.integrations.slack.SlackClient.post_message')
    def test_post_review_summary(self, mock_post):
        """Test posting review summary."""
        mock_post.return_value = {'ok': True}
        
        result = Mock()
        result.findings = [{'severity': 'high', 'title': 'Test'}]
        result.files_reviewed = 5
        result.provider_stats = {'total_time': '10s'}
        
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        
        response = post_review_summary(result, config)
        
        assert response['ok'] is True
        mock_post.assert_called_once()
    
    @patch('reviewr.integrations.slack.SlackClient.post_message')
    def test_post_critical_alert(self, mock_post):
        """Test posting critical alert."""
        mock_post.return_value = {'ok': True}
        
        findings = [
            {'title': 'SQL Injection', 'file': 'app.py', 'line': 42, 'severity': 'critical'}
        ]
        
        config = SlackConfig(webhook_url='https://hooks.slack.com/test')
        
        response = post_critical_alert(findings, config)
        
        assert response['ok'] is True
        mock_post.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

