"""
Unified JavaScript/TypeScript Analyzer

Orchestrates all specialized JavaScript/TypeScript analyzers:
- Security analysis
- Performance analysis
- Type safety analysis (TypeScript)
- Code quality analysis (from original JavaScriptAnalyzer)
"""

from dataclasses import dataclass
from typing import List, Optional
from .base import LocalAnalyzer, LocalFinding
from .javascript_analyzer import JavaScriptAnalyzer
from .javascript_security_analyzer import JavaScriptSecurityAnalyzer
from .javascript_performance_analyzer import JavaScriptPerformanceAnalyzer
from .javascript_type_analyzer import JavaScriptTypeAnalyzer


@dataclass
class JavaScriptAnalyzerConfig:
    """Configuration for JavaScript/TypeScript analysis."""
    enable_security: bool = True
    enable_performance: bool = True
    enable_type_safety: bool = True  # Only for TypeScript
    enable_quality: bool = True  # Original analyzer (complexity, code smells, etc.)
    min_severity: str = 'info'  # info, low, medium, high, critical
    
    # Thresholds
    cyclomatic_threshold: int = 10
    max_function_lines: int = 50
    max_function_params: int = 5


class JavaScriptUnifiedAnalyzer(LocalAnalyzer):
    """
    Unified analyzer for JavaScript and TypeScript.
    
    Orchestrates multiple specialized analyzers:
    - JavaScriptSecurityAnalyzer: XSS, SQL injection, command injection, etc.
    - JavaScriptPerformanceAnalyzer: DOM operations, memory leaks, React patterns
    - JavaScriptTypeAnalyzer: TypeScript type safety (TypeScript only)
    - JavaScriptAnalyzer: Code quality, complexity, code smells
    """
    
    def __init__(self, config: Optional[JavaScriptAnalyzerConfig] = None):
        """
        Initialize the unified analyzer.
        
        Args:
            config: Optional configuration for the analyzer
        """
        self.config = config or JavaScriptAnalyzerConfig()
        
        # Initialize analyzers based on configuration
        self.analyzers = []
        
        if self.config.enable_security:
            self.analyzers.append(JavaScriptSecurityAnalyzer())
        
        if self.config.enable_performance:
            self.analyzers.append(JavaScriptPerformanceAnalyzer())
        
        if self.config.enable_type_safety:
            self.analyzers.append(JavaScriptTypeAnalyzer())
        
        if self.config.enable_quality:
            quality_analyzer = JavaScriptAnalyzer()
            quality_analyzer.complexity_threshold = self.config.cyclomatic_threshold
            quality_analyzer.max_function_lines = self.config.max_function_lines
            quality_analyzer.max_function_params = self.config.max_function_params
            self.analyzers.append(quality_analyzer)
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() in ['javascript', 'typescript', 'jsx', 'tsx']
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze JavaScript/TypeScript code using all enabled analyzers.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of findings from all analyzers
        """
        all_findings = []
        
        # Determine if this is TypeScript
        is_typescript = file_path.endswith(('.ts', '.tsx'))
        
        # Run each enabled analyzer
        for analyzer in self.analyzers:
            # Skip TypeScript-only analyzers for JavaScript files
            if isinstance(analyzer, JavaScriptTypeAnalyzer) and not is_typescript:
                continue
            
            try:
                findings = analyzer.analyze(file_path, content)
                all_findings.extend(findings)
            except Exception as e:
                # Log error but continue with other analyzers
                print(f"Warning: {analyzer.__class__.__name__} failed: {e}")
        
        # Filter by severity
        filtered_findings = self._filter_by_severity(all_findings)
        
        # Sort by severity and line number
        sorted_findings = sorted(
            filtered_findings,
            key=lambda f: (self._severity_order(f.severity), f.line_start)
        )
        
        return sorted_findings
    
    def _filter_by_severity(self, findings: List[LocalFinding]) -> List[LocalFinding]:
        """Filter findings by minimum severity level."""
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
        """Get numeric order for severity (for sorting)."""
        order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'info': 4
        }
        return order.get(severity.lower(), 5)
    
    def get_summary(self, findings: List[LocalFinding]) -> str:
        """
        Generate a summary of findings.
        
        Args:
            findings: List of findings
            
        Returns:
            Summary string
        """
        if not findings:
            return "✓ No issues found"
        
        # Count by severity
        by_severity = {}
        for finding in findings:
            severity = finding.severity.lower()
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by category
        by_category = {}
        for finding in findings:
            category = finding.category or 'other'
            by_category[category] = by_category.get(category, 0) + 1
        
        # Build summary
        lines = [
            f"Found {len(findings)} issue(s):",
            "",
            "By Severity:",
        ]
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = by_severity.get(severity, 0)
            if count > 0:
                icon = self._get_severity_icon(severity)
                lines.append(f"  {icon} {severity.upper()}: {count}")
        
        lines.extend([
            "",
            "By Category:",
        ])
        
        for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
            icon = self._get_category_icon(category)
            lines.append(f"  {icon} {category}: {count}")
        
        return "\n".join(lines)
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level."""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '⚪'
        }
        return icons.get(severity.lower(), '⚪')
    
    def _get_category_icon(self, category: str) -> str:
        """Get icon for category."""
        icons = {
            'security': '🔒',
            'performance': '⚡',
            'type_safety': '🏷️',
            'complexity': '🧩',
            'smell': '👃',
            'standards': '📏',
            'quality': '✨'
        }
        return icons.get(category, '📋')


def create_javascript_analyzer(
    enable_security: bool = True,
    enable_performance: bool = True,
    enable_type_safety: bool = True,
    enable_quality: bool = True,
    min_severity: str = 'info',
    cyclomatic_threshold: int = 10,
    max_function_lines: int = 50,
    max_function_params: int = 5
) -> JavaScriptUnifiedAnalyzer:
    """
    Create a JavaScript/TypeScript analyzer with custom configuration.
    
    Args:
        enable_security: Enable security analysis
        enable_performance: Enable performance analysis
        enable_type_safety: Enable type safety analysis (TypeScript only)
        enable_quality: Enable code quality analysis
        min_severity: Minimum severity level to report
        cyclomatic_threshold: Maximum cyclomatic complexity
        max_function_lines: Maximum function length
        max_function_params: Maximum function parameters
        
    Returns:
        Configured JavaScriptUnifiedAnalyzer
    """
    config = JavaScriptAnalyzerConfig(
        enable_security=enable_security,
        enable_performance=enable_performance,
        enable_type_safety=enable_type_safety,
        enable_quality=enable_quality,
        min_severity=min_severity,
        cyclomatic_threshold=cyclomatic_threshold,
        max_function_lines=max_function_lines,
        max_function_params=max_function_params
    )
    
    return JavaScriptUnifiedAnalyzer(config)

