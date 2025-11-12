"""
Tests for Microsoft Teams integration.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from reviewr.integrations.teams import (
    TeamsConfig,
    TeamsClient,
    AdaptiveCardBuilder,
    TeamsMessageType,
    TeamsSeverityColor,
    create_review_summary_card,
    create_critical_alert_card,
    create_finding_card,
    send_review_summary,
    send_critical_alert
)


class TestTeamsConfig:
    """Test TeamsConfig."""
    
    def test_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv('TEAMS_WEBHOOK_URL', 'https://outlook.office.com/webhook/test')
        monkeypatch.setenv('TEAMS_BOT_TOKEN', 'test-token')
        monkeypatch.setenv('TEAMS_CHANNEL_ID', '19:test-channel')
        monkeypatch.setenv('TEAMS_TEAM_ID', 'test-team')
        
        config = TeamsConfig.from_env()
        
        assert config.webhook_url == 'https://outlook.office.com/webhook/test'
        assert config.bot_token == 'test-token'
        assert config.channel_id == '19:test-channel'
        assert config.team_id == 'test-team'
    
    def test_from_env_defaults(self, monkeypatch):
        """Test creating config with defaults."""
        # Clear environment variables
        monkeypatch.delenv('TEAMS_WEBHOOK_URL', raising=False)
        monkeypatch.delenv('TEAMS_BOT_TOKEN', raising=False)
        
        config = TeamsConfig.from_env()
        
        assert config.webhook_url is None
        assert config.bot_token is None


class TestAdaptiveCardBuilder:
    """Test AdaptiveCardBuilder."""
    
    def test_add_header(self):
        """Test adding header to card."""
        builder = AdaptiveCardBuilder()
        builder.add_header("Test Title", "Test Subtitle")
        
        card = builder.build()
        
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert len(card["body"]) == 2
        assert card["body"][0]["type"] == "TextBlock"
        assert card["body"][0]["text"] == "Test Title"
        assert card["body"][1]["text"] == "Test Subtitle"
    
    def test_add_text(self):
        """Test adding text to card."""
        builder = AdaptiveCardBuilder()
        builder.add_text("Test text", color="attention", weight="bolder")
        
        card = builder.build()
        
        assert len(card["body"]) == 1
        assert card["body"][0]["text"] == "Test text"
        assert card["body"][0]["color"] == "attention"
        assert card["body"][0]["weight"] == "bolder"
    
    def test_add_fact_set(self):
        """Test adding fact set to card."""
        builder = AdaptiveCardBuilder()
        facts = [
            {"title": "Key1", "value": "Value1"},
            {"title": "Key2", "value": "Value2"}
        ]
        builder.add_fact_set(facts)
        
        card = builder.build()
        
        assert len(card["body"]) == 1
        assert card["body"][0]["type"] == "FactSet"
        assert len(card["body"][0]["facts"]) == 2
    
    def test_add_action_button(self):
        """Test adding action button to card."""
        builder = AdaptiveCardBuilder()
        builder.add_action_button("View", "https://example.com")
        
        card = builder.build()
        
        assert len(card["actions"]) == 1
        assert card["actions"][0]["type"] == "Action.OpenUrl"
        assert card["actions"][0]["title"] == "View"
        assert card["actions"][0]["url"] == "https://example.com"


class TestTeamsClient:
    """Test TeamsClient."""
    
    def test_init_no_credentials(self):
        """Test initialization without credentials."""
        config = TeamsConfig()
        
        with pytest.raises(ValueError, match="Either webhook_url or bot_token must be provided"):
            TeamsClient(config)
    
    def test_init_with_webhook(self):
        """Test initialization with webhook URL."""
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        assert client.config.webhook_url == 'https://outlook.office.com/webhook/test'
    
    def test_init_with_bot_token(self):
        """Test initialization with bot token."""
        config = TeamsConfig(
            bot_token='test-token',
            channel_id='19:test-channel',
            team_id='test-team'
        )
        client = TeamsClient(config)
        
        assert client.config.bot_token == 'test-token'
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_send_webhook_text(self, mock_post):
        """Test sending text message via webhook."""
        mock_post.return_value.status_code = 200
        
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        response = client.send_message("Test message")
        
        assert response["ok"] is True
        assert mock_post.called
        
        # Verify payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["text"] == "Test message"
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_send_webhook_card(self, mock_post):
        """Test sending card via webhook."""
        mock_post.return_value.status_code = 200
        
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        card = {"type": "AdaptiveCard", "body": []}
        response = client.send_message("Test message", card=card)
        
        assert response["ok"] is True
        assert mock_post.called
        
        # Verify payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["type"] == "message"
        assert "attachments" in payload
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_send_webhook_error(self, mock_post):
        """Test webhook error handling."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        with pytest.raises(Exception, match="Failed to send Teams webhook"):
            client.send_message("Test message")
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_send_api_text(self, mock_post):
        """Test sending text message via Bot API."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "message-id"}
        
        config = TeamsConfig(
            bot_token='test-token',
            channel_id='19:test-channel',
            team_id='test-team'
        )
        client = TeamsClient(config)
        
        response = client.send_message("Test message")
        
        assert response["id"] == "message-id"
        assert mock_post.called
        
        # Verify headers
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-token"
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_test_connection_webhook(self, mock_post):
        """Test connection test with webhook."""
        mock_post.return_value.status_code = 200
        
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        result = client.test_connection()
        
        assert result is True
    
    @patch('reviewr.integrations.teams.requests.post')
    def test_test_connection_failure(self, mock_post):
        """Test connection test failure."""
        mock_post.side_effect = Exception("Connection error")
        
        config = TeamsConfig(webhook_url='https://outlook.office.com/webhook/test')
        client = TeamsClient(config)
        
        result = client.test_connection()
        
        assert result is False


class TestCardCreation:
    """Test card creation functions."""
    
    def test_create_review_summary_card_no_issues(self):
        """Test creating review summary card with no issues."""
        findings = []
        card = create_review_summary_card(findings, "Test Project")
        
        assert card["type"] == "AdaptiveCard"
        assert "🟢" in card["body"][0]["text"]
        assert "No Issues Found" in card["body"][1]["text"]
    
    def test_create_review_summary_card_with_critical(self):
        """Test creating review summary card with critical issues."""
        findings = [
            {"severity": "critical", "title": "Critical issue"},
            {"severity": "high", "title": "High issue"}
        ]
        card = create_review_summary_card(findings, "Test Project")
        
        assert card["type"] == "AdaptiveCard"
        assert "🔴" in card["body"][0]["text"]
        assert "Critical Issues Found" in card["body"][1]["text"]
    
    def test_create_review_summary_card_with_url(self):
        """Test creating review summary card with repository URL."""
        findings = [{"severity": "medium", "title": "Medium issue"}]
        card = create_review_summary_card(
            findings,
            "Test Project",
            "https://github.com/test/repo"
        )
        
        assert len(card["actions"]) == 1
        assert card["actions"][0]["url"] == "https://github.com/test/repo"
    
    def test_create_critical_alert_card(self):
        """Test creating critical alert card."""
        finding = {
            "title": "SQL Injection",
            "severity": "critical",
            "type": "security",
            "file": "app.py",
            "line": 42,
            "description": "Potential SQL injection vulnerability",
            "recommendation": "Use parameterized queries"
        }
        card = create_critical_alert_card(finding, "Test Project")

        assert card["type"] == "AdaptiveCard"
        assert "🚨" in card["body"][0]["text"]
        assert "SQL Injection" in card["body"][1]["text"]  # Subtitle contains the title
    
    def test_create_finding_card(self):
        """Test creating finding card."""
        finding = {
            "title": "Code smell",
            "severity": "medium",
            "type": "maintainability",
            "file": "utils.py",
            "line": 10,
            "description": "Function is too complex"
        }
        card = create_finding_card(finding)
        
        assert card["type"] == "AdaptiveCard"
        assert "🟡" in card["body"][0]["text"]


class TestHighLevelFunctions:
    """Test high-level functions."""
    
    @patch('reviewr.integrations.teams.TeamsClient')
    def test_send_review_summary(self, mock_client_class):
        """Test sending review summary."""
        mock_client = Mock()
        mock_client.send_message.return_value = {"ok": True}
        mock_client_class.return_value = mock_client
        
        findings = [{"severity": "high", "title": "Issue"}]
        response = send_review_summary(
            findings,
            webhook_url='https://outlook.office.com/webhook/test',
            project_name="Test Project"
        )
        
        assert response["ok"] is True
        assert mock_client.send_message.called
    
    @patch('reviewr.integrations.teams.TeamsClient')
    def test_send_critical_alert(self, mock_client_class):
        """Test sending critical alert."""
        mock_client = Mock()
        mock_client.send_message.return_value = {"ok": True}
        mock_client_class.return_value = mock_client
        
        finding = {"severity": "critical", "title": "Critical Issue"}
        response = send_critical_alert(
            finding,
            webhook_url='https://outlook.office.com/webhook/test',
            project_name="Test Project"
        )
        
        assert response["ok"] is True
        assert mock_client.send_message.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

