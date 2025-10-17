# reviewr

**Catch bugs before they ship.** A CLI tool that provides AI-powered code review for pre-commit validation and seamless integration with GitLab/GitHub CI/CD pipelines for post-commit (MR/PR) code reviews.

<<<<<<< HEAD
## Quick Start

```bash
# Install
pip install -e .

# Review a Python file
reviewr app.py --all --output-format sarif

# Review JavaScript/TypeScript with local analysis
reviewr src/app.js --all --output-format markdown

# Use custom rules for team standards
reviewr . --all --rules team-rules.yml

# Interactive mode for reviewing findings
reviewr . --all --interactive

# GitHub PR integration
reviewr-github review --pr 123 --repo owner/repo
```

=======
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
## Why reviewr?

**Ship faster with confidence** - Automated code review catches security vulnerabilities, performance issues, and bugs before they reach production, reducing debugging time by up to 70%.

**Save development costs** - Early detection prevents expensive production fixes. One critical security vulnerability caught in development saves thousands in incident response and reputation damage.

**Seamless workflow integration** - Works as a pre-commit hook for instant feedback and integrates with CI/CD pipelines for automated PR/MR reviews, requiring zero workflow changes.

**Comprehensive analysis** - Covers security, performance, correctness, maintainability, architecture, and coding standards with detailed SARIF and Markdown reports for easy tracking and compliance.

**Multi-LLM flexibility** - Choose from Claude, OpenAI GPT, or Google Gemini based on your needs, budget, and compliance requirements.

## Features

### Core Features
- **Multiple LLM Providers**: Support for Claude, OpenAI GPT, and Google Gemini
- **Comprehensive Reviews**: Security, performance, correctness, maintainability, architecture, and standards
- **Code Explanation**: `--explain` flag to understand unfamiliar code quickly
- **Flexible Input**: Review single files or entire directories
- **Multiple Output Formats**: SARIF JSON, Markdown, HTML, and JUnit XML
- **Smart Chunking**: Intelligent code chunking for large files
- **Language Detection**: Automatic programming language detection (30+ languages)
- **Retry Logic**: Automatic retries with exponential backoff
- **Progress Tracking**: Beautiful progress bars and status updates

### Performance & Security
<<<<<<< HEAD
- **Parallel Processing**: Multiple review types run concurrently for faster results (6x speedup)
- **Intelligent Caching**: Hash-based caching with automatic invalidation (50-80% API call reduction)
- **Local-First Analysis**: AST-based analysis for Python and JavaScript/TypeScript (no API calls required)
- **Custom Rules Engine**: Define team-specific rules with regex patterns (YAML/JSON configuration)
- **Interactive Mode**: Review findings one-by-one with accept/reject/fix actions
- **Secrets Detection**: Local regex-based scanning for API keys and credentials (30+ patterns)
- **GitHub Integration**: Automated PR reviews with inline comments
- **Cache Statistics**: Real-time hit/miss rates and performance metrics
=======
- **Parallel Processing**: Multiple review types run concurrently for faster results
- **Secrets Detection**: Local regex-based scanning for API keys and credentials (30+ patterns)
- **Smart Caching**: Reduce API calls and costs with intelligent caching
- **Local-First**: Secrets scanning and validation happen locally before AI processing
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4

### Configuration & Integration
- **Flexible Configuration**: Support for YAML (.reviewr.yml), TOML (.reviewr.toml), and pyproject.toml
- **Pre-commit Hooks**: Git pre-commit integration with configurable quality thresholds
- **VS Code Extension**: Native VS Code integration with Problems panel support
- **CI/CD Ready**: Examples for GitHub Actions and GitLab CI with SARIF upload support

## Example Project Cost 
- **Small** (10 files): ~$0.20-0.30
- **Medium** (50 files): ~$0.90-1.00
- **Large** (200 files): ~$3.60-4.00

## Installation

### Using Poetry (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd reviewr

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
<<<<<<< HEAD
# Basic installation
pip install -e .

# With GitHub integration
pip install -e ".[github]"

# With all extras
pip install -e ".[all]"
```

**Note**: This project requires Python 3.9 or higher.

=======
pip install -e .
```

>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
## Quick Start

1. **Set up API keys** (choose one or more providers):

```bash
export ANTHROPIC_API_KEY="your-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_API_KEY="your-gemini-api-key"
```

2. **Review your code**:

```bash
# Review a single file with all review types, output as SARIF
reviewr path/to/file.py --all --output-format sarif

# Review with specific types, output as HTML
reviewr path/to/file.py --security --performance --output-format html

# Review a directory with all types, output as Markdown
reviewr path/to/project --all --output-format markdown

# Explain code (great for understanding unfamiliar code)
reviewr path/to/file.py --explain --output-format html

# Output as JUnit XML for CI/CD integration
reviewr path/to/file.py --all --output-format junit
```

