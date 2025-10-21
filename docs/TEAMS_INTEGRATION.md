# Microsoft Teams Integration

Comprehensive guide for integrating **reviewr** with Microsoft Teams for automated code review notifications and collaboration.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Adaptive Cards](#adaptive-cards)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The Microsoft Teams integration enables **reviewr** to:
- Post review summaries to Teams channels
- Send critical security alerts in real-time
- Use rich Adaptive Cards for interactive messages
- Support both webhook and bot token authentication
- Integrate seamlessly with CI/CD pipelines

## Features

### ✅ Adaptive Cards
- **Rich Formatting**: Interactive cards with colors, facts, and buttons
- **Severity Indicators**: Color-coded severity levels (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
- **Action Buttons**: Quick links to repositories and files
- **Fact Sets**: Organized key-value pairs for metrics

### ✅ Multiple Authentication Methods
- **Webhook Integration**: Simple incoming webhook (no authentication required)
- **Bot Token Integration**: Full Teams Bot API with OAuth 2.0
- **Environment Variables**: Secure credential storage

### ✅ Message Types
- **Review Summary**: Complete review results with statistics
- **Critical Alerts**: Immediate notifications for critical issues
- **Finding Cards**: Individual issue details
- **Success Messages**: Confirmation of clean code

### ✅ CI/CD Integration
- **GitHub Actions**: Automatic Teams notifications
- **GitLab CI**: Pipeline integration
- **Azure Pipelines**: Native Teams integration
- **Jenkins**: Build notifications
- **CircleCI**: Workflow notifications

## Quick Start

### Option 1: Using Incoming Webhook (Recommended for Simple Use)

1. **Create an Incoming Webhook in Teams:**
   - Go to your Teams channel
   - Click the "..." menu → Connectors
   - Search for "Incoming Webhook"
   - Click "Configure"
   - Give it a name (e.g., "reviewr")
   - Copy the webhook URL

2. **Set the webhook URL as an environment variable:**

```bash
export TEAMS_WEBHOOK_URL='https://outlook.office.com/webhook/...'
```

3. **Run a code review and send results to Teams:**

```bash
# Run review
reviewr . --output review-results.json

# Send to Teams
reviewr teams send review-results.json --project-name "My Project"
```

### Option 2: Using Bot Token (Advanced)

1. **Register a bot in Azure Bot Service:**
   - Go to Azure Portal
   - Create a new Bot Service
   - Get the bot token, team ID, and channel ID

2. **Set environment variables:**

```bash
export TEAMS_BOT_TOKEN='your-bot-token'
export TEAMS_TEAM_ID='your-team-id'
export TEAMS_CHANNEL_ID='19:...'
```

3. **Run a code review and send results to Teams:**

```bash
reviewr . --output review-results.json
reviewr teams send review-results.json --project-name "My Project"
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TEAMS_WEBHOOK_URL` | Incoming webhook URL | Yes* | None |
| `TEAMS_BOT_TOKEN` | Bot token for Bot API | Yes* | None |
| `TEAMS_CHANNEL_ID` | Channel ID (for Bot API) | No** | None |
| `TEAMS_TEAM_ID` | Team ID (for Bot API) | No** | None |

*Either `TEAMS_WEBHOOK_URL` or `TEAMS_BOT_TOKEN` must be provided  
**Required when using Bot API

### Creating an Incoming Webhook

1. Open Microsoft Teams
2. Navigate to the channel where you want to receive notifications
3. Click the "..." menu next to the channel name
4. Select "Connectors"
5. Search for "Incoming Webhook"
6. Click "Configure"
7. Provide a name (e.g., "reviewr")
8. Optionally upload an image
9. Click "Create"
10. Copy the webhook URL
11. Click "Done"

### Setting Up Bot Integration

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Azure Bot" resource
3. Configure the bot settings
4. Get the bot token from the Configuration page
5. Add the bot to your Teams team
6. Get the team ID and channel ID from Teams
7. Set the environment variables

## CLI Commands

### `reviewr teams send`

Send review results to Microsoft Teams channel.

```bash
reviewr teams send <results_file> [OPTIONS]
```

**Arguments:**
- `results_file`: Path to review results JSON file

**Options:**
- `--webhook-url TEXT`: Teams webhook URL (overrides env var)
- `--bot-token TEXT`: Teams bot token (overrides env var)
- `--channel-id TEXT`: Teams channel ID (overrides env var)
- `--team-id TEXT`: Teams team ID (overrides env var)
- `--project-name TEXT`: Project name for the message (default: "Code Review")
- `--repository-url TEXT`: Repository URL to include in the message
- `--critical-only`: Only send critical findings

**Examples:**

```bash
# Send all findings
reviewr teams send review-results.json --project-name "My App"

# Send only critical findings
reviewr teams send review-results.json --critical-only

# Include repository URL
reviewr teams send review-results.json \
  --project-name "My App" \
  --repository-url "https://github.com/myorg/myapp"

# Use specific webhook
reviewr teams send review-results.json \
  --webhook-url "https://outlook.office.com/webhook/..."
```

### `reviewr teams setup`

Set up Microsoft Teams integration and test connection.

```bash
reviewr teams setup [OPTIONS]
```

**Options:**
- `--webhook-url TEXT`: Teams webhook URL to test
- `--bot-token TEXT`: Teams bot token to test
- `--channel-id TEXT`: Teams channel ID
- `--team-id TEXT`: Teams team ID

**Example:**

```bash
reviewr teams setup --webhook-url "https://outlook.office.com/webhook/..."
```

### `reviewr teams test`

Test Microsoft Teams webhook or bot configuration.

```bash
reviewr teams test [OPTIONS]
```

**Options:**
- `--webhook-url TEXT`: Teams webhook URL to test
- `--bot-token TEXT`: Teams bot token to test
- `--channel-id TEXT`: Teams channel ID
- `--team-id TEXT`: Teams team ID
- `--message TEXT`: Test message to send (default: "Test message from reviewr")

**Example:**

```bash
reviewr teams test --webhook-url "https://outlook.office.com/webhook/..."
```

## Adaptive Cards

### Review Summary Card

The review summary card displays:
- Overall status with emoji (🟢 No issues, 🟡 Issues found, 🟠 High priority, 🔴 Critical)
- Total issue count
- Breakdown by severity (Critical, High, Medium, Low)
- Action button to view repository

**Example:**

```
🟢 My Project
No Issues Found

Total Issues: 0
Critical: 🔴 0
High: 🟠 0
Medium: 🟡 0
Low: 🟢 0

[View Repository]
```

### Critical Alert Card

The critical alert card displays:
- Alert header with 🚨 emoji
- Issue title
- Severity, type, file, and line number
- Description
- Recommendation
- Action button to view file

**Example:**

```
🚨 Critical Issue Detected - My Project
SQL Injection Vulnerability

Severity: 🔴 CRITICAL
Type: security
File: app.py
Line: 42

Description:
Potential SQL injection vulnerability detected

Recommendation:
Use parameterized queries

[View File]
```

### Finding Card

The finding card displays:
- Issue title with severity emoji
- Severity level
- Type, file, and line number
- Description
- Action button to view file

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
      
      - name: Install reviewr
        run: pip install reviewr
      
      - name: Run code review
        run: reviewr . --output review-results.json
      
      - name: Send to Teams
        env:
          TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}
        run: |
          reviewr teams send review-results.json \
            --project-name "${{ github.repository }}" \
            --repository-url "${{ github.server_url }}/${{ github.repository }}"
```

### GitLab CI

```yaml
code_review:
  stage: test
  script:
    - pip install reviewr
    - reviewr . --output review-results.json
    - |
      reviewr teams send review-results.json \
        --project-name "$CI_PROJECT_NAME" \
        --repository-url "$CI_PROJECT_URL"
  variables:
    TEAMS_WEBHOOK_URL: $TEAMS_WEBHOOK_URL
```

### Azure Pipelines

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.10'

- script: |
    pip install reviewr
    reviewr . --output review-results.json
  displayName: 'Run code review'

- script: |
    reviewr teams send review-results.json \
      --project-name "$(Build.Repository.Name)" \
      --repository-url "$(Build.Repository.Uri)"
  env:
    TEAMS_WEBHOOK_URL: $(TEAMS_WEBHOOK_URL)
  displayName: 'Send to Teams'
```

### Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        TEAMS_WEBHOOK_URL = credentials('teams-webhook-url')
    }
    
    stages {
        stage('Code Review') {
            steps {
                sh 'pip install reviewr'
                sh 'reviewr . --output review-results.json'
                sh '''
                    reviewr teams send review-results.json \
                      --project-name "${JOB_NAME}" \
                      --repository-url "${GIT_URL}"
                '''
            }
        }
    }
}
```

### CircleCI

```yaml
version: 2.1

