# Slack Integration

reviewr provides comprehensive Slack integration for posting code review results, critical alerts, and custom notifications to your team's Slack workspace.

## Features

- **Review Summaries**: Post formatted review summaries with severity breakdown
- **Critical Alerts**: Automatic alerts for critical security issues
- **Thread Support**: Reply to messages in threads (with bot token)
- **Reactions**: Add emoji reactions to messages (with bot token)
- **Custom Notifications**: Send custom messages for CI/CD events
- **Rich Formatting**: Block Kit formatting with colors and emojis
- **Flexible Configuration**: Support for webhooks (simple) or bot tokens (advanced)

## Quick Start

### 1. Set Up Slack Integration

#### Option A: Using Webhook (Recommended for Simple Use Cases)

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy the webhook URL

```bash
# Configure reviewr
reviewr slack setup --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Add to environment
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
export SLACK_CHANNEL='#code-reviews'
```

#### Option B: Using Bot Token (Advanced Features)

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Add Bot Token Scopes:
 - `chat:write` - Post messages
 - `chat:write.public` - Post to public channels
 - `reactions:write` - Add reactions
4. Install app to workspace
5. Copy the Bot User OAuth Token

```bash
# Configure reviewr
reviewr slack setup --bot-token xoxb-your-bot-token --channel #code-reviews

# Add to environment
export SLACK_BOT_TOKEN='xoxb-your-bot-token'
export SLACK_CHANNEL='#code-reviews'
```

### 2. Test the Integration

```bash
reviewr slack test
```

### 3. Run a Review with Slack Notifications

```bash
# Post all review results
reviewr /path/to/code --all --output-format sarif --slack

# Post only if critical issues found
reviewr /path/to/code --all --output-format sarif --slack --slack-critical-only

# Post to specific channel
reviewr /path/to/code --all --output-format sarif --slack --slack-channel #security
```

## CLI Commands

### `reviewr slack setup`

Configure Slack integration.

```bash
# Using webhook
reviewr slack setup --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Using bot token
reviewr slack setup --bot-token xoxb-your-bot-token --channel #code-reviews

# Custom username and icon
reviewr slack setup \
 --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
 --username "Code Review Bot" \
 --icon-emoji ":robot_face:"
```