**Note**: You must specify:
- At least one review type (or `--all`)
- An output format (`--output-format`)

3. **Optional: Initialize configuration**:

```bash
# Creates .reviewr.yml in current directory
reviewr init

# Or create .reviewr.toml for TOML format
# Or add [tool.reviewr] section to pyproject.toml
```

## Usage

### Basic Commands

```bash
# Review code with all types, output as SARIF
reviewr <path> --all --output-format sarif

# Review with specific types, output as Markdown
reviewr <path> --security --performance --correctness --output-format markdown

# Review with specific types, output as HTML
reviewr <path> --security --output-format html

# Review with specific types, output as JUnit XML
reviewr <path> --all --output-format junit

# Use a specific provider
reviewr <path> --all --output-format sarif --provider claude

# Verbose output
reviewr <path> --all --output-format sarif --verbose

# Disable caching
reviewr <path> --all --output-format sarif --no-cache

# Use custom config file
reviewr <path> --all --output-format sarif --config /path/to/config.yml
```

### Options

- `--security`: Security review (vulnerabilities, injections, auth issues)
- `--performance`: Performance review (inefficient algorithms, bottlenecks)
- `--correctness`: Correctness review (logic errors, edge cases)
- `--maintainability`: Maintainability review (clarity, documentation)
- `--architecture`: Architecture review (design patterns, SOLID principles)
- `--standards`: Standards review (idioms, conventions, style)
- `--explain`: Comprehensive code explanation and overview
- `--all`: Run all review types (except explain)
- `--output-format`: **Required** - Output format (sarif, markdown, html, junit)
- `--config`, `-c`: Path to configuration file
- `--provider`, `-p`: Override default LLM provider (claude, openai, gemini)
- `--verbose`, `-v`: Increase verbosity
- `--no-cache`: Disable caching for this run
- `--language`, `-l`: Explicitly specify programming language
- `--include`: File patterns to include (can be used multiple times)
- `--exclude`: File patterns to exclude (can be used multiple times)

### Review Types

- `--security`: Security vulnerabilities, injections, authentication issues (includes local secrets detection)
- `--performance`: Inefficient algorithms, bottlenecks, optimization opportunities
- `--correctness`: Logic errors, edge cases, potential bugs
- `--maintainability`: Code clarity, documentation, naming conventions
- `--architecture`: Design patterns, SOLID principles, code structure
- `--standards`: Language idioms, conventions, style guidelines
- `--explain`: Comprehensive code explanation and overview (great for understanding unfamiliar code)
- `--all`: Run all review types (except explain)

**Note**: All reviews include automatic local secrets detection before AI processing.

### Review Command Options

- `--language`, `-l`: Explicitly specify programming language (auto-detected if not provided)
- `--include`: File patterns to include (can be used multiple times)
- `--exclude`: File patterns to exclude (can be used multiple times)

### Configuration

Configuration is loaded from multiple sources with the following precedence (highest to lowest):

1. Command-line arguments
2. Environment variables (`REVIEWR_*` and API keys)
3. Project config (`.reviewr.yml` in current directory)
4. User config (`~/.config/reviewr/config.yml`)
5. Default values

#### Environment Variables

**API Keys:**
- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google Gemini API key

**Configuration Overrides:**
- `REVIEWR_DEFAULT_PROVIDER`: Override default provider
- `REVIEWR_CACHE_ENABLED`: Enable/disable caching (true/false)

#### Example Configuration File

```yaml
# .reviewr.yml
providers:
  claude:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
    max_tokens: 8192
    temperature: 0.0
    timeout: 60

  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo-preview
    max_tokens: 4096
    temperature: 0.0
    timeout: 60

  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
    max_tokens: 4096
    temperature: 0.0
    timeout: 60

default_provider: claude

review:
  default_types:
    - security
    - performance
  severity_threshold: medium
  max_findings_per_file: 50
  confidence_threshold: 0.5

chunking:
  max_chunk_size: 3000
  overlap: 200
  strategy: ast_aware
  context_lines: 10

cache:
  directory: ~/.cache/reviewr
  ttl: 86400  # 24 hours
  max_size_mb: 500
  enabled: true

rate_limiting:
  requests_per_minute: 60
  requests_per_hour: null  # optional
  retry_max_attempts: 3
  retry_backoff: exponential
  initial_retry_delay: 1.0
```

### Supported Models

#### Claude (Anthropic)
- `claude-sonnet-4-20250514` (default, 200K context)
- `claude-3-5-sonnet-20241022` (200K context)
- `claude-3-opus-20240229` (200K context)
- `claude-3-sonnet-20240229` (200K context)
- `claude-3-haiku-20240307` (200K context)

#### OpenAI
- `gpt-4-turbo-preview` (default, 128K context)
- `gpt-4-turbo` (128K context)
- `gpt-4` (8K context)
- `gpt-3.5-turbo` (16K context)
- `gpt-3.5-turbo-16k` (16K context)

