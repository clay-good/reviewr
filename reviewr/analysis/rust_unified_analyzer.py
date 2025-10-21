"""
Rust Unified Analyzer

Orchestrates all Rust analyzers (ownership, safety, performance, quality)
with flexible configuration and comprehensive reporting.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from .base import LocalAnalyzer, LocalFinding
from .rust_ownership_analyzer import RustOwnershipAnalyzer
from .rust_safety_analyzer import RustSafetyAnalyzer
from .rust_performance_analyzer import RustPerformanceAnalyzer
from .rust_quality_analyzer import RustQualityAnalyzer


@dataclass
class RustAnalyzerConfig:
    """Configuration for Rust unified analyzer."""
    
    # Analyzer toggles
    enable_ownership: bool = True
    enable_safety: bool = True
    enable_performance: bool = True
    enable_quality: bool = True
    
    # Severity filtering
    min_severity: str = 'info'  # info, low, medium, high, critical
    
    # Thresholds
    max_function_params: int = 5
    max_nesting_level: int = 4
    max_function_lines: int = 50
    
    # Specific warnings
    warn_unwrap: bool = True
    warn_clone: bool = True
    warn_unsafe: bool = True
    warn_panic: bool = True


class RustUnifiedAnalyzer(LocalAnalyzer):
    """Unified analyzer for Rust code."""
    
    def __init__(self, config: Optional[RustAnalyzerConfig] = None):
        """
        Initialize unified analyzer.
        
        Args:
            config: Configuration for analyzers
        """
        self.config = config or RustAnalyzerConfig()
        self.analyzers = []
        
        # Initialize enabled analyzers
        if self.config.enable_ownership:
            self.analyzers.append(RustOwnershipAnalyzer())
        
        if self.config.enable_safety:
            self.analyzers.append(RustSafetyAnalyzer())
        
        if self.config.enable_performance:
            self.analyzers.append(RustPerformanceAnalyzer())
        
        if self.config.enable_quality:
            self.analyzers.append(RustQualityAnalyzer())
    
    def supports_language(self, language: str) -> bool:
        """
        Check if this analyzer supports the given language.
        
        Args:
            language: Language name
            
        Returns:
            True if language is supported
        """
        return language.lower() == 'rust'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Rust code with all enabled analyzers.
        
        Args:
            file_path: Path to the Rust file
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
        Get summary statistics for findings.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_findings': len(findings),
            'by_severity': {},
            'by_category': {},
            'by_analyzer': {}
        }
        
        # Count by severity
        for finding in findings:
            severity = finding.severity
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        # Count by category
        for finding in findings:
            category = finding.category or 'other'
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        # Map categories to analyzers
        category_to_analyzer = {
            'ownership': 'ownership',
            'safety': 'safety',
            'performance': 'performance',
            'quality': 'quality'
        }
        
        for finding in findings:
            analyzer = category_to_analyzer.get(finding.category, 'other')
            summary['by_analyzer'][analyzer] = summary['by_analyzer'].get(analyzer, 0) + 1
        
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
        
        output = [f"\n📊 Rust Analysis Summary: {summary['total_findings']} issues found\n"]
        
        # By severity
        output.append("  By Severity:")
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
                output.append(f"    {icon} {severity.upper()}: {count}")
        
        # By category
        output.append("\n  By Category:")
        category_icons = {
            'ownership': '🔗',
            'safety': '🛡️',
            'performance': '⚡',
            'quality': '✨'
        }
        
        for category, count in sorted(summary['by_category'].items(), key=lambda x: -x[1]):
            icon = category_icons.get(category, '📋')
            output.append(f"    {icon} {category}: {count}")
        
        # By analyzer
        output.append("\n  By Analyzer:")
        for analyzer, count in sorted(summary['by_analyzer'].items(), key=lambda x: -x[1]):
            output.append(f"    • {analyzer.capitalize()}: {count} issues")
        
        return '\n'.join(output)
    
    def get_critical_findings(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """
        Get only critical and high severity findings.
        
        Args:
            findings: List of findings
            
        Returns:
            List of critical/high findings
        """
        return [f for f in findings if f.severity in ['critical', 'high']]
    
    def get_findings_by_category(self, findings: List[LocalFinding], category: str) -> List[LocalFinding]:
        """
        Get findings for a specific category.
        
        Args:
            findings: List of findings
            category: Category to filter by
            
        Returns:
            List of findings for category
        """
        return [f for f in findings if f.category == category]
    
    def has_critical_issues(self, findings: List[LocalFinding]) -> bool:
        """
        Check if there are any critical issues.
        
        Args:
            findings: List of findings
            
        Returns:
            True if critical issues exist
        """
        return any(f.severity == 'critical' for f in findings)
    
    def get_metrics(self, findings: List[LocalFinding]) -> Dict[str, any]:
        """
        Get detailed metrics about findings.
        
        Args:
            findings: List of findings
            
        Returns:
            Dictionary with metrics
        """
        summary = self.get_summary(findings)
        
        # Calculate risk score (weighted by severity)
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1,
            'info': 0
        }
        
        risk_score = sum(
            severity_weights.get(f.severity, 0)
            for f in findings
        )
        
        return {
            'total_findings': summary['total_findings'],
            'critical_count': summary['by_severity'].get('critical', 0),
            'high_count': summary['by_severity'].get('high', 0),
            'medium_count': summary['by_severity'].get('medium', 0),
            'low_count': summary['by_severity'].get('low', 0),
            'info_count': summary['by_severity'].get('info', 0),
            'risk_score': risk_score,
            'categories': list(summary['by_category'].keys()),
            'analyzers_used': list(summary['by_analyzer'].keys())
        }
    
    def __repr__(self) -> str:
        """String representation."""
        enabled = []
        if self.config.enable_ownership:
            enabled.append('ownership')
        if self.config.enable_safety:
            enabled.append('safety')
        if self.config.enable_performance:
            enabled.append('performance')
        if self.config.enable_quality:
            enabled.append('quality')
        
        return f"RustUnifiedAnalyzer(analyzers={enabled}, min_severity={self.config.min_severity})"

