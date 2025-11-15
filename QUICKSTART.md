# Reviewr Quick Start Guide

Get AI-powered security reviews running in your GitLab pipeline in 5 minutes.

## 1-Minute Setup

### Local Installation

```bash
# Install
pip install reviewr

# Set API key
export AUGMENTCODE_API_KEY="your-api-key-here"

# Run your first security scan
reviewr . --security --output-format html --enhanced-html
```

### GitLab CI/CD Setup

**Step 1:** Create `.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/claygood/reviewr/main/gitlab-ci-simple.yml'
```

**Step 2:** Add CI/CD variable:
- Go to **Settings → CI/CD → Variables**
- Add variable: `AUGMENTCODE_API_KEY` = `your-api-key`
- Enable "Protect" and "Mask"

**Step 3:** Create a merge request - Reviewr runs automatically!

## What You Get

### Example Security Finding

```
🔴 CRITICAL SECURITY ISSUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 File: api/auth.py
📍 Lines: 23-27
🔍 Type: SQL Injection (CWE-89)
💯 Confidence: 0.95

❌ VULNERABILITY:
User-supplied input is directly concatenated into SQL query without
sanitization, allowing attackers to execute arbitrary SQL commands.

⚡ EXPLOITATION SCENARIO:
An attacker can bypass authentication by submitting:
  username: admin' OR '1'='1'--
  password: anything

This returns all users, bypassing the password check.

💥 IMPACT:
- Complete database access (read/write/delete)
- Authentication bypass
- Privilege escalation
- Data exfiltration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIX OPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION 1: Quick Fix - Parameterized Query
──────────────────────────────────────────

CODE:
```python
cursor.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password_hash)
)
```

✅ PROS:
- Simple one-line change
- Prevents SQL injection completely
- No new dependencies needed

❌ CONS:
- Still using raw SQL (harder to maintain)
- No type safety
- Doesn't address password hashing issue

TIME TO FIX: 2 minutes
RISK AFTER FIX: Low


OPTION 2: Secure Fix - ORM with Parameterization
─────────────────────────────────────────────────

CODE:
```python
from werkzeug.security import check_password_hash

user = User.query.filter_by(username=username).first()
if user and check_password_hash(user.password_hash, password):
    return user
```

✅ PROS:
- Type-safe ORM queries
- Proper password hashing
- Cleaner, more maintainable code
- Prevents SQL injection

❌ CONS:
- Requires SQLAlchemy setup
- More code changes needed
- Team needs ORM knowledge

TIME TO FIX: 15 minutes
RISK AFTER FIX: Very Low


OPTION 3: Best Practice - ORM + Input Validation + Rate Limiting
─────────────────────────────────────────────────────────────────

CODE:
```python
from werkzeug.security import check_password_hash
from flask_limiter import Limiter
from validators import validate_username

@limiter.limit("5 per minute")
def login(username, password):
    # Validate input
    username = validate_username(username)
    if not username:
        raise ValueError("Invalid username format")

    # Query with ORM
    user = User.query.filter_by(username=username).first()

    # Check password with timing-safe comparison
    if user and check_password_hash(user.password_hash, password):
        return user

    # Log failed attempts
    log_failed_login(username)
    return None
```

✅ PROS:
- Defense in depth (multiple security layers)
- Rate limiting prevents brute force
- Input validation catches malformed data
- Audit trail for security monitoring
- Industry best practice

❌ CONS:
- More code to write and maintain
- Requires additional libraries
- Team training needed

TIME TO FIX: 30 minutes
RISK AFTER FIX: Minimal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ Use OPTION 3 (Best Practice)

REASONING:
This is a CRITICAL authentication vulnerability in a production system.
The additional 15 minutes to implement defense-in-depth is worth it to:
- Prevent brute force attacks (rate limiting)
- Stop malformed inputs (validation)
- Enable security monitoring (logging)
- Follow industry standards

If time is extremely constrained, implement Option 2 immediately,
then upgrade to Option 3 in the next sprint.

⚠️  DO NOT ship Option 1 to production - missing password hashing!
```

## Common Use Cases

### 1. Pre-Commit Check (Local)

```bash
# Quick security scan before committing
reviewr . --security --diff --diff-base main --output-format markdown
```

**Use when**: Making changes locally, want quick feedback

### 2. Merge Request Review (GitLab CI/CD)

```yaml
# Automatic scan on every MR
security_review:
  script:
    - reviewr . --security --diff --output-format sarif
```

