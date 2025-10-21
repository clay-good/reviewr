"""
Unified analyzer that orchestrates all specialized analyzers.

This module provides a comprehensive analysis by running all available
specialized analyzers (security, dataflow, complexity, type safety,
performance, semantic) and aggregating their findings.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .base import LocalAnalyzer, LocalFinding
from .security_analyzer import SecurityAnalyzer
from .dataflow_analyzer import DataFlowAnalyzer
from .complexity_analyzer import ComplexityAnalyzer
from .type_analyzer import TypeAnalyzer
from .performance_analyzer import PerformanceAnalyzer
from .semantic_analyzer import SemanticAnalyzer


@dataclass
class AnalyzerConfig:
    """Configuration for the unified analyzer."""
    
    # Enable/disable specific analyzers
    enable_security: bool = True
    enable_dataflow: bool = True
    enable_complexity: bool = True
    enable_type_safety: bool = True
    enable_performance: bool = True
    enable_semantic: bool = True
    
    # Complexity thresholds
    cyclomatic_threshold: int = 10
    cognitive_threshold: int = 15
    maintainability_threshold: int = 65
    halstead_difficulty_threshold: int = 30
    
    # Severity filters
    min_severity: str = 'info'  # 'critical', 'high', 'medium', 'low', 'info'
    
    # Performance options
    parallel_execution: bool = True
    max_findings_per_analyzer: Optional[int] = None


@dataclass
class AnalysisStats:
    """Statistics from the unified analysis."""
    
    total_findings: int = 0
    findings_by_category: Dict[str, int] = field(default_factory=dict)
    findings_by_severity: Dict[str, int] = field(default_factory=dict)
    analyzers_run: List[str] = field(default_factory=list)
    analysis_time_ms: float = 0.0


class UnifiedAnalyzer(LocalAnalyzer):
    """
    Unified analyzer that runs all specialized analyzers.
    
    This analyzer orchestrates multiple specialized analyzers to provide
    comprehensive code analysis covering:
    - Security vulnerabilities
    - Data flow and taint tracking
    - Code complexity metrics
    - Type safety issues
    - Performance anti-patterns
    - Semantic code understanding
    """
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        """
        Initialize the unified analyzer.
        
        Args:
            config: Configuration for the analyzer (uses defaults if not provided)
        """
        self.config = config or AnalyzerConfig()
        self.stats = AnalysisStats()
        
        # Initialize all specialized analyzers
        self.analyzers: Dict[str, LocalAnalyzer] = {}
        
        if self.config.enable_security:
            self.analyzers['security'] = SecurityAnalyzer()
        
        if self.config.enable_dataflow:
            self.analyzers['dataflow'] = DataFlowAnalyzer()
        
        if self.config.enable_complexity:
            complexity_analyzer = ComplexityAnalyzer()
            # Configure thresholds
            complexity_analyzer.cyclomatic_threshold = self.config.cyclomatic_threshold
            complexity_analyzer.cognitive_threshold = self.config.cognitive_threshold
            complexity_analyzer.maintainability_threshold = self.config.maintainability_threshold
            complexity_analyzer.halstead_difficulty_threshold = self.config.halstead_difficulty_threshold
            self.analyzers['complexity'] = complexity_analyzer
        
        if self.config.enable_type_safety:
            self.analyzers['type_safety'] = TypeAnalyzer()
        
        if self.config.enable_performance:
            self.analyzers['performance'] = PerformanceAnalyzer()
        
        if self.config.enable_semantic:
            self.analyzers['semantic'] = SemanticAnalyzer()
    
    def supports_language(self, language: str) -> bool:
        """
        Check if this analyzer supports the given language.
        
        Currently supports Python. Can be extended for other languages.
        
        Args:
            language: Language name
            
        Returns:
            True if supported
        """
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Perform comprehensive analysis using all enabled analyzers.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of all findings from all analyzers
        """
        import time
        start_time = time.time()
        
        all_findings: List[LocalFinding] = []
        self.stats = AnalysisStats()
        
        # Run each enabled analyzer
        for analyzer_name, analyzer in self.analyzers.items():
            try:
                findings = analyzer.analyze(file_path, content)
                
                # Apply max findings limit if configured
                if self.config.max_findings_per_analyzer:
                    findings = findings[:self.config.max_findings_per_analyzer]
                
                # Filter by minimum severity
                findings = self._filter_by_severity(findings)
                
                all_findings.extend(findings)
                self.stats.analyzers_run.append(analyzer_name)
                
                # Update category stats
                for finding in findings:
                    category = finding.category
                    self.stats.findings_by_category[category] = \
                        self.stats.findings_by_category.get(category, 0) + 1
                    
                    severity = finding.severity
                    self.stats.findings_by_severity[severity] = \
                        self.stats.findings_by_severity.get(severity, 0) + 1
                
            except Exception as e:
                # Log error but continue with other analyzers
                print(f"Warning: {analyzer_name} analyzer failed: {e}")
                continue
        
        # Sort findings by severity (critical first) and then by line number
        all_findings = self._sort_findings(all_findings)
        
        self.stats.total_findings = len(all_findings)
        self.stats.analysis_time_ms = (time.time() - start_time) * 1000
        
        return all_findings
    
    def _filter_by_severity(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """Filter findings by minimum severity level."""
        severity_order = ['info', 'low', 'medium', 'high', 'critical']
        min_level = severity_order.index(self.config.min_severity)
        
        filtered = []
        for finding in findings:
            try:
                finding_level = severity_order.index(finding.severity)
                if finding_level >= min_level:
                    filtered.append(finding)
            except ValueError:
                # Unknown severity, include it
                filtered.append(finding)
        
        return filtered
    
    def _sort_findings(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """Sort findings by severity (critical first) and line number."""
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        
        return sorted(
            findings,
            key=lambda f: (
                severity_order.get(f.severity, 5),  # Unknown severity goes last
                f.line_start,
                f.category
            )
        )
    
    def get_stats(self) -> AnalysisStats:
        """Get statistics from the last analysis run."""
        return self.stats
    
    def get_findings_by_category(self, findings: List[LocalFinding]) -> Dict[str, List[LocalFinding]]:
        """Group findings by category."""
        by_category: Dict[str, List[LocalFinding]] = {}
        
        for finding in findings:
            category = finding.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)
        
        return by_category
    
    def get_findings_by_severity(self, findings: List[LocalFinding]) -> Dict[str, List[LocalFinding]]:
        """Group findings by severity."""
        by_severity: Dict[str, List[LocalFinding]] = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        for finding in findings:
            if finding.severity in by_severity:
                by_severity[finding.severity].append(finding)
        
        return by_severity
    
    def get_summary(self, findings: List[LocalFinding]) -> str:
        """
        Generate a human-readable summary of the analysis.
        
        Args:
            findings: List of findings to summarize
            
        Returns:
            Formatted summary string
        """
        by_severity = self.get_findings_by_severity(findings)
        by_category = self.get_findings_by_category(findings)
        
        summary_lines = [
            "=" * 60,
            "UNIFIED ANALYSIS SUMMARY",
            "=" * 60,
            "",
            f"Total Findings: {len(findings)}",
            f"Analyzers Run: {', '.join(self.stats.analyzers_run)}",
            f"Analysis Time: {self.stats.analysis_time_ms:.2f}ms",
            "",
            "By Severity:",
        ]
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                icon = self._get_severity_icon(severity)
                summary_lines.append(f"  {icon} {severity.upper()}: {count}")
        
        summary_lines.extend([
            "",
            "By Category:",
        ])
        
        for category, category_findings in sorted(by_category.items(), key=lambda x: -len(x[1])):
            summary_lines.append(f"  • {category}: {len(category_findings)}")
        
        summary_lines.append("=" * 60)
        
        return "\n".join(summary_lines)
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get an icon for the severity level."""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '⚪'
        }
        return icons.get(severity, '•')

