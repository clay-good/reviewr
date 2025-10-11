# reviewr

**Catch bugs before they ship.** A CLI tool that provides AI-powered code review for pre-commit validation and seamless integration with GitLab/GitHub CI/CD pipelines for post-commit (MR/PR) code reviews.

## Why reviewr?

**Ship faster with confidence** - Automated code review catches security vulnerabilities, performance issues, and bugs before they reach production, reducing debugging time by up to 70%.

**Save development costs** - Early detection prevents expensive production fixes. One critical security vulnerability caught in development saves thousands in incident response and reputation damage.

**Seamless workflow integration** - Works as a pre-commit hook for instant feedback and integrates with CI/CD pipelines for automated PR/MR reviews, requiring zero workflow changes.

**Comprehensive analysis** - Covers security, performance, correctness, maintainability, architecture, and coding standards with detailed SARIF and Markdown reports for easy tracking and compliance.

**⚡ Multi-LLM flexibility** - Choose from Claude, OpenAI GPT, or Google Gemini based on your needs, budget, and compliance requirements.

## Features

- **Multiple LLM Providers**: Support for Claude, OpenAI GPT, and Google Gemini
- **Comprehensive Reviews**: Security, performance, correctness, maintainability, architecture, and standards
- **Code Explanation**: `--explain` flag to understand unfamiliar code quickly
- **Flexible Input**: Review single files or entire directories
- **SARIF + Markdown Output**: Automatic generation of SARIF JSON and Markdown reports for CI/CD integration and compliance
- **Configurable**: YAML configuration with environment variable support
- **Smart Chunking**: Intelligent code chunking for large files
- **Language Detection**: Automatic programming language detection (30+ languages)
- **Retry Logic**: Automatic retries with exponential backoff
- **Progress Tracking**: Beautiful progress bars and status updates
- **CI/CD Integration**: Ready-to-use examples for GitHub Actions and GitLab CI with SARIF upload support

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

2. **Initialize configuration** (optional):

```bash
reviewr init
```

This creates a `.reviewr.yml` file in your current directory.

3. **Review your code** (automatically generates SARIF and Markdown reports):

```bash
# Review a single file (creates reviewr-report.sarif and reviewr-report.md)
reviewr review path/to/file.py

# Review a directory
reviewr review path/to/project

# Review with specific types
reviewr review path/to/file.py --security --performance

# Review all types
reviewr review path/to/file.py --all

# Generate only Markdown report
reviewr review path/to/file.py --output markdown

# Generate only SARIF report
reviewr review path/to/file.py --output sarif
```

## Usage

### Basic Commands

```bash
# Review code (default: security and performance, generates both SARIF and Markdown)
reviewr review <path>

# Review with specific types
reviewr review <path> --security --performance --correctness

# Review all types
reviewr review <path> --all

# Use a specific provider
reviewr review <path> --provider claude

# Generate only Markdown report
reviewr review <path> --output markdown

# Generate only SARIF report
reviewr review <path> --output sarif

# Show current configuration
reviewr show-config

# Initialize configuration file
reviewr init

# Global options (can be used with any command)
reviewr --config /path/to/config.yml review <path>
reviewr --provider openai review <path>
reviewr --verbose review <path>
reviewr --no-cache review <path>
reviewr --output markdown review <path>
```

### Global Options

- `--config`, `-c`: Path to configuration file
- `--provider`, `-p`: Override default LLM provider (claude, openai, gemini)
- `--verbose`, `-v`: Increase verbosity (use -vv for more detail)
- `--no-cache`: Disable caching for this run
- `--output`, `-o`: Output format (sarif, markdown, both) - default: both

### Review Types

- `--security`: Security vulnerabilities, injections, authentication issues
- `--performance`: Inefficient algorithms, bottlenecks, optimization opportunities
- `--correctness`: Logic errors, edge cases, potential bugs
- `--maintainability`: Code clarity, documentation, naming conventions
- `--architecture`: Design patterns, SOLID principles, code structure
- `--standards`: Language idioms, conventions, style guidelines
- `--explain`: Comprehensive code explanation and overview (great for understanding unfamiliar code)
- `--all`: Run all review types (except explain)

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
reviewr review app.py --security
```

### Review a project directory with all checks

```bash
reviewr review ./src --all
# Creates: reviewr-report.sarif and reviewr-report.md
```

### Review with a specific provider

```bash
reviewr review app.py --provider openai --performance
```

### Review with custom patterns

```bash
reviewr review ./src --include "*.py" --exclude "test_*.py"
```

### Review with explicit language specification

```bash
reviewr review script.txt --language python --security
```

### Explain code to understand it quickly

```bash
# Get a comprehensive explanation of a file
reviewr review complex_module.py --explain

# Explain an entire directory
reviewr review ./src --explain
```

## Output Formats

### Default: SARIF + Markdown (recommended)

By default, reviewr generates both formats automatically:
- `reviewr-report.sarif` - SARIF 2.1.0 JSON for CI/CD integration and compliance
- `reviewr-report.md` - Human-readable Markdown report

### SARIF Only

```bash
reviewr review app.py --output sarif
```

Generates only the SARIF JSON file for automated processing and CI/CD integration.

### Markdown Only

```bash
reviewr review app.py --output markdown
```

Generates only the Markdown report for documentation or manual review.

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

### Pre-commit Hook

For local development, you can set up a pre-commit hook to review code before committing.

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

echo "Running reviewr on staged files..."

# Review staged files
for file in $STAGED_FILES; do
  if [ -f "$file" ]; then
    echo "Reviewing $file"
    reviewr review "$file" --security --correctness

    if [ $? -ne 0 ]; then
      echo "Review found issues in $file"
      echo "Commit aborted. Fix issues or use 'git commit --no-verify' to skip."
      exit 1
    fi
  fi
done

echo "Review complete. Proceeding with commit."
exit 0
```

Make the hook executable:

```bash
chmod +x .git/hooks/pre-commit
```

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