#### Google Gemini
- `gemini-pro` (default, 32K context)
- `gemini-1.5-pro` (1M context)
- `gemini-1.5-flash` (1M context)

## Examples

### Review a Python file for security issues

```bash
reviewr app.py --security --output-format sarif
```

### Review a project directory with all checks

```bash
reviewr ./src --all --output-format markdown
```

### Review with a specific provider

```bash
reviewr app.py --performance --output-format html --provider openai
```

### Review with custom patterns

```bash
reviewr ./src --all --output-format sarif --include "*.py" --exclude "test_*.py"
```

### Review with explicit language specification

```bash
reviewr script.txt --security --output-format sarif --language python
```

### Explain code to understand it quickly

```bash
# Get a comprehensive explanation of a file
reviewr complex_module.py --explain --output-format html

# Explain an entire directory
reviewr ./src --explain --output-format markdown
```

## Output Formats

reviewr supports multiple output formats to fit different use cases. You must specify the format using `--output-format`.

### SARIF JSON

```bash
reviewr app.py --all --output-format sarif
```

SARIF 2.1.0 JSON format for CI/CD integration and compliance. Creates `reviewr-report.sarif`.

### Markdown

```bash
reviewr app.py --all --output-format markdown
```

Human-readable Markdown report for documentation. Creates `reviewr-report.md`.

### HTML

```bash
reviewr app.py --all --output-format html
```

Beautiful HTML report with styling for easy viewing in browsers. Creates `reviewr-report.html`.

### JUnit XML

```bash
reviewr app.py --all --output-format junit
```

JUnit XML format for test integration and CI/CD systems. Creates `reviewr-report.xml`.

### SARIF Integration Benefits

**GitHub Integration**: SARIF files automatically appear in GitHub's Security tab, providing:
- Inline code annotations in pull requests
- Security dashboard integration
- Compliance reporting and tracking
- Integration with GitHub Advanced Security

**GitLab Integration**: SARIF files integrate with GitLab's security features:
- Security dashboard visibility
- Merge request security widgets
- Compliance pipeline integration
- Vulnerability management

**Tool Compatibility**: SARIF is the industry standard, supported by:
- SonarQube, CodeQL, Semgrep, and other security tools
- IDE extensions and security platforms
- Compliance and audit tools
- Custom security workflows

## CI/CD Integration

### GitHub Actions

You can integrate reviewr into your GitHub Actions workflow to automatically review pull requests.

#### Basic GitHub Actions Workflow

Create `.github/workflows/reviewr.yml`:

```yaml
name: Code Review with reviewr

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install reviewr
        run: |
          pip install -e .

      - name: Run reviewr on changed files
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          # Get list of changed files
          git diff --name-only origin/${{ github.base_ref }}...HEAD > changed_files.txt

          # Review each changed file (generates both SARIF and Markdown)
          while IFS= read -r file; do
            if [ -f "$file" ]; then
              echo "Reviewing $file"
              reviewr review "$file" --security --performance --correctness
            fi
          done < changed_files.txt

      - name: Upload SARIF results to GitHub
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: reviewr-report.sarif
          category: reviewr

      - name: Comment PR with review
        uses: actions/github-script@v6
        if: always()
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            if (fs.existsSync('reviewr-report.md')) {
              const report = fs.readFileSync('reviewr-report.md', 'utf8');
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: '## Code Review Report\n\n' + report
              });
            }
```

#### Advanced GitHub Actions with Annotations

For inline annotations on pull requests:

```yaml
name: Advanced Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      checks: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install reviewr
        run: pip install -e .

      - name: Run security review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          reviewr review . --security

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: reviewr-report.sarif
          category: reviewr-security

      - name: Upload review reports as artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: review-reports
          path: |
            reviewr-report.sarif
            reviewr-report.md

      - name: Post review summary
        uses: actions/github-script@v6
        if: always()
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            if (fs.existsSync('reviewr-report.md')) {
              const report = fs.readFileSync('reviewr-report.md', 'utf8');
              await github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: report
              });
            }
```

#### GitHub Actions Configuration Tips

1. **Store API keys as secrets**: Go to repository Settings > Secrets and variables > Actions
2. **Add secrets**:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
3. **Customize review types**: Adjust the `--security --performance` flags based on your needs
4. **Filter file types**: Add file extension filters to review only specific languages
5. **Set up branch protection**: Require the reviewr check to pass before merging

### GitLab CI/CD

You can integrate reviewr into your GitLab CI/CD pipeline to review merge requests.

#### Basic GitLab CI Configuration

Create or update `.gitlab-ci.yml`:

