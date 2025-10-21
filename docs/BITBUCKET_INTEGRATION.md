# Bitbucket Integration

Automated code review for Bitbucket pull requests with inline comments, summary reports, and auto-approval.

## Features

- ✅ **Automated PR Reviews** - Review pull requests automatically in Bitbucket Pipelines
- ✅ **Inline Comments** - Post findings as inline comments on specific lines
- ✅ **Summary Reports** - Generate comprehensive summary comments
- ✅ **Auto-Approval** - Automatically approve PRs with no critical issues
- ✅ **Build Status** - Update commit build status based on review results
- ✅ **Bitbucket Cloud** - Full support for bitbucket.org
- ✅ **Bitbucket Server/Data Center** - Support for self-hosted instances
- ✅ **Incremental Analysis** - Review only changed code with `--diff` flag

## Quick Start

### 1. Setup Credentials

#### Bitbucket Cloud

Create an app password:
1. Go to https://bitbucket.org/account/settings/app-passwords/
2. Click "Create app password"
3. Give it a label (e.g., "reviewr")
4. Select permissions:
   - **Pull requests**: Read, Write
   - **Repositories**: Read
5. Click "Create" and save the password

Set environment variables:
```bash
export BITBUCKET_USERNAME='your-username'
export BITBUCKET_APP_PASSWORD='your-app-password'
export ANTHROPIC_API_KEY='your-api-key'  # or OPENAI_API_KEY, GEMINI_API_KEY
```

#### Bitbucket Server/Data Center

Set environment variables:
```bash
export BITBUCKET_USERNAME='your-username'
export BITBUCKET_APP_PASSWORD='your-app-password'
export BITBUCKET_SERVER_URL='https://bitbucket.company.com'
export ANTHROPIC_API_KEY='your-api-key'
```

### 2. Configure Bitbucket Pipelines

Create `.bitbucket/bitbucket-pipelines.yml`:

```yaml
image: python:3.9

pipelines:
  pull-requests:
    '**':
      - step:
          name: Code Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --all --auto-approve
```

### 3. Add Repository Variables

In your Bitbucket repository:
1. Go to **Repository Settings** > **Pipelines** > **Repository variables**
2. Add secured variables:
   - `BITBUCKET_APP_PASSWORD`: Your app password
   - `ANTHROPIC_API_KEY`: Your LLM provider API key

**Note**: `BITBUCKET_USERNAME`, `BITBUCKET_PR_ID`, and `BITBUCKET_COMMIT` are automatically provided by Bitbucket Pipelines.

## Usage

### Basic Review

Review a pull request with all review types:

```bash
reviewr bitbucket review --all
```

### Specific Review Types

Review specific aspects:

```bash
# Security only
reviewr bitbucket review --security

# Security and performance
reviewr bitbucket review --security --performance

# All types with auto-approval
reviewr bitbucket review --all --auto-approve
```

### Incremental Analysis

Review only changed code (much faster):

```bash
# Review only changes from main branch
reviewr bitbucket review --all --diff --diff-base origin/main

# Review only changes from HEAD
reviewr bitbucket review --all --diff
```

### Manual PR Review

Review a specific PR (outside of Bitbucket Pipelines):

```bash
reviewr bitbucket review --pr 123 --all
```

### Bitbucket Server

For self-hosted Bitbucket Server/Data Center:

```bash
reviewr bitbucket review --all --is-server --server-url https://bitbucket.company.com
```

### Custom Configuration

Use a custom configuration file:

```bash
reviewr bitbucket review --all --config .reviewr.yml
```

### Specify Provider

Override the default LLM provider:

```bash
reviewr bitbucket review --all --provider claude
reviewr bitbucket review --all --provider openai
reviewr bitbucket review --all --provider gemini
```

## Configuration Examples

### Example 1: Basic PR Review

```yaml
# .bitbucket/bitbucket-pipelines.yml
image: python:3.9

pipelines:
  pull-requests:
    '**':
      - step:
          name: Code Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --all --auto-approve
```

