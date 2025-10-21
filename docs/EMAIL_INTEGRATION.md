# Email Reports Integration

Comprehensive guide for sending **reviewr** code review reports via email with HTML templates, scheduled reports, and critical alerts.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Email Templates](#email-templates)
- [CI/CD Integration](#cicd-integration)
- [Scheduled Reports](#scheduled-reports)
- [Troubleshooting](#troubleshooting)

## Overview

The Email Reports integration enables **reviewr** to:
- Send review summaries via email
- Deliver critical security alerts in real-time
- Generate digest reports (daily/weekly)
- Support multiple email providers (SMTP, SendGrid, AWS SES)
- Use responsive HTML templates
- Attach review results (JSON, PDF, SARIF)

## Features

### ✅ Multiple Email Providers
- **SMTP**: Standard SMTP server (Gmail, Outlook, custom)
- **SendGrid**: SendGrid API for reliable delivery
- **AWS SES**: Amazon Simple Email Service for scalability

### ✅ HTML Email Templates
- **Responsive Design**: Mobile-friendly HTML templates
- **Inline CSS**: Compatible with all email clients
- **Severity Colors**: Color-coded severity levels (🔴 🟠 🟡 🟢)
- **Rich Formatting**: Tables, gradients, and professional styling

### ✅ Report Types
- **Review Summary**: Complete review results with statistics
- **Critical Alerts**: Immediate notifications for critical issues
- **Digest Reports**: Daily/weekly summaries of multiple reviews
- **Custom Reports**: Flexible template system

### ✅ Advanced Features
- **Multiple Recipients**: Send to multiple email addresses
- **CC/BCC Support**: Carbon copy and blind carbon copy
- **Attachments**: Attach JSON, PDF, or SARIF files
- **Environment Variables**: Secure credential storage

## Quick Start

### Option 1: Using SMTP (Gmail Example)

1. **Enable App Password for Gmail:**
   - Go to https://myaccount.google.com/apppasswords
   - Generate an app password

2. **Set environment variables:**

```bash
export EMAIL_FROM='your-email@gmail.com'
export SMTP_HOST='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USERNAME='your-email@gmail.com'
export SMTP_PASSWORD='your-app-password'
```

3. **Run review and send email:**

```bash
# Run review
reviewr . --output review-results.json

# Send email
reviewr email send review-results.json \
  --to recipient@example.com \
  --project-name "My Project"
```

### Option 2: Using SendGrid

1. **Create SendGrid account and API key:**
   - Sign up at https://signup.sendgrid.com/
   - Create API key at https://app.sendgrid.com/settings/api_keys

2. **Set environment variables:**

```bash
export EMAIL_FROM='your-email@example.com'
export SENDGRID_API_KEY='your-api-key'
```

3. **Run review and send email:**

```bash
reviewr . --output review-results.json
reviewr email send review-results.json \
  --to recipient@example.com \
  --provider sendgrid \
  --project-name "My Project"
```

### Option 3: Using AWS SES

1. **Set up AWS SES and verify email:**
   - Go to https://console.aws.amazon.com/ses/
   - Verify your email address or domain

2. **Set environment variables:**

```bash
export EMAIL_FROM='your-email@example.com'
export AWS_REGION='us-east-1'
export AWS_ACCESS_KEY_ID='your-access-key'
export AWS_SECRET_ACCESS_KEY='your-secret-key'
```

3. **Run review and send email:**

```bash
reviewr . --output review-results.json
reviewr email send review-results.json \
  --to recipient@example.com \
  --provider aws_ses \
  --project-name "My Project"
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `EMAIL_FROM` | Sender email address | Yes | None |
| `EMAIL_FROM_NAME` | Sender display name | No | None |
| `EMAIL_PROVIDER` | Email provider (smtp, sendgrid, aws_ses) | No | smtp |

#### SMTP Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SMTP_HOST` | SMTP server host | Yes* | None |
| `SMTP_PORT` | SMTP server port | No | 587 |
| `SMTP_USERNAME` | SMTP username | No | None |
| `SMTP_PASSWORD` | SMTP password | No | None |
| `SMTP_USE_TLS` | Use TLS encryption | No | true |

*Required when using SMTP provider

#### SendGrid Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SENDGRID_API_KEY` | SendGrid API key | Yes* | None |

*Required when using SendGrid provider

#### AWS SES Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AWS_REGION` | AWS region | No | us-east-1 |
| `AWS_ACCESS_KEY_ID` | AWS access key ID | Yes* | None |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key | Yes* | None |

*Required when using AWS SES provider

### Common SMTP Servers

**Gmail:**
- Host: `smtp.gmail.com`
- Port: `587`
- TLS: Yes
- Note: Use App Password, not regular password

**Outlook/Office 365:**
- Host: `smtp.office365.com`
- Port: `587`
- TLS: Yes

**Yahoo:**
- Host: `smtp.mail.yahoo.com`
- Port: `587`
- TLS: Yes

**Custom SMTP:**
- Host: Your SMTP server
- Port: Usually 587 (TLS) or 465 (SSL)

## CLI Commands

### `reviewr email send`

Send review results via email.

```bash
reviewr email send <results_file> [OPTIONS]
```

**Arguments:**
- `results_file`: Path to review results JSON file

**Options:**
- `--to EMAIL`: Recipient email address (can be used multiple times)
- `--from-email EMAIL`: Sender email address (overrides env var)
- `--provider CHOICE`: Email provider (smtp, sendgrid, aws_ses)
- `--smtp-host TEXT`: SMTP server host
- `--smtp-port INT`: SMTP server port (default: 587)
- `--smtp-username TEXT`: SMTP username
- `--smtp-password TEXT`: SMTP password
- `--sendgrid-api-key TEXT`: SendGrid API key
- `--aws-region TEXT`: AWS region (default: us-east-1)
- `--project-name TEXT`: Project name for the email
- `--repository-url TEXT`: Repository URL to include
- `--cc EMAIL`: CC email address (can be used multiple times)
- `--bcc EMAIL`: BCC email address (can be used multiple times)
- `--critical-only`: Only send critical findings
- `--attach-json`: Attach JSON results file

**Examples:**

```bash
# Send to single recipient
reviewr email send review-results.json \
  --to developer@example.com \
  --project-name "My App"

# Send to multiple recipients with CC
reviewr email send review-results.json \
  --to developer1@example.com \
  --to developer2@example.com \
  --cc manager@example.com \
  --project-name "My App"

# Send only critical findings
reviewr email send review-results.json \
  --to security@example.com \
  --critical-only \
  --project-name "My App"

# Include repository URL
reviewr email send review-results.json \
  --to team@example.com \
  --project-name "My App" \
  --repository-url "https://github.com/myorg/myapp"

# Attach JSON file
reviewr email send review-results.json \
  --to team@example.com \
  --attach-json \
  --project-name "My App"

# Use SendGrid
reviewr email send review-results.json \
  --to team@example.com \
  --provider sendgrid \
  --sendgrid-api-key "your-api-key" \
  --project-name "My App"
```

### `reviewr email setup`

Set up email integration and test connection.

```bash
reviewr email setup [OPTIONS]
```

**Options:**
- `--provider CHOICE`: Email provider (smtp, sendgrid, aws_ses)
- `--from-email EMAIL`: Sender email address
- `--smtp-host TEXT`: SMTP server host
- `--smtp-port INT`: SMTP server port
- `--smtp-username TEXT`: SMTP username
- `--smtp-password TEXT`: SMTP password
- `--sendgrid-api-key TEXT`: SendGrid API key
- `--aws-region TEXT`: AWS region

**Example:**

```bash
reviewr email setup \
  --provider smtp \
  --from-email "your-email@gmail.com" \
  --smtp-host "smtp.gmail.com" \
  --smtp-port 587 \
  --smtp-username "your-email@gmail.com" \
  --smtp-password "your-app-password"
```

### `reviewr email test`

Test email configuration.

```bash
reviewr email test [OPTIONS]
```

**Options:**
- `--to EMAIL`: Test recipient email address (required)
- `--from-email EMAIL`: Sender email address
- `--provider CHOICE`: Email provider
- `--smtp-host TEXT`: SMTP server host
- `--smtp-port INT`: SMTP server port
- `--smtp-username TEXT`: SMTP username
- `--smtp-password TEXT`: SMTP password
- `--sendgrid-api-key TEXT`: SendGrid API key
- `--aws-region TEXT`: AWS region

**Example:**

```bash
reviewr email test --to your-email@example.com
```

## Email Templates

### Review Summary Template

The review summary template displays:
- Project name and review date
- Overall status with color-coded indicator
- Total issue count
- Breakdown by severity (Critical, High, Medium, Low)
- List of findings (up to 20)
- Repository link button (if provided)

**Example:**

```
📊 Code Review Report
My Project

🔴 Critical Issues Found
Review Date: 2024-01-15 10:30:00

Summary
Total Issues: 5
🔴 Critical: 2
🟠 High: 1
🟡 Medium: 1
🟢 Low: 1

Findings
[Table with severity, issue, and type columns]

[View Repository Button]
```

### Critical Alert Template

The critical alert template displays:
- Alert header with 🚨 emoji
- Issue title and severity
- File and line number
- Description
- Recommendation
- Action button to view file

**Example:**

```
🚨 Critical Issue Detected
My Project

🔴 SQL Injection Vulnerability

Severity: 🔴 CRITICAL
Type: security
File: app.py
Line: 42

Description:
Potential SQL injection vulnerability detected

Recommendation:
Use parameterized queries

[View File Button]
```

### Digest Template

The digest template displays:
- Period (Daily/Weekly) and date range
- Total reviews and issues
- Breakdown by severity
- List of reviews with project name, date, and issue count

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
      
      - name: Send email report
        env:
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
        run: |
          reviewr email send review-results.json \
            --to team@example.com \
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
      reviewr email send review-results.json \
        --to team@example.com \
        --project-name "$CI_PROJECT_NAME" \
        --repository-url "$CI_PROJECT_URL"
  variables:
    EMAIL_FROM: $EMAIL_FROM
    SMTP_HOST: $SMTP_HOST
    SMTP_PORT: $SMTP_PORT
    SMTP_USERNAME: $SMTP_USERNAME
    SMTP_PASSWORD: $SMTP_PASSWORD
```

## Scheduled Reports

### Daily Digest with Cron

Create a script `daily-digest.sh`:

```bash
#!/bin/bash

# Run reviews for all projects
reviewr /path/to/project1 --output /tmp/project1-results.json
reviewr /path/to/project2 --output /tmp/project2-results.json

# Send digest email
reviewr email send /tmp/project1-results.json \
  --to team@example.com \
  --project-name "Daily Code Review Digest"

# Clean up
rm /tmp/*-results.json
```

Add to crontab:

```bash
# Run daily at 9 AM
0 9 * * * /path/to/daily-digest.sh
```

### Weekly Digest

```bash
# Run weekly on Monday at 9 AM
0 9 * * 1 /path/to/weekly-digest.sh
```

## Troubleshooting

### SMTP Authentication Errors

**Error**: `535 Authentication failed`

**Solutions**:
- For Gmail: Use App Password instead of regular password
- Verify username and password are correct
- Check if 2FA is enabled (requires App Password)

### Connection Errors

**Error**: `Connection refused` or `Timeout`

**Solutions**:
- Verify SMTP host and port are correct
- Check firewall settings
- Ensure TLS/SSL settings match server requirements

### SendGrid Errors

**Error**: `401 Unauthorized`

**Solution**: Verify SendGrid API key is correct and has send permissions

### AWS SES Errors

**Error**: `Email address is not verified`

**Solution**: Verify your email address or domain in AWS SES console

### Email Not Received

**Checklist**:
1. Check spam/junk folder
2. Verify recipient email address is correct
3. Check email provider logs
4. Test with `reviewr email test` command

## Best Practices

1. **Use Environment Variables**: Store credentials in environment variables or CI/CD secrets
2. **Test Configuration**: Use `reviewr email test` before integrating with CI/CD
3. **Critical-Only Mode**: For production branches, use `--critical-only` to reduce noise
4. **Include Repository URLs**: Always include repository URLs for easy navigation
5. **Schedule Digests**: Use cron for daily/weekly digest reports
6. **Monitor Delivery**: Check email provider logs for delivery issues

## Next Steps

- [Slack Integration](SLACK_INTEGRATION.md)
- [Microsoft Teams Integration](TEAMS_INTEGRATION.md)
- [CI/CD Best Practices](CI_CD_BEST_PRACTICES.md)
- [Security Scanning Guide](SECURITY_SCANNING.md)

