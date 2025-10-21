"""
Java Performance Analyzer

Detects performance anti-patterns in Java code including memory leaks,
inefficient collections, autoboxing, and string concatenation issues.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaPerformanceAnalyzer(LocalAnalyzer):
    """Analyzes Java code for performance issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'java'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Java code for performance issues.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_string_concatenation(content, file_path, lines))
        findings.extend(self._detect_autoboxing(content, file_path, lines))
        findings.extend(self._detect_inefficient_collections(content, file_path, lines))
        findings.extend(self._detect_stream_issues(content, file_path, lines))
        findings.extend(self._detect_regex_compilation(content, file_path, lines))
        findings.extend(self._detect_exception_control_flow(content, file_path, lines))
        findings.extend(self._detect_reflection_issues(content, file_path, lines))
        findings.extend(self._detect_resource_leaks(content, file_path, lines))
        findings.extend(self._detect_unnecessary_object_creation(content, file_path, lines))
        
        return findings
    
    def _detect_string_concatenation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient string concatenation."""
        findings = []
        
        # String concatenation in loops
        pattern = r'for\s*\([^)]+\)\s*\{[^}]*\+\s*=\s*[^}]*\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            match_text = match.group()
            if '+=' in match_text and ('String' in match_text or '"' in match_text):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='performance',
                    message='String concatenation in loop - creates many temporary objects',
                    suggestion='Use StringBuilder for string concatenation in loops',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Multiple string concatenations with +
        pattern = r'String\s+\w+\s*=\s*[^;]*\+[^;]*\+[^;]*\+[^;]*;'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Count number of concatenations
            concat_count = match.group().count('+')
            
            if concat_count >= 3:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message=f'Multiple string concatenations ({concat_count}+) - inefficient',
                    suggestion='Use StringBuilder for multiple concatenations',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_autoboxing(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect autoboxing/unboxing issues."""
        findings = []
        
        # Boxed primitives in collections
        pattern = r'(List|Set|Map)<\s*(Integer|Long|Double|Float|Boolean|Character|Byte|Short)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            collection_type = match.group(1)
            boxed_type = match.group(2)
            
            # Check if in a loop or frequently accessed
            context_start = max(0, match.start() - 500)
            context_end = min(len(content), match.end() + 500)
            context = content[context_start:context_end]
            
            if 'for' in context or 'while' in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='performance',
                    message=f'{collection_type}<{boxed_type}> causes autoboxing overhead',
                    suggestion=f'Consider using primitive collections (e.g., TIntArrayList) for performance-critical code',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Unnecessary boxing
        pattern = r'(Integer|Long|Double|Float|Boolean|Character|Byte|Short)\.valueOf\s*\(\s*\d+\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Unnecessary boxing of primitive value',
                suggestion='Use primitive type directly when possible',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_inefficient_collections(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient collection usage."""
        findings = []
        
        # ArrayList without initial capacity
        pattern = r'new\s+ArrayList\s*\(\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if in a loop or if size is known
            context_start = max(0, match.start() - 300)
            context = content[context_start:match.start()]
            
            if 'for' in context or 'while' in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message='ArrayList created without initial capacity',
                    suggestion='Specify initial capacity if size is known: new ArrayList<>(expectedSize)',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Using contains() on List instead of Set
        pattern = r'List<[^>]+>\s+\w+[^;]*;[^}]*\w+\.contains\('
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Using contains() on List - O(n) operation',
                suggestion='Use HashSet for O(1) contains() if order is not important',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Iterating with get(i) instead of iterator
        pattern = r'for\s*\(\s*int\s+\w+\s*=\s*0[^)]*\.size\(\)[^)]*\)[^}]*\.get\s*\('
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Iterating with get(i) - inefficient for LinkedList',
                suggestion='Use enhanced for-loop or iterator for better performance',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_stream_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect Stream API performance issues."""
        findings = []
        
        # Parallel stream on small collections
        pattern = r'\.parallelStream\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='parallelStream() has overhead - only beneficial for large collections',
                suggestion='Use regular stream() for small collections (< 1000 elements)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Multiple terminal operations on same stream
        pattern = r'Stream<[^>]+>\s+(\w+)\s*=[^;]+;[^}]*\1\.[^;]+;[^}]*\1\.'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Reusing stream variable - streams can only be used once',
                suggestion='Create new stream for each terminal operation',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_regex_compilation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect regex compilation in loops."""
        findings = []
        
        # Pattern.compile in loop
        pattern = r'(for|while)\s*\([^)]+\)\s*\{[^}]*Pattern\.compile\('
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='Pattern.compile() in loop - expensive operation',
                suggestion='Compile pattern once as static final field',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # String.matches() (compiles pattern each time)
        pattern = r'\.matches\s*\(\s*"[^"]+"\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if in loop
            context_start = max(0, match.start() - 300)
            context = content[context_start:match.start()]
            
            if 'for' in context or 'while' in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='performance',
                    message='String.matches() in loop - compiles pattern each time',
                    suggestion='Use pre-compiled Pattern.matcher() instead',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_exception_control_flow(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect exceptions used for control flow."""
        findings = []
        
        # Empty catch block
        pattern = r'catch\s*\([^)]+\)\s*\{\s*\}'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Empty catch block - exceptions are expensive',
                suggestion='Avoid using exceptions for control flow, validate inputs instead',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Catching Exception in loop
        pattern = r'(for|while)\s*\([^)]+\)\s*\{[^}]*try\s*\{[^}]*\}\s*catch'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Try-catch in loop - exceptions are expensive',
                suggestion='Move try-catch outside loop if possible',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_reflection_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect reflection performance issues."""
        findings = []
        
        # Reflection in loops
        pattern = r'(for|while)\s*\([^)]+\)\s*\{[^}]*(Class\.forName|Method\.invoke|Field\.get|Constructor\.newInstance)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='Reflection in loop - very expensive operation',
                suggestion='Cache reflection objects (Method, Field, Constructor) outside loop',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_resource_leaks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential resource leaks."""
        findings = []
        
        # InputStream/OutputStream without try-with-resources
        pattern = r'(FileInputStream|FileOutputStream|BufferedReader|BufferedWriter|FileReader|FileWriter)\s+\w+\s*=\s*new'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if in try-with-resources
            context_start = max(0, match.start() - 100)
            context = content[context_start:match.start()]
            
            if 'try (' not in context[-50:]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='performance',
                    message='Resource not using try-with-resources - potential leak',
                    suggestion='Use try-with-resources to ensure proper resource cleanup',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_unnecessary_object_creation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary object creation."""
        findings = []
        
        # new String(string)
        pattern = r'new\s+String\s*\(\s*"[^"]*"\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Unnecessary String object creation',
                suggestion='Use string literal directly',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Boolean.valueOf(true/false)
        pattern = r'Boolean\.valueOf\s*\(\s*(true|false)\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Unnecessary Boolean object creation',
                suggestion='Use Boolean.TRUE or Boolean.FALSE constants',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings

