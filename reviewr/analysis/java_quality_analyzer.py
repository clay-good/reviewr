"""
Java Quality Analyzer

Detects code quality issues in Java including exception handling problems,
resource leaks, code smells, and complexity issues.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaQualityAnalyzer(LocalAnalyzer):
    """Analyzes Java code for quality issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'java'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Java code for quality issues.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_exception_handling(content, file_path, lines))
        findings.extend(self._detect_null_checks(content, file_path, lines))
        findings.extend(self._detect_equals_hashcode(content, file_path, lines))
        findings.extend(self._detect_clone_issues(content, file_path, lines))
        findings.extend(self._detect_finalize_usage(content, file_path, lines))
        findings.extend(self._detect_complexity_issues(content, file_path, lines))
        findings.extend(self._detect_naming_conventions(content, file_path, lines))
        findings.extend(self._detect_code_smells(content, file_path, lines))
        findings.extend(self._detect_deprecated_api(content, file_path, lines))
        
        return findings
    
    def _detect_exception_handling(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect exception handling issues."""
        findings = []
        
        # Catching generic Exception
        pattern = r'catch\s*\(\s*Exception\s+\w+\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='quality',
                message='Catching generic Exception - too broad',
                suggestion='Catch specific exception types',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Catching Throwable
        pattern = r'catch\s*\(\s*Throwable\s+\w+\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='quality',
                message='Catching Throwable - catches errors that should not be caught',
                suggestion='Catch specific exceptions, not Throwable',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Swallowing exceptions
        pattern = r'catch\s*\([^)]+\)\s*\{\s*//[^\n]*\n\s*\}'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='quality',
                message='Swallowing exception - only comment in catch block',
                suggestion='Log exception or rethrow as appropriate',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Throwing generic Exception
        pattern = r'throws?\s+Exception\b'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Throwing generic Exception',
                suggestion='Throw specific exception types',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # printStackTrace() usage
        pattern = r'\.printStackTrace\s*\(\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='quality',
                message='Using printStackTrace() - not suitable for production',
                suggestion='Use proper logging framework (SLF4J, Log4j)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_null_checks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect null check issues."""
        findings = []
        
        # Comparing with null using ==
        pattern = r'if\s*\(\s*\w+\s*==\s*null\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='quality',
                message='Null check with == - consider using Objects.isNull()',
                suggestion='Use Objects.isNull() or Objects.nonNull() for clarity',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Returning null from collection methods
        pattern = r'return\s+null\s*;'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if in a method returning collection
            context_start = max(0, match.start() - 500)
            context = content[context_start:match.start()]
            
            collection_types = ['List', 'Set', 'Map', 'Collection', 'Array']
            
            if any(ctype in context for ctype in collection_types):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='Returning null from collection method',
                    suggestion='Return empty collection instead (Collections.emptyList(), etc.)',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_equals_hashcode(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect equals/hashCode issues."""
        findings = []
        
        # equals() without hashCode()
        has_equals = re.search(r'public\s+boolean\s+equals\s*\(\s*Object', content)
        has_hashcode = re.search(r'public\s+int\s+hashCode\s*\(\s*\)', content)
        
        if has_equals and not has_hashcode:
            line_num = content[:has_equals.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='quality',
                message='equals() overridden without hashCode()',
                suggestion='Always override hashCode() when overriding equals()',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # hashCode() without equals()
        if has_hashcode and not has_equals:
            line_num = content[:has_hashcode.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='quality',
                message='hashCode() overridden without equals()',
                suggestion='Override equals() when overriding hashCode()',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_clone_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect clone() implementation issues."""
        findings = []
        
        # clone() without Cloneable
        pattern = r'public\s+\w+\s+clone\s*\(\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if class implements Cloneable
            if 'implements Cloneable' not in content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='clone() method without implementing Cloneable',
                    suggestion='Implement Cloneable interface or use copy constructor',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_finalize_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect finalize() usage."""
        findings = []
        
        # finalize() method
        pattern = r'protected\s+void\s+finalize\s*\(\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='quality',
                message='finalize() is deprecated and unreliable',
                suggestion='Use try-with-resources or Cleaner API (Java 9+)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_complexity_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect complexity issues."""
        findings = []
        
        # Methods with too many parameters
        pattern = r'(public|private|protected)\s+[^(]+\([^)]{100,}\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            param_count = match.group().count(',') + 1
            
            if param_count > 5:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message=f'Method has {param_count} parameters (> 5)',
                    suggestion='Consider using parameter object or builder pattern',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Deep nesting
        for i, line in enumerate(lines, 1):
            indent_level = (len(line) - len(line.lstrip())) // 4
            
            if indent_level >= 5 and line.strip() and not line.strip().startswith('//'):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i,
                    line_end=i,
                    severity='medium',
                    category='quality',
                    message=f'Deep nesting detected (level {indent_level})',
                    suggestion='Extract nested logic into separate methods',
                    code_snippet=line
                ))
        
        return findings
    
    def _detect_naming_conventions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect naming convention violations."""
        findings = []
        
        # Class names not in PascalCase
        pattern = r'class\s+([a-z_]\w*)\s*'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            class_name = match.group(1)
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message=f'Class name "{class_name}" not in PascalCase',
                suggestion='Use PascalCase for class names',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Constants not in UPPER_SNAKE_CASE
        pattern = r'(public|private|protected)\s+static\s+final\s+\w+\s+([a-z]\w*)\s*='
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            const_name = match.group(2)
            
            if not const_name.isupper():
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Constant "{const_name}" not in UPPER_SNAKE_CASE',
                    suggestion='Use UPPER_SNAKE_CASE for constants',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_code_smells(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect code smells."""
        findings = []
        
        # TODO comments
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i,
                    line_end=i,
                    severity='info',
                    category='quality',
                    message='TODO/FIXME comment found',
                    suggestion='Address TODO or create tracking issue',
                    code_snippet=line
                ))
        
        # Magic numbers
        pattern = r'(?<![a-zA-Z_])[0-9]{3,}(?![a-zA-Z_])'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Skip if in constant declaration
            if 'final' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Magic number detected: {match.group()}',
                    suggestion='Extract to named constant',
                    code_snippet=line_content
                ))
        
        # System.out.println in production code
        pattern = r'System\.(out|err)\.print'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Skip if in test file
            if 'Test' not in file_path:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='System.out/err in production code',
                    suggestion='Use proper logging framework',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_deprecated_api(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect usage of deprecated APIs."""
        findings = []
        
        # Date class usage (deprecated in favor of java.time)
        pattern = r'new\s+Date\s*\('
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Using legacy Date class',
                suggestion='Use java.time API (LocalDate, LocalDateTime, Instant)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Vector usage (legacy)
        pattern = r'new\s+Vector\s*<'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Using legacy Vector class',
                suggestion='Use ArrayList or CopyOnWriteArrayList',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Hashtable usage (legacy)
        pattern = r'new\s+Hashtable\s*<'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Using legacy Hashtable class',
                suggestion='Use HashMap or ConcurrentHashMap',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings

