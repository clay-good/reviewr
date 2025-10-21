"""
Go Unified Analyzer

Orchestrates all Go analyzers:
- GoSecurityAnalyzer
- GoPerformanceAnalyzer
- GoQualityAnalyzer

Provides flexible configuration and comprehensive analysis.
"""

from dataclasses import dataclass
from typing import List, Optional
from .base import LocalAnalyzer, LocalFinding
from .go_security_analyzer import GoSecurityAnalyzer
from .go_performance_analyzer import GoPerformanceAnalyzer
from .go_quality_analyzer import GoQualityAnalyzer


@dataclass
class GoAnalyzerConfig:
    """Configuration for Go analyzers."""
    
    # Analyzer toggles
    enable_security: bool = True
    enable_performance: bool = True
    enable_quality: bool = True
    
    # Severity filtering
    min_severity: str = 'info'  # info, low, medium, high, critical
    
    # Complexity thresholds
    max_function_params: int = 5
    max_nesting_level: int = 4
    
    # Performance thresholds
    warn_goroutine_without_cancel: bool = True
    warn_n_plus_one: bool = True
    
    # Quality thresholds
    warn_ignored_errors: bool = True
    warn_panic_without_recover: bool = True


class GoUnifiedAnalyzer(LocalAnalyzer):
    """
    Unified analyzer that orchestrates all Go analyzers.
    
    Provides comprehensive analysis of Go code including:
    - Security vulnerabilities (12 types)
    - Performance anti-patterns (9 types)
    - Code quality issues (8 types)
    """
    
    def __init__(self, config: Optional[GoAnalyzerConfig] = None):
        """
        Initialize the unified analyzer.
        
        Args:
            config: Configuration for analyzers
        """
        self.config = config or GoAnalyzerConfig()
        self.analyzers = []
        
        # Initialize enabled analyzers
        if self.config.enable_security:
            self.analyzers.append(GoSecurityAnalyzer())
        
        if self.config.enable_performance:
            self.analyzers.append(GoPerformanceAnalyzer())
        
        if self.config.enable_quality:
            self.analyzers.append(GoQualityAnalyzer())
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Go code with all enabled analyzers.
        
        Args:
            file_path: Path to the Go file
            content: File content
            
        Returns:
            List of findings from all analyzers
        """
        all_findings = []
        
        # Run each analyzer
        for analyzer in self.analyzers:
            findings = analyzer.analyze(file_path, content)
            all_findings.extend(findings)
        
        # Filter by severity
        filtered_findings = self._filter_by_severity(all_findings)
        
        # Sort by severity and line number
        filtered_findings.sort(key=lambda f: (
            self._severity_order(f.severity),
            f.line_start
        ))
        
        return filtered_findings
    
    def _filter_by_severity(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """Filter findings by minimum severity."""
        severity_levels = {
            'info': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        min_level = severity_levels.get(self.config.min_severity, 0)
        
        return [
            f for f in findings
            if severity_levels.get(f.severity, 0) >= min_level
        ]
    
    def _severity_order(self, severity: str) -> int:
        """Get sort order for severity."""
        order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'info': 4
        }
        return order.get(severity, 5)
    
    def get_summary(self, findings: List[LocalFinding]) -> dict:
        """
        Generate a summary of findings.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_findings': len(findings),
            'by_severity': {},
            'by_category': {},
            'by_analyzer': {
                'security': 0,
                'performance': 0,
                'quality': 0
            }
        }
        
        # Count by severity
        for finding in findings:
            severity = finding.severity
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        # Count by category
        for finding in findings:
            category = finding.category or 'other'
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        # Estimate by analyzer (based on category)
        for finding in findings:
            if finding.category == 'security':
                summary['by_analyzer']['security'] += 1
            elif finding.category == 'performance':
                summary['by_analyzer']['performance'] += 1
            elif finding.category == 'quality':
                summary['by_analyzer']['quality'] += 1
        
        return summary
    
    def format_summary(self, findings: List[LocalFinding]) -> str:
        """
        Format summary as a string.
        
        Args:
            findings: List of findings
            
        Returns:
            Formatted summary string
        """
        summary = self.get_summary(findings)
        
        lines = []
        lines.append(f"\n📊 Go Analysis Summary: {summary['total_findings']} issues found")
        
        # Severity breakdown
        if summary['by_severity']:
            lines.append("\n  By Severity:")
            severity_icons = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🔵',
                'info': '⚪'
            }
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                count = summary['by_severity'].get(severity, 0)
                if count > 0:
                    icon = severity_icons.get(severity, '⚪')
                    lines.append(f"    {icon} {severity.upper()}: {count}")
        
        # Category breakdown
        if summary['by_category']:
            lines.append("\n  By Category:")
            category_icons = {
                'security': '🔒',
                'performance': '⚡',
                'quality': '✨'
            }
            for category, count in sorted(summary['by_category'].items(), key=lambda x: -x[1]):
                icon = category_icons.get(category, '📋')
                lines.append(f"    {icon} {category}: {count}")
        
        # Analyzer breakdown
        if summary['by_analyzer']:
            lines.append("\n  By Analyzer:")
            for analyzer, count in summary['by_analyzer'].items():
                if count > 0:
                    lines.append(f"    • {analyzer.capitalize()}: {count} issues")
        
        return '\n'.join(lines)
    
    def get_critical_findings(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """
        Get only critical and high severity findings.
        
        Args:
            findings: List of findings
            
        Returns:
            List of critical/high findings
        """
        return [
            f for f in findings
            if f.severity in ['critical', 'high']
        ]
    
    def get_findings_by_category(self, findings: List[LocalFinding], category: str) -> List[LocalFinding]:
        """
        Get findings for a specific category.
        
        Args:
            findings: List of findings
            category: Category to filter by
            
        Returns:
            List of findings in category
        """
        return [
            f for f in findings
            if f.category == category
        ]
    
    def has_critical_issues(self, findings: List[LocalFinding]) -> bool:
        """
        Check if there are any critical issues.
        
        Args:
            findings: List of findings
            
        Returns:
            True if critical issues exist
        """
        return any(f.severity == 'critical' for f in findings)
    
    def get_metrics(self, findings: List[LocalFinding]) -> dict:
        """
        Get metrics from findings.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'total_issues': len(findings),
            'critical_issues': len([f for f in findings if f.severity == 'critical']),
            'high_issues': len([f for f in findings if f.severity == 'high']),
            'security_issues': len([f for f in findings if f.category == 'security']),
            'performance_issues': len([f for f in findings if f.category == 'performance']),
            'quality_issues': len([f for f in findings if f.category == 'quality']),
        }
        
        # Calculate risk score (weighted by severity)
        risk_score = (
            metrics['critical_issues'] * 10 +
            metrics['high_issues'] * 5 +
            len([f for f in findings if f.severity == 'medium']) * 2 +
            len([f for f in findings if f.severity == 'low']) * 1
        )
        metrics['risk_score'] = risk_score
        
        return metrics
    
    def supports_language(self, language: str) -> bool:
        """
        Check if this analyzer supports the given language.

        Args:
            language: Language name

        Returns:
            True if language is supported
        """
        return language.lower() == 'go'

    def __repr__(self) -> str:
        """String representation."""
        enabled = []
        if self.config.enable_security:
            enabled.append('security')
        if self.config.enable_performance:
            enabled.append('performance')
        if self.config.enable_quality:
            enabled.append('quality')

        return f"GoUnifiedAnalyzer(analyzers={enabled}, min_severity={self.config.min_severity})"

