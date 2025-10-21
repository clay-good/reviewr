"""
Slack integration for reviewr.

Provides:
- Post review summaries to channels
- Thread discussions
- Alert on critical issues
- Interactive commands
- Slash commands
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import requests


class SlackMessageType(Enum):
    """Slack message types."""
    SUMMARY = "summary"
    CRITICAL_ALERT = "critical_alert"
    FINDING = "finding"
    THREAD_REPLY = "thread_reply"


@dataclass
class SlackConfig:
    """Slack configuration."""
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    channel: Optional[str] = None
    username: str = "reviewr"
    icon_emoji: str = ":robot_face:"
    
    @classmethod
    def from_env(cls) -> 'SlackConfig':
        """Create config from environment variables."""
        return cls(
            webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            bot_token=os.getenv('SLACK_BOT_TOKEN'),
            channel=os.getenv('SLACK_CHANNEL', '#code-reviews'),
            username=os.getenv('SLACK_USERNAME', 'reviewr'),
            icon_emoji=os.getenv('SLACK_ICON_EMOJI', ':robot_face:')
        )


class SlackClient:
    """Slack API client."""
    
    API_BASE_URL = "https://slack.com/api"
    
    def __init__(self, config: SlackConfig):
        """Initialize Slack client."""
        self.config = config
        
        if not config.webhook_url and not config.bot_token:
            raise ValueError("Either webhook_url or bot_token must be provided")
    
    def post_message(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a message to Slack.
        
        Args:
            text: Message text (fallback for notifications)
            blocks: Block Kit blocks for rich formatting
            channel: Channel to post to (overrides config)
            thread_ts: Thread timestamp for replies
        
        Returns:
            Response from Slack API
        """
        channel = channel or self.config.channel
        
        if self.config.webhook_url:
            return self._post_webhook(text, blocks)
        else:
            return self._post_api(text, blocks, channel, thread_ts)
    
    def _post_webhook(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Post message using webhook."""
        payload = {
            "text": text,
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji
        }
        
        if blocks:
            payload["blocks"] = blocks
        
        response = requests.post(
            self.config.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Slack webhook failed: {response.text}")
        
        return {"ok": True, "webhook": True}
    
    def _post_api(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        channel: str = None,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post message using API."""
        payload = {
            "channel": channel,
            "text": text,
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji
        }
        
        if blocks:
            payload["blocks"] = blocks
        
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        response = requests.post(
            f"{self.API_BASE_URL}/chat.postMessage",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.bot_token}",
                "Content-Type": "application/json"
            }
        )
        
        result = response.json()
        
        if not result.get("ok"):
            raise Exception(f"Slack API failed: {result.get('error')}")
        
        return result
    
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing message."""
        if not self.config.bot_token:
            raise ValueError("Bot token required for updating messages")
        
        payload = {
            "channel": channel,
            "ts": ts,
            "text": text
        }
        
        if blocks:
            payload["blocks"] = blocks
        
        response = requests.post(
            f"{self.API_BASE_URL}/chat.update",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.bot_token}",
                "Content-Type": "application/json"
            }
        )
        
        result = response.json()
        
        if not result.get("ok"):
            raise Exception(f"Slack API failed: {result.get('error')}")
        
        return result
    
    def add_reaction(
        self,
        channel: str,
        timestamp: str,
        reaction: str
    ) -> Dict[str, Any]:
        """Add a reaction to a message."""
        if not self.config.bot_token:
            raise ValueError("Bot token required for reactions")
        
        response = requests.post(
            f"{self.API_BASE_URL}/reactions.add",
            json={
                "channel": channel,
                "timestamp": timestamp,
                "name": reaction
            },
            headers={
                "Authorization": f"Bearer {self.config.bot_token}",
                "Content-Type": "application/json"
            }
        )
        
        result = response.json()
        
        if not result.get("ok"):
            raise Exception(f"Slack API failed: {result.get('error')}")
        
        return result


class SlackFormatter:
    """Format review results for Slack."""
    
    @staticmethod
    def format_summary(result: Any) -> Dict[str, Any]:
        """
        Format review summary for Slack.
        
        Args:
            result: ReviewResult object
        
        Returns:
            Slack message payload with blocks
        """
        # Count findings by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for finding in result.findings:
            severity = finding.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Determine overall status
        if severity_counts['critical'] > 0:
            status_emoji = ":red_circle:"
            status_text = "Critical Issues Found"
        elif severity_counts['high'] > 0:
            status_emoji = ":large_orange_diamond:"
            status_text = "High Priority Issues Found"
        elif severity_counts['medium'] > 0:
            status_emoji = ":large_yellow_circle:"
            status_text = "Medium Priority Issues Found"
        else:
            status_emoji = ":white_check_mark:"
            status_text = "Review Complete"
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Code Review Summary"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Files Reviewed:*\n{result.files_reviewed}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Findings:*\n{len(result.findings)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:*\n{result.provider_stats.get('total_time', 'N/A')}"
                    }
                ]
            }
        ]
        
        # Add severity breakdown if there are findings
        if len(result.findings) > 0:
            severity_text = []
            if severity_counts['critical'] > 0:
                severity_text.append(f":red_circle: Critical: {severity_counts['critical']}")
            if severity_counts['high'] > 0:
                severity_text.append(f":large_orange_diamond: High: {severity_counts['high']}")
            if severity_counts['medium'] > 0:
                severity_text.append(f":large_yellow_circle: Medium: {severity_counts['medium']}")
            if severity_counts['low'] > 0:
                severity_text.append(f":small_blue_diamond: Low: {severity_counts['low']}")
            if severity_counts['info'] > 0:
                severity_text.append(f":information_source: Info: {severity_counts['info']}")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Severity Breakdown:*\n" + "\n".join(severity_text)
                }
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        text = f"{status_emoji} Code Review: {len(result.findings)} findings in {result.files_reviewed} files"
        
        return {
            "text": text,
            "blocks": blocks
        }
    
    @staticmethod
    def format_critical_alert(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format critical findings alert."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":rotating_light: Critical Issues Detected"
                }
            }
        ]
        
        for finding in findings[:5]:  # Limit to 5 findings
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{finding.get('title', 'Unknown Issue')}*\n"
                        f"File: `{finding.get('file', 'unknown')}`\n"
                        f"Line: {finding.get('line', 'N/A')}\n"
                        f"Severity: :red_circle: {finding.get('severity', 'critical').upper()}"
                    )
                }
            })
        
        if len(findings) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(findings) - 5} more critical issues_"
                    }
                ]
            })
        
        text = f":rotating_light: {len(findings)} critical issues detected"
        
        return {
            "text": text,
            "blocks": blocks
        }


def post_review_summary(result: Any, config: Optional[SlackConfig] = None) -> Dict[str, Any]:
    """
    Post review summary to Slack.
    
    Args:
        result: ReviewResult object
        config: Slack configuration (uses env vars if not provided)
    
    Returns:
        Slack API response
    """
    if config is None:
        config = SlackConfig.from_env()
    
    client = SlackClient(config)
    formatter = SlackFormatter()
    
    message = formatter.format_summary(result)
    
    return client.post_message(
        text=message["text"],
        blocks=message["blocks"]
    )


def post_critical_alert(
    findings: List[Dict[str, Any]],
    config: Optional[SlackConfig] = None
) -> Dict[str, Any]:
    """
    Post critical findings alert to Slack.
    
    Args:
        findings: List of critical findings
        config: Slack configuration (uses env vars if not provided)
    
    Returns:
        Slack API response
    """
    if config is None:
        config = SlackConfig.from_env()
    
    client = SlackClient(config)
    formatter = SlackFormatter()
    
    message = formatter.format_critical_alert(findings)
    
    return client.post_message(
        text=message["text"],
        blocks=message["blocks"]
    )

