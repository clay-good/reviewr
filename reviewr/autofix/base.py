"""Base classes for auto-fix functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class FixStatus(Enum):
    """Status of a fix application."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class FixCategory(Enum):
    """Categories of fixes."""
    FORMATTING = "formatting"
    IMPORTS = "imports"
    TYPE_HINTS = "type_hints"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    STYLE = "style"
    DOCUMENTATION = "documentation"


@dataclass
class Fix:
    """Represents a code fix that can be applied."""
    
    # Identification
    fix_id: str  # Unique identifier for this fix
    category: FixCategory
    
    # Location
    file_path: str
    line_start: int
    line_end: int
    
    # Fix details
    description: str
    old_code: str  # Original code to be replaced
    new_code: str  # New code to replace with
    
    # Metadata
    confidence: float = 1.0  # Confidence in the fix (0.0-1.0)
    safe: bool = True  # Whether this fix is considered safe to auto-apply
    requires_validation: bool = False  # Whether validation is needed after applying
    
    # Context
    finding_message: Optional[str] = None  # Original finding message
    explanation: Optional[str] = None  # Detailed explanation of the fix
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fix_id": self.fix_id,
            "category": self.category.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "description": self.description,
            "old_code": self.old_code,
            "new_code": self.new_code,
            "confidence": self.confidence,
            "safe": self.safe,
            "requires_validation": self.requires_validation,
            "finding_message": self.finding_message,
            "explanation": self.explanation,
        }


@dataclass
class FixResult:
    """Result of applying a fix."""
    
    fix: Fix
    status: FixStatus
    message: str
    
    # Backup information
    backup_path: Optional[str] = None
    
    # Validation results
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Diff information
    diff: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fix": self.fix.to_dict(),
            "status": self.status.value,
            "message": self.message,
            "backup_path": self.backup_path,
            "validation_passed": self.validation_passed,
            "validation_errors": self.validation_errors,
            "diff": self.diff,
        }


class FixGenerator(ABC):
    """Abstract base class for fix generators."""
    
    def __init__(self, language: str):
        """
        Initialize fix generator.
        
        Args:
            language: Programming language this generator handles
        """
        self.language = language
    
    @abstractmethod
    def can_fix(self, finding: Any) -> bool:
        """
        Check if this generator can create a fix for the given finding.
        
        Args:
            finding: ReviewFinding or LocalFinding to check
            
        Returns:
            True if this generator can create a fix
        """
        pass
    
    @abstractmethod
    def generate_fix(self, finding: Any, file_content: str) -> Optional[Fix]:
        """
        Generate a fix for the given finding.
        
        Args:
            finding: ReviewFinding or LocalFinding to fix
            file_content: Full content of the file
            
        Returns:
            Fix object if a fix can be generated, None otherwise
        """
        pass
    
    def generate_fixes(self, findings: List[Any], file_contents: Dict[str, str]) -> List[Fix]:
        """
        Generate fixes for multiple findings.
        
        Args:
            findings: List of findings to fix
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            List of Fix objects
        """
        fixes = []
        
        for finding in findings:
            if not self.can_fix(finding):
                continue
            
            file_path = finding.file_path
            if file_path not in file_contents:
                continue
            
            fix = self.generate_fix(finding, file_contents[file_path])
            if fix:
                fixes.append(fix)
        
        return fixes
    
    def _extract_code_lines(self, content: str, start_line: int, end_line: int) -> str:
        """
        Extract specific lines from file content.
        
        Args:
            content: Full file content
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based, inclusive)
            
        Returns:
            Extracted code as string
        """
        lines = content.splitlines()
        
        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def _get_indentation(self, line: str) -> str:
        """
        Get the indentation of a line.
        
        Args:
            line: Line of code
            
        Returns:
            Indentation string (spaces or tabs)
        """
        return line[:len(line) - len(line.lstrip())]
    
    def _generate_fix_id(self, finding: Any) -> str:
        """
        Generate a unique fix ID from a finding.
        
        Args:
            finding: Finding to generate ID for
            
        Returns:
            Unique fix ID
        """
        import hashlib
        
        # Create a unique ID based on file path, line numbers, and message
        unique_str = f"{finding.file_path}:{finding.line_start}:{finding.line_end}:{finding.message}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]


class CompositeFixGenerator:
    """Combines multiple fix generators."""
    
    def __init__(self):
        """Initialize composite generator."""
        self.generators: List[FixGenerator] = []
    
    def add_generator(self, generator: FixGenerator):
        """
        Add a fix generator.
        
        Args:
            generator: FixGenerator to add
        """
        self.generators.append(generator)
    
    def generate_fixes(self, findings: List[Any], file_contents: Dict[str, str]) -> List[Fix]:
        """
        Generate fixes using all registered generators.
        
        Args:
            findings: List of findings to fix
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            List of Fix objects from all generators
        """
        all_fixes = []
        
        for generator in self.generators:
            fixes = generator.generate_fixes(findings, file_contents)
            all_fixes.extend(fixes)
        
        return all_fixes
    
    def get_generator_for_language(self, language: str) -> Optional[FixGenerator]:
        """
        Get a fix generator for a specific language.
        
        Args:
            language: Programming language
            
        Returns:
            FixGenerator if found, None otherwise
        """
        for generator in self.generators:
            if generator.language.lower() == language.lower():
                return generator
        
        return None

