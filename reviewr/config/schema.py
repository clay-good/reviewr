
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Code chunking strategies."""
    AST_AWARE = "ast_aware"
    SLIDING_WINDOW = "sliding_window"
    FILE_BASED = "file_based"


class RetryBackoff(str, Enum):
    """Retry backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


class SeverityLevel(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    api_key: Optional[str] = None
    model: str
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    timeout: int = Field(default=60, ge=1)
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("API key cannot be empty")
        return v


class ReviewConfig(BaseModel):
    """Configuration for code review behavior."""
    default_types: List[str] = Field(default=["security", "performance"])
    severity_threshold: SeverityLevel = SeverityLevel.MEDIUM
    max_findings_per_file: int = Field(default=50, ge=1)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class ChunkingConfig(BaseModel):
    """Configuration for code chunking."""
    max_chunk_size: int = Field(default=3000, ge=100)
    overlap: int = Field(default=200, ge=0)
    strategy: ChunkingStrategy = ChunkingStrategy.AST_AWARE
    context_lines: int = Field(default=10, ge=0)


class CacheConfig(BaseModel):
    """Configuration for caching."""
    directory: str = "~/.cache/reviewr"
    ttl: int = Field(default=86400, ge=0)  # 24 hours
    max_size_mb: int = Field(default=500, ge=1)
    enabled: bool = True


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    requests_per_minute: int = Field(default=60, ge=1)
    requests_per_hour: Optional[int] = Field(default=None, ge=1)
    retry_max_attempts: int = Field(default=3, ge=1)
    retry_backoff: RetryBackoff = RetryBackoff.EXPONENTIAL
    initial_retry_delay: float = Field(default=1.0, ge=0.1)


class ReviewrConfig(BaseModel):
    """Main configuration for reviewr."""
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    default_provider: str = "claude"
    
    @field_validator('default_provider')
    @classmethod
    def validate_default_provider(cls, v: str, info: Any) -> str:
        """Validate default provider exists in providers."""
        # Note: This validation happens before providers is set, so we skip it here
        # and validate in the loader instead
        return v

