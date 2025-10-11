# reviewr

AI-powered code review CLI tool supporting multiple LLM providers (Claude, OpenAI, Gemini).

## Features

- **Multiple LLM Providers**: Support for Claude, OpenAI GPT, and Google Gemini
- **Comprehensive Reviews**: Security, performance, correctness, maintainability, architecture, and standards
- **Code Explanation**: NEW! `--explain` flag to understand unfamiliar code quickly
- **Flexible Input**: Review single files or entire directories
- **Multiple Output Formats**: Terminal (with colors) and Markdown
- **Configurable**: YAML configuration with environment variable support
- **Smart Chunking**: Intelligent code chunking for large files
- **Language Detection**: Automatic programming language detection (30+ languages)
- **Retry Logic**: Automatic retries with exponential backoff
- **Progress Tracking**: Beautiful progress bars and status updates

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

3. **Review your code**:

```bash
# Review a single file
reviewr review path/to/file.py

# Review a directory
reviewr review path/to/project

# Review with specific types
reviewr review path/to/file.py --security --performance

# Review all types
reviewr review path/to/file.py --all
```

## Usage

### Basic Commands

```bash
# Review code (default: security and performance)
reviewr review <path>

# Review with specific types
reviewr review <path> --security --performance --correctness

# Review all types
reviewr review <path> --all

# Use a specific provider
reviewr review <path> --provider claude

# Output as Markdown
reviewr review <path> --output markdown

# Show current configuration
reviewr show-config

# Initialize configuration file
reviewr init
```

### Review Types

- `--security`: Security vulnerabilities, injections, authentication issues
- `--performance`: Inefficient algorithms, bottlenecks, optimization opportunities
- `--correctness`: Logic errors, edge cases, potential bugs
- `--maintainability`: Code clarity, documentation, naming conventions
- `--architecture`: Design patterns, SOLID principles, code structure
- `--standards`: Language idioms, conventions, style guidelines
- `--explain`: Comprehensive code explanation and overview (great for understanding unfamiliar code!)
- `--all`: Run all review types (except explain)

### Configuration

Configuration is loaded from multiple sources with the following precedence (highest to lowest):

1. Command-line arguments
2. Environment variables (`REVIEWR_*`)
3. Project config (`.reviewr.yml` in current directory)
4. User config (`~/.config/reviewr/config.yml`)
5. Default values

#### Example Configuration File

```yaml
# .reviewr.yml
providers:
  claude:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    max_tokens: 4096
    temperature: 0.0
    
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo-preview
    max_tokens: 4096
    
  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
    max_tokens: 4096

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
  retry_max_attempts: 3
  retry_backoff: exponential
  initial_retry_delay: 1.0
```

## Examples

### Review a Python file for security issues

```bash
reviewr review app.py --security
```

### Review a project directory with all checks

```bash
reviewr review ./src --all --output markdown > review.md
```

### Review with a specific provider

```bash
reviewr review app.py --provider openai --performance
```

### Review with custom patterns

```bash
reviewr review ./src --include "*.py" --exclude "test_*.py"
```

### Explain code to understand it quickly

```bash
# Get a comprehensive explanation of a file
reviewr review complex_module.py --explain

# Explain an entire directory
reviewr review ./src --explain
```

## Output Formats

### Terminal (default)

Colorful, formatted output with emojis and syntax highlighting.

### Markdown

```bash
reviewr review app.py --output markdown > review.md
```

Generates a Markdown report suitable for documentation or GitHub.

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

## Implementation Status

reviewr is **production-ready** for local file and directory reviews!

### Fully Implemented
- Multi-provider support (Claude, OpenAI, Gemini)
- All 7 review types (including --explain)
- CLI with all core commands
- Configuration system
- File discovery and language detection
- Output formatting (terminal, markdown)
- Error handling and retries
- Comprehensive documentation

### Planned Features
- Git integration and PR reviews
- Active caching system
- Advanced rate limiting
- AST-aware code chunking
- Comprehensive test suite
- Cost tracking with detailed pricing

## Development

### Running Tests

```bash
# Tests structure is ready, implementation pending
pytest tests/
```

### Code Formatting

```bash
black reviewr/
ruff check reviewr/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Priority areas for contribution:
- Test suite implementation
- Git/PR integration
- AST-aware chunking
- Active caching
- Additional language support

