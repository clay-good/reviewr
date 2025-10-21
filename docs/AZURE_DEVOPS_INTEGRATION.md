# Azure DevOps Integration

Comprehensive guide for integrating **reviewr** with Azure DevOps for automated pull request reviews.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Azure Pipelines Integration](#azure-pipelines-integration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The Azure DevOps integration enables **reviewr** to:
- Post review summaries and inline comments on pull requests
- Vote on pull requests (approve/reject)
- Update build status for commits
- Link work items to pull requests
- Support both Azure DevOps Services (cloud) and Azure DevOps Server (on-premises)

## Features

### ✅ Pull Request Reviews
- **Summary Comments**: Post comprehensive review summaries with severity breakdown
- **Inline Comments**: Post comments on specific lines with file context
- **Thread Support**: Create comment threads for discussions

### ✅ Voting System
- **Auto-Approval**: Automatically approve PRs with no critical/high issues
- **Vote Options**: APPROVED, APPROVED_WITH_SUGGESTIONS, NO_VOTE, WAITING_FOR_AUTHOR, REJECTED

### ✅ Build Status
- **Status Updates**: Update commit status (succeeded, failed, pending, error)
- **Custom Context**: Set custom status context/name
- **CI/CD Integration**: Integrate with Azure Pipelines build status

### ✅ Work Item Linking
- **Automatic Linking**: Link PRs to work items (user stories, bugs, tasks)
- **Traceability**: Maintain traceability between code changes and work items

### ✅ Deployment Support
- **Azure DevOps Services**: Full support for dev.azure.com
- **Azure DevOps Server**: Support for on-premises installations

## Quick Start

### 1. Create Personal Access Token (PAT)

1. Go to `https://dev.azure.com/{organization}/_usersSettings/tokens`
2. Click **New Token**
3. Set name: `reviewr`
4. Select scopes:
   - **Code**: Read & Write
   - **Pull Request Threads**: Read & Write
   - **Build**: Read & Execute
5. Click **Create** and copy the token

### 2. Set Environment Variables

```bash
export AZURE_DEVOPS_PAT='your-personal-access-token'
export AZURE_DEVOPS_ORG='your-organization'
export AZURE_DEVOPS_PROJECT='your-project'
export AZURE_DEVOPS_REPO='your-repository'
```

### 3. Test Connection

```bash
reviewr azure setup \
  --pat $AZURE_DEVOPS_PAT \
  --organization $AZURE_DEVOPS_ORG \
  --project $AZURE_DEVOPS_PROJECT \
  --repository $AZURE_DEVOPS_REPO
```

### 4. Review a Pull Request

```bash
# Review current PR (auto-detected from Azure Pipelines)
reviewr azure review

# Review specific PR
reviewr azure review --pr-id 123

# Review with auto-approval
reviewr azure review --auto-approve
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_DEVOPS_PAT` | Personal Access Token | Yes |
| `AZURE_DEVOPS_ORG` | Organization name | Yes* |
| `AZURE_DEVOPS_PROJECT` | Project name | Yes* |
| `AZURE_DEVOPS_REPO` | Repository name | Yes* |
| `AZURE_DEVOPS_SERVER_URL` | Server URL (for on-premises) | No |
| `SYSTEM_PULLREQUEST_PULLREQUESTID` | PR ID (set by Azure Pipelines) | No |

*Auto-detected from git remote if not provided

### Azure Pipelines Variables

Azure Pipelines automatically sets these variables:
- `SYSTEM_PULLREQUEST_PULLREQUESTID`: Pull request ID
- `BUILD_SOURCEBRANCH`: Source branch (e.g., `refs/pull/123/merge`)
- `BUILD_SOURCEVERSION`: Commit SHA
- `BUILD_REASON`: Build reason (e.g., `PullRequest`)

## CLI Commands

### `reviewr azure review`

Review a pull request and post results to Azure DevOps.

```bash
reviewr azure review [OPTIONS] [PATH]
```

**Options:**
- `--pr-id INTEGER`: Pull request ID (auto-detected if not provided)
- `--pat TEXT`: Personal Access Token
- `--organization TEXT`: Organization name
- `--project TEXT`: Project name
- `--repository TEXT`: Repository name
- `--auto-approve`: Automatically approve PR if no critical/high issues
- `--no-inline-comments`: Skip posting inline comments
- `--work-item INTEGER`: Link work item to PR

**Examples:**

```bash
# Review current PR
reviewr azure review

# Review specific PR with auto-approval
reviewr azure review --pr-id 123 --auto-approve

# Review and link work item
reviewr azure review --work-item 456

# Review specific directory
reviewr azure review ./src
```

### `reviewr azure setup`

Set up Azure DevOps integration and test connection.

```bash
reviewr azure setup [OPTIONS]
```

**Options:**
- `--pat TEXT`: Personal Access Token
- `--organization TEXT`: Organization name
- `--project TEXT`: Project name
- `--repository TEXT`: Repository name

**Example:**

```bash
reviewr azure setup \
  --pat YOUR_PAT \
  --organization myorg \
  --project myproject \
  --repository myrepo
```

### `reviewr azure status`

Update build status for a commit.

```bash
reviewr azure status [OPTIONS]
```

**Options:**
- `--commit-id TEXT`: Commit SHA (required)
- `--state CHOICE`: Build status (succeeded, failed, pending, error) (required)
- `--description TEXT`: Status description (required)
- `--context TEXT`: Status context (default: reviewr)
- `--pat TEXT`: Personal Access Token
- `--organization TEXT`: Organization name
- `--project TEXT`: Project name
- `--repository TEXT`: Repository name

**Examples:**

```bash
# Update status to succeeded
reviewr azure status \
  --commit-id abc123 \
  --state succeeded \
  --description "Code review passed"

# Update status to failed
reviewr azure status \
  --commit-id abc123 \
  --state failed \
  --description "Critical issues found"
```

### `reviewr azure link-work-item`

Link a work item to a pull request.

```bash
reviewr azure link-work-item [OPTIONS]
```

**Options:**
- `--pr-id INTEGER`: Pull request ID (required)
- `--work-item-id INTEGER`: Work item ID (required)
- `--pat TEXT`: Personal Access Token
- `--organization TEXT`: Organization name
- `--project TEXT`: Project name
- `--repository TEXT`: Repository name

**Example:**

```bash
reviewr azure link-work-item --pr-id 123 --work-item-id 456
```

## Azure Pipelines Integration

### Basic Configuration

Create `.azure-pipelines/azure-pipelines.yml`:

```yaml
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: reviewr-config  # Contains AZURE_DEVOPS_PAT

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.9'
  
  - script: pip install reviewr
    displayName: 'Install reviewr'
  
  - script: reviewr azure review --auto-approve
    displayName: 'Code Review'
    env:
      AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
    condition: eq(variables['Build.Reason'], 'PullRequest')
```

### Advanced Configuration

```yaml
stages:
  - stage: CodeReview
    jobs:
      - job: ReviewCode
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.9'
          
          - script: pip install reviewr
            displayName: 'Install reviewr'
          
          - script: |
              reviewr azure review \
                --review-type security correctness maintainability \
                --security-scan \
                --code-metrics \
                --auto-approve
            displayName: 'Comprehensive Review'
            env:
              AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
          
          - script: |
              reviewr azure status \
                --commit-id $(Build.SourceVersion) \
                --state succeeded \
                --description "Review passed"
            displayName: 'Update Status'
            env:
              AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
            condition: succeeded()
```

### Work Item Linking

```yaml
- script: |
    # Extract work item ID from branch name
    WORK_ITEM_ID=$(echo "$(System.PullRequest.SourceBranch)" | grep -oP '\d+' | head -1)
    
    if [ -n "$WORK_ITEM_ID" ]; then
      reviewr azure review --auto-approve --work-item $WORK_ITEM_ID
    else
      reviewr azure review --auto-approve
    fi
  displayName: 'Review with Work Item Linking'
  env:
    AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
```

## Advanced Usage

### Custom Review Types

```bash
# Security-focused review
reviewr azure review \
  --review-type security \
  --security-scan \
  --check-vulnerabilities \
  --check-licenses

# Code quality review
reviewr azure review \
  --review-type correctness maintainability \
  --code-metrics \
  --check-complexity \
  --check-duplication
```

### Using Presets

```bash
# Strict preset for production
reviewr azure review --preset strict --auto-approve

# Balanced preset for feature branches
reviewr azure review --preset balanced --auto-approve

# Quick preset for rapid iteration
reviewr azure review --preset quick
```

### Combining with Slack

```bash
reviewr azure review \
  --auto-approve \
  --slack \
  --slack-channel '#code-reviews' \
  --slack-critical-only
```

## Troubleshooting

### Authentication Errors

**Error**: `Azure DevOps PAT not provided`

**Solution**: Set the `AZURE_DEVOPS_PAT` environment variable or pass `--pat` option.

### Repository Detection Errors

**Error**: `Could not detect Azure DevOps repository`

**Solution**: Provide organization, project, and repository explicitly:

```bash
reviewr azure review \
  --organization myorg \
  --project myproject \
  --repository myrepo
```

### PR ID Detection Errors

**Error**: `Could not detect PR ID`

**Solution**: Run in Azure Pipelines or provide `--pr-id` explicitly:

```bash
reviewr azure review --pr-id 123
```

### Permission Errors

**Error**: `403 Forbidden`

**Solution**: Ensure your PAT has the required scopes:
- Code (Read & Write)
- Pull Request Threads (Read & Write)
- Build (Read & Execute)

### On-Premises Server

For Azure DevOps Server (on-premises):

```bash
export AZURE_DEVOPS_SERVER_URL='https://azuredevops.company.com'
reviewr azure review
```

## Best Practices

1. **Store PAT Securely**: Use Azure Pipelines variable groups with secret variables
2. **Auto-Approval**: Use `--auto-approve` only for non-critical branches
3. **Work Item Linking**: Always link PRs to work items for traceability
4. **Build Status**: Update build status for better visibility
5. **Custom Presets**: Use appropriate presets for different branches
6. **Scheduled Reviews**: Run weekly reviews for code quality monitoring

## Next Steps

- [Security Scanning Guide](SECURITY_SCANNING.md)
- [Code Metrics Guide](CODE_METRICS.md)
- [Slack Integration](SLACK_INTEGRATION.md)
- [CI/CD Best Practices](CI_CD_BEST_PRACTICES.md)

