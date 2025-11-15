# GitLab CI/CD Setup Guide for Reviewr

This guide will help you set up Reviewr to automatically scan your code for security vulnerabilities on every merge request.

## Prerequisites

- A GitLab repository
- An API key from one of these providers:
  - **Augment Code** (recommended for security focus)
  - **Anthropic Claude**
  - **OpenAI**
  - **Google Gemini**

## Quick Setup (5 minutes)

### Step 1: Add Configuration File

Create `.gitlab-ci.yml` in your repository root:

```yaml
# Use the simple pre-configured pipeline
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/gitlab-ci-simple.yml'
```

### Step 2: Set API Key as CI/CD Variable

1. Go to your GitLab project
2. Navigate to **Settings → CI/CD**
3. Expand **Variables**
4. Click **Add variable**
5. Configure:
   - **Key**: `AUGMENTCODE_API_KEY` (or `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`)
   - **Value**: Your API key
   - **Type**: Variable
   - **Environment scope**: All
   - **Protect variable**: ✓ (recommended)
   - **Mask variable**: ✓ (recommended)
   - **Expand variable reference**: ✗

6. Click **Add variable**

### Step 3: (Optional) Enable MR Comments

To have Reviewr post findings directly to your merge requests:

1. Create a GitLab Personal Access Token:
   - Go to **Settings → Access Tokens**
   - Name: "Reviewr CI/CD"
   - Scopes: ✓ `api`, ✓ `write_repository`
   - Click **Create personal access token**

2. Add as CI/CD variable:
   - **Key**: `GITLAB_TOKEN`
   - **Value**: Your personal access token
   - **Protect variable**: ✓
   - **Mask variable**: ✓

### Step 4: Create a Merge Request

That's it! Create a merge request and Reviewr will automatically:
- ✅ Scan changed code for critical security issues
- ✅ Generate SARIF report for GitLab Security Dashboard
- ✅ Generate interactive HTML report
- ✅ Post findings as MR comments (if `GITLAB_TOKEN` is set)
- ✅ Block merge if critical vulnerabilities are found

## Pipeline Options

### Option A: Simple Pipeline (Recommended)

Best for: Quick setup, most projects

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/gitlab-ci-simple.yml'
```

**Features:**
- Uses Python image (faster than Docker build)
- Scans only changed files (`--diff`)
- Generates SARIF + HTML reports
- Posts MR comments
- Blocks critical issues

### Option B: Docker Pipeline

Best for: Consistent environment, complex dependencies

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/.gitlab-ci.yml'
```

**Features:**
- Builds Docker container
- Isolated environment
- Same features as Option A

### Option C: Custom Pipeline

Best for: Fine-tuned control

```yaml
variables:
  REVIEWR_PROVIDER: "augmentcode"

stages:
  - security

security_scan:
  stage: security
  image: python:3.11-slim
  before_script:
    - pip install reviewr[all]
  script:
    - |
      reviewr . \
        --security \
        --performance \
        --correctness \
        --output-format sarif \
        --output-file reviewr-report.sarif \
        --provider $REVIEWR_PROVIDER \
        --deduplicate \
        --diff \
        --diff-base $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
  artifacts:
    reports:
      sast: reviewr-report.sarif
    paths:
      - reviewr-report.sarif
  only:
    - merge_requests
```

## Customization

### Change AI Provider

```yaml
variables:
  REVIEWR_PROVIDER: "augmentcode"  # Options: augmentcode, claude, openai, gemini
```

### Adjust Review Types

```yaml
script:
  - reviewr . --security --performance --output-format sarif  # Security + performance only
  - reviewr . --all --output-format sarif  # All review types
```

### Change Quality Gate Behavior

```yaml
# Allow merge even with critical issues (not recommended)
security_gate:
  allow_failure: true
```

### Scan Specific Directories

```yaml
script:
  - reviewr src/ api/ --security --output-format sarif  # Only scan src/ and api/
```

### Adjust Confidence Threshold

```yaml
script:
  - reviewr . --security --min-confidence 0.9 --output-format sarif  # Only high-confidence findings
```

## Pipeline Stages Explained

### 1. Security Review Stage

```yaml
security_review:
  stage: review
  script:
    - reviewr . --security --performance --output-format sarif --diff
```

**What it does:**
- Scans only files changed in the MR (`--diff`)
- Focuses on security and performance issues
- Generates SARIF report for GitLab Security Dashboard
- Takes 2-3 minutes on average

### 2. Post Results Stage

```yaml
post_results:
  stage: report
  script:
    - reviewr-gitlab --mr-iid $CI_MERGE_REQUEST_IID --security
```

**What it does:**
- Posts findings as comments on the MR
- Links to line numbers in code
- Includes fix suggestions
- Requires `GITLAB_TOKEN`

