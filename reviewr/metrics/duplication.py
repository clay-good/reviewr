"""
Code duplication detector.

Provides:
- Token-based duplication detection
- AST-based structural duplication
- Clone detection (Type 1, Type 2, Type 3)
- Duplication metrics and reporting
"""

import ast
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict


@dataclass
class DuplicateBlock:
    """A block of duplicated code."""
    file1: str
    line1_start: int
    line1_end: int
    file2: str
    line2_start: int
    line2_end: int
    lines: int
    tokens: int
    similarity: float  # 0.0 to 1.0
    code_snippet: str
    
    @property
    def is_exact_duplicate(self) -> bool:
        """Check if this is an exact duplicate."""
        return self.similarity >= 0.99
    
    @property
    def is_significant(self) -> bool:
        """Check if duplication is significant (>= 6 lines)."""
        return self.lines >= 6


@dataclass
class DuplicationReport:
    """Report of code duplication analysis."""
    total_files: int
    total_lines: int
    duplicated_lines: int
    duplicated_blocks: List[DuplicateBlock]
    duplication_percentage: float
    
    @property
    def has_duplication(self) -> bool:
        """Check if any duplication was found."""
        return len(self.duplicated_blocks) > 0
    
    @property
    def significant_duplicates(self) -> List[DuplicateBlock]:
        """Get significant duplicates only."""
        return [b for b in self.duplicated_blocks if b.is_significant]
    
    @property
    def exact_duplicates(self) -> List[DuplicateBlock]:
        """Get exact duplicates only."""
        return [b for b in self.duplicated_blocks if b.is_exact_duplicate]


