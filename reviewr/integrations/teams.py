"""
Microsoft Teams integration for reviewr.

Provides:
- Post review summaries to channels
- Adaptive Cards for rich formatting
- Webhook and Bot Token support
- Critical alerts
- Interactive action buttons
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests


class TeamsMessageType(Enum):
    """Teams message types."""
    SUMMARY = "summary"
    CRITICAL_ALERT = "critical_alert"
    FINDING = "finding"
    SUCCESS = "success"


class TeamsSeverityColor(Enum):
    """Color codes for severity levels."""
    CRITICAL = "attention"  # Red
    HIGH = "warning"  # Orange
    MEDIUM = "accent"  # Blue
    LOW = "good"  # Green
    INFO = "default"  # Gray


@dataclass
class TeamsConfig:
    """Microsoft Teams configuration."""
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    team_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'TeamsConfig':
        """Create config from environment variables."""
        return cls(
            webhook_url=os.getenv('TEAMS_WEBHOOK_URL'),
            bot_token=os.getenv('TEAMS_BOT_TOKEN'),
            channel_id=os.getenv('TEAMS_CHANNEL_ID'),
            team_id=os.getenv('TEAMS_TEAM_ID')
        )


class AdaptiveCardBuilder:
    """Builder for Microsoft Teams Adaptive Cards."""
    
    def __init__(self):
        """Initialize card builder."""
        self.card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [],
            "actions": []
        }
    
    def add_header(self, title: str, subtitle: Optional[str] = None) -> 'AdaptiveCardBuilder':
        """Add header to card."""
        header = {
            "type": "TextBlock",
            "text": title,
            "weight": "bolder",
            "size": "large",
            "wrap": True
        }
        self.card["body"].append(header)
        
        if subtitle:
            subtitle_block = {
                "type": "TextBlock",
                "text": subtitle,
                "size": "medium",
                "wrap": True,
                "spacing": "none"
            }
            self.card["body"].append(subtitle_block)
        
        return self
    
    def add_text(self, text: str, color: Optional[str] = None, weight: str = "default") -> 'AdaptiveCardBuilder':
        """Add text block to card."""
        text_block = {
            "type": "TextBlock",
            "text": text,
            "wrap": True,
            "weight": weight
        }
        
        if color:
            text_block["color"] = color
        
        self.card["body"].append(text_block)
        return self
    
    def add_fact_set(self, facts: List[Dict[str, str]]) -> 'AdaptiveCardBuilder':
        """Add fact set (key-value pairs) to card."""
        fact_set = {
            "type": "FactSet",
            "facts": facts
        }
        self.card["body"].append(fact_set)
        return self
    
    def add_separator(self) -> 'AdaptiveCardBuilder':
        """Add separator line."""
        self.card["body"].append({"type": "Container", "separator": True})
        return self
    
    def add_action_button(self, title: str, url: str) -> 'AdaptiveCardBuilder':
        """Add action button to card."""
        action = {
            "type": "Action.OpenUrl",
            "title": title,
            "url": url
        }
        self.card["actions"].append(action)
        return self
    
    def add_column_set(self, columns: List[Dict[str, Any]]) -> 'AdaptiveCardBuilder':
        """Add column set to card."""
        column_set = {
            "type": "ColumnSet",
            "columns": columns
        }
        self.card["body"].append(column_set)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the card."""
        return self.card


