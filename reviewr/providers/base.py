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

        # Build comprehensive review instructions
        review_instructions = self._build_review_instructions(review_types)

        prompt = f"""You are a senior software engineer conducting a comprehensive code review. Analyze the following {chunk.language} code for the specified review types.

FILE: {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})

```{chunk.language}
{chunk.content}
```"""

        if chunk.context:
            prompt += f"\n\nCONTEXT:\n```{chunk.language}\n{chunk.context}\n```"

        prompt += f"""

REVIEW CRITERIA:
{review_instructions}

INSTRUCTIONS:
- Only report genuine issues with clear impact on code quality, security, or maintainability
- Be specific about the problem and provide actionable suggestions
- Include line numbers for precise issue location
- Rate confidence based on certainty of the issue (0.0-1.0)
- Use appropriate severity levels: critical (security/data loss), high (bugs/major issues), medium (improvements), low (minor issues), info (suggestions)

RESPONSE FORMAT (JSON array):
[{{"type":"<review_type>","severity":"critical|high|medium|low|info","line_start":<n>,"line_end":<n>,"message":"<specific issue description>","suggestion":"<actionable fix>","confidence":<0.0-1.0>}}]

Return [] if no issues found.
"""
        return prompt

    def _build_review_instructions(self, review_types: List[ReviewType]) -> str:
        """Build detailed instructions for each review type."""
        instructions = []

        for review_type in review_types:
            if review_type == ReviewType.SECURITY:
                instructions.append("""SECURITY REVIEW:
- SQL injection, XSS, CSRF vulnerabilities
- Authentication/authorization bypasses
- Insecure data handling (passwords, tokens, PII)
- Cryptographic weaknesses
- Input validation failures
- Path traversal vulnerabilities
- Insecure deserialization
- Race conditions and TOCTOU issues""")

            elif review_type == ReviewType.PERFORMANCE:
                instructions.append("""PERFORMANCE REVIEW:
- Inefficient algorithms (O(n²) where O(n) possible)
- Unnecessary loops or nested iterations
- Memory leaks and excessive allocations
- Database N+1 queries
- Blocking I/O in performance-critical paths
- Missing caching opportunities
- Inefficient data structures
- Resource contention issues""")

            elif review_type == ReviewType.CORRECTNESS:
                instructions.append("""CORRECTNESS REVIEW:
- Logic errors and edge case handling
- Null pointer/undefined reference risks
- Off-by-one errors and boundary conditions
- Race conditions and concurrency issues
- Exception handling gaps
- Type mismatches and casting errors
- Resource cleanup failures
- State management inconsistencies""")

            elif review_type == ReviewType.MAINTAINABILITY:
                instructions.append("""MAINTAINABILITY REVIEW:
- Code clarity and readability
- Function/class size and complexity
- Naming conventions and descriptiveness
- Code duplication and DRY violations
- Missing or inadequate documentation
- Hard-coded values that should be configurable
- Overly complex conditional logic
- Tight coupling between components""")

            elif review_type == ReviewType.ARCHITECTURE:
                instructions.append("""ARCHITECTURE REVIEW:
- SOLID principle violations
- Design pattern misuse or opportunities
- Separation of concerns issues
- Dependency injection opportunities
- Layer boundary violations
- Circular dependencies
- Interface segregation needs
- Single responsibility violations""")

            elif review_type == ReviewType.STANDARDS:
                instructions.append("""STANDARDS REVIEW:
- Language-specific idiom violations
- Code style and formatting issues
- Naming convention inconsistencies
- Import/include organization
- Comment style and placement
- Error handling patterns
- Logging and debugging practices
- API design consistency""")

        return "\n\n".join(instructions)

    def _build_explain_prompt(self, chunk: CodeChunk) -> str:
        """
        Build an explanation prompt for code understanding.

        Args:
            chunk: Code chunk to explain

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a senior software engineer providing a comprehensive code explanation. Analyze and explain the following {chunk.language} code in detail.

FILE: {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})

```{chunk.language}
{chunk.content}
```"""

        if chunk.context:
            prompt += f"\n\nCONTEXT:\n```{chunk.language}\n{chunk.context}\n```"

        prompt += f"""

EXPLANATION REQUIREMENTS:
1. PURPOSE: What does this code accomplish? What problem does it solve?
2. KEY COMPONENTS: Identify main classes, functions, variables, and their roles
3. LOGIC FLOW: Trace the execution path and decision points
4. PATTERNS: Identify design patterns, algorithms, or architectural approaches used
5. DEPENDENCIES: External libraries, modules, or services this code relies on
6. ENTRY POINTS: How is this code typically invoked or used?
7. DATA FLOW: How data moves through the code and transforms
8. ERROR HANDLING: How errors and edge cases are managed
9. PERFORMANCE CONSIDERATIONS: Any notable performance characteristics
10. RECOMMENDATIONS: Suggestions for improvements or best practices

RESPONSE FORMAT (JSON):
[{{"type":"explain","severity":"info","line_start":{chunk.start_line},"line_end":{chunk.end_line},"message":"<comprehensive explanation covering all requirements>","suggestion":"<recommendations for improvements, usage tips, or related best practices>","confidence":1.0}}]
"""
        return prompt