```yaml
stages:
  - review

code_review:
  stage: review
  image: python:3.9
  before_script:
    - pip install -e .
  script:
    - |
      # Get list of changed files in merge request
      git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
      git diff --name-only origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD > changed_files.txt

      # Review changed files (generates both SARIF and Markdown)
      while IFS= read -r file; do
        if [ -f "$file" ]; then
          echo "Reviewing $file"
          reviewr review "$file" --security --performance --correctness
        fi
      done < changed_files.txt

      # Display summary
      echo "Review completed. Reports generated:"
      ls -la reviewr-report.*
  artifacts:
    paths:
      - reviewr-report.sarif
      - reviewr-report.md
    reports:
      sast: reviewr-report.sarif
    expire_in: 1 week
  only:
    - merge_requests
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
    OPENAI_API_KEY: $OPENAI_API_KEY
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

#### Advanced GitLab CI with MR Comments

For posting review comments directly to merge requests:

```yaml
stages:
  - review
  - report

code_review:
  stage: review
  image: python:3.9
  before_script:
    - pip install -e .
  script:
    - reviewr review . --all
  artifacts:
    paths:
      - reviewr-report.sarif
      - reviewr-report.md
    reports:
      sast: reviewr-report.sarif
    expire_in: 1 week
  only:
    - merge_requests
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY

post_review_comment:
  stage: report
  image: alpine:latest
  before_script:
    - apk add --no-cache curl jq
  script:
    - |
      if [ -f "reviewr-report.md" ]; then
        REPORT=$(cat reviewr-report.md)
        curl --request POST \
          --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          --header "Content-Type: application/json" \
          --data "{\"body\": \"## Code Review Report\n\n$REPORT\"}" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
      fi
  dependencies:
    - code_review
  only:
    - merge_requests
  variables:
    GITLAB_TOKEN: $GITLAB_TOKEN
```

#### GitLab CI Configuration Tips

1. **Store API keys as CI/CD variables**: Go to Settings > CI/CD > Variables
2. **Add variables**:
   - `ANTHROPIC_API_KEY` (masked, protected)
   - `OPENAI_API_KEY` (masked, protected)
   - `GOOGLE_API_KEY` (masked, protected)
   - `GITLAB_TOKEN` (for posting comments, needs `api` scope)
3. **Use protected variables**: Enable "Protected" for production branches
4. **Customize review scope**: Adjust review types and file patterns
5. **Set up merge request approvals**: Require review completion before merging

### Pre-commit Hook Integration

reviewr includes built-in support for pre-commit hooks using the [pre-commit framework](https://pre-commit.com/).

#### Installation

1. **Install pre-commit**:

```bash
pip install pre-commit
```

2. **Create `.pre-commit-config.yaml`** in your repository:

```yaml
repos:
  - repo: local
    hooks:
      # Full review (security + correctness)
      - id: reviewr
        name: reviewr code review
        entry: reviewr-pre-commit
        language: system
        types: [python, javascript, typescript, java, go, rust]
        pass_filenames: true
        require_serial: true
        stages: [commit]

      # Secrets scanner (fast, no AI required)
      - id: reviewr-secrets
        name: reviewr secrets scanner
        entry: reviewr-pre-commit --secrets-only
        language: system
        types: [text]
        pass_filenames: true
        stages: [commit]
```

3. **Install the hooks**:

```bash
pre-commit install
```

#### Usage

The hooks will run automatically on `git commit`. To run manually:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Skip hooks for a specific commit
git commit --no-verify
```

#### Hook Options

The `reviewr-pre-commit` command supports several options:

```bash
# Security-only review (faster)
reviewr-pre-commit --security-only file.py

# Secrets-only scan (very fast, no AI)
reviewr-pre-commit --secrets-only file.py

# Custom fail threshold
reviewr-pre-commit --fail-on high file.py

# Verbose output
reviewr-pre-commit --verbose file.py
```

#### Benefits

- **Catch issues early**: Find problems before they reach the repository
- **Fast feedback**: Get immediate feedback during development
- **Configurable**: Choose which checks to run and when
- **No AI for secrets**: Secrets scanning is instant and doesn't require API calls
- **Team consistency**: Ensure all team members run the same checks

### VS Code Extension

reviewr includes a lightweight VS Code extension that integrates directly with the Problems panel.

#### Installation

1. **Install reviewr CLI** (if not already installed):

```bash
pip install -e /path/to/reviewr
```

2. **Build and install the extension**:

```bash
cd vscode-extension
npm install
npm run compile
npm run package
code --install-extension reviewr-vscode-0.1.0.vsix
```

#### Usage

**Command Palette** (Ctrl+Shift+P / Cmd+Shift+P):
- `reviewr: Review Current File` - Analyze the active file
- `reviewr: Review Entire Workspace` - Analyze all files in workspace

**Context Menu**:
- Right-click in editor or on a file in Explorer
- Select "Review Current File"

#### Configuration