class TeamsClient:
    """Microsoft Teams API client."""
    
    GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, config: TeamsConfig):
        """Initialize Teams client."""
        self.config = config
        
        if not config.webhook_url and not config.bot_token:
            raise ValueError("Either webhook_url or bot_token must be provided")
    
    def send_message(
        self,
        text: str,
        card: Optional[Dict[str, Any]] = None,
        channel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Teams.
        
        Args:
            text: Message text (fallback for notifications)
            card: Adaptive Card for rich formatting
            channel_id: Channel ID to post to (overrides config)
        
        Returns:
            Response from Teams API
        """
        if self.config.webhook_url:
            return self._send_webhook(text, card)
        else:
            return self._send_api(text, card, channel_id)
    
    def _send_webhook(
        self,
        text: str,
        card: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message using webhook."""
        if card:
            # Webhook with Adaptive Card
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card
                    }
                ]
            }
        else:
            # Simple text message
            payload = {
                "text": text
            }
        
        response = requests.post(
            self.config.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send Teams webhook: {response.status_code} - {response.text}")
        
        return {"ok": True, "status_code": response.status_code}
    
    def _send_api(
        self,
        text: str,
        card: Optional[Dict[str, Any]] = None,
        channel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message using Bot API."""
        channel_id = channel_id or self.config.channel_id
        team_id = self.config.team_id
        
        if not channel_id or not team_id:
            raise ValueError("channel_id and team_id are required for Bot API")
        
        url = f"{self.GRAPH_API_BASE_URL}/teams/{team_id}/channels/{channel_id}/messages"
        
        if card:
            # Message with Adaptive Card
            payload = {
                "body": {
                    "contentType": "html",
                    "content": text
                },
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": json.dumps(card)
                    }
                ]
            }
        else:
            # Simple text message
            payload = {
                "body": {
                    "content": text
                }
            }
        
        headers = {
            "Authorization": f"Bearer {self.config.bot_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to send Teams message: {response.status_code} - {response.text}")
        
        return response.json()
    
    def test_connection(self) -> bool:
        """Test Teams connection."""
        try:
            if self.config.webhook_url:
                # Test webhook with simple message
                self._send_webhook("reviewr connection test ✅")
                return True
            else:
                # Test bot API
                self._send_api("reviewr connection test ✅")
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def create_review_summary_card(
    findings: List[Dict[str, Any]],
    project_name: str = "Code Review",
    repository_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Adaptive Card for review summary.
    
    Args:
        findings: List of review findings
        project_name: Name of the project
        repository_url: URL to the repository
    
    Returns:
        Adaptive Card dictionary
    """
    # Count findings by severity
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    }
    
    for finding in findings:
        severity = finding.get("severity", "info").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    total_issues = sum(severity_counts.values())
    
    # Determine overall status
    if severity_counts["critical"] > 0:
        status_emoji = "🔴"
        status_text = "Critical Issues Found"
        status_color = "attention"
    elif severity_counts["high"] > 0:
        status_emoji = "🟠"
        status_text = "High Priority Issues Found"
        status_color = "warning"
    elif total_issues > 0:
        status_emoji = "🟡"
        status_text = "Issues Found"
        status_color = "accent"
    else:
        status_emoji = "🟢"
        status_text = "No Issues Found"
        status_color = "good"
    
    # Build card
    builder = AdaptiveCardBuilder()
    builder.add_header(
        f"{status_emoji} {project_name}",
        status_text
    )
    
    # Add summary facts
    facts = [
        {"title": "Total Issues", "value": str(total_issues)},
        {"title": "Critical", "value": f"🔴 {severity_counts['critical']}"},
        {"title": "High", "value": f"🟠 {severity_counts['high']}"},
        {"title": "Medium", "value": f"🟡 {severity_counts['medium']}"},
        {"title": "Low", "value": f"🟢 {severity_counts['low']}"}
    ]
    builder.add_fact_set(facts)
    
    # Add repository link if provided
    if repository_url:
        builder.add_action_button("View Repository", repository_url)
    
    return builder.build()


def create_critical_alert_card(
    finding: Dict[str, Any],
    project_name: str = "Code Review",
    file_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Adaptive Card for critical alert.

    Args:
        finding: Critical finding details
        project_name: Name of the project
        file_url: URL to the file with the issue

    Returns:
        Adaptive Card dictionary
    """
    builder = AdaptiveCardBuilder()
    builder.add_header(
        f"🚨 Critical Issue Detected - {project_name}",
        finding.get("title", "Security Issue")
    )

    # Add finding details
    facts = [
        {"title": "Severity", "value": "🔴 CRITICAL"},
        {"title": "Type", "value": finding.get("type", "Unknown")},
        {"title": "File", "value": finding.get("file", "Unknown")},
        {"title": "Line", "value": str(finding.get("line", "N/A"))}
    ]
    builder.add_fact_set(facts)

    # Add description
    if "description" in finding:
        builder.add_separator()
        builder.add_text("Description:", weight="bolder")
        builder.add_text(finding["description"])

    # Add recommendation
    if "recommendation" in finding:
        builder.add_separator()
        builder.add_text("Recommendation:", weight="bolder")
        builder.add_text(finding["recommendation"])

    # Add action button
    if file_url:
        builder.add_action_button("View File", file_url)

    return builder.build()


def create_finding_card(
    finding: Dict[str, Any],
    file_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Adaptive Card for a single finding.

    Args:
        finding: Finding details
        file_url: URL to the file with the issue

    Returns:
        Adaptive Card dictionary
    """
    severity = finding.get("severity", "info").lower()

    # Map severity to emoji and color
    severity_map = {
        "critical": ("🔴", "attention"),
        "high": ("🟠", "warning"),
        "medium": ("🟡", "accent"),
        "low": ("🟢", "good"),
        "info": ("ℹ️", "default")
    }

    emoji, color = severity_map.get(severity, ("ℹ️", "default"))

    builder = AdaptiveCardBuilder()
    builder.add_header(
        f"{emoji} {finding.get('title', 'Code Issue')}",
        f"Severity: {severity.upper()}"
    )

    # Add finding details
    facts = [
        {"title": "Type", "value": finding.get("type", "Unknown")},
        {"title": "File", "value": finding.get("file", "Unknown")},
        {"title": "Line", "value": str(finding.get("line", "N/A"))}
    ]
    builder.add_fact_set(facts)

    # Add description
    if "description" in finding:
        builder.add_separator()
        builder.add_text(finding["description"])

    # Add action button
    if file_url:
        builder.add_action_button("View File", file_url)

    return builder.build()


def send_review_summary(
    findings: List[Dict[str, Any]],
    webhook_url: Optional[str] = None,
    bot_token: Optional[str] = None,
    channel_id: Optional[str] = None,
    team_id: Optional[str] = None,
    project_name: str = "Code Review",
    repository_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send review summary to Teams.

    Args:
        findings: List of review findings
        webhook_url: Teams webhook URL
        bot_token: Teams bot token
        channel_id: Channel ID (for bot API)
        team_id: Team ID (for bot API)
        project_name: Name of the project
        repository_url: URL to the repository

    Returns:
        Response from Teams API
    """
    config = TeamsConfig(
        webhook_url=webhook_url,
        bot_token=bot_token,
        channel_id=channel_id,
        team_id=team_id
    )

    client = TeamsClient(config)
    card = create_review_summary_card(findings, project_name, repository_url)

    return client.send_message(
        text=f"Code review completed for {project_name}",
        card=card
    )


def send_critical_alert(
    finding: Dict[str, Any],
    webhook_url: Optional[str] = None,
    bot_token: Optional[str] = None,
    channel_id: Optional[str] = None,
    team_id: Optional[str] = None,
    project_name: str = "Code Review",
    file_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send critical alert to Teams.

    Args:
        finding: Critical finding details
        webhook_url: Teams webhook URL
        bot_token: Teams bot token
        channel_id: Channel ID (for bot API)
        team_id: Team ID (for bot API)
        project_name: Name of the project
        file_url: URL to the file with the issue

    Returns:
        Response from Teams API
    """
    config = TeamsConfig(
        webhook_url=webhook_url,
        bot_token=bot_token,
        channel_id=channel_id,
        team_id=team_id
    )

    client = TeamsClient(config)
    card = create_critical_alert_card(finding, project_name, file_url)

    return client.send_message(
        text=f"🚨 Critical issue detected in {project_name}",
        card=card
    )

