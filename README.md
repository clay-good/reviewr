# reviewr

**Catch bugs before they ship.** A CLI tool that provides AI-powered code review for pre-commit validation and seamless integration with GitLab/GitHub CI/CD pipelines for post-commit (MR/PR) code reviews.

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
- **Parallel Processing**: Multiple review types run concurrently for faster results
- **Secrets Detection**: Local regex-based scanning for API keys and credentials (30+ patterns)
- **Smart Caching**: Reduce API calls and costs with intelligent caching
- **Local-First**: Secrets scanning and validation happen locally before AI processing

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
pip install -e .
```

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
