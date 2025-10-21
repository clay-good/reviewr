"""
Java Unified Analyzer

Orchestrates all Java analyzers (Security, Concurrency, Performance, Quality)
and provides comprehensive analysis with flexible configuration.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from collections import Counter

from .base import LocalAnalyzer, LocalFinding
from .java_security_analyzer import JavaSecurityAnalyzer
from .java_concurrency_analyzer import JavaConcurrencyAnalyzer
from .java_performance_analyzer import JavaPerformanceAnalyzer
from .java_quality_analyzer import JavaQualityAnalyzer


@dataclass
class JavaAnalyzerConfig:
    """Configuration for Java unified analyzer."""
    
    # Analyzer toggles
    enable_security: bool = True
    enable_concurrency: bool = True
    enable_performance: bool = True
    enable_quality: bool = True
    
    # Filtering
    min_severity: str = 'info'  # info, low, medium, high, critical
    
    # Complexity thresholds
    max_method_lines: int = 50
    max_class_lines: int = 500
    max_method_params: int = 5
    max_nesting_level: int = 4
    max_cyclomatic_complexity: int = 10
    
    # Performance thresholds
    warn_on_autoboxing: bool = True
    warn_on_string_concat: bool = True
    warn_on_reflection: bool = True


class JavaUnifiedAnalyzer(LocalAnalyzer):
    """Unified analyzer that orchestrates all Java analyzers."""
    
    def __init__(self, config: Optional[JavaAnalyzerConfig] = None):
        """
        Initialize unified analyzer.
        
        Args:
            config: Configuration for the analyzer
        """
        self.config = config or JavaAnalyzerConfig()
        self.analyzers = []
        
        # Initialize enabled analyzers
        if self.config.enable_security:
            self.analyzers.append(JavaSecurityAnalyzer())
        
        if self.config.enable_concurrency:
            self.analyzers.append(JavaConcurrencyAnalyzer())
        
        if self.config.enable_performance:
            self.analyzers.append(JavaPerformanceAnalyzer())
        
        if self.config.enable_quality:
            self.analyzers.append(JavaQualityAnalyzer())
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'java'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Java code using all enabled analyzers.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            List of findings from all analyzers
        """
        all_findings = []
        
        # Run all enabled analyzers
        for analyzer in self.analyzers:
            findings = analyzer.analyze(file_path, content)
            all_findings.extend(findings)
        
        # Filter by severity
        filtered_findings = self._filter_by_severity(all_findings)
        
        # Sort by severity and line number
        sorted_findings = sorted(
            filtered_findings,
            key=lambda f: (
                self._severity_order(f.severity),
                f.line_start
            )
        )
        
        return sorted_findings
    
    def analyze_with_summary(self, file_path: str, content: str) -> Dict:
        """
        Analyze Java code and return findings with summary statistics.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            Dictionary with findings and summary
        """
        findings = self.analyze(file_path, content)
        
        # Calculate statistics
        severity_counts = Counter(f.severity for f in findings)
        category_counts = Counter(f.category for f in findings)
        
        # Calculate risk score (weighted by severity)
        risk_score = (
            severity_counts.get('critical', 0) * 10 +
            severity_counts.get('high', 0) * 5 +
            severity_counts.get('medium', 0) * 2 +
            severity_counts.get('low', 0) * 1
        )
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = 'critical'
        elif risk_score >= 20:
            risk_level = 'high'
        elif risk_score >= 10:
            risk_level = 'medium'
        elif risk_score > 0:
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        return {
            'file_path': file_path,
            'findings': findings,
            'summary': {
                'total_findings': len(findings),
                'by_severity': dict(severity_counts),
                'by_category': dict(category_counts),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'analyzers_run': [
                    type(analyzer).__name__ for analyzer in self.analyzers
                ]
            }
        }
    
    def _filter_by_severity(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """Filter findings by minimum severity."""
        severity_levels = {
            'info': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        min_level = severity_levels.get(self.config.min_severity.lower(), 0)
        
        return [
            f for f in findings
            if severity_levels.get(f.severity.lower(), 0) >= min_level
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
        return order.get(severity.lower(), 5)
    
    def get_metrics(self, content: str) -> Dict:
        """
        Calculate code metrics for Java code.
        
        Args:
            content: File content
            
        Returns:
            Dictionary of metrics
        """
        lines = content.split('\n')
        
        # Count lines
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('//'))
        comment_lines = sum(1 for line in lines if line.strip().startswith('//'))
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # Count methods
        method_pattern = r'(public|private|protected)\s+[^(]+\([^)]*\)\s*\{'
        import re
        methods = len(re.findall(method_pattern, content))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        classes = len(re.findall(class_pattern, content))
        
        # Count imports
        import_pattern = r'import\s+[^;]+;'
        imports = len(re.findall(import_pattern, content))
        
        # Estimate complexity (simple heuristic)
        complexity_keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||']
        complexity = sum(content.count(keyword) for keyword in complexity_keywords)
        
        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'methods': methods,
            'classes': classes,
            'imports': imports,
            'estimated_complexity': complexity,
            'avg_method_length': code_lines // methods if methods > 0 else 0
        }
    
    def format_findings_report(self, file_path: str, content: str) -> str:
        """
        Generate a formatted report of findings.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            Formatted report string
        """
        result = self.analyze_with_summary(file_path, content)
        findings = result['findings']
        summary = result['summary']
        metrics = self.get_metrics(content)
        
        report = []
        report.append("=" * 80)
        report.append(f"Java Analysis Report: {file_path}")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Findings: {summary['total_findings']}")
        report.append(f"Risk Level: {summary['risk_level'].upper()} (score: {summary['risk_score']})")
        report.append("")
        
        # Severity breakdown
        report.append("By Severity:")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = summary['by_severity'].get(severity, 0)
            if count > 0:
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}
                report.append(f"  {emoji.get(severity, '•')} {severity.capitalize()}: {count}")
        report.append("")
        
        # Category breakdown
        report.append("By Category:")
        for category, count in summary['by_category'].items():
            report.append(f"  • {category.capitalize()}: {count}")
        report.append("")
        
        # Metrics
        report.append("📈 METRICS")
        report.append("-" * 80)
        report.append(f"Lines of Code: {metrics['code_lines']}")
        report.append(f"Methods: {metrics['methods']}")
        report.append(f"Classes: {metrics['classes']}")
        report.append(f"Avg Method Length: {metrics['avg_method_length']} lines")
        report.append(f"Estimated Complexity: {metrics['estimated_complexity']}")
        report.append("")
        
        # Findings
        if findings:
            report.append("🔍 FINDINGS")
            report.append("-" * 80)
            
            for i, finding in enumerate(findings, 1):
                emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵',
                    'info': '⚪'
                }
                
                report.append(f"\n{i}. {emoji.get(finding.severity, '•')} [{finding.severity.upper()}] Line {finding.line_start}")
                report.append(f"   Category: {finding.category}")
                report.append(f"   Message: {finding.message}")
                report.append(f"   Suggestion: {finding.suggestion}")
                if finding.code_snippet:
                    report.append(f"   Code: {finding.code_snippet.strip()}")
        else:
            report.append("✅ No issues found!")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

