"""
Finding optimizer for better reviewer experience.

This module provides utilities to:
- Deduplicate similar findings
- Prioritize findings by impact
- Group findings by file and category
- Filter findings by various criteria
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import difflib
from ..providers.base import ReviewFinding, ReviewType


@dataclass
class FindingPriority:
    """Priority score for a finding."""
    finding: ReviewFinding
    priority_score: float  # 0-100, higher is more important
    reasons: List[str] = field(default_factory=list)


class FindingOptimizer:
    """Optimize findings for better reviewer experience."""
    
    # Severity weights for prioritization
    SEVERITY_WEIGHTS = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25,
        'info': 10
    }
    
    # Category weights (security issues are more important)
    CATEGORY_WEIGHTS = {
        'security': 1.5,
        'correctness': 1.3,
        'performance': 1.2,
        'maintainability': 1.0,
        'style': 0.8,
        'quality': 1.0
    }
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize the optimizer.
        
        Args:
            similarity_threshold: Threshold for considering findings as duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def deduplicate_findings(self, findings: List[ReviewFinding]) -> List[ReviewFinding]:
        """
        Remove duplicate or very similar findings.
        
        Args:
            findings: List of findings to deduplicate
            
        Returns:
            Deduplicated list of findings
        """
        if not findings:
            return findings
        
        unique_findings = []
        seen_signatures = set()
        
        for finding in findings:
            # Create a signature for exact duplicates
            signature = self._create_finding_signature(finding)
            
            if signature in seen_signatures:
                continue
            
            # Check for similar findings (fuzzy matching)
            is_duplicate = False
            for unique_finding in unique_findings:
                if self._are_findings_similar(finding, unique_finding):
                    # Keep the one with higher confidence
                    if finding.confidence > unique_finding.confidence:
                        unique_findings.remove(unique_finding)
                        unique_findings.append(finding)
                        seen_signatures.add(signature)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_findings.append(finding)
                seen_signatures.add(signature)
        
        return unique_findings
    
    def prioritize_findings(self, findings: List[ReviewFinding]) -> List[FindingPriority]:
        """
        Prioritize findings by impact and importance.
        
        Args:
            findings: List of findings to prioritize
            
        Returns:
            List of findings with priority scores, sorted by priority (highest first)
        """
        prioritized = []
        
        for finding in findings:
            priority_score, reasons = self._calculate_priority_score(finding)
            prioritized.append(FindingPriority(
                finding=finding,
                priority_score=priority_score,
                reasons=reasons
            ))
        
        # Sort by priority score (highest first)
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)
        
        return prioritized
    
    def group_by_file(self, findings: List[ReviewFinding]) -> Dict[str, List[ReviewFinding]]:
        """
        Group findings by file path.
        
        Args:
            findings: List of findings to group
            
        Returns:
            Dictionary mapping file paths to findings
        """
        grouped = defaultdict(list)
        for finding in findings:
            grouped[finding.file_path].append(finding)
        
        # Sort findings within each file by line number
        for file_path in grouped:
            grouped[file_path].sort(key=lambda f: f.line_start)
        
        return dict(grouped)
    
    def group_by_category(self, findings: List[ReviewFinding]) -> Dict[str, List[ReviewFinding]]:
        """
        Group findings by category.
        
        Args:
            findings: List of findings to group
            
        Returns:
            Dictionary mapping categories to findings
        """
        grouped = defaultdict(list)
        for finding in findings:
            category = finding.category or finding.type.value
            grouped[category].append(finding)
        
        return dict(grouped)
    
    def filter_findings(
        self,
        findings: List[ReviewFinding],
        min_severity: Optional[str] = None,
        max_severity: Optional[str] = None,
        min_confidence: Optional[float] = None,
        categories: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None
    ) -> List[ReviewFinding]:
        """
        Filter findings by various criteria.
        
        Args:
            findings: List of findings to filter
            min_severity: Minimum severity level (critical, high, medium, low, info)
            max_severity: Maximum severity level
            min_confidence: Minimum confidence threshold (0-1)
            categories: List of categories to include
            file_patterns: List of file patterns to include (simple glob-like matching)
            
        Returns:
            Filtered list of findings
        """
        severity_order = ['info', 'low', 'medium', 'high', 'critical']
        
        filtered = findings
        
        # Filter by severity
        if min_severity:
            min_idx = severity_order.index(min_severity)
            filtered = [f for f in filtered if severity_order.index(f.severity) >= min_idx]
        
        if max_severity:
            max_idx = severity_order.index(max_severity)
            filtered = [f for f in filtered if severity_order.index(f.severity) <= max_idx]
        
        # Filter by confidence
        if min_confidence is not None:
            filtered = [f for f in filtered if f.confidence >= min_confidence]
        
        # Filter by category
        if categories:
            filtered = [
                f for f in filtered
                if (f.category in categories) or (f.type.value in categories)
            ]
        
        # Filter by file patterns
        if file_patterns:
            import fnmatch
            filtered = [
                f for f in filtered
                if any(fnmatch.fnmatch(f.file_path, pattern) for pattern in file_patterns)
            ]
        
        return filtered
    
    def get_quick_summary(self, findings: List[ReviewFinding]) -> Dict[str, any]:
        """
        Get a quick summary of findings for fast triage.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary with summary statistics
        """
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        by_file = defaultdict(int)
        
        high_confidence_critical = 0
        actionable_count = 0
        
        for finding in findings:
            by_severity[finding.severity] += 1
            category = finding.category or finding.type.value
            by_category[category] += 1
            by_file[finding.file_path] += 1
            
            if finding.severity in ('critical', 'high') and finding.confidence >= 0.8:
                high_confidence_critical += 1
            
            if finding.suggestion:
                actionable_count += 1
        
        # Find files with most issues
        top_files = sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_findings': len(findings),
            'by_severity': dict(by_severity),
            'by_category': dict(by_category),
            'high_confidence_critical': high_confidence_critical,
            'actionable_findings': actionable_count,
            'files_affected': len(by_file),
            'top_files': top_files,
            'needs_immediate_attention': high_confidence_critical > 0
        }
    
    def _create_finding_signature(self, finding: ReviewFinding) -> str:
        """Create a unique signature for exact duplicate detection."""
        return f"{finding.file_path}:{finding.line_start}:{finding.severity}:{finding.message[:50]}"
    
    def _are_findings_similar(self, f1: ReviewFinding, f2: ReviewFinding) -> bool:
        """
        Check if two findings are similar enough to be considered duplicates.
        
        Args:
            f1: First finding
            f2: Second finding
            
        Returns:
            True if findings are similar
        """
        # Must be in the same file
        if f1.file_path != f2.file_path:
            return False
        
        # Must be close in line numbers (within 5 lines)
        if abs(f1.line_start - f2.line_start) > 5:
            return False
        
        # Must have the same severity
        if f1.severity != f2.severity:
            return False
        
        # Check message similarity using difflib
        similarity = difflib.SequenceMatcher(None, f1.message, f2.message).ratio()
        
        return similarity >= self.similarity_threshold
    
    def _calculate_priority_score(self, finding: ReviewFinding) -> Tuple[float, List[str]]:
        """
        Calculate priority score for a finding.
        
        Args:
            finding: Finding to score
            
        Returns:
            Tuple of (priority_score, reasons)
        """
        score = 0.0
        reasons = []
        
        # Base score from severity
        severity_score = self.SEVERITY_WEIGHTS.get(finding.severity, 50)
        score += severity_score
        reasons.append(f"{finding.severity} severity")
        
        # Category weight multiplier
        category = finding.category or finding.type.value
        category_weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
        score *= category_weight
        if category_weight > 1.0:
            reasons.append(f"{category} category (high priority)")
        
        # Confidence boost
        if finding.confidence >= 0.9:
            score *= 1.2
            reasons.append("high confidence (≥90%)")
        elif finding.confidence >= 0.8:
            score *= 1.1
            reasons.append("good confidence (≥80%)")
        
        # Actionable findings (with suggestions) get a boost
        if finding.suggestion:
            score *= 1.15
            reasons.append("has actionable suggestion")
        
        # Security-related findings get extra priority
        if finding.type == ReviewType.SECURITY or category == 'security':
            score *= 1.3
            reasons.append("security-related")
        
        return min(score, 100.0), reasons

