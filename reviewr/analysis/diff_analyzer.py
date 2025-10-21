"""
Diff-based analysis for incremental code review.

This module provides functionality to analyze only changed code sections,
dramatically reducing API calls and review time for PR/MR workflows.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import re


@dataclass
class DiffHunk:
    """Represents a changed section of code."""
    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]
    context_before: List[str]
    context_after: List[str]
    
    @property
    def changed_line_numbers(self) -> List[int]:
        """Get list of changed line numbers in the new file."""
        return list(range(self.new_start, self.new_start + self.new_count))
    
    @property
    def full_content(self) -> str:
        """Get full content including context."""
        all_lines = self.context_before + self.lines + self.context_after
        return '\n'.join(all_lines)


@dataclass
class FileDiff:
    """Represents all changes in a single file."""
    file_path: str
    old_path: Optional[str]
    is_new: bool
    is_deleted: bool
    is_renamed: bool
    hunks: List[DiffHunk]
    
    @property
    def has_changes(self) -> bool:
        """Check if file has actual changes."""
        return len(self.hunks) > 0 or self.is_new or self.is_deleted
    
    @property
    def all_changed_lines(self) -> List[int]:
        """Get all changed line numbers across all hunks."""
        lines = []
        for hunk in self.hunks:
            lines.extend(hunk.changed_line_numbers)
        return sorted(set(lines))


class DiffAnalyzer:
    """Analyzes git diffs to identify changed code sections."""
    
    def __init__(self, context_lines: int = 5):
        """
        Initialize diff analyzer.
        
        Args:
            context_lines: Number of context lines to include before/after changes
        """
        self.context_lines = context_lines
    
    def get_changed_files(
        self,
        base_ref: str = "HEAD",
        target_ref: Optional[str] = None,
        repo_path: Optional[Path] = None
    ) -> List[str]:
        """
        Get list of changed files between two refs.
        
        Args:
            base_ref: Base reference (branch, commit, tag)
            target_ref: Target reference (defaults to working directory)
            repo_path: Path to git repository (defaults to current directory)
            
        Returns:
            List of changed file paths
        """
        repo_path = repo_path or Path.cwd()
        
        # Build git diff command
        cmd = ["git", "diff", "--name-only"]
        if target_ref:
            cmd.append(f"{base_ref}...{target_ref}")
        else:
            cmd.append(base_ref)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return files
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get changed files: {e.stderr}")
    
    def get_file_diff(
        self,
        file_path: str,
        base_ref: str = "HEAD",
        target_ref: Optional[str] = None,
        repo_path: Optional[Path] = None
    ) -> Optional[FileDiff]:
        """
        Get diff for a specific file.
        
        Args:
            file_path: Path to file
            base_ref: Base reference
            target_ref: Target reference
            repo_path: Path to git repository
            
        Returns:
            FileDiff object or None if file unchanged
        """
        repo_path = repo_path or Path.cwd()
        
        # Build git diff command with unified format
        cmd = ["git", "diff", f"-U{self.context_lines}"]
        if target_ref:
            cmd.append(f"{base_ref}...{target_ref}")
        else:
            cmd.append(base_ref)
        cmd.extend(["--", file_path])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return None  # No changes
            
            return self._parse_diff(result.stdout, file_path)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get diff for {file_path}: {e.stderr}")
    
    def _parse_diff(self, diff_output: str, file_path: str) -> FileDiff:
        """Parse git diff output into FileDiff object."""
        lines = diff_output.split('\n')
        
        # Parse header
        is_new = False
        is_deleted = False
        is_renamed = False
        old_path = None
        
        for line in lines[:10]:  # Check first few lines for headers
            if line.startswith('new file mode'):
                is_new = True
            elif line.startswith('deleted file mode'):
                is_deleted = True
            elif line.startswith('rename from'):
                is_renamed = True
                old_path = line.split('rename from ')[1].strip()
        
        # Parse hunks
        hunks = []
        current_hunk = None
        hunk_lines = []
        context_before = []
        context_after = []
        in_hunk = False
        
        for line in lines:
            # Hunk header: @@ -old_start,old_count +new_start,new_count @@
            if line.startswith('@@'):
                # Save previous hunk
                if current_hunk:
                    current_hunk.lines = hunk_lines
                    current_hunk.context_before = context_before
                    current_hunk.context_after = context_after
                    hunks.append(current_hunk)
                
                # Parse new hunk header
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    current_hunk = DiffHunk(
                        file_path=file_path,
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=[],
                        context_before=[],
                        context_after=[]
                    )
                    hunk_lines = []
                    context_before = []
                    context_after = []
                    in_hunk = True
            
            elif in_hunk and not line.startswith('---') and not line.startswith('+++'):
                # Collect hunk lines
                if line.startswith('+') or line.startswith('-'):
                    hunk_lines.append(line[1:])  # Remove +/- prefix
                elif line.startswith(' '):
                    # Context line
                    if not hunk_lines:
                        context_before.append(line[1:])
                    else:
                        context_after.append(line[1:])
        
        # Save last hunk
        if current_hunk:
            current_hunk.lines = hunk_lines
            current_hunk.context_before = context_before
            current_hunk.context_after = context_after
            hunks.append(current_hunk)
        
        return FileDiff(
            file_path=file_path,
            old_path=old_path,
            is_new=is_new,
            is_deleted=is_deleted,
            is_renamed=is_renamed,
            hunks=hunks
        )
    
    def get_changed_content(
        self,
        file_path: str,
        base_ref: str = "HEAD",
        target_ref: Optional[str] = None,
        repo_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Get only the changed content from a file with context.
        
        Args:
            file_path: Path to file
            base_ref: Base reference
            target_ref: Target reference
            repo_path: Path to git repository
            
        Returns:
            Changed content with context, or None if no changes
        """
        file_diff = self.get_file_diff(file_path, base_ref, target_ref, repo_path)
        
        if not file_diff or not file_diff.has_changes:
            return None
        
        # Combine all hunks with separators
        content_parts = []
        for i, hunk in enumerate(file_diff.hunks):
            if i > 0:
                content_parts.append(f"\n{'='*60}\n")
            content_parts.append(f"# Changed section at lines {hunk.new_start}-{hunk.new_start + hunk.new_count - 1}\n")
            content_parts.append(hunk.full_content)
        
        return '\n'.join(content_parts)
    
    def should_review_line(
        self,
        file_path: str,
        line_number: int,
        file_diff: Optional[FileDiff] = None
    ) -> bool:
        """
        Check if a specific line should be reviewed based on diff.
        
        Args:
            file_path: Path to file
            line_number: Line number to check
            file_diff: Pre-computed FileDiff (optional)
            
        Returns:
            True if line is in changed section
        """
        if not file_diff:
            return True  # If no diff info, review everything
        
        changed_lines = file_diff.all_changed_lines
        
        # Check if line is in changed section or nearby context
        for changed_line in changed_lines:
            if abs(line_number - changed_line) <= self.context_lines:
                return True
        
        return False

