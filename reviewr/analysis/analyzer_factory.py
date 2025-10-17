from typing import Optional, List
from .base import LocalAnalyzer, LocalFinding
from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer


class AnalyzerFactory:
    """Factory for creating language-specific local analyzers."""

    _analyzers = {
        'python': PythonAnalyzer,
        'javascript': JavaScriptAnalyzer,
        'typescript': JavaScriptAnalyzer,
        'jsx': JavaScriptAnalyzer,
        'tsx': JavaScriptAnalyzer,
    }
    
    @classmethod
    def get_analyzer(cls, language: str) -> Optional[LocalAnalyzer]:
        """
        Get an analyzer for the specified language.
        
        Args:
            language: Programming language name
            
        Returns:
            LocalAnalyzer instance or None if not supported
        """
        analyzer_class = cls._analyzers.get(language.lower())
        if analyzer_class:
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


def analyze_file(file_path: str, content: str, language: str) -> List[LocalFinding]:
    """
    Analyze a file using the appropriate language analyzer.
    
    Args:
        file_path: Path to the file
        content: File content
        language: Programming language
        
    Returns:
        List of local findings
    """
    analyzer = AnalyzerFactory.get_analyzer(language)
    if analyzer:
        return analyzer.analyze(file_path, content)
    return []

