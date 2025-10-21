from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class FindingSeverity(Enum):
    """Severity levels for local findings."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LocalFinding:
    """A finding from local analysis."""
    
    file_path: str
    line_start: int
    line_end: int
    severity: str
    category: str  # 'complexity', 'dead_code', 'imports', 'smell', etc.
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    metric_value: Optional[float] = None  # For complexity metrics
    metric_name: Optional[str] = None  # e.g., 'cyclomatic_complexity'
    
    def to_review_finding(self):
        """Convert to ReviewFinding format."""
        from ..providers.base import ReviewFinding, ReviewType

        return ReviewFinding(
            file_path=self.file_path,
            line_start=self.line_start,
            line_end=self.line_end,
            severity=self.severity,
            type=ReviewType.CORRECTNESS,  # Use enum instead of string
            message=self.message,
            suggestion=self.suggestion or "",
            confidence=1.0,  # Local analysis is deterministic
            code_snippet=self.code_snippet or "",
            category=self.category,  # Preserve category
            metric_name=self.metric_name,  # Preserve metric name
            metric_value=self.metric_value  # Preserve metric value
        )


class LocalAnalyzer(ABC):
    """Abstract base class for language-specific local analyzers."""
    
    @abstractmethod
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze code and return findings.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of local findings
        """
        pass
    
    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if this analyzer supports the given language.
        
        Args:
            language: Language name
            
        Returns:
            True if supported
        """
        pass
    
    def get_complexity_threshold(self) -> int:
        """Get the complexity threshold for warnings."""
        return 10  # Default threshold
    
    def get_max_function_lines(self) -> int:
        """Get the maximum recommended lines per function."""
        return 50  # Default threshold

