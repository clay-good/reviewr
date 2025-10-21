"""Batch processor for applying multiple fixes efficiently."""

import asyncio
from typing import List, Dict, Optional, Callable
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

from .base import Fix, FixResult, FixStatus
from .applicator import FixApplicator


@dataclass
class BatchResult:
    """Result of batch fix application."""
    
    total_fixes: int
    successful: int
    failed: int
    skipped: int
    results: List[FixResult]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_fixes == 0:
            return 0.0
        return self.successful / self.total_fixes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_fixes": self.total_fixes,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": self.success_rate,
            "results": [r.to_dict() for r in self.results]
        }


class BatchFixProcessor:
    """Process multiple fixes efficiently with conflict resolution."""
    
    def __init__(
        self,
        applicator: FixApplicator,
        interactive: bool = False,
        confirmation_callback: Optional[Callable[[Fix], bool]] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            applicator: FixApplicator instance
            interactive: If True, ask for confirmation before each fix
            confirmation_callback: Optional callback for interactive confirmation
        """
        self.applicator = applicator
        self.interactive = interactive
        self.confirmation_callback = confirmation_callback
    
    def process_fixes(
        self,
        fixes: List[Fix],
        safe_only: bool = False,
        min_confidence: float = 0.0,
        categories: Optional[List[str]] = None
    ) -> BatchResult:
        """
        Process multiple fixes with conflict detection and resolution.
        
        Args:
            fixes: List of fixes to apply
            safe_only: If True, only apply fixes marked as safe
            min_confidence: Minimum confidence threshold
            categories: Optional list of categories to filter by
            
        Returns:
            BatchResult with statistics and individual results
        """
        # Filter fixes
        filtered_fixes = self._filter_fixes(fixes, safe_only, min_confidence, categories)
        
        # Group fixes by file
        fixes_by_file = self._group_fixes_by_file(filtered_fixes)
        
        # Detect and resolve conflicts
        resolved_fixes = self._resolve_conflicts(fixes_by_file)
        
        # Apply fixes
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for fix in resolved_fixes:
            # Interactive confirmation
            if self.interactive:
                if not self._confirm_fix(fix):
                    results.append(FixResult(
                        fix=fix,
                        status=FixStatus.SKIPPED,
                        message="Skipped by user"
                    ))
                    skipped += 1
                    continue
            
            # Apply fix
            result = self.applicator.apply_fix(fix)
            results.append(result)
            
            if result.status == FixStatus.SUCCESS:
                successful += 1
            elif result.status == FixStatus.FAILED:
                failed += 1
            else:
                skipped += 1
        
        return BatchResult(
            total_fixes=len(resolved_fixes),
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results
        )
    
    async def process_fixes_async(
        self,
        fixes: List[Fix],
        safe_only: bool = False,
        min_confidence: float = 0.0,
        categories: Optional[List[str]] = None,
        max_concurrent: int = 5
    ) -> BatchResult:
        """
        Process fixes asynchronously for better performance.
        
        Args:
            fixes: List of fixes to apply
            safe_only: If True, only apply fixes marked as safe
            min_confidence: Minimum confidence threshold
            categories: Optional list of categories to filter by
            max_concurrent: Maximum concurrent fix applications
            
        Returns:
            BatchResult with statistics and individual results
        """
        # Filter fixes
        filtered_fixes = self._filter_fixes(fixes, safe_only, min_confidence, categories)
        
        # Group fixes by file
        fixes_by_file = self._group_fixes_by_file(filtered_fixes)
        
        # Detect and resolve conflicts
        resolved_fixes = self._resolve_conflicts(fixes_by_file)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Apply fixes concurrently
        tasks = []
        for fix in resolved_fixes:
            task = self._apply_fix_async(fix, semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        successful = sum(1 for r in results if r.status == FixStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == FixStatus.FAILED)
        skipped = sum(1 for r in results if r.status == FixStatus.SKIPPED)
        
        return BatchResult(
            total_fixes=len(resolved_fixes),
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results
        )
    
    async def _apply_fix_async(self, fix: Fix, semaphore: asyncio.Semaphore) -> FixResult:
        """
        Apply a fix asynchronously with semaphore control.
        
        Args:
            fix: Fix to apply
            semaphore: Semaphore for concurrency control
            
        Returns:
            FixResult
        """
        async with semaphore:
            # Interactive confirmation
            if self.interactive:
                if not self._confirm_fix(fix):
                    return FixResult(
                        fix=fix,
                        status=FixStatus.SKIPPED,
                        message="Skipped by user"
                    )
            
            # Apply fix in thread pool (since it's I/O bound)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.applicator.apply_fix, fix)
            return result
    
    def _filter_fixes(
        self,
        fixes: List[Fix],
        safe_only: bool,
        min_confidence: float,
        categories: Optional[List[str]]
    ) -> List[Fix]:
        """
        Filter fixes based on criteria.
        
        Args:
            fixes: List of fixes
            safe_only: Only include safe fixes
            min_confidence: Minimum confidence threshold
            categories: Optional list of categories to include
            
        Returns:
            Filtered list of fixes
        """
        filtered = []
        
        for fix in fixes:
            # Check safe flag
            if safe_only and not fix.safe:
                continue
            
            # Check confidence
            if fix.confidence < min_confidence:
                continue
            
            # Check category
            if categories:
                if fix.category.value not in categories:
                    continue
            
            filtered.append(fix)
        
        return filtered
    
    def _group_fixes_by_file(self, fixes: List[Fix]) -> Dict[str, List[Fix]]:
        """
        Group fixes by file path.
        
        Args:
            fixes: List of fixes
            
        Returns:
            Dictionary mapping file paths to lists of fixes
        """
        grouped = defaultdict(list)
        
        for fix in fixes:
            grouped[fix.file_path].append(fix)
        
        return dict(grouped)
    
    def _resolve_conflicts(self, fixes_by_file: Dict[str, List[Fix]]) -> List[Fix]:
        """
        Detect and resolve conflicts between fixes.
        
        Conflicts occur when:
        1. Multiple fixes target overlapping line ranges
        2. Fixes depend on each other
        
        Resolution strategy:
        1. Sort fixes by line number
        2. Merge overlapping fixes if possible
        3. Skip conflicting fixes with lower confidence
        
        Args:
            fixes_by_file: Dictionary mapping file paths to lists of fixes
            
        Returns:
            List of resolved fixes (non-conflicting)
        """
        resolved = []
        
        for file_path, file_fixes in fixes_by_file.items():
            # Sort fixes by line number
            sorted_fixes = sorted(file_fixes, key=lambda f: (f.line_start, f.line_end))
            
            # Detect conflicts
            non_conflicting = []
            i = 0
            
            while i < len(sorted_fixes):
                current_fix = sorted_fixes[i]
                
                # Check for conflicts with next fixes
                conflicts = [current_fix]
                j = i + 1
                
                while j < len(sorted_fixes):
                    next_fix = sorted_fixes[j]
                    
                    # Check if ranges overlap
                    if self._ranges_overlap(
                        current_fix.line_start, current_fix.line_end,
                        next_fix.line_start, next_fix.line_end
                    ):
                        conflicts.append(next_fix)
                        j += 1
                    else:
                        break
                
                # Resolve conflicts
                if len(conflicts) == 1:
                    # No conflict
                    non_conflicting.append(current_fix)
                else:
                    # Multiple conflicting fixes - choose highest confidence
                    best_fix = max(conflicts, key=lambda f: f.confidence)
                    non_conflicting.append(best_fix)
                
                i = j if j > i + 1 else i + 1
            
            resolved.extend(non_conflicting)
        
        return resolved
    
    def _ranges_overlap(self, start1: int, end1: int, start2: int, end2: int) -> bool:
        """
        Check if two line ranges overlap.
        
        Args:
            start1: Start of first range
            end1: End of first range
            start2: Start of second range
            end2: End of second range
            
        Returns:
            True if ranges overlap
        """
        return not (end1 < start2 or end2 < start1)
    
    def _confirm_fix(self, fix: Fix) -> bool:
        """
        Ask user for confirmation to apply fix.
        
        Args:
            fix: Fix to confirm
            
        Returns:
            True if user confirms, False otherwise
        """
        if self.confirmation_callback:
            return self.confirmation_callback(fix)
        
        # Default confirmation (always yes if no callback)
        return True

