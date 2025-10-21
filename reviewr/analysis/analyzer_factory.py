from typing import Optional, List
from .base import LocalAnalyzer, LocalFinding
from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .unified_analyzer import UnifiedAnalyzer, AnalyzerConfig
from .javascript_unified_analyzer import JavaScriptUnifiedAnalyzer, JavaScriptAnalyzerConfig
from .go_unified_analyzer import GoUnifiedAnalyzer, GoAnalyzerConfig
from .rust_unified_analyzer import RustUnifiedAnalyzer, RustAnalyzerConfig
from .java_unified_analyzer import JavaUnifiedAnalyzer, JavaAnalyzerConfig


class AnalyzerFactory:
    """Factory for creating language-specific local analyzers."""

    _analyzers = {
        'python': UnifiedAnalyzer,  # Use unified analyzer for comprehensive Python analysis
        'python_basic': PythonAnalyzer,  # Keep basic analyzer available
        'javascript': JavaScriptUnifiedAnalyzer,  # Use unified analyzer for comprehensive JS/TS analysis
        'typescript': JavaScriptUnifiedAnalyzer,
        'jsx': JavaScriptUnifiedAnalyzer,
        'tsx': JavaScriptUnifiedAnalyzer,
        'javascript_basic': JavaScriptAnalyzer,  # Keep basic analyzer available
        'go': GoUnifiedAnalyzer,  # Use unified analyzer for comprehensive Go analysis
        'rust': RustUnifiedAnalyzer,  # Use unified analyzer for comprehensive Rust analysis
        'java': JavaUnifiedAnalyzer,  # Use unified analyzer for comprehensive Java analysis
    }
    
    @classmethod
    def get_analyzer(cls, language: str, config: Optional[AnalyzerConfig] = None,
                     js_config: Optional[JavaScriptAnalyzerConfig] = None,
                     go_config: Optional[GoAnalyzerConfig] = None,
                     rust_config: Optional[RustAnalyzerConfig] = None,
                     java_config: Optional[JavaAnalyzerConfig] = None) -> Optional[LocalAnalyzer]:
        """
        Get an analyzer for the specified language.

        Args:
            language: Programming language name
            config: Optional configuration for Python UnifiedAnalyzer
            js_config: Optional configuration for JavaScript/TypeScript UnifiedAnalyzer
            go_config: Optional configuration for Go UnifiedAnalyzer
            rust_config: Optional configuration for Rust UnifiedAnalyzer
            java_config: Optional configuration for Java UnifiedAnalyzer

        Returns:
            LocalAnalyzer instance or None if not supported
        """
        analyzer_class = cls._analyzers.get(language.lower())
        if analyzer_class:
            # Pass config to UnifiedAnalyzer if provided
            if analyzer_class == UnifiedAnalyzer and config:
                return analyzer_class(config)
            # Pass js_config to JavaScriptUnifiedAnalyzer if provided
            elif analyzer_class == JavaScriptUnifiedAnalyzer and js_config:
                return analyzer_class(js_config)
            # Pass go_config to GoUnifiedAnalyzer if provided
            elif analyzer_class == GoUnifiedAnalyzer and go_config:
                return analyzer_class(go_config)
            # Pass rust_config to RustUnifiedAnalyzer if provided
            elif analyzer_class == RustUnifiedAnalyzer and rust_config:
                return analyzer_class(rust_config)
            # Pass java_config to JavaUnifiedAnalyzer if provided
            elif analyzer_class == JavaUnifiedAnalyzer and java_config:
                return analyzer_class(java_config)
            return analyzer_class()
        return None
    
    @classmethod
    def supports_language(cls, language: str) -> bool:
        """
        Check if local analysis is supported for the language.
        
        Args:
            language: Programming language name
            
        Returns:
            True if supported
        """
        return language.lower() in cls._analyzers
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported languages."""
        return list(cls._analyzers.keys())


    @classmethod
    def get_unified_analyzer(cls, config: Optional[AnalyzerConfig] = None) -> Optional[UnifiedAnalyzer]:
        """
        Get a unified analyzer with optional configuration.

        Args:
            config: Optional configuration for the analyzer

        Returns:
            UnifiedAnalyzer instance
        """
        return UnifiedAnalyzer(config)

    @classmethod
    def create_custom_config(
        cls,
        enable_security: bool = True,
        enable_dataflow: bool = True,
        enable_complexity: bool = True,
        enable_type_safety: bool = True,
        enable_performance: bool = True,
        enable_semantic: bool = True,
        min_severity: str = 'info'
    ) -> AnalyzerConfig:
        """
        Create a custom Python analyzer configuration.

        Args:
            enable_security: Enable security analysis
            enable_dataflow: Enable data flow analysis
            enable_complexity: Enable complexity analysis
            enable_type_safety: Enable type safety analysis
            enable_performance: Enable performance analysis
            enable_semantic: Enable semantic analysis
            min_severity: Minimum severity level to report

        Returns:
            AnalyzerConfig instance
        """
        return AnalyzerConfig(
            enable_security=enable_security,
            enable_dataflow=enable_dataflow,
            enable_complexity=enable_complexity,
            enable_type_safety=enable_type_safety,
            enable_performance=enable_performance,
            enable_semantic=enable_semantic,
            min_severity=min_severity
        )

    @classmethod
    def create_javascript_config(
        cls,
        enable_security: bool = True,
        enable_performance: bool = True,
        enable_type_safety: bool = True,
        enable_quality: bool = True,
        min_severity: str = 'info',
        cyclomatic_threshold: int = 10,
        max_function_lines: int = 50,
        max_function_params: int = 5
    ) -> JavaScriptAnalyzerConfig:
        """
        Create a custom JavaScript/TypeScript analyzer configuration.

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
            JavaScriptAnalyzerConfig instance
        """
        return JavaScriptAnalyzerConfig(
            enable_security=enable_security,
            enable_performance=enable_performance,
            enable_type_safety=enable_type_safety,
            enable_quality=enable_quality,
            min_severity=min_severity,
            cyclomatic_threshold=cyclomatic_threshold,
            max_function_lines=max_function_lines,
            max_function_params=max_function_params
        )

    @classmethod
    def get_javascript_analyzer(cls, config: Optional[JavaScriptAnalyzerConfig] = None) -> JavaScriptUnifiedAnalyzer:
        """
        Get a JavaScript/TypeScript unified analyzer with optional configuration.

        Args:
            config: Optional configuration for the analyzer

        Returns:
            JavaScriptUnifiedAnalyzer instance
        """
        return JavaScriptUnifiedAnalyzer(config)

    @classmethod
    def create_go_config(
        cls,
        enable_security: bool = True,
        enable_performance: bool = True,
        enable_quality: bool = True,
        min_severity: str = 'info',
        max_function_params: int = 5,
        max_nesting_level: int = 4
    ) -> GoAnalyzerConfig:
        """
        Create a custom Go analyzer configuration.

        Args:
            enable_security: Enable security analysis
            enable_performance: Enable performance analysis
            enable_quality: Enable code quality analysis
            min_severity: Minimum severity level to report
            max_function_params: Maximum function parameters
            max_nesting_level: Maximum nesting level

        Returns:
            GoAnalyzerConfig instance
        """
        return GoAnalyzerConfig(
            enable_security=enable_security,
            enable_performance=enable_performance,
            enable_quality=enable_quality,
            min_severity=min_severity,
            max_function_params=max_function_params,
            max_nesting_level=max_nesting_level
        )

    @classmethod
    def get_go_analyzer(cls, config: Optional[GoAnalyzerConfig] = None) -> GoUnifiedAnalyzer:
        """
        Get a Go unified analyzer with optional configuration.

        Args:
            config: Optional configuration for the analyzer

        Returns:
            GoUnifiedAnalyzer instance
        """
        return GoUnifiedAnalyzer(config)

    @classmethod
    def create_rust_config(
        cls,
        enable_ownership: bool = True,
        enable_safety: bool = True,
        enable_performance: bool = True,
        enable_quality: bool = True,
        min_severity: str = 'info',
        max_function_params: int = 5,
        max_nesting_level: int = 4,
        max_function_lines: int = 50
    ) -> RustAnalyzerConfig:
        """
        Create a custom Rust analyzer configuration.

        Args:
            enable_ownership: Enable ownership/borrowing analysis
            enable_safety: Enable safety analysis
            enable_performance: Enable performance analysis
            enable_quality: Enable code quality analysis
            min_severity: Minimum severity level to report
            max_function_params: Maximum function parameters
            max_nesting_level: Maximum nesting level
            max_function_lines: Maximum function lines

        Returns:
            RustAnalyzerConfig instance
        """
        return RustAnalyzerConfig(
            enable_ownership=enable_ownership,
            enable_safety=enable_safety,
            enable_performance=enable_performance,
            enable_quality=enable_quality,
            min_severity=min_severity,
            max_function_params=max_function_params,
            max_nesting_level=max_nesting_level,
            max_function_lines=max_function_lines
        )

    @classmethod
    def get_rust_analyzer(cls, config: Optional[RustAnalyzerConfig] = None) -> RustUnifiedAnalyzer:
        """
        Get a Rust unified analyzer with optional configuration.

        Args:
            config: Optional configuration for the analyzer

        Returns:
            RustUnifiedAnalyzer instance
        """
        return RustUnifiedAnalyzer(config)

    @classmethod
    def create_java_config(
        cls,
        enable_security: bool = True,
        enable_concurrency: bool = True,
        enable_performance: bool = True,
        enable_quality: bool = True,
        min_severity: str = 'info',
        max_method_params: int = 5,
        max_nesting_level: int = 4,
        max_method_lines: int = 50
    ) -> JavaAnalyzerConfig:
        """
        Create a custom Java analyzer configuration.

        Args:
            enable_security: Enable security analysis
            enable_concurrency: Enable concurrency analysis
            enable_performance: Enable performance analysis
            enable_quality: Enable code quality analysis
            min_severity: Minimum severity level to report
            max_method_params: Maximum method parameters
            max_nesting_level: Maximum nesting level
            max_method_lines: Maximum method lines

        Returns:
            JavaAnalyzerConfig instance
        """
        return JavaAnalyzerConfig(
            enable_security=enable_security,
            enable_concurrency=enable_concurrency,
            enable_performance=enable_performance,
            enable_quality=enable_quality,
            min_severity=min_severity,
            max_method_params=max_method_params,
            max_nesting_level=max_nesting_level,
            max_method_lines=max_method_lines
        )

    @classmethod
    def get_java_analyzer(cls, config: Optional[JavaAnalyzerConfig] = None) -> JavaUnifiedAnalyzer:
        """
        Get a Java unified analyzer with optional configuration.

        Args:
            config: Optional configuration for the analyzer

        Returns:
            JavaUnifiedAnalyzer instance
        """
        return JavaUnifiedAnalyzer(config)


def analyze_file(file_path: str, content: str, language: str,
                 config: Optional[AnalyzerConfig] = None,
                 js_config: Optional[JavaScriptAnalyzerConfig] = None,
                 go_config: Optional[GoAnalyzerConfig] = None,
                 rust_config: Optional[RustAnalyzerConfig] = None,
                 java_config: Optional[JavaAnalyzerConfig] = None) -> List[LocalFinding]:
    """
    Analyze a file using the appropriate language analyzer.

    Args:
        file_path: Path to the file
        content: File content
        language: Programming language
        config: Optional configuration for Python UnifiedAnalyzer
        js_config: Optional configuration for JavaScript/TypeScript UnifiedAnalyzer
        go_config: Optional configuration for Go UnifiedAnalyzer
        rust_config: Optional configuration for Rust UnifiedAnalyzer
        java_config: Optional configuration for Java UnifiedAnalyzer

    Returns:
        List of local findings
    """
    analyzer = AnalyzerFactory.get_analyzer(language, config, js_config, go_config, rust_config, java_config)
    if analyzer:
        return analyzer.analyze(file_path, content)
    return []