Open VS Code Settings (Ctrl+, / Cmd+,) and search for "reviewr":

```json
{
  "reviewr.cliPath": "reviewr",
  "reviewr.useAllReviewTypes": true,
  "reviewr.reviewTypes": ["security", "performance", "correctness"],
  "reviewr.autoReview": false,
  "reviewr.clearProblemsOnReview": true
}
```

#### Features

- **Problems Panel Integration**: View findings directly in VS Code's Problems panel
- **Click to Navigate**: Click on any finding to jump to the relevant code
- **Auto-review on Save**: Optionally run reviews automatically when you save files
- **Configurable Review Types**: Choose which types of reviews to run
- **SARIF Support**: Uses SARIF format for rich diagnostic information

#### Benefits

- **Seamless Integration**: Works within your existing VS Code workflow
- **Instant Feedback**: See issues as you code
- **No Context Switching**: Stay in your editor
- **Rich Diagnostics**: Detailed information and suggestions inline

### Docker Integration

You can run reviewr in a Docker container for consistent environments.

#### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["reviewr"]
CMD ["--help"]
```

#### Build and run

```bash
# Build the image
docker build -t reviewr:latest .

# Run reviewr in container
docker run --rm \
  -v $(pwd):/code \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  reviewr:latest review /code --security
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  reviewr:
    build: .
    volumes:
      - ./code:/code
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    command: review /code --all
```

Run with:

```bash
docker-compose run reviewr
```

<<<<<<< HEAD
## Local-First Analysis

reviewr includes powerful local analysis capabilities that provide instant feedback without any API calls.

### What is Local Analysis?

Local analysis uses Abstract Syntax Tree (AST) parsing and static analysis to detect issues directly in your code, without sending anything to an AI service. This means:

- **Instant results** (no network latency)
- **Zero API costs** (no LLM calls)
- **Complete privacy** (code never leaves your machine)
- **Deterministic results** (same code = same findings)

### Supported Languages

Currently supported:
- **Python**: Full AST-based analysis with 10+ checks
- **JavaScript/TypeScript**: Regex-based analysis with 10+ checks (includes JSX/TSX)

Coming soon: Java, Go, Ruby, and more!

### What Does It Detect?

#### Python Analysis

**Complexity Issues:**
- Cyclomatic complexity: Functions with too many decision points
- Nesting depth: Deeply nested code blocks
- Function length: Functions that are too long
- Parameter count: Functions with too many parameters

**Code Smells:**
- Bare except clauses: Catching all exceptions without specificity
- Swallowed exceptions: Exception handlers with only pass
- Mutable default arguments: The classic Python gotcha
- Duplicate code: Functions with identical implementations

**Dead Code:**
- Unused functions: Functions that are never called
- Unreachable code: Code after return statements
- Unused imports: Imported modules that are never used
- Wildcard imports: from module import *

#### JavaScript/TypeScript Analysis

**Complexity Issues:**
- Cyclomatic complexity: Functions with too many decision points
- Function length: Functions that are too long
- Callback hell: Deeply nested callbacks

**Code Quality:**
- Console statements: console.log/debug/info/warn/error
- var usage: Detects var instead of let/const
- Equality operators: Detects == instead of ===
- Empty catch blocks: Exception handling without logic
- Nested ternary operators: Reduces readability
- Magic numbers: Numeric literals without constants
- Unused variables: Basic unused variable detection

### Usage

Local analysis is **enabled by default** and runs automatically:

```bash
# Local analysis runs automatically
reviewr app.py --all --output-format sarif

# Disable local analysis if needed
reviewr app.py --all --output-format sarif --no-local-analysis
```

### Example Output

```
Review Summary:
Files reviewed: 5
Total findings: 23

Local Analysis:
Files analyzed: 5
Issues found: 12
No API calls required for local analysis

API requests: 8
Tokens used: 15,234
```

### Performance Benefits

- **30-40% fewer AI calls**: Many issues caught locally
- **Instant feedback**: No waiting for API responses
- **Cost savings**: Reduced LLM API usage
- **Better UX**: Immediate results for common issues

### Example Findings

```python
# High complexity detected
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x > 10:
                    if y > 10:
                        return "too complex"
# → Function has cyclomatic complexity of 6 (target: <10)

# Mutable default argument detected
def append_to_list(item, lst=[]):
    lst.append(item)
    return lst
# → Use None as default: def func(item, lst=None): lst = lst or []

# Unused import detected
import os  # Never used
import sys

def main():
    print(sys.version)
# → Remove unused import 'os'
```

## GitHub Integration

reviewr can automatically review GitHub Pull Requests and post inline comments directly on your PRs!

### Quick Start

```bash
# Install with GitHub support
pip install -e ".[github]"

# Set GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Review a PR (auto-detects PR number in CI)
reviewr-github --all

# Review specific PR
reviewr-github --pr-number 123 --all

