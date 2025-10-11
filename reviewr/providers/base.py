"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ReviewType(Enum):
    """Types of code reviews."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    ARCHITECTURE = "architecture"
    STANDARDS = "standards"
    EXPLAIN = "explain"


@dataclass
class CodeChunk:
    """A chunk of code to be reviewed."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    context: Optional[str] = None  # Surrounding code for context


@dataclass
class ReviewFinding:
    """A single finding from a code review."""
    type: ReviewType
    severity: str  # critical, high, medium, low, info
    file_path: str
    line_start: int
    line_end: int
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "message": self.message,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "confidence": self.confidence,
        }


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str, max_tokens: int = 4096, 
                 temperature: float = 0.0, timeout: int = 60):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            max_tokens: Maximum tokens for responses
            temperature: Temperature for generation
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._request_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
    
    @abstractmethod
    async def review_code(
        self,
        chunk: CodeChunk,
        review_types: List[ReviewType],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[ReviewFinding]:
        """
        Review a code chunk and return findings.
        
        Args:
            chunk: Code chunk to review
            review_types: Types of reviews to perform
            additional_context: Optional additional context
            
        Returns:
            List of review findings
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def get_max_context_size(self) -> int:
        """
        Get the maximum context size for this provider/model.
        
        Returns:
            Maximum context size in tokens
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "request_count": self._request_count,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
        }
    
    def _track_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage."""
        self._request_count += 1
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
    
    def _build_review_prompt(self, chunk: CodeChunk, review_types: List[ReviewType]) -> str:
        """
        Build a review prompt for the given chunk and review types.

        Args:
            chunk: Code chunk to review
            review_types: Types of reviews to perform

        Returns:
            Formatted prompt string
        """
        # Check if this is an explain-only request
        if len(review_types) == 1 and review_types[0] == ReviewType.EXPLAIN:
            return self._build_explain_prompt(chunk)

        review_types_str = ', '.join(rt.value for rt in review_types)

        prompt = f"""Senior engineer reviewing {chunk.language} code for {review_types_str}.

{chunk.file_path} (L{chunk.start_line}-{chunk.end_line})

```{chunk.language}
{chunk.content}
```"""

        if chunk.context:
            prompt += f"\n\nContext:\n```{chunk.language}\n{chunk.context}\n```"

        prompt += f"""

Return JSON array. Only genuine issues with clear impact. Be concise.

[{{"type":"{review_types_str}","severity":"critical|high|medium|low|info","line_start":<n>,"line_end":<n>,"message":"Issue","suggestion":"Fix","confidence":<0-1>}}]

[] if none.
"""
        return prompt

    def _build_explain_prompt(self, chunk: CodeChunk) -> str:
        """
        Build an explanation prompt for code understanding.

        Args:
            chunk: Code chunk to explain

        Returns:
            Formatted prompt string
        """
        prompt = f"""Explain this {chunk.language} code clearly.

{chunk.file_path} (L{chunk.start_line}-{chunk.end_line})

```{chunk.language}
{chunk.content}
```"""

        if chunk.context:
            prompt += f"\n\nContext:\n```{chunk.language}\n{chunk.context}\n```"

        prompt += """

Explain: purpose, key components, logic flow, patterns, dependencies, entry points.

[{{"type":"explain","severity":"info","line_start":1,"line_end":<n>,"message":"Explanation","suggestion":"Context/recommendations","confidence":1.0}}]
"""
        return prompt

