# CircleCI Integration

Comprehensive guide for integrating **reviewr** with CircleCI for automated code reviews in CI/CD pipelines.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Orb Usage](#orb-usage)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The CircleCI integration enables **reviewr** to:
- Run automated code reviews in CircleCI workflows
- Publish review reports as CircleCI artifacts
- Integrate with CircleCI test results
- Support both orb-based and manual integration
- Provide flexible workflow configurations

## Features

### ✅ CircleCI Orb
- **Reusable Configuration**: Pre-built commands and jobs
- **Parameterized**: Customizable presets, review types, and options
- **Multiple Executors**: Python 3.8, 3.9, 3.10, 3.11 support
- **Easy Integration**: One-line workflow integration

### ✅ Artifact Publishing
- **Review Reports**: Publish JSON reports as artifacts
- **Test Results**: Integrate with CircleCI test results
- **SARIF Format**: Support for SARIF security reports

### ✅ Flexible Workflows
- **Basic Review**: Simple code review workflow
- **Security Scan**: Security-focused review
- **Quality Check**: Code quality and metrics
- **Parallel Execution**: Run multiple reviews in parallel

### ✅ Auto-Detection
- **Project Detection**: Automatic project slug detection
- **Workflow Context**: Read workflow ID and job number
- **Environment Variables**: Full CircleCI environment support

## Quick Start

### Option 1: Using the Orb (Recommended)

1. **Add the reviewr orb to your `.circleci/config.yml`:**

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  review:
    jobs:
      - reviewr/code-review
```

2. **Add CircleCI API token and AI provider credentials:**

Go to Project Settings → Environment Variables and add:
- `CIRCLE_TOKEN`: Your CircleCI API token
- `OPENAI_API_KEY`: Your OpenAI API key (or other AI provider)

3. **Commit and push!**

### Option 2: Manual Integration

1. **Add reviewr to your `.circleci/config.yml`:**

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
          command: reviewr circleci review --output review-report.json
      - store_artifacts:
          path: review-report.json
          destination: artifacts/review-report.json

workflows:
  version: 2
  review:
    jobs:
      - code-review
```

2. **Add environment variables** (same as Option 1)

3. **Commit and push!**

## Configuration

### Environment Variables

| Variable | Description | Required | Auto-Set by CircleCI |
|----------|-------------|----------|----------------------|
| `CIRCLE_TOKEN` | CircleCI API token | Yes* | No |
| `CIRCLE_PROJECT_USERNAME` | Organization/username | No | Yes |
| `CIRCLE_PROJECT_REPONAME` | Repository name | No | Yes |
| `CIRCLE_REPOSITORY_URL` | Repository URL | No | Yes |
| `CIRCLE_WORKFLOW_ID` | Workflow ID | No | Yes |
| `CIRCLE_BUILD_NUM` | Build/job number | No | Yes |

*Required for API access (optional for basic review)

### CircleCI API Token

1. Go to [CircleCI User Settings](https://app.circleci.com/settings/user/tokens)
2. Click **Create New Token**
3. Give it a name (e.g., `reviewr`)
4. Copy the token
5. Add to Project Settings → Environment Variables as `CIRCLE_TOKEN`

## CLI Commands

### `reviewr circleci review`

Review code in CircleCI workflow.

```bash
reviewr circleci review [OPTIONS] [PATH]
```

**Options:**
- `--api-token TEXT`: CircleCI API token (defaults to CIRCLE_TOKEN env var)
- `--project-slug TEXT`: Project slug (format: vcs-slug/org-name/repo-name)
- `--workflow-id TEXT`: Workflow ID (defaults to CIRCLE_WORKFLOW_ID env var)
- `--output TEXT`: Output file for review report (JSON)
- `--preset CHOICE`: Review preset (balanced, strict, quick, security-focused)
- `--review-type CHOICE`: Review types (can be specified multiple times)
- `--security-scan`: Run security scanning
- `--code-metrics`: Calculate code metrics

**Examples:**

```bash
# Review current workflow (auto-detected)
reviewr circleci review

# Review with specific preset
reviewr circleci review --preset strict

# Security-focused review
reviewr circleci review --preset security-focused --security-scan

# Review and save report
reviewr circleci review --output review-report.json
```

### `reviewr circleci setup`

Set up CircleCI integration and test connection.

```bash
reviewr circleci setup [OPTIONS]
```

**Options:**
- `--api-token TEXT`: CircleCI API token
- `--project-slug TEXT`: Project slug

**Example:**

```bash
reviewr circleci setup --api-token YOUR_TOKEN
```

### `reviewr circleci publish`

Publish results as CircleCI artifact.

```bash
reviewr circleci publish [OPTIONS] FILE_PATH
```

**Options:**
- `--api-token TEXT`: CircleCI API token
- `--project-slug TEXT`: Project slug

**Example:**

```bash
reviewr circleci publish review-report.json
```

### `reviewr circleci workflow-info`

Get workflow information.

```bash
reviewr circleci workflow-info [OPTIONS]
```

**Options:**
- `--api-token TEXT`: CircleCI API token
- `--workflow-id TEXT`: Workflow ID

**Example:**

```bash
reviewr circleci workflow-info
```

## Orb Usage

### Basic Code Review

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  review:
    jobs:
      - reviewr/code-review
```

### Security Scan

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  security:
    jobs:
      - reviewr/security-scan
```

### Custom Configuration

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  custom-review:
    jobs:
      - reviewr/code-review:
          python-version: "3.11"
          preset: strict
          review-types: "security,performance,correctness"
          security-scan: true
          code-metrics: true
          fail-on-issues: true
```

### Parallel Reviews

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  comprehensive-review:
    jobs:
      - reviewr/security-scan:
          name: security-review
      - reviewr/quality-check:
          name: quality-review
      - reviewr/code-review:
          name: full-review
          preset: strict
          requires:
            - security-review
            - quality-review
```

### Branch-Specific Presets

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  branch-review:
    jobs:
      # Strict review for main branch
      - reviewr/code-review:
          name: main-review
          preset: strict
          fail-on-issues: true
          filters:
            branches:
              only: main
      
      # Quick review for feature branches
      - reviewr/code-review:
          name: feature-review
          preset: quick
          fail-on-issues: false
          filters:
            branches:
              ignore: main
```

### Scheduled Security Scans

```yaml
version: 2.1

orbs:
  reviewr: reviewr/reviewr@1.0.0

workflows:
  version: 2
  
  # Run on every commit
  commit-review:
    jobs:
      - reviewr/code-review:
          preset: balanced
  
  # Run security scan daily at midnight
  nightly-security:
    triggers:
      - schedule:
          cron: "0 0 * * *"
          filters:
            branches:
              only: main
    jobs:
      - reviewr/security-scan:
          fail-on-issues: true
```

## Advanced Usage

### Multiple Review Types

```bash
reviewr circleci review \
  --review-type security \
  --review-type performance \
  --review-type correctness \
  --security-scan \
  --code-metrics
```

### Using Presets

```bash
# Strict preset for production
reviewr circleci review --preset strict

# Balanced preset for feature branches
reviewr circleci review --preset balanced

# Quick preset for rapid iteration
reviewr circleci review --preset quick

# Security-focused preset
reviewr circleci review --preset security-focused --security-scan
```

### Combining with Slack

```bash
reviewr circleci review \
  --slack \
  --slack-channel '#code-reviews' \
  --slack-critical-only
```

## Troubleshooting

### Authentication Errors

**Error**: `CircleCI API token not provided`

**Solution**: Set the `CIRCLE_TOKEN` environment variable in Project Settings → Environment Variables.

### Workflow Detection Errors

**Error**: `Workflow ID not provided`

**Solution**: Ensure you're running inside a CircleCI workflow, or provide `--workflow-id` explicitly.

### Permission Errors

**Error**: `403 Forbidden`

**Solution**: Ensure your API token has the required permissions:
- Read project data
- Read workflow data
- Read job data

### Connection Errors

**Error**: `Connection refused`

**Solution**: Check that you have internet access and CircleCI API is accessible.

## Best Practices

1. **Use the Orb**: The orb provides the easiest integration and is maintained by the reviewr team
2. **Store Credentials Securely**: Use CircleCI environment variables for API tokens
3. **Archive Reports**: Always store review reports as artifacts for later reference
4. **Use Presets**: Use appropriate presets for different branches (strict for main, quick for features)
5. **Parallel Execution**: Run multiple review types in parallel for faster workflows
6. **Scheduled Scans**: Set up nightly security scans for production branches
7. **Slack Integration**: Notify team of critical issues immediately

## Next Steps

- [Security Scanning Guide](SECURITY_SCANNING.md)
- [Code Metrics Guide](CODE_METRICS.md)
- [Slack Integration](SLACK_INTEGRATION.md)
- [CI/CD Best Practices](CI_CD_BEST_PRACTICES.md)

