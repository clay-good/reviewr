"""
Policy rules for enterprise enforcement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Pattern
import re
from pathlib import Path


@dataclass
class RuleViolation:
    """A violation of a policy rule."""
    rule_id: str
    rule_name: str
    severity: str  # critical, high, medium, low
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PolicyRule(ABC):
    """Base class for policy rules."""
    
    def __init__(self, rule_id: str, name: str, description: str, severity: str = "high"):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """
        Evaluate the rule against the given context.
        
        Args:
            context: Context containing findings, files, metrics, etc.
            
        Returns:
            List of violations found
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'severity': self.severity,
        }


class SeverityRule(PolicyRule):
    """Rule that checks severity thresholds."""
    
    def __init__(
        self,
        rule_id: str = "severity-threshold",
        max_critical: int = 0,
        max_high: int = 0,
        max_medium: int = 10,
        max_low: int = 50
    ):
        super().__init__(
            rule_id=rule_id,
            name="Severity Threshold",
            description=f"Max issues: {max_critical} critical, {max_high} high, {max_medium} medium, {max_low} low",
            severity="high"
        )
        self.max_critical = max_critical
        self.max_high = max_high
        self.max_medium = max_medium
        self.max_low = max_low
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check if findings exceed severity thresholds."""
        findings = context.get('findings', [])
        
        # Count by severity
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in findings:
            severity = finding.severity.lower() if hasattr(finding, 'severity') else 'low'
            if severity in counts:
                counts[severity] += 1
        
        violations = []
        
        if counts['critical'] > self.max_critical:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity='critical',
                message=f"Found {counts['critical']} critical issues (max: {self.max_critical})",
                suggestion=f"Fix {counts['critical'] - self.max_critical} critical issue(s) before proceeding",
                metadata={'count': counts['critical'], 'threshold': self.max_critical}
            ))
        
        if counts['high'] > self.max_high:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity='high',
                message=f"Found {counts['high']} high severity issues (max: {self.max_high})",
                suggestion=f"Fix {counts['high'] - self.max_high} high severity issue(s) before proceeding",
                metadata={'count': counts['high'], 'threshold': self.max_high}
            ))
        
        if counts['medium'] > self.max_medium:
            violations.append(RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity='medium',
                message=f"Found {counts['medium']} medium severity issues (max: {self.max_medium})",
                suggestion=f"Consider fixing {counts['medium'] - self.max_medium} medium severity issue(s)",
                metadata={'count': counts['medium'], 'threshold': self.max_medium}
            ))
        
        return violations


class FilePatternRule(PolicyRule):
    """Rule that checks for issues in specific file patterns."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        patterns: List[str],
        max_issues: int = 0,
        severity: str = "high"
    ):
        super().__init__(
            rule_id=rule_id,
            name=name,
            description=f"Max {max_issues} issues in files matching: {', '.join(patterns)}",
            severity=severity
        )
        self.patterns = [self._glob_to_regex(p) for p in patterns]
        self.max_issues = max_issues
    
    @staticmethod
    def _glob_to_regex(pattern: str) -> Pattern:
        """Convert glob pattern to regex."""
        # Simple glob to regex conversion
        regex = pattern.replace('.', r'\.')
        regex = regex.replace('*', '.*')
        regex = regex.replace('?', '.')
        return re.compile(regex)
    
    def _matches_pattern(self, file_path: str) -> bool:
        """Check if file path matches any pattern."""
        return any(pattern.match(file_path) for pattern in self.patterns)
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check for issues in files matching patterns."""
        findings = context.get('findings', [])
        
        # Filter findings to matching files
        matching_findings = [
            f for f in findings
            if hasattr(f, 'file_path') and self._matches_pattern(f.file_path)
        ]
        
        if len(matching_findings) > self.max_issues:
            return [RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                message=f"Found {len(matching_findings)} issues in sensitive files (max: {self.max_issues})",
                suggestion="Review and fix issues in security-sensitive files",
                metadata={'count': len(matching_findings), 'threshold': self.max_issues}
            )]
        
        return []


class ComplexityRule(PolicyRule):
    """Rule that checks code complexity."""
    
    def __init__(
        self,
        rule_id: str = "complexity-threshold",
        max_complexity: int = 15,
        severity: str = "medium"
    ):
        super().__init__(
            rule_id=rule_id,
            name="Complexity Threshold",
            description=f"Max cyclomatic complexity: {max_complexity}",
            severity=severity
        )
        self.max_complexity = max_complexity
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check if complexity exceeds threshold."""
        findings = context.get('findings', [])
        
        violations = []
        for finding in findings:
            # Check if this is a complexity finding
            if hasattr(finding, 'category') and 'complexity' in finding.category.lower():
                if hasattr(finding, 'metric_value') and finding.metric_value:
                    if finding.metric_value > self.max_complexity:
                        violations.append(RuleViolation(
                            rule_id=self.rule_id,
                            rule_name=self.name,
                            severity=self.severity,
                            message=f"Complexity {finding.metric_value} exceeds threshold {self.max_complexity}",
                            file_path=finding.file_path if hasattr(finding, 'file_path') else None,
                            line_number=finding.line_start if hasattr(finding, 'line_start') else None,
                            suggestion="Refactor to reduce complexity",
                            metadata={'complexity': finding.metric_value, 'threshold': self.max_complexity}
                        ))
        
        return violations