# Approve if no issues
reviewr-github --all --approve-if-no-issues

# Request changes on critical issues
reviewr-github --all --request-changes-on-critical
```

### GitHub Actions Setup

Create `.github/workflows/reviewr-pr.yml`:

```yaml
name: reviewr PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install reviewr
        run: pip install -e ".[github]"

      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          reviewr-github \
            --pr-number ${{ github.event.pull_request.number }} \
            --all \
            --request-changes-on-critical
```

### Features

- ✅ **Automated PR Reviews**: Reviews all changed files automatically
- ✅ **Inline Comments**: Posts findings as inline comments on specific lines
- ✅ **Review Status**: Can approve PRs or request changes
- ✅ **Smart Filtering**: Only comments on changed files
- ✅ **Rich Summaries**: Posts comprehensive review summaries
- ✅ **Auto-detection**: Automatically detects PR number and repository

### Example Output

reviewr posts inline comments like:

```
🟠 HIGH: SQL injection vulnerability detected

The user input is directly concatenated into the SQL query.

Suggestion: Use parameterized queries to prevent SQL injection.

Confidence: 95%
```

And a summary comment:

```markdown
## 🤖 reviewr Code Review Summary

**Files reviewed**: 5
**Total findings**: 12

**Findings by severity**:
🔴 2 critical, 🟠 3 high, 🟡 4 medium, 🔵 3 low

**Local analysis**: 8 issues found (no API calls)

⚠️ **This PR has critical or high severity issues that should be addressed.**
```

**See [GITHUB_INTEGRATION.md](GITHUB_INTEGRATION.md) for complete documentation.**

## Intelligent Caching

reviewr includes an intelligent caching system that dramatically reduces API calls and costs by caching review results.

### How It Works

- **Hash-based**: Cache keys are based on file content hash (SHA-256), not file path
- **Automatic Invalidation**: Cache is automatically invalidated when file content changes
- **Multi-dimensional**: Separate cache entries for different review types, providers, and models
- **Persistent**: Cache survives across sessions (stored in `~/.cache/reviewr/`)
- **TTL Support**: Cache entries expire after 7 days by default

### Performance Benefits

- **50-80% reduction** in API calls for repeated reviews
- **Instant results** for cached files
- **Cost savings** on LLM API usage
- **Faster CI/CD** pipelines with cached results

### Usage

```bash
# First run - cache miss, calls API
reviewr app.py --security --output-format sarif
# ⏱️  Takes 5 seconds

# Second run - cache hit, instant results!
reviewr app.py --security --output-format sarif
# ⚡ Takes <1 second

# Disable caching when needed
reviewr app.py --security --output-format sarif --no-cache

# Cache is automatically invalidated when file changes
echo "# new code" >> app.py
reviewr app.py --security --output-format sarif
# ⏱️  Cache miss, calls API again
```

### Cache Statistics

reviewr displays cache performance metrics after each run:

```
Review Summary:
Files reviewed: 5
Total findings: 12

Cache Performance:
Cache hits: 3
Cache misses: 2
Hit rate: 60.0%
```

### Cache Management

The cache is stored in `~/.cache/reviewr/` and can be manually cleared if needed:

```bash
# Clear cache directory
rm -rf ~/.cache/reviewr/
```

## Custom Rules Engine

reviewr includes a powerful custom rules engine that allows you to define team-specific coding standards and patterns using regex-based rules.

### What is the Custom Rules Engine?

The custom rules engine allows you to:

- Define custom patterns to detect in your codebase
- Enforce team-specific coding standards
- Catch project-specific anti-patterns
- Create language-specific rules
- Run rules locally without API calls

### Rule Definition Format

Rules can be defined in YAML or JSON format:

#### YAML Format

```yaml
rules:
  - id: no-hardcoded-api-keys
    name: No Hardcoded API Keys
    description: Detect hardcoded API keys in code
    pattern: '(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']'
    severity: critical
    message: Hardcoded API key detected
    suggestion: Use environment variables or a secrets manager
    languages:
      - python
      - javascript
      - typescript
    enabled: true
    case_sensitive: false
    multiline: false

  - id: no-console-log
    name: No Console Statements
    description: Detect console.log statements
    pattern: 'console\.(log|debug|info)'
    severity: low
    message: Console statement detected
    suggestion: Remove console statements before committing
    languages:
      - javascript
      - typescript
    enabled: true