jobs:
  code-review:
    docker:
      - image: cimg/python:3.10
    steps:
      - checkout
      - run:
          name: Install reviewr
          command: pip install reviewr
      - run:
          name: Run code review
          command: reviewr . --output review-results.json
      - run:
          name: Send to Teams
          command: |
            reviewr teams send review-results.json \
              --project-name "${CIRCLE_PROJECT_REPONAME}" \
              --repository-url "${CIRCLE_REPOSITORY_URL}"

workflows:
  review:
    jobs:
      - code-review
```

## Troubleshooting

### Webhook Errors

**Error**: `Failed to send Teams webhook: 400 - Bad Request`

**Solution**: Verify your webhook URL is correct and hasn't expired. Webhooks can be disabled or deleted in Teams.

### Bot API Errors

**Error**: `Failed to send Teams message: 401 - Unauthorized`

**Solution**: Verify your bot token is correct and hasn't expired. Check that the bot has been added to the team.

### Permission Errors

**Error**: `Failed to send Teams message: 403 - Forbidden`

**Solution**: Ensure the bot has permission to post messages in the channel. Check the bot's permissions in Azure Portal.

### Connection Errors

**Error**: `Connection test failed: Connection refused`

**Solution**: Check your internet connection and ensure Teams API is accessible.

## Best Practices

1. **Use Webhooks for Simple Integration**: Webhooks are easier to set up and don't require Azure configuration
2. **Store Credentials Securely**: Use environment variables or CI/CD secrets for webhook URLs and tokens
3. **Use Critical-Only Mode**: For production branches, use `--critical-only` to reduce noise
4. **Include Repository URLs**: Always include repository URLs for easy navigation
5. **Test Configuration**: Use `reviewr teams test` to verify your setup before integrating with CI/CD
6. **Monitor Webhook Health**: Webhooks can be disabled if they fail repeatedly

## Next Steps

- [Slack Integration](SLACK_INTEGRATION.md)
- [CI/CD Best Practices](CI_CD_BEST_PRACTICES.md)
- [Security Scanning Guide](SECURITY_SCANNING.md)
- [Code Metrics Guide](CODE_METRICS.md)