### 3. Quality Gate Stage

```yaml
quality_gate:
  stage: report
  script:
    - jq '[.runs[].results[] | select(.level == "error")] | length' reviewr-report.sarif
```

**What it does:**
- Checks SARIF report for critical issues
- Fails pipeline if critical issues found
- Blocks merge until fixed

## Viewing Results

### GitLab Security Dashboard

1. Go to **Security & Compliance → Vulnerability Report**
2. View all findings with severity levels
3. Filter by type, severity, or file
4. Track remediation status

### HTML Report

1. Go to pipeline page
2. Click **Browse** under artifacts
3. Download `reviewr-report.html`
4. Open in browser for interactive report

### MR Comments

If `GITLAB_TOKEN` is set, findings appear as MR comments with:
- Severity badge
- Line numbers
- Issue description
- Multiple fix options with tradeoffs
- Code snippets

## Troubleshooting

### "API key not found"

**Problem**: Pipeline fails with "No API key found"

**Solution**:
1. Verify CI/CD variable is named correctly:
   - `AUGMENTCODE_API_KEY` for Augment Code
   - `ANTHROPIC_API_KEY` for Claude
   - `OPENAI_API_KEY` for OpenAI
   - `GOOGLE_API_KEY` for Gemini
2. Ensure variable is not protected if running on unprotected branches
3. Check that variable is not expired

### Pipeline Timeout

**Problem**: Pipeline runs too long and times out

**Solution**:
```yaml
# Scan only changed files
script:
  - reviewr . --security --diff --diff-base main --output-format sarif

# Or scan specific directories only
script:
  - reviewr src/ --security --output-format sarif
```

### Too Many Findings

**Problem**: Overwhelmed by number of findings

**Solution**:
```yaml
# Use Augment Code provider (focuses on critical issues)
variables:
  REVIEWR_PROVIDER: "augmentcode"

# Enable deduplication
script:
  - reviewr . --security --deduplicate --output-format sarif

# Increase confidence threshold
script:
  - reviewr . --security --min-confidence 0.9 --output-format sarif
```

### Quality Gate Always Failing

**Problem**: Pipeline always fails on quality gate

**Solution**:
```yaml
# Review HTML report to see issues
# Fix critical issues first

# Temporarily allow failure while fixing
quality_gate:
  allow_failure: true  # Remove once issues fixed
```

### MR Comments Not Appearing

**Problem**: No comments posted to MR

**Solution**:
1. Verify `GITLAB_TOKEN` is set
2. Ensure token has `api` and `write_repository` scopes
3. Check `post_results` job logs for errors
4. Verify token is not expired

## Cost Optimization

### Use Incremental Scanning

```yaml
script:
  - reviewr . --security --diff --diff-base $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
```

**Saves**: 70-90% on API costs by scanning only changed files

### Enable Caching

Reviewr automatically caches results for 24 hours. Same code won't be re-analyzed.

### Use Augment Code Provider

Augment Code is optimized for security scanning and uses fewer tokens.

## Advanced Configuration

### Multi-Stage Pipeline

```yaml
stages:
  - quick_scan
  - full_scan
  - deploy

quick_security_scan:
  stage: quick_scan
  script:
    - reviewr . --security --diff --preset quick --output-format sarif
  only:
    - merge_requests

full_security_scan:
  stage: full_scan
  script:
    - reviewr . --all --output-format sarif
  only:
    - main
    - production
```

### Policy Enforcement

```yaml
policy_check:
  stage: review
  script:
    - reviewr . --security --policy security-critical --fail-on-violation
```

### Multiple Reports

```yaml
script:
  - reviewr . --security --output-format sarif --output-file security.sarif
  - reviewr . --security --output-format html --enhanced-html --output-file security.html
  - reviewr . --security --output-format markdown --output-file security.md
artifacts:
  paths:
    - security.sarif
    - security.html
    - security.md
```

## Best Practices

1. **Start with security-only scans**: `--security`
2. **Use `--diff` mode**: Only scan changed code
3. **Enable deduplication**: `--deduplicate`
4. **Set up MR comments**: Improves developer workflow
5. **Review HTML reports regularly**: Better visualization
6. **Fix critical issues immediately**: Don't merge with critical vulnerabilities
7. **Use protected variables**: Keep API keys secure
8. **Monitor pipeline performance**: Optimize if scans take too long

## Getting Help

- **Issues**: https://github.com/claygood/reviewr/issues
- **Documentation**: See main README.md
- **Examples**: Check `gitlab-ci-simple.yml` and `.gitlab-ci.yml`

---

**Ready to secure your code?** Follow the Quick Setup above and you'll be protected in 5 minutes!