**Use when**: Opening/updating merge requests

### 3. Full Codebase Audit

```bash
# Comprehensive review of entire codebase
reviewr . \
  --security \
  --performance \
  --correctness \
  --output-format html \
  --enhanced-html \
  --deduplicate
```

**Use when**: Initial setup, major refactoring, compliance audit

### 4. Specific File/Directory Review

```bash
# Review only authentication code
reviewr api/auth/ models/user.py --security --output-format html
```

**Use when**: Working on specific feature, targeted review

### 5. Production Deployment Gate

```yaml
# Block deployment if critical issues found
production_gate:
  script:
    - reviewr . --security --fail-on critical
  only:
    - main
```

**Use when**: Protecting production deployments

## CLI Cheat Sheet

```bash
# Basic security scan
reviewr . --security --output-format html

# Security + performance
reviewr . --security --performance --output-format sarif

# All review types
reviewr . --all --output-format html --enhanced-html

# Only changed files (fast!)
reviewr . --security --diff --diff-base main

# Specific provider
reviewr . --security --provider augmentcode --output-format sarif

# Remove duplicates
reviewr . --security --deduplicate --output-format html

# High confidence only
reviewr . --security --min-confidence 0.9 --output-format sarif

# Multiple directories
reviewr src/ api/ lib/ --security --output-format html

# With preset
reviewr . --preset security --output-format sarif

# Interactive mode
reviewr . --security --interactive
```

## Provider Comparison

| Provider | Best For | Speed | Cost | API Key |
|----------|----------|-------|------|---------|
| **Augment Code** | Security focus, multiple solutions | Fast | Low | `AUGMENTCODE_API_KEY` |
| **Claude** | Comprehensive analysis, accuracy | Fast | Medium | `ANTHROPIC_API_KEY` |
| **OpenAI** | General purpose | Medium | Medium | `OPENAI_API_KEY` |
| **Gemini** | Large codebases | Fast | Low | `GOOGLE_API_KEY` |

## Output Formats

### SARIF (for CI/CD)

```bash
reviewr . --security --output-format sarif
```

**Best for**: GitLab Security Dashboard, automated tools
**File**: `reviewr-report.sarif`

### HTML (for humans)

```bash
reviewr . --security --output-format html --enhanced-html
```

**Best for**: Interactive review, presentations, sharing
**File**: `reviewr-report.html`

Features:
- Click to filter by severity/category
- Search findings
- Expand/collapse details
- Mobile-friendly

### Markdown (for documentation)

```bash
reviewr . --security --output-format markdown
```

**Best for**: Commit messages, wiki pages, issue tracking
**File**: `reviewr-report.md`

### JUnit XML (for test reporting)

```bash
reviewr . --security --output-format junit
```

**Best for**: Test runners, CI/CD test reports
**File**: `reviewr-report.xml`

## Cost Examples

With caching and `--diff` mode:

| Project Size | Files Changed | Cost per Scan | Monthly Cost* |
|--------------|---------------|---------------|---------------|
| Small | 5-10 files | $0.10-0.20 | $2-4 |
| Medium | 20-30 files | $0.40-0.60 | $8-12 |
| Large | 50+ files | $1.00-1.50 | $20-30 |

*Based on 20 MRs per month

**Tip**: Use `--diff` mode in CI/CD to scan only changed files!

## Next Steps

### 1. Set up GitLab CI/CD
Follow [GITLAB_SETUP.md](GITLAB_SETUP.md) for detailed instructions

### 2. Configure for Your Team
Create `.reviewr.yml`:

```yaml
review:
  default_provider: augmentcode
  deduplicate_findings: true
  severity_threshold: high

analysis:
  enable_security_analysis: true
  enable_performance_analysis: true

output:
  default_format: html
  enhanced_html: true
```

### 3. Set Up Policies
Define security standards:

```bash
reviewr policy create security-critical my-policy
reviewr policy check --scope pre-commit
```

### 4. Train Your Team
- Review example outputs together
- Discuss fix options and tradeoffs
- Establish workflow (when to run, how to fix)

## Getting Help

- **Documentation**: See main [README.md](README.md)
- **GitLab Setup**: See [GITLAB_SETUP.md](GITLAB_SETUP.md)
- **Issues**: https://github.com/claygood/reviewr/issues

---

**Start securing your code now!** Run your first scan in 60 seconds:

```bash
pip install reviewr
export AUGMENTCODE_API_KEY="your-key"
reviewr . --security --output-format html --enhanced-html
```