```

#### JSON Format

```json
{
  "rules": [
    {
      "id": "no-hardcoded-api-keys",
      "name": "No Hardcoded API Keys",
      "description": "Detect hardcoded API keys in code",
      "pattern": "(api[_-]?key|apikey)\\s*=\\s*[\"'][^\"']+[\"']",
      "severity": "critical",
      "message": "Hardcoded API key detected",
      "suggestion": "Use environment variables or a secrets manager",
      "languages": ["python", "javascript", "typescript"],
      "enabled": true,
      "case_sensitive": false,
      "multiline": false
    }
  ]
}
```

### Default Rules

reviewr includes 8 built-in recommended rules:

1. **no-hardcoded-secrets**: Detects API keys, passwords, tokens
2. **no-todo-comments**: Detects TODO comments
3. **no-fixme-comments**: Detects FIXME comments
4. **no-debugger**: Detects debugger statements (JS/TS)
5. **no-print-statements**: Detects print statements (Python)
6. **no-eval**: Detects eval() usage
7. **no-sql-concat**: Detects SQL injection via concatenation
8. **no-weak-crypto**: Detects MD5, SHA1, DES usage

### Usage

```bash
# Use custom rules file
reviewr app.py --all --rules my-rules.yml

# Custom rules work with any review type
reviewr src/ --security --rules team-standards.json

# Combine with other features
reviewr . --all --rules rules.yml --output-format sarif
```

### Example Output

```
Review Summary:
Files reviewed: 10
Total findings: 15

Custom Rules:
Files analyzed: 10
Issues found: 8
No API calls required for custom rules

API requests: 12
Tokens used: 8,234
```

### Rule Severity Levels

- **critical**: Security vulnerabilities, data leaks
- **high**: Major bugs, performance issues
- **medium**: Code quality issues, maintainability concerns
- **low**: Style issues, minor improvements
- **info**: Informational findings

### Language Filtering

Rules can be restricted to specific languages:

```yaml
rules:
  - id: python-specific-rule
    pattern: 'some_pattern'
    languages:
      - python
    # This rule only runs on Python files

  - id: javascript-specific-rule
    pattern: 'another_pattern'
    languages:
      - javascript
      - typescript
      - jsx
      - tsx
    # This rule only runs on JavaScript/TypeScript files
```

### Pattern Tips

- Use raw strings in YAML to avoid escaping issues
- Test patterns with online regex testers
- Use word boundaries (\b) for precise matching
- Consider case sensitivity for your use case
- Use multiline mode for patterns spanning multiple lines

### Example: Team-Specific Rules

```yaml
rules:
  # Enforce company naming conventions
  - id: component-naming
    pattern: 'class\s+(?!Component)[A-Z]\w+\s*\('
    severity: medium
    message: Component classes must end with 'Component'
    languages: [python]

  # Prevent deprecated API usage
  - id: no-deprecated-api
    pattern: 'old_api_function\('
    severity: high
    message: old_api_function is deprecated
    suggestion: Use new_api_function instead
    languages: [python, javascript]

  # Enforce error handling
  - id: require-error-handling
    pattern: 'fetch\([^)]+\)(?!\s*\.catch)'
    severity: medium
    message: fetch calls must include error handling
    suggestion: Add .catch() or try/catch block
    languages: [javascript, typescript]
```

## Interactive Mode

reviewr includes an interactive mode that allows you to review findings one-by-one, making decisions about each issue before generating the final report.

### What is Interactive Mode?

Interactive mode provides a guided review experience where you can:

- Review each finding individually with full context
- Accept findings you agree with
- Reject false positives or irrelevant findings
- Apply suggested fixes automatically (when available)
- Skip findings to decide later
- Export your decisions for future reference

### Usage

```bash
# Enable interactive mode with -i or --interactive
reviewr app.py --all --interactive

# Works with any review type
reviewr src/ --security --performance --interactive

# Combine with other features
reviewr . --all --interactive --rules custom-rules.yml
```

### Interactive Review Flow

When you run reviewr in interactive mode, you will see each finding displayed with:

1. **Severity level** (critical, high, medium, low, info)
2. **File path and line numbers**
3. **Issue type** (security, performance, etc.)
4. **Detailed message** explaining the issue
5. **Suggestion** for how to fix it (when available)
6. **Code snippet** showing the problematic code
7. **Confidence level** (if less than 100%)

### Available Actions

For each finding, you can choose:

- **[a]ccept**: Include this finding in the final report
- **[r]eject**: Exclude this finding (with optional note)
- **[f]ix**: Apply the suggested fix automatically (when available)
- **[s]kip**: Skip this finding for now (default)

### Example Session

```
Interactive Review Mode
Found 5 issue(s) to review

Finding 1/5
CRITICAL
File: app.py
Lines: 45-47
Type: security

Message:
Hardcoded API key detected in source code

Suggestion:
Move API key to environment variable or secrets manager

Code:
45  def connect_api():
46      api_key = "sk-1234567890abcdef"
47      return ApiClient(api_key)

Action (accept, reject, fix, skip): a

Finding 2/5
MEDIUM
File: utils.py
Lines: 23-25
Type: performance

Message:
List comprehension would be more efficient than loop

Suggestion:
Replace loop with: results = [process(item) for item in items]

