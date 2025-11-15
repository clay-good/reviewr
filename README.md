# reviewr

AI-powered code security review platform that runs in your GitLab CI/CD pipeline to catch critical vulnerabilities before they reach production.

## Quick Start with GitLab CI/CD (Recommended)

### 1. Add to Your GitLab Repository

Create `.gitlab-ci.yml` in your repository root:

```yaml
# Simple setup - runs on every merge request
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/gitlab-ci-simple.yml'
```

### 2. Set Your API Key

Go to **Settings → CI/CD → Variables** and add:

- **Variable**: `AUGMENTCODE_API_KEY` (or `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)
- **Value**: Your API key
- **Protected**: ✓ Yes
- **Masked**: ✓ Yes

### 3. Create a Merge Request

That's it! Reviewr will automatically:
- ✅ Scan your code for critical security vulnerabilities
- ✅ Post findings as comments on your MR
- ✅ Block merges if critical issues are found
- ✅ Generate HTML and SARIF reports

## What You Get

**Focus on What Matters:**
- 🎯 Critical security vulnerabilities only (SQL injection, XSS, auth bypasses, etc.)
- 🔍 Multiple fix options with tradeoffs explained
- 💡 Concrete code examples for each solution
- 🚫 Blocks dangerous code from reaching production

**Smart Analysis:**
- Runs only on changed code (fast!)
- Deduplicates similar findings
- 90%+ confidence scores on critical issues
- Supports 10+ languages

**Pipeline Integration:**
- ⚡ 2-3 minute scan times
- 📊 SARIF format for GitLab Security Dashboard
- 📱 Interactive HTML reports
- 🔒 Quality gates to enforce security standards

## GitLab CI/CD Setup Options

### Option A: Simple Setup (Recommended)

Uses pre-built Python image for fastest setup:

```yaml
# .gitlab-ci.yml
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/gitlab-ci-simple.yml'
```

**CI/CD Variables Required:**
- `AUGMENTCODE_API_KEY` (or `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`)
- `GITLAB_TOKEN` (optional - for posting MR comments)

### Option B: Docker Setup (More Control)

Uses Docker container for consistent environment:

```yaml
# .gitlab-ci.yml
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/.gitlab-ci.yml'
```

Same variables required as Option A.

### Option C: Custom Configuration

Copy and customize the pipeline:

```yaml
security_review:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install reviewr[all]
  script:
    - |
      reviewr . \
        --security \
        --performance \
        --output-format sarif \
        --provider augmentcode \
        --deduplicate \
        --diff
  artifacts:
    reports:
      sast: reviewr-report.sarif
  only:
    - merge_requests
```

## Supported AI Models

Choose your provider with `--provider` flag or `REVIEWR_PROVIDER` variable:

| Provider | Model | Best For | API Key Variable |
|----------|-------|----------|------------------|
| **Augment Code** | augment-code-1 | Security focus, multiple solutions | `AUGMENTCODE_API_KEY` |
| **Claude** | claude-sonnet-4 | Comprehensive analysis, accuracy | `ANTHROPIC_API_KEY` |
| **OpenAI** | gpt-4-turbo | General purpose | `OPENAI_API_KEY` |
| **Gemini** | gemini-1.5-pro | Large codebases | `GOOGLE_API_KEY` |

## Local Installation (Optional)

For local development and testing:

```bash
# Install
pip install reviewr

# Set API key
export AUGMENTCODE_API_KEY="your-key"

# Run security review
reviewr . --security --output-format html --enhanced-html

# Review only changed files
reviewr . --security --diff --diff-base main
```

## Example: Security Review Output

When Reviewr finds a critical SQL injection vulnerability:

```
🔴 CRITICAL: SQL Injection Vulnerability (CWE-89)

File: api/users.py, Lines 42-45
Confidence: 0.95

ISSUE:
User input is directly concatenated into SQL query, allowing attackers to
execute arbitrary SQL commands and access/modify/delete database data.

EXPLOITATION:
An attacker can append `' OR '1'='1` to bypass authentication or use
`'; DROP TABLE users--` to delete data.

FIX OPTIONS:

OPTION 1 - Quick Fix (Parameterized Query):
```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```
✅ Pros: Simple, prevents injection
❌ Cons: Still using raw SQL, not ORM

OPTION 2 - Secure Fix (ORM):
```python
user = User.query.filter_by(username=username).first()
```
✅ Pros: Type-safe, prevents injection, easier to maintain
❌ Cons: Requires ORM setup

OPTION 3 - Best Practice (ORM + Input Validation):
```python
from validators import validate_username
username = validate_username(request.form['username'])
user = User.query.filter_by(username=username).first()
```
✅ Pros: Defense in depth, validates input, uses ORM
❌ Cons: More code, requires validator library

RECOMMENDATION: Option 3 - Provides multiple security layers
```

## Configuration

### Pipeline Customization

```yaml
# .gitlab-ci.yml
variables:
  REVIEWR_PROVIDER: "augmentcode"  # or claude, openai, gemini
  REVIEWR_PRESET: "security"       # security, performance, comprehensive
  REVIEWR_MIN_CONFIDENCE: "0.8"    # Filter findings below this confidence
```

### Local Configuration

```yaml
# .reviewr.yml
review:
  deduplicate_findings: true
  default_provider: augmentcode
  focus_critical: true              # Only report critical/high severity

analysis:
  enable_security_analysis: true
  enable_performance_analysis: true
  enable_correctness_analysis: false

output:
  default_format: html
  enhanced_html: true
```

## Advanced Features

### Interactive HTML Reports

```bash
reviewr . --security --output-format html --enhanced-html
```

Features:
- Filter by severity, category, file
- Search findings in real-time
- Priority scoring
- Quick summary of critical issues

### Policy Enforcement

Define security policies for your team:

```bash
# Create policy from template
reviewr policy create security-critical my-policy

# Check code against policy
reviewr policy check --scope pre-commit

# In GitLab CI/CD
reviewr . --policy my-policy --fail-on-violation
```

### Auto-Fix (Experimental)

```bash
# Preview fixes
reviewr fix app.py --dry-run

# Apply fixes interactively
reviewr fix app.py --interactive
```

Fixes: unused imports, type hints, SQL injection, XSS, weak crypto, and more.

## Supported Languages

Python • JavaScript/TypeScript • Go • Rust • Java • C++ • Ruby • PHP • Shell • Kotlin

## Cost Estimate (with caching)

- **Small project** (10 files): $0.20-0.30 per scan
- **Medium project** (50 files): $0.90-1.00 per scan
- **Large project** (200 files): $3.60-4.00 per scan

Incremental scans (--diff mode) reduce costs by 70-90%.

## CLI Reference

### Basic Usage

```bash
reviewr <path> [options]
```

### Key Options

| Option | Description |
|--------|-------------|
| `--security` | Security vulnerabilities (recommended) |
| `--performance` | Performance issues |
| `--correctness` | Logic errors and bugs |
| `--all` | All review types |
| `--output-format` | sarif, html, markdown, junit |
| `--provider` | augmentcode, claude, openai, gemini |
| `--deduplicate` | Remove duplicate findings |
| `--diff` | Only review changed code |
| `--diff-base` | Base branch (default: main) |
| `--enhanced-html` | Interactive HTML reports |

### Examples

```bash
# Security review for GitLab MR
reviewr . --security --output-format sarif --diff

# Comprehensive review with HTML report
reviewr src/ --all --output-format html --enhanced-html

# Security scan with specific provider
reviewr . --security --provider augmentcode --deduplicate

# Review specific files only
reviewr api/ models/ --security --output-format sarif
```

## GitHub Actions

Reviewr also works with GitHub:

```yaml
name: Security Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install reviewr
      - run: reviewr . --security --output-format sarif
        env:
          AUGMENTCODE_API_KEY: ${{ secrets.AUGMENTCODE_API_KEY }}
      - uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: reviewr-report.sarif
```

## Docker Usage

### Build Image

```bash
docker build -t reviewr .
```

### Run Review

```bash
docker run --rm \
  -v $(pwd):/code \
  -e AUGMENTCODE_API_KEY="your-key" \
  reviewr /code --security --output-format sarif
```

## Troubleshooting

**"No API key found"**
```bash
# Set in GitLab CI/CD Variables or locally:
export AUGMENTCODE_API_KEY="your-key"
```

**"Pipeline timeout"**
```yaml
# Use --diff to only scan changed files:
reviewr . --security --diff --diff-base main
```

**"Too many findings"**
```bash
# Focus on critical/high only with augmentcode provider:
reviewr . --security --provider augmentcode --deduplicate
```

**"Quality gate failing"**
```bash
# Review the HTML report in pipeline artifacts
# Fix critical issues before merge
```

## Support & Documentation

- **Issues**: https://github.com/claygood/reviewr/issues
- **Full Docs**: https://github.com/claygood/reviewr
- **CI/CD Examples**: See `gitlab-ci-simple.yml` and `.gitlab-ci.yml`

## License

MIT License - see LICENSE file

---

**Start securing your code today!** Add reviewr to your GitLab pipeline in 5 minutes.