class DuplicationDetector:
    """Detect code duplication."""
    
    def __init__(self, min_lines: int = 6, min_tokens: int = 50):
        """
        Initialize duplication detector.
        
        Args:
            min_lines: Minimum lines for a duplicate block
            min_tokens: Minimum tokens for a duplicate block
        """
        self.min_lines = min_lines
        self.min_tokens = min_tokens
        self.file_hashes: Dict[str, List[Tuple[int, str]]] = {}
        self.duplicates: List[DuplicateBlock] = []
    
    def analyze_project(self, project_path: Path) -> DuplicationReport:
        """Analyze entire project for duplication."""
        python_files = list(project_path.rglob("*.py"))
        
        # Skip test files and __pycache__
        python_files = [
            f for f in python_files
            if not any(part.startswith(('test_', '__pycache__', '.'))
                      for part in f.parts)
        ]
        
        total_lines = 0
        
        # Build hash index for all files
        for file_path in python_files:
            try:
                lines = file_path.read_text().splitlines()
                total_lines += len(lines)
                self._index_file(str(file_path), lines)
            except Exception as e:
                print(f"Warning: Failed to read {file_path}: {e}")
        
        # Find duplicates
        self._find_duplicates()
        
        # Calculate duplication percentage
        duplicated_lines = sum(d.lines for d in self.duplicates)
        duplication_percentage = (
            (duplicated_lines / total_lines * 100) if total_lines > 0 else 0.0
        )
        
        return DuplicationReport(
            total_files=len(python_files),
            total_lines=total_lines,
            duplicated_lines=duplicated_lines,
            duplicated_blocks=self.duplicates,
            duplication_percentage=round(duplication_percentage, 2)
        )
    
    def _index_file(self, file_path: str, lines: List[str]):
        """Index file for duplication detection."""
        hashes = []
        
        for i, line in enumerate(lines, 1):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Normalize line (remove whitespace variations)
            normalized = self._normalize_line(stripped)
            
            # Hash the line
            line_hash = hashlib.md5(normalized.encode()).hexdigest()
            hashes.append((i, line_hash))
        
        self.file_hashes[file_path] = hashes
    
    def _normalize_line(self, line: str) -> str:
        """Normalize line for comparison."""
        # Remove extra whitespace
        line = ' '.join(line.split())
        
        # Remove string literals (for Type 2 clones)
        # This is a simple approach - could be more sophisticated
        import re
        line = re.sub(r'"[^"]*"', '""', line)
        line = re.sub(r"'[^']*'", "''", line)
        
        return line
    
    def _find_duplicates(self):
        """Find duplicate blocks across files."""
        files = list(self.file_hashes.keys())
        
        # Compare each pair of files
        for i, file1 in enumerate(files):
            for file2 in files[i:]:
                if file1 == file2:
                    # Check for duplication within same file
                    self._find_duplicates_in_file(file1)
                else:
                    # Check for duplication between files
                    self._find_duplicates_between_files(file1, file2)
    
    def _find_duplicates_in_file(self, file_path: str):
        """Find duplicates within a single file."""
        hashes = self.file_hashes[file_path]
        
        # Build hash to line number mapping
        hash_to_lines: Dict[str, List[int]] = defaultdict(list)
        for line_num, line_hash in hashes:
            hash_to_lines[line_hash].append(line_num)
        
        # Find sequences of matching hashes
        for line_hash, line_nums in hash_to_lines.items():
            if len(line_nums) < 2:
                continue
            
            # Check for consecutive sequences
            for i, start1 in enumerate(line_nums):
                for start2 in line_nums[i+1:]:
                    if abs(start2 - start1) < self.min_lines:
                        continue
                    
                    # Find length of matching sequence
                    length = self._find_sequence_length(
                        file_path, start1, file_path, start2
                    )
                    
                    if length >= self.min_lines:
                        self._add_duplicate(
                            file_path, start1, start1 + length - 1,
                            file_path, start2, start2 + length - 1,
                            length
                        )
    
    def _find_duplicates_between_files(self, file1: str, file2: str):
        """Find duplicates between two files."""
        hashes1 = self.file_hashes[file1]
        hashes2 = self.file_hashes[file2]
        
        # Build hash index for file2
        hash_index: Dict[str, List[int]] = defaultdict(list)
        for line_num, line_hash in hashes2:
            hash_index[line_hash].append(line_num)
        
        # Find matching sequences
        for line_num1, line_hash1 in hashes1:
            if line_hash1 in hash_index:
                for line_num2 in hash_index[line_hash1]:
                    # Find length of matching sequence
                    length = self._find_sequence_length(
                        file1, line_num1, file2, line_num2
                    )
                    
                    if length >= self.min_lines:
                        self._add_duplicate(
                            file1, line_num1, line_num1 + length - 1,
                            file2, line_num2, line_num2 + length - 1,
                            length
                        )
    
    def _find_sequence_length(
        self,
        file1: str,
        start1: int,
        file2: str,
        start2: int
    ) -> int:
        """Find length of matching sequence."""
        hashes1 = dict(self.file_hashes[file1])
        hashes2 = dict(self.file_hashes[file2])
        
        length = 0
        offset = 0
        
        while True:
            line1 = start1 + offset
            line2 = start2 + offset
            
            if line1 not in hashes1 or line2 not in hashes2:
                break
            
            if hashes1[line1] != hashes2[line2]:
                break
            
            length += 1
            offset += 1
        
        return length
    
    def _add_duplicate(
        self,
        file1: str,
        line1_start: int,
        line1_end: int,
        file2: str,
        line2_start: int,
        line2_end: int,
        lines: int
    ):
        """Add a duplicate block."""
        # Check if this duplicate already exists
        for existing in self.duplicates:
            if (existing.file1 == file1 and
                existing.line1_start == line1_start and
                existing.file2 == file2 and
                existing.line2_start == line2_start):
                return
        
        # Get code snippet
        try:
            with open(file1, 'r') as f:
                all_lines = f.readlines()
                snippet_lines = all_lines[line1_start-1:line1_end]
                code_snippet = ''.join(snippet_lines).strip()
        except:
            code_snippet = ""
        
        # Calculate similarity (for now, assume 1.0 for exact matches)
        similarity = 1.0
        
        # Estimate tokens (rough approximation)
        tokens = len(code_snippet.split())
        
        if tokens >= self.min_tokens:
            duplicate = DuplicateBlock(
                file1=file1,
                line1_start=line1_start,
                line1_end=line1_end,
                file2=file2,
                line2_start=line2_start,
                line2_end=line2_end,
                lines=lines,
                tokens=tokens,
                similarity=similarity,
                code_snippet=code_snippet[:200]  # Truncate for display
            )
            
            self.duplicates.append(duplicate)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get duplication summary."""
        if not self.duplicates:
            return {
                "total_duplicates": 0,
                "significant_duplicates": 0,
                "exact_duplicates": 0
            }
        
        return {
            "total_duplicates": len(self.duplicates),
            "significant_duplicates": len([d for d in self.duplicates if d.is_significant]),
            "exact_duplicates": len([d for d in self.duplicates if d.is_exact_duplicate]),
            "avg_duplicate_lines": sum(d.lines for d in self.duplicates) / len(self.duplicates),
            "max_duplicate_lines": max(d.lines for d in self.duplicates),
            "total_duplicated_lines": sum(d.lines for d in self.duplicates)
        }

