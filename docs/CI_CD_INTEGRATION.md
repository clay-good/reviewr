# CI/CD Integration Guide

This guide explains how to integrate **reviewr** into your CI/CD pipelines for automated code review on every pull request or merge request.

## Table of Contents

- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

---

## Overview

reviewr can automatically review code changes in your CI/CD pipeline and:

- Post detailed review comments on PRs/MRs
- Fail builds on critical issues
- Track code quality over time
- Provide actionable feedback to developers
- Support multiple languages (Python, JS/TS, Go, Rust, Java)

### Benefits

- **Catch issues early** - Before code reaches production
- **Consistent reviews** - Same standards applied to all code
- **Fast feedback** - Results in minutes, not hours
- **Reduced review burden** - Focus on logic, not syntax/security
- **Learning tool** - Developers learn from AI suggestions

---

## GitHub Actions

### Quick Start

1. **Add API Key as Secret**

 Go to your repository → Settings → Secrets and variables → Actions → New repository secret

 - Name: `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` or `GEMINI_API_KEY`)
 - Value: Your API key

2. **Create Workflow File**

 Create `.github/workflows/reviewr.yml`:

 ```yaml
 name: reviewr Code Review

 on:
 pull_request:
 types: [opened, synchronize, reopened]

 permissions:
 contents: read
 pull-requests: write
 checks: write

 jobs:
 code-review:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v4
 
 - name: Run reviewr
 uses: ./.github/actions/reviewr-action
 with:
 api-key: ${{ secrets.ANTHROPIC_API_KEY }}
 provider: claude
 fail-on-critical: true
 fail-on-high-threshold: 5
 ```

3. **Commit and Push**

 The workflow will run automatically on new PRs!

### Using the Reusable Action

The reviewr action supports many configuration options:

```yaml
- name: Run reviewr
 uses: ./.github/actions/reviewr-action
 with:
 # Required
 api-key: ${{ secrets.ANTHROPIC_API_KEY }}
 
 # Optional
 provider: claude # claude, openai, or gemini
 files: 'src/ tests/' # Files to analyze
 review-types: all # or: security,performance,correctness
 fail-on-critical: true # Fail build on critical issues
 fail-on-high-threshold: 5 # Fail if high issues > threshold
 post-comment: true # Post PR comment
 max-findings: 50 # Max findings in comment
 github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Full Workflow Example

See [`.github/workflows/reviewr.yml`](../.github/workflows/reviewr.yml) for a complete example with:
- Changed files detection
- Conditional execution
- Result artifacts
- Status checks

---

## GitLab CI

### Quick Start

1. **Add API Key as CI/CD Variable**

 Go to your project → Settings → CI/CD → Variables → Add variable

 - Key: `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` or `GEMINI_API_KEY`)
 - Value: Your API key
 - Protected: (recommended)
 - Masked: (recommended)

2. **Add GitLab Token**

 Add another variable for posting comments:

 - Key: `GITLAB_TOKEN`
 - Value: Your personal access token with `api` scope
 - Protected: 
 - Masked: 

3. **Create CI Configuration**

 Create or update `.gitlab-ci.yml`:

 ```yaml
 include:
 - local: '.gitlab-ci-reviewr.yml'
 ```

 Or copy the full template from [`.gitlab-ci-reviewr.yml`](../.gitlab-ci-reviewr.yml)

4. **Commit and Push**

 The pipeline will run automatically on new MRs!

### Configuration Variables

Customize reviewr behavior with CI/CD variables:

```yaml
variables:
 REVIEWR_PROVIDER: "claude" # claude, openai, or gemini
 REVIEWR_FAIL_ON_CRITICAL: "true" # Fail on critical issues
 REVIEWR_HIGH_THRESHOLD: "5" # Fail if high issues > threshold
 REVIEWR_MAX_FINDINGS: "50" # Max findings in comment