**Options:**
- `--webhook-url TEXT` - Slack webhook URL
- `--bot-token TEXT` - Slack bot token
- `--channel TEXT` - Default channel (default: #code-reviews)
- `--username TEXT` - Bot username (default: reviewr)
- `--icon-emoji TEXT` - Bot icon emoji (default: :robot_face:)

### `reviewr slack test`

Test Slack integration by sending a test message.

```bash
# Test with default channel
reviewr slack test

# Test with specific channel
reviewr slack test --channel #test-channel
```

**Options:**
- `--channel TEXT` - Channel to post to (overrides env var)

### `reviewr slack post`

Post a review report to Slack.

```bash
# Post SARIF report
reviewr slack post reviewr-report.sarif

# Post to specific channel
reviewr slack post reviewr-report.sarif --channel #security

# Post only if critical issues found
reviewr slack post reviewr-report.sarif --critical-only
```

**Options:**
- `--channel TEXT` - Channel to post to (overrides env var)
- `--critical-only` - Only post if critical issues found

### `reviewr slack notify`

Send a custom notification to Slack.

```bash
# Info notification
reviewr slack notify "Deployment started"

# Warning notification
reviewr slack notify "Build took longer than expected" --severity warning

# Error notification
reviewr slack notify "Build failed" --severity error

# Post to specific channel
reviewr slack notify "Tests passed" --channel #ci-cd
```

**Options:**
- `--channel TEXT` - Channel to post to (overrides env var)
- `--severity [info|warning|error]` - Message severity (default: info)

## Review Command Integration

Add `--slack` flag to any review command to automatically post results to Slack.

```bash
# Basic review with Slack
reviewr . --all --output-format sarif --slack

# Security review with Slack
reviewr . --security --output-format sarif --slack

# Comprehensive review with Slack
reviewr . --all --security-scan --metrics --output-format sarif --slack

# Post only critical issues
reviewr . --all --output-format sarif --slack --slack-critical-only

# Post to specific channel
reviewr . --all --output-format sarif --slack --slack-channel #security
```

## Message Formats

### Review Summary

```
🟢 Code Review Summary

Status: Review Complete
Files Reviewed: 15
Total Findings: 23
Duration: 45s

Severity Breakdown:
 Critical: 2
🟠 High: 5
🟡 Medium: 10
 Low: 4
ℹ Info: 2
```

### Critical Alert

```
 Critical Issues Detected

SQL Injection
File: `app.py`
Line: 42
Severity: CRITICAL

Command Injection
File: `utils.py`
Line: 100
Severity: CRITICAL

...and 3 more critical issues
```

## Environment Variables

Configure Slack integration using environment variables:

```bash
# Webhook configuration (simple)
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
export SLACK_CHANNEL='#code-reviews'
export SLACK_USERNAME='reviewr'
export SLACK_ICON_EMOJI=':robot_face:'

# Bot token configuration (advanced)
export SLACK_BOT_TOKEN='xoxb-your-bot-token'
export SLACK_CHANNEL='#code-reviews'
export SLACK_USERNAME='reviewr'
export SLACK_ICON_EMOJI=':robot_face:'
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Review
on: [pull_request]

jobs:
 review:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.9'
 
 - name: Install reviewr
 run: pip install reviewr
 
 - name: Run review with Slack notification
 env:
 ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
 SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
 SLACK_CHANNEL: '#code-reviews'
 run: |
 reviewr . --all --output-format sarif --slack --slack-critical-only
```

### GitLab CI

```yaml
code_review:
 stage: test
 script:
 - pip install reviewr
 - reviewr . --all --output-format sarif --slack --slack-critical-only
 variables:
 SLACK_WEBHOOK_URL: $SLACK_WEBHOOK_URL
 SLACK_CHANNEL: '#code-reviews'
```

### Bitbucket Pipelines

```yaml
pipelines:
 pull-requests:
 '**':
 - step:
 name: Code Review
 script:
 - pip install reviewr
 - reviewr . --all --output-format sarif --slack --slack-critical-only
 variables:
 SLACK_WEBHOOK_URL: $SLACK_WEBHOOK_URL
 SLACK_CHANNEL: '#code-reviews'
```

### Jenkins

```groovy
pipeline {
 agent any
 
 environment {
 SLACK_WEBHOOK_URL = credentials('slack-webhook-url')
 SLACK_CHANNEL = '#code-reviews'
 }
 
 stages {
 stage('Code Review') {
 steps {
 sh 'pip install reviewr'
 sh 'reviewr . --all --output-format sarif --slack --slack-critical-only'
 }
 }
 }
}
```

## Python API

Use Slack integration programmatically:

```python
from reviewr.integrations.slack import (
 SlackClient,
 SlackConfig,
 SlackFormatter,
 post_review_summary,
 post_critical_alert
)

# Configure Slack
config = SlackConfig(
 webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
 channel='#code-reviews',
 username='reviewr',
 icon_emoji=':robot_face:'
)

# Post review summary
post_review_summary(review_result, config)

# Post critical alert
critical_findings = [f for f in review_result.findings if f['severity'] == 'critical']
if critical_findings:
 post_critical_alert(critical_findings, config)

# Custom message
client = SlackClient(config)
client.post_message(
 text="Custom notification",
 blocks=[
 {
 "type": "section",
 "text": {
 "type": "mrkdwn",
 "text": "*Custom notification*\n\nThis is a custom message."
 }
 }
 ]
)
```

## Best Practices

1. **Use Webhooks for Simple Use Cases**: Webhooks are easier to set up and sufficient for most use cases
2. **Use Bot Tokens for Advanced Features**: Bot tokens enable threads, reactions, and message updates
3. **Configure Critical-Only Mode**: Use `--slack-critical-only` to reduce noise in busy channels
4. **Use Dedicated Channels**: Create dedicated channels like `#code-reviews` or `#security-alerts`
5. **Set Up Proper Permissions**: Ensure the bot has permission to post to the target channels
6. **Test Before Production**: Always test with `reviewr slack test` before using in CI/CD
7. **Secure Your Credentials**: Store webhook URLs and bot tokens as secrets in your CI/CD system
8. **Monitor Rate Limits**: Slack has rate limits; avoid posting too frequently

## Troubleshooting

### "Either webhook_url or bot_token must be provided"

You need to configure Slack integration first:

```bash
reviewr slack setup --webhook-url https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### "Slack webhook failed: invalid_payload"

Check that your webhook URL is correct and the webhook is still active in Slack.

### "Slack API failed: channel_not_found"

The bot doesn't have access to the channel. Invite the bot to the channel:

```
/invite @reviewr
```

### "Slack API failed: not_authed"

Your bot token is invalid or expired. Generate a new token and update the configuration.

### Messages not appearing

1. Check that the bot is invited to the channel
2. Verify the channel name starts with `#`
3. Test with `reviewr slack test`
4. Check Slack app permissions

## Security Considerations

- **Protect Webhook URLs**: Treat webhook URLs as secrets; anyone with the URL can post to your channel
- **Protect Bot Tokens**: Bot tokens provide full access to your Slack workspace
- **Use Environment Variables**: Never hardcode credentials in code or config files
- **Rotate Credentials**: Regularly rotate webhook URLs and bot tokens
- **Limit Permissions**: Grant only necessary permissions to the bot
- **Monitor Usage**: Monitor Slack integration usage for suspicious activity

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/reviewr/issues
- Documentation: https://reviewr.dev/docs/slack
- Slack Community: https://reviewr-community.slack.com