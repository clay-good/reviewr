# 🚀 Quick Start: CI/CD Integration

Get automated code review on every PR/MR in **5 minutes**.

---

## GitHub Actions

### Step 1: Add API Key

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

- **Name:** `ANTHROPIC_API_KEY`
- **Value:** Your Claude API key

### Step 2: Create Workflow

Create `.github/workflows/reviewr.yml`:

```yaml
name: reviewr Code Review
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
          fail-on-critical: true
```

### Step 3: Done! 🎉

Open a PR and watch reviewr automatically review your code!

---

## GitLab CI

### Step 1: Add API Keys

Go to your project → **Settings** → **CI/CD** → **Variables** → **Add variable**

**Variable 1:**
- **Key:** `ANTHROPIC_API_KEY`
- **Value:** Your Claude API key
- **Protected:** ✅
- **Masked:** ✅

**Variable 2:**
- **Key:** `GITLAB_TOKEN`
- **Value:** Your personal access token (with `api` scope)
- **Protected:** ✅
- **Masked:** ✅

### Step 2: Create Pipeline

Create or update `.gitlab-ci.yml`:

```yaml
include:
  - local: '.gitlab-ci-reviewr.yml'
```

### Step 3: Done! 🎉

Open an MR and watch reviewr automatically review your code!

---

## What You Get

### Automated PR/MR Comments

```markdown
## 🤖 reviewr Code Review

### 🔴 **Action Required**

| Metric | Value |
|--------|-------|
| Files Reviewed | 5 |
| Total Issues | 12 |
| 🔴 Critical | 2 |
| 🟠 High | 3 |
| 🟡 Medium | 5 |

### 🚨 Critical & High Severity Issues

#### 🔴 🔒 Security
**📄 File:** `src/auth.py` (Lines 10-15)
**Issue:** SQL injection vulnerability detected
💡 **Suggestion:** Use parameterized queries
```

### Commit Status Checks

- ✅ **Pass** - No critical issues
- ❌ **Fail** - Critical issues found

### Changed Files Only

Only reviews files that changed in the PR/MR (fast and efficient!)

---

## Configuration

### Fail on Critical Issues

```yaml
fail-on-critical: true  # Fail build if critical issues found
```

### Fail on High Severity Threshold

```yaml
fail-on-high-threshold: 5  # Fail if > 5 high severity issues
```

### Choose AI Provider

```yaml
provider: claude  # or: openai, gemini
```

### Review Specific Types

```yaml
review-types: security,performance,correctness
```

Or review everything:

```yaml
review-types: all
```

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

### Production Setup (GitHub)

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
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/reviewr-action
        with:
          api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          provider: claude
          fail-on-critical: true
          fail-on-high-threshold: 5
          max-findings: 50
```

### Custom Configuration (GitLab)

```yaml
include:
  - local: '.gitlab-ci-reviewr.yml'

variables:
  REVIEWR_PROVIDER: "claude"
  REVIEWR_FAIL_ON_CRITICAL: "true"
  REVIEWR_HIGH_THRESHOLD: "3"
  REVIEWR_MAX_FINDINGS: "30"
```

---

## Troubleshooting

### "No API key found"

**Solution:** Add API key as a secret/variable in your repository settings.

### "Permission denied" when posting comments

**GitHub Solution:**
```yaml
permissions:
  pull-requests: write
```

**GitLab Solution:** Add `GITLAB_TOKEN` variable with `api` scope.

### "No files to analyze"

**Solution:** Ensure your file patterns match changed files:
```yaml
files: |
  **/*.py
  **/*.js
  **/*.ts
```

### Build fails unexpectedly

**Solution:** Adjust failure thresholds:
```yaml
fail-on-critical: false
fail-on-high-threshold: 0
```

---

## Next Steps

- 📖 [Full Documentation](docs/CI_CD_INTEGRATION.md)
- 🔧 [Configuration Guide](docs/CI_CD_INTEGRATION.md#configuration)
- 🐛 [Troubleshooting](docs/CI_CD_INTEGRATION.md#troubleshooting)
- 💬 [Get Help](https://github.com/clay-good/reviewr/issues)

---

## Benefits

✅ **Zero manual work** - Automatic reviews on every PR/MR  
✅ **Fast feedback** - Results in minutes, not hours  
✅ **Catch bugs early** - Before they reach production  
✅ **Consistent standards** - Same quality bar for all code  
✅ **Learning tool** - Developers learn from AI suggestions  
✅ **Cost savings** - Prevent expensive production fixes  

---

**Built by world-class engineers** 🌟

**Status:** ✅ Production Ready