```

### Full Pipeline Example

See [`.gitlab-ci-reviewr.yml`](../.gitlab-ci-reviewr.yml) for a complete example with:
- Changed files detection
- MR comment posting
- Artifact storage
- Failure conditions

---

## Configuration

### Review Types

Control which types of analysis to run:

**All types (recommended):**
```yaml
review-types: all
```

**Specific types:**
```yaml
review-types: security,performance,correctness
```

Available types:
- `security` - Security vulnerabilities
- `performance` - Performance issues
- `correctness` - Logic errors
- `maintainability` - Code quality
- `architecture` - Design patterns
- `standards` - Best practices

### Failure Conditions

Control when the build should fail:

**Fail on critical issues:**
```yaml
fail-on-critical: true
```

**Fail on high severity threshold:**
```yaml
fail-on-high-threshold: 5 # Fail if > 5 high severity issues
```

**Never fail (report only):**
```yaml
fail-on-critical: false
fail-on-high-threshold: 0
```

### File Filtering

Analyze specific files or directories:

**All files:**
```yaml
files: .
```

**Specific directories:**
```yaml
files: src/ tests/
```

**Changed files only (GitHub):**
```yaml
- uses: tj-actions/changed-files@v41
 id: changed-files
 with:
 files: |
 **/*.py
 **/*.js
 **/*.ts

- uses: ./.github/actions/reviewr-action
 with:
 files: ${{ steps.changed-files.outputs.all_changed_files }}
```

---

## Advanced Usage

### Multiple AI Providers

Use different providers for different scenarios:

```yaml
# Use Claude for PRs (best quality)
- name: Review with Claude
 if: github.event_name == 'pull_request'
 uses: ./.github/actions/reviewr-action
 with:
 api-key: ${{ secrets.ANTHROPIC_API_KEY }}
 provider: claude

# Use OpenAI for scheduled reviews (faster)
- name: Review with OpenAI
 if: github.event_name == 'schedule'
 uses: ./.github/actions/reviewr-action
 with:
 api-key: ${{ secrets.OPENAI_API_KEY }}
 provider: openai
```

### Custom Thresholds per Branch

```yaml
# Strict for main branch
- name: Review main branch
 if: github.base_ref == 'main'
 with:
 fail-on-critical: true
 fail-on-high-threshold: 0 # No high severity allowed

# Lenient for feature branches
- name: Review feature branch
 if: github.base_ref != 'main'
 with:
 fail-on-critical: true
 fail-on-high-threshold: 10
```

### Scheduled Full Repository Scans

```yaml
on:
 schedule:
 - cron: '0 0 * * 0' # Weekly on Sunday

jobs:
 full-scan:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v4
 
 - uses: ./.github/actions/reviewr-action
 with:
 api-key: ${{ secrets.ANTHROPIC_API_KEY }}
 files: .
 post-comment: false # Don't post comment for scheduled scans
```

### Save Results as Artifacts

**GitHub Actions:**
```yaml
- uses: actions/upload-artifact@v4
 if: always()
 with:
 name: reviewr-results
 path: reviewr-output/
 retention-days: 30
```

**GitLab CI:**
```yaml
artifacts:
 when: always
 paths:
 - reviewr-output/
 expire_in: 30 days
```

---

## Troubleshooting

### Common Issues

#### 1. "No API key found"

**Solution:** Ensure you've added the API key as a secret/variable:
- GitHub: Repository → Settings → Secrets → Actions
- GitLab: Project → Settings → CI/CD → Variables

#### 2. "Permission denied" when posting comments

**GitHub Solution:**
```yaml
permissions:
 pull-requests: write # Required for posting comments
```

**GitLab Solution:**
- Create personal access token with `api` scope
- Add as `GITLAB_TOKEN` variable

#### 3. "No files to analyze"

**Solution:** Check file patterns and ensure changed files match:
```yaml
# GitHub
files: |
 **/*.py
 **/*.js
 **/*.ts
 **/*.go
 **/*.rs
 **/*.java
```

#### 4. Build fails unexpectedly

**Solution:** Check failure thresholds:
```yaml
fail-on-critical: false # Disable to debug
fail-on-high-threshold: 0 # Disable to debug
```

#### 5. API rate limits

**Solution:** 
- Use caching for unchanged files
- Analyze only changed files in PRs
- Use different providers for different workflows

### Debug Mode

Enable verbose logging:

**GitHub Actions:**
```yaml
env:
 ACTIONS_STEP_DEBUG: true
```

**GitLab CI:**
```yaml
variables:
 CI_DEBUG_TRACE: "true"
```

### Getting Help

- [Documentation](https://github.com/clay-good/reviewr)
- [Issue Tracker](https://github.com/clay-good/reviewr/issues)
- [Discussions](https://github.com/clay-good/reviewr/discussions)

---

## Examples

### Minimal Setup (GitHub)

```yaml
name: reviewr
on: [pull_request]
permissions:
 pull-requests: write
jobs:
 review:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v4
 - uses: ./.github/actions/reviewr-action
 with:
 api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Minimal Setup (GitLab)

```yaml
include:
 - local: '.gitlab-ci-reviewr.yml'
```

### Production Setup

See full examples:
- [`.github/workflows/reviewr.yml`](../.github/workflows/reviewr.yml)
- [`.gitlab-ci-reviewr.yml`](../.gitlab-ci-reviewr.yml)

---

**Built by world-class engineers** 

**Status:** Production Ready