Code:
23  results = []
24  for item in items:
25      results.append(process(item))

Action (accept, reject, fix, skip): f
Applying fix...
This is a suggestion only. Manual review recommended.
Proceed with applying fix? (y/n): n
Fix not applied.

Finding 3/5
LOW
File: test.py
Lines: 100-100
Type: maintainability

Message:
TODO comment found

Code:
100  # TODO: refactor this later

Action (accept, reject, fix, skip): r
Add a note? (y/n): y
Note: This is intentional, tracked in JIRA-123

Review Summary
Action          Count
accept          1
reject          1
skip            3

Rejected findings with notes:
  - test.py:100: This is intentional, tracked in JIRA-123

Decisions exported to: reviewr-decisions.json
```

### Decision Export

All decisions are automatically exported to `reviewr-decisions.json`:

```json
[
  {
    "file": "app.py",
    "line": 45,
    "severity": "critical",
    "message": "Hardcoded API key detected in source code",
    "action": "accept",
    "note": null
  },
  {
    "file": "test.py",
    "line": 100,
    "severity": "low",
    "message": "TODO comment found",
    "action": "reject",
    "note": "This is intentional, tracked in JIRA-123"
  }
]
```

### Benefits

- **Reduce false positives**: Filter out irrelevant findings before reporting
- **Learn from findings**: Understand each issue in detail
- **Quick triage**: Make fast decisions on what matters
- **Track decisions**: Export decisions for team review
- **Better reports**: Only include findings you care about

### Use Cases

**Pre-commit review:**
```bash
# Review changes before committing
git diff --name-only | xargs reviewr --all --interactive
```

**Team code review:**
```bash
# Review PR changes interactively
reviewr src/ --all --interactive --output-format markdown
```

**Learning and training:**
```bash
# Use interactive mode to learn about code quality issues
reviewr examples/ --all --interactive
```

### Tips

- Use interactive mode for smaller changesets (1-50 findings)
- For large reviews, use filters to reduce findings first
- Rejected findings with notes help document false positives
- Export decisions to share with your team
- Combine with custom rules for team-specific standards

### When Cache is Invalidated

- File content changes (detected via SHA-256 hash)
- Different review types requested
- Different LLM provider or model used
- Cache entry expires (after 7 days)

=======
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
## Secrets Detection

reviewr includes built-in local secrets detection that scans for hardcoded credentials before sending code to AI.

### Features

- **30+ Secret Patterns**: Detects AWS keys, GitHub tokens, API keys, database URLs, and more
- **Local Processing**: No AI required, instant results
- **Automatic Redaction**: Secrets are redacted before AI processing
- **Zero False Negatives**: Comprehensive pattern matching
- **Smart Filtering**: Reduces false positives with context-aware detection

### Detected Secret Types

- AWS Access Keys & Secret Keys
- GitHub Tokens (PAT, OAuth, App tokens)
- Google API Keys & OAuth tokens
- Slack Tokens & Webhooks
- Stripe API Keys
- Heroku API Keys
- Database Connection Strings
- Private Keys (RSA, EC, DSA)
- JWT Tokens
- Bearer Tokens
- SSH Keys
- And 20+ more patterns

### Usage

Secrets detection runs automatically during all security reviews:

```bash
# Secrets are detected and reported automatically
reviewr app.py --security --output-format sarif

# Use pre-commit hook for instant feedback
reviewr-pre-commit --secrets-only app.py
```

### Example Output

```
    Secrets detected in app.py:
  Line 15: aws_access_key - AKIA...XXXX
  Line 16: github_token - ghp_...XXXX
  Line 42: database_url - postgres://user:pass@...

    Found 3 potential secret(s)
Remove hardcoded secrets and use environment variables or a secrets management system.
```

## Supported Languages

- Python
- JavaScript/TypeScript
- Java
- C/C++
- C#
- Go
- Rust
- Ruby
- PHP
- Swift
- Kotlin
- And many more...

## Troubleshooting

### API Key Issues

If you encounter authentication errors:

1. Verify your API keys are set correctly:
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $OPENAI_API_KEY
   echo $GOOGLE_API_KEY
   ```

2. Ensure keys are exported in your current shell session

3. For CI/CD, verify secrets/variables are configured correctly

### Rate Limiting

If you hit rate limits:

1. Adjust `requests_per_minute` in `.reviewr.yml`
2. Use a different provider with higher limits
3. Review fewer files at once
4. Enable caching to reduce API calls

### Installation Issues

If installation fails:

1. Ensure Python 3.9+ is installed:
   ```bash
   python3 --version
   ```

2. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

3. Install in a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```
<<<<<<< HEAD
=======

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

Built with:
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Anthropic](https://www.anthropic.com/) - Claude API
- [OpenAI](https://openai.com/) - GPT API
- [Google](https://ai.google.dev/) - Gemini API
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