### Example 2: Incremental Review (Faster)

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Incremental Code Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --all --diff --diff-base origin/main
```

### Example 3: Different Reviews for Different Branches

```yaml
pipelines:
  pull-requests:
    feature/*:
      - step:
          name: Feature Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --security --performance
    
    hotfix/*:
      - step:
          name: Hotfix Review (Critical Only)
          script:
            - pip install reviewr
            - reviewr bitbucket review --security --correctness
```

### Example 4: Parallel Reviews

```yaml
pipelines:
  pull-requests:
    '**':
      - parallel:
          - step:
              name: Security Review
              script:
                - pip install reviewr
                - reviewr . --security --local-only
          - step:
              name: Performance Review
              script:
                - pip install reviewr
                - reviewr . --performance --local-only
```

### Example 5: Custom Configuration

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Custom Review
          script:
            - pip install reviewr
            - reviewr bitbucket review --config .reviewr.yml
```

### Example 6: Bitbucket Server

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Code Review (Server)
          script:
            - pip install reviewr
            - reviewr bitbucket review --all --is-server
```

## CLI Reference

### `reviewr bitbucket review`

Review a Bitbucket pull request.

**Options:**

- `--pr INTEGER` - Pull request number (auto-detected in Bitbucket Pipelines)
- `--workspace TEXT` - Bitbucket workspace (auto-detected from git remote)
- `--repo-slug TEXT` - Repository slug (auto-detected from git remote)
- `--username TEXT` - Bitbucket username (defaults to `BITBUCKET_USERNAME` env var)
- `--app-password TEXT` - App password (defaults to `BITBUCKET_APP_PASSWORD` env var)
- `--is-server` - Use Bitbucket Server/Data Center instead of Cloud
- `--server-url TEXT` - Bitbucket Server URL (required if `--is-server`)
- `--security` - Security review
- `--performance` - Performance review
- `--correctness` - Correctness review
- `--maintainability` - Maintainability review
- `--all` - Run all review types
- `--auto-approve` - Auto-approve PR if no critical issues
- `--config PATH` - Path to config file
- `--provider CHOICE` - LLM provider (claude, openai, gemini)
- `--verbose, -v` - Increase verbosity
- `--diff` - Only review changed code (incremental analysis)
- `--diff-base TEXT` - Base reference for diff (default: HEAD)

### `reviewr bitbucket setup`

Interactive setup guide for Bitbucket integration.

```bash
reviewr bitbucket setup
```

## Environment Variables

### Required

- `BITBUCKET_USERNAME` - Your Bitbucket username
- `BITBUCKET_APP_PASSWORD` - Your Bitbucket app password
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `GEMINI_API_KEY` - LLM provider API key

### Optional

- `BITBUCKET_SERVER_URL` - Bitbucket Server URL (required for Server/Data Center)

### Auto-Provided by Bitbucket Pipelines

- `BITBUCKET_PR_ID` - Pull request ID
- `BITBUCKET_COMMIT` - Current commit SHA
- `BITBUCKET_BRANCH` - Current branch name
- `BITBUCKET_REPO_SLUG` - Repository slug
- `BITBUCKET_WORKSPACE` - Workspace name

## How It Works

1. **Detect PR** - Automatically detects PR number from Bitbucket Pipelines environment
2. **Get Changed Files** - Fetches list of files changed in the PR
3. **Run Review** - Analyzes code using local analyzers and/or AI
4. **Filter Findings** - Filters findings to only include files in the PR
5. **Post Comments** - Posts inline comments on specific lines
6. **Post Summary** - Posts a summary comment with all findings
7. **Update Status** - Updates commit build status (SUCCESSFUL/FAILED)
8. **Auto-Approve** - Optionally approves PR if no critical issues

## Review Output

### Inline Comments

Each finding is posted as an inline comment on the specific line:

```
🔴 CRITICAL: SQL injection vulnerability detected

Suggestion: Use parameterized queries instead of string concatenation

Category: security
Type: security
```

### Summary Comment

A summary comment is posted with all findings:

```markdown
## 🔍 Code Review Summary

**Total findings**: 5

🔴 **Critical**: 1
🟠 **High**: 2
🟡 **Medium**: 2

---
*Automated review by reviewr*
```

### Build Status

The commit build status is updated based on review results:

- ✅ **SUCCESSFUL** - No critical or high severity issues
- ❌ **FAILED** - Critical or high severity issues found
- 🔄 **INPROGRESS** - Review in progress

## Best Practices

### 1. Use Incremental Analysis

For faster reviews and lower costs, use `--diff` flag:

```bash
reviewr bitbucket review --all --diff --diff-base origin/main
```

**Benefits:**
- 5-10x faster
- 70-90% cost reduction
- Only reviews changed code

### 2. Use Auto-Approval Carefully

Only enable auto-approval for trusted repositories:

```bash
reviewr bitbucket review --all --auto-approve
```

**Recommendation**: Require manual approval for:
- Production branches
- Security-sensitive code
- Critical infrastructure

### 3. Cache Dependencies

Speed up pipeline execution by caching pip packages:

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Code Review
          caches:
            - pip
          script:
            - pip install reviewr
            - reviewr bitbucket review --all
```

### 4. Use Local-Only Mode for Fast Feedback

For quick feedback without AI costs:

```bash
reviewr . --local-only --all
```

### 5. Combine with Other Checks

Integrate reviewr with other quality checks:

```yaml
pipelines:
  pull-requests:
    '**':
      - parallel:
          - step:
              name: Code Review
              script:
                - pip install reviewr
                - reviewr bitbucket review --all
          - step:
              name: Unit Tests
              script:
                - pytest
          - step:
              name: Linting
              script:
                - flake8
```

## Troubleshooting

### Issue: "Could not determine PR number"

**Solution**: Ensure you're running in Bitbucket Pipelines or provide `--pr` option:

```bash
reviewr bitbucket review --pr 123 --all
```

### Issue: "Bitbucket credentials not provided"

**Solution**: Set environment variables:

```bash
export BITBUCKET_USERNAME='your-username'
export BITBUCKET_APP_PASSWORD='your-app-password'
```

### Issue: "Could not detect Bitbucket repository"

**Solution**: Provide workspace and repo slug explicitly:

```bash
reviewr bitbucket review --workspace myworkspace --repo-slug myrepo --all
```

### Issue: "Failed to post comment"

**Possible causes:**
- Invalid app password
- Insufficient permissions
- Network issues

**Solution**: Verify app password has correct permissions:
- Pull requests: Read, Write
- Repositories: Read

### Issue: "Bitbucket Server URL not provided"

**Solution**: Set environment variable or provide option:

```bash
export BITBUCKET_SERVER_URL='https://bitbucket.company.com'
# or
reviewr bitbucket review --is-server --server-url https://bitbucket.company.com --all
```

## Performance

### Typical PR Review (5 files, 200 lines changed)

**Without `--diff`:**
- Time: ~30-45 seconds
- API calls: ~50
- Cost: ~$0.40

**With `--diff`:**
- Time: ~3-5 seconds
- API calls: ~5
- Cost: ~$0.04

**Savings: 90% faster, 90% cheaper**

## Security

- App passwords are more secure than account passwords
- Passwords are never logged or stored
- Use Bitbucket's secured variables for sensitive data
- Supports fine-grained permissions

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/reviewr/issues
- Documentation: https://github.com/yourusername/reviewr/blob/main/README.md

## See Also

- [GitHub Integration](GITHUB_INTEGRATION.md)
- [GitLab Integration](GITLAB_INTEGRATION.md)
- [Incremental Analysis](INCREMENTAL_ANALYSIS.md)
- [Configuration Guide](CONFIG.md)

