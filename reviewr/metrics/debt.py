"""
Technical debt estimation.

Provides:
- Technical debt calculation based on code quality metrics
- SQALE methodology implementation
- Remediation time estimation
- Debt categorization and prioritization
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
import math


class DebtSeverity(Enum):
    """Technical debt severity levels."""
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class DebtCategory(Enum):
    """Technical debt categories (SQALE)."""
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    RELIABILITY = "reliability"
    TESTABILITY = "testability"
    DOCUMENTATION = "documentation"


@dataclass
class DebtItem:
    """A single technical debt item."""
    category: DebtCategory
    severity: DebtSeverity
    description: str
    file_path: str
    line_number: int
    remediation_minutes: int
    impact: str  # Description of impact
    recommendation: str  # How to fix
    
    @property
    def remediation_hours(self) -> float:
        """Get remediation time in hours."""
        return self.remediation_minutes / 60
    
    @property
    def remediation_days(self) -> float:
        """Get remediation time in days (8-hour workday)."""
        return self.remediation_hours / 8


@dataclass
class DebtReport:
    """Technical debt report."""
    total_debt_minutes: int
    debt_items: List[DebtItem]
    debt_by_category: Dict[DebtCategory, int]
    debt_by_severity: Dict[DebtSeverity, int]
    debt_ratio: float  # Debt / Total LOC
    sqale_rating: str  # A, B, C, D, E
    
    @property
    def total_debt_hours(self) -> float:
        """Get total debt in hours."""
        return self.total_debt_minutes / 60
    
    @property
    def total_debt_days(self) -> float:
        """Get total debt in days (8-hour workday)."""
        return self.total_debt_hours / 8
    
    @property
    def critical_items(self) -> List[DebtItem]:
        """Get critical and blocker items."""
        return [
            item for item in self.debt_items
            if item.severity in (DebtSeverity.CRITICAL, DebtSeverity.BLOCKER)
        ]
    
    @property
    def has_critical_debt(self) -> bool:
        """Check if there is critical debt."""
        return len(self.critical_items) > 0


class TechnicalDebtEstimator:
    """Estimate technical debt."""
    
    # SQALE remediation constants (minutes)
    COMPLEXITY_BASE = 5  # Minutes per complexity point above threshold
    DUPLICATION_BASE = 2  # Minutes per duplicated line
    MAINTAINABILITY_BASE = 30  # Minutes per unmaintainable function
    SECURITY_BASE = 60  # Minutes per security issue
    
    # SQALE rating thresholds (debt ratio %)
    SQALE_THRESHOLDS = {
        'A': 0.05,  # <= 5%
        'B': 0.10,  # <= 10%
        'C': 0.20,  # <= 20%
        'D': 0.50,  # <= 50%
        'E': 1.00   # > 50%
    }
    
    def __init__(self):
        self.debt_items: List[DebtItem] = []
    
    def estimate_from_metrics(
        self,
        complexity_metrics: List[Any],
        duplication_report: Optional[Any] = None,
        security_findings: Optional[List[Dict]] = None,
        total_loc: int = 0
    ) -> DebtReport:
        """
        Estimate technical debt from various metrics.
        
        Args:
            complexity_metrics: List of ComplexityMetrics
            duplication_report: DuplicationReport
            security_findings: List of security findings
            total_loc: Total lines of code
        """
        self.debt_items = []
        
        # Analyze complexity debt
        self._analyze_complexity_debt(complexity_metrics)
        
        # Analyze duplication debt
        if duplication_report:
            self._analyze_duplication_debt(duplication_report)
        
        # Analyze security debt
        if security_findings:
            self._analyze_security_debt(security_findings)
        
        # Calculate totals
        total_debt_minutes = sum(item.remediation_minutes for item in self.debt_items)
        
        # Calculate debt by category
        debt_by_category = {}
        for category in DebtCategory:
            debt_by_category[category] = sum(
                item.remediation_minutes
                for item in self.debt_items
                if item.category == category
            )
        
        # Calculate debt by severity
        debt_by_severity = {}
        for severity in DebtSeverity:
            debt_by_severity[severity] = sum(
                item.remediation_minutes
                for item in self.debt_items
                if item.severity == severity
            )
        
        # Calculate debt ratio
        # Debt ratio = (Total debt in minutes) / (Total LOC * average minutes per line)
        # Assuming 1 line = 0.5 minutes to write
        if total_loc > 0:
            debt_ratio = total_debt_minutes / (total_loc * 0.5)
        else:
            debt_ratio = 0.0
        
        # Calculate SQALE rating
        sqale_rating = self._calculate_sqale_rating(debt_ratio)
        
        return DebtReport(
            total_debt_minutes=total_debt_minutes,
            debt_items=self.debt_items,
            debt_by_category=debt_by_category,
            debt_by_severity=debt_by_severity,
            debt_ratio=round(debt_ratio, 4),
            sqale_rating=sqale_rating
        )
    
    def _analyze_complexity_debt(self, complexity_metrics: List[Any]):
        """Analyze complexity-related debt."""
        for metric in complexity_metrics:
            # High cyclomatic complexity
            if metric.cyclomatic > 10:
                excess = metric.cyclomatic - 10
                remediation = excess * self.COMPLEXITY_BASE
                
                severity = self._get_complexity_severity(metric.cyclomatic)
                
                self.debt_items.append(DebtItem(
                    category=DebtCategory.COMPLEXITY,
                    severity=severity,
                    description=f"High cyclomatic complexity ({metric.cyclomatic})",
                    file_path=f"function {metric.name}",
                    line_number=metric.line_start,
                    remediation_minutes=remediation,
                    impact="Difficult to understand, test, and maintain",
                    recommendation="Refactor into smaller functions, reduce branching"
                ))
            
            # High cognitive complexity
            if metric.cognitive > 15:
                excess = metric.cognitive - 15
                remediation = excess * self.COMPLEXITY_BASE
                
                severity = self._get_complexity_severity(metric.cognitive)
                
                self.debt_items.append(DebtItem(
                    category=DebtCategory.COMPLEXITY,
                    severity=severity,
                    description=f"High cognitive complexity ({metric.cognitive})",
                    file_path=f"function {metric.name}",
                    line_number=metric.line_start,
                    remediation_minutes=remediation,
                    impact="Hard to understand and reason about",
                    recommendation="Simplify logic, extract nested conditions"
                ))
            
            # Low maintainability
            if metric.maintainability_index < 65:
                remediation = self.MAINTAINABILITY_BASE
                
                if metric.maintainability_index < 20:
                    severity = DebtSeverity.CRITICAL
                elif metric.maintainability_index < 40:
                    severity = DebtSeverity.MAJOR
                else:
                    severity = DebtSeverity.MINOR
                
                self.debt_items.append(DebtItem(
                    category=DebtCategory.MAINTAINABILITY,
                    severity=severity,
                    description=f"Low maintainability index ({metric.maintainability_index:.1f})",
                    file_path=f"function {metric.name}",
                    line_number=metric.line_start,
                    remediation_minutes=remediation,
                    impact="Expensive to maintain and modify",
                    recommendation="Refactor to improve code quality"
                ))
            
            # Too many parameters
            if metric.parameters > 5:
                remediation = (metric.parameters - 5) * 10
                
                self.debt_items.append(DebtItem(
                    category=DebtCategory.MAINTAINABILITY,
                    severity=DebtSeverity.MINOR,
                    description=f"Too many parameters ({metric.parameters})",
                    file_path=f"function {metric.name}",
                    line_number=metric.line_start,
                    remediation_minutes=remediation,
                    impact="Hard to use and test",
                    recommendation="Use parameter objects or builder pattern"
                ))
            
            # Deep nesting
            if metric.nesting_depth > 4:
                remediation = (metric.nesting_depth - 4) * 15
                
                self.debt_items.append(DebtItem(
                    category=DebtCategory.COMPLEXITY,
                    severity=DebtSeverity.MAJOR,
                    description=f"Deep nesting ({metric.nesting_depth} levels)",
                    file_path=f"function {metric.name}",
                    line_number=metric.line_start,
                    remediation_minutes=remediation,
                    impact="Hard to follow control flow",
                    recommendation="Extract nested logic, use early returns"
                ))
    
    def _analyze_duplication_debt(self, duplication_report: Any):
        """Analyze duplication-related debt."""
        for duplicate in duplication_report.significant_duplicates:
            remediation = duplicate.lines * self.DUPLICATION_BASE
            
            if duplicate.lines > 50:
                severity = DebtSeverity.MAJOR
            elif duplicate.lines > 20:
                severity = DebtSeverity.MINOR
            else:
                severity = DebtSeverity.INFO
            
            self.debt_items.append(DebtItem(
                category=DebtCategory.DUPLICATION,
                severity=severity,
                description=f"Code duplication ({duplicate.lines} lines)",
                file_path=duplicate.file1,
                line_number=duplicate.line1_start,
                remediation_minutes=remediation,
                impact="Changes must be made in multiple places",
                recommendation="Extract common code into reusable function"
            ))
    
    def _analyze_security_debt(self, security_findings: List[Dict]):
        """Analyze security-related debt."""
        for finding in security_findings:
            severity_map = {
                'critical': DebtSeverity.BLOCKER,
                'high': DebtSeverity.CRITICAL,
                'medium': DebtSeverity.MAJOR,
                'low': DebtSeverity.MINOR
            }
            
            severity = severity_map.get(
                finding.get('severity', 'medium').lower(),
                DebtSeverity.MAJOR
            )
            
            # Security issues get higher remediation time
            base_time = self.SECURITY_BASE
            if severity == DebtSeverity.BLOCKER:
                remediation = base_time * 2
            elif severity == DebtSeverity.CRITICAL:
                remediation = base_time * 1.5
            else:
                remediation = base_time
            
            self.debt_items.append(DebtItem(
                category=DebtCategory.SECURITY,
                severity=severity,
                description=finding.get('title', 'Security issue'),
                file_path=finding.get('file', 'unknown'),
                line_number=finding.get('line', 0),
                remediation_minutes=int(remediation),
                impact="Potential security vulnerability",
                recommendation=finding.get('recommendation', 'Fix security issue')
            ))
    
    def _get_complexity_severity(self, complexity: int) -> DebtSeverity:
        """Get severity based on complexity value."""
        if complexity > 50:
            return DebtSeverity.BLOCKER
        elif complexity > 30:
            return DebtSeverity.CRITICAL
        elif complexity > 20:
            return DebtSeverity.MAJOR
        elif complexity > 10:
            return DebtSeverity.MINOR
        else:
            return DebtSeverity.INFO
    
    def _calculate_sqale_rating(self, debt_ratio: float) -> str:
        """Calculate SQALE rating."""
        for rating, threshold in self.SQALE_THRESHOLDS.items():
            if debt_ratio <= threshold:
                return rating
        return 'E'
    
    def get_summary(self) -> Dict[str, Any]:
        """Get debt summary."""
        if not self.debt_items:
            return {
                "total_items": 0,
                "total_minutes": 0,
                "total_hours": 0,
                "total_days": 0
            }
        
        return {
            "total_items": len(self.debt_items),
            "total_minutes": sum(item.remediation_minutes for item in self.debt_items),
            "total_hours": sum(item.remediation_hours for item in self.debt_items),
            "total_days": sum(item.remediation_days for item in self.debt_items),
            "critical_items": len([i for i in self.debt_items if i.severity in (DebtSeverity.CRITICAL, DebtSeverity.BLOCKER)]),
            "by_category": {
                cat.value: len([i for i in self.debt_items if i.category == cat])
                for cat in DebtCategory
            }
        }

