
from .schema import (
    ProviderConfig,
    ReviewConfig,
    ChunkingConfig,
    CacheConfig,
    RateLimitConfig,
    ReviewrConfig,
    ChunkingStrategy,
    RetryBackoff,
    SeverityLevel,
)


def get_default_config() -> ReviewrConfig:
    """Get default configuration."""
    return ReviewrConfig(
        providers={
            "claude": ProviderConfig(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                temperature=0.0,
            ),
            "openai": ProviderConfig(
                model="gpt-4-turbo-preview",
                max_tokens=4096,
                temperature=0.0,
            ),
            "gemini": ProviderConfig(
                model="gemini-pro",
                max_tokens=4096,
                temperature=0.0,
            ),
        },
        review=ReviewConfig(
            default_types=["security", "performance"],
            severity_threshold=SeverityLevel.MEDIUM,
            max_findings_per_file=50,
            confidence_threshold=0.5,
        ),
        chunking=ChunkingConfig(
            max_chunk_size=3000,
            overlap=200,
            strategy=ChunkingStrategy.AST_AWARE,
            context_lines=10,
        ),
        cache=CacheConfig(
            directory="~/.cache/reviewr",
            ttl=86400,
            max_size_mb=500,
            enabled=True,
        ),
        rate_limiting=RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=None,
            retry_max_attempts=3,
            retry_backoff=RetryBackoff.EXPONENTIAL,
            initial_retry_delay=1.0,
        ),
        default_provider="claude",
    )


DEFAULT_CONFIG_TEMPLATE_YAML = """# reviewr configuration file
# This file uses YAML format and supports environment variable expansion

providers:
  claude:
    api_key: ${ANTHROPIC_API_KEY}  # Set via environment variable
    model: claude-sonnet-4-20250514
    max_tokens: 8192
    temperature: 0.0
    
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo-preview
    max_tokens: 4096
    temperature: 0.0
    
  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
    max_tokens: 4096
    temperature: 0.0

# Default provider to use
default_provider: claude

# Review configuration
review:
  # Default review types to run if none specified
  default_types:
    - security
    - performance
  
  # Minimum severity level to report
  severity_threshold: medium  # critical, high, medium, low, info
  
  # Maximum findings to report per file
  max_findings_per_file: 50
  
  # Minimum confidence threshold (0.0-1.0)
  confidence_threshold: 0.5

# Code chunking configuration
chunking:
  # Maximum chunk size in tokens
  max_chunk_size: 3000
  
  # Overlap between chunks in tokens
  overlap: 200
  
  # Chunking strategy: ast_aware, sliding_window, file_based
  strategy: ast_aware
  
  # Number of context lines to include
  context_lines: 10

# Caching configuration
cache:
  # Cache directory
  directory: ~/.cache/reviewr
  
  # Time to live in seconds (86400 = 24 hours)
  ttl: 86400
  
  # Maximum cache size in MB
  max_size_mb: 500
  
  # Enable/disable caching
  enabled: true

# Rate limiting configuration
rate_limiting:
  # Maximum requests per minute
  requests_per_minute: 60
  
  # Maximum requests per hour (optional)
  # requests_per_hour: 1000
  
  # Maximum retry attempts
  retry_max_attempts: 3
  
  # Retry backoff strategy: exponential, linear, constant
  retry_backoff: exponential
  
  # Initial retry delay in seconds
  initial_retry_delay: 1.0
"""

DEFAULT_CONFIG_TEMPLATE_TOML = """# reviewr configuration file
# This file uses TOML format

[providers.claude]
api_key = "${ANTHROPIC_API_KEY}"  # Set via environment variable
model = "claude-sonnet-4-20250514"
max_tokens = 8192
temperature = 0.0

[providers.openai]
api_key = "${OPENAI_API_KEY}"
model = "gpt-4-turbo-preview"
max_tokens = 4096
temperature = 0.0

[providers.gemini]
api_key = "${GOOGLE_API_KEY}"
model = "gemini-pro"
max_tokens = 4096
temperature = 0.0

# Default provider to use
default_provider = "claude"

[review]
# Default review types to run if none specified
default_types = ["security", "performance"]

# Minimum severity level to report
severity_threshold = "medium"  # critical, high, medium, low, info

# Maximum findings to report per file
max_findings_per_file = 50

# Minimum confidence threshold (0.0-1.0)
confidence_threshold = 0.5

[chunking]
# Maximum chunk size in tokens
max_chunk_size = 3000

# Overlap between chunks in tokens
overlap = 200

# Chunking strategy: ast_aware, sliding_window, file_based
strategy = "ast_aware"

# Number of context lines to include
context_lines = 10

[cache]
# Cache directory
directory = "~/.cache/reviewr"

# Time to live in seconds (86400 = 24 hours)
ttl = 86400

# Maximum cache size in MB
max_size_mb = 500

# Enable/disable caching
enabled = true

[rate_limiting]
# Maximum requests per minute
requests_per_minute = 60

# Maximum retry attempts
retry_max_attempts = 3

# Retry backoff strategy: exponential, linear, constant
retry_backoff = "exponential"

# Initial retry delay in seconds
initial_retry_delay = 1.0
"""

# Alias for backward compatibility
DEFAULT_CONFIG_TEMPLATE = DEFAULT_CONFIG_TEMPLATE_YAML