class SecurityRule(PolicyRule):
    """Rule that checks for security issues."""
    
    def __init__(
        self,
        rule_id: str = "security-issues",
        max_issues: int = 0,
        severity: str = "critical"
    ):
        super().__init__(
            rule_id=rule_id,
            name="Security Issues",
            description=f"Max security issues: {max_issues}",
            severity=severity
        )
        self.max_issues = max_issues
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check for security issues."""
        findings = context.get('findings', [])
        
        # Filter to security findings
        security_findings = [
            f for f in findings
            if hasattr(f, 'category') and 'security' in f.category.lower()
        ]
        
        if len(security_findings) > self.max_issues:
            return [RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                message=f"Found {len(security_findings)} security issues (max: {self.max_issues})",
                suggestion="Fix all security issues before proceeding",
                metadata={'count': len(security_findings), 'threshold': self.max_issues}
            )]
        
        return []


class LicenseRule(PolicyRule):
    """Rule that checks license compliance."""
    
    def __init__(
        self,
        rule_id: str = "license-compliance",
        allowed_licenses: Optional[List[str]] = None,
        severity: str = "high"
    ):
        super().__init__(
            rule_id=rule_id,
            name="License Compliance",
            description="Check license compliance",
            severity=severity
        )
        self.allowed_licenses = set(allowed_licenses or [])
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check license compliance."""
        # This would integrate with the existing license checker
        # For now, return empty list
        return []


class CoverageRule(PolicyRule):
    """Rule that checks test coverage."""
    
    def __init__(
        self,
        rule_id: str = "test-coverage",
        min_coverage: float = 0.8,
        severity: str = "medium"
    ):
        super().__init__(
            rule_id=rule_id,
            name="Test Coverage",
            description=f"Min test coverage: {min_coverage * 100}%",
            severity=severity
        )
        self.min_coverage = min_coverage
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Check test coverage."""
        coverage = context.get('test_coverage')
        
        if coverage is not None and coverage < self.min_coverage:
            return [RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                message=f"Test coverage {coverage * 100:.1f}% is below threshold {self.min_coverage * 100}%",
                suggestion=f"Add tests to reach {self.min_coverage * 100}% coverage",
                metadata={'coverage': coverage, 'threshold': self.min_coverage}
            )]
        
        return []


class CustomRule(PolicyRule):
    """Custom rule defined by user."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        evaluator: callable,
        severity: str = "medium"
    ):
        super().__init__(rule_id, name, description, severity)
        self.evaluator = evaluator
    
    def evaluate(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """Evaluate using custom evaluator function."""
        return self.evaluator(context, self)

