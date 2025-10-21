"""
Rust Performance Analyzer

Detects performance anti-patterns in Rust code including allocation issues,
clone abuse, inefficient iterators, and async/await patterns.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class RustPerformanceAnalyzer(LocalAnalyzer):
    """Analyzes Rust code for performance issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'rust'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Rust code for performance issues.
        
        Args:
            file_path: Path to the Rust file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_excessive_cloning(content, file_path, lines))
        findings.extend(self._detect_string_allocation(content, file_path, lines))
        findings.extend(self._detect_vec_allocation(content, file_path, lines))
        findings.extend(self._detect_inefficient_iterators(content, file_path, lines))
        findings.extend(self._detect_collect_unnecessary(content, file_path, lines))
        findings.extend(self._detect_async_issues(content, file_path, lines))
        findings.extend(self._detect_mutex_contention(content, file_path, lines))
        findings.extend(self._detect_box_unnecessary(content, file_path, lines))
        findings.extend(self._detect_format_in_loops(content, file_path, lines))
        
        return findings
    
    def _detect_excessive_cloning(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect excessive use of .clone()."""
        findings = []
        
        # Clone in loops
        pattern = r'for\s+\w+\s+in\s+[^{]+\{[^}]*\.clone\(\)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='Cloning inside loop - can cause significant allocations',
                suggestion='Consider borrowing (&) or restructure to avoid cloning',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Multiple clones of same value
        pattern = r'(\w+)\.clone\(\).*\n.*\1\.clone\(\)'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num + 1,
                severity='medium',
                category='performance',
                message='Multiple clones of same value',
                suggestion='Clone once and reuse, or use Rc/Arc for shared ownership',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_string_allocation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary string allocations."""
        findings = []
        
        # .to_string() in loops
        pattern = r'for\s+\w+\s+in\s+[^{]+\{[^}]*\.to_string\(\)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='String allocation (.to_string()) inside loop',
                suggestion='Use &str references or allocate outside loop',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # String::from() when &str would work
        pattern = r'String::from\([^)]+\)\s*(?:;|\))'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Check if it's in a function signature or return
            if '->' not in line_content and 'fn ' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message='String::from() allocates - consider if &str would work',
                    suggestion='Use &str for borrowed strings, String only when ownership needed',
                    code_snippet=line_content
                ))
        
        # String concatenation with +
        pattern = r'"\s*\+\s*&?\w+\s*\+\s*"'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='String concatenation with + creates multiple allocations',
                suggestion='Use format!() macro or String::push_str() for better performance',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_vec_allocation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient Vec allocations."""
        findings = []
        
        # Vec::new() followed by push in loop without capacity
        pattern = r'let\s+mut\s+(\w+)\s*=\s*Vec::new\(\);\s*\n\s*for\s+[^{]+\{[^}]*\1\.push\('
        
        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Vec::new() without capacity before loop - causes reallocations',
                suggestion='Use Vec::with_capacity(n) if size is known',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Repeated push without capacity
        pattern = r'Vec::new\(\);\s*\n(?:\s*\w+\.push\([^)]+\);\s*\n){3,}'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Multiple pushes without pre-allocated capacity',
                suggestion='Use Vec::with_capacity() or vec![] macro',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_inefficient_iterators(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient iterator usage."""
        findings = []
        
        # .iter().map().collect() when into_iter() would work
        pattern = r'\.iter\(\)\.map\([^)]+\)\.collect\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='.iter().map().collect() - consider into_iter() if ownership not needed',
                suggestion='Use .into_iter() to consume and avoid cloning',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # .collect::<Vec<_>>().len() when .count() would work
        pattern = r'\.collect::<Vec<[^>]+>>.*\.len\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Collecting to Vec just to get length - use .count() instead',
                suggestion='Replace .collect::<Vec<_>>().len() with .count()',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # for loop when iterator methods would work
        pattern = r'for\s+\w+\s+in\s+[^{]+\{[^}]*if\s+[^{]+\{[^}]*\.push\('
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='performance',
                message='Manual filtering in loop - consider .filter().collect()',
                suggestion='Use iterator methods: .filter().map().collect() for clarity and performance',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_collect_unnecessary(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary .collect() calls."""
        findings = []
        
        # .collect() followed immediately by .iter()
        pattern = r'\.collect::<Vec<[^>]+>>\(\)\.iter\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='Unnecessary .collect() followed by .iter() - removes lazy evaluation',
                suggestion='Remove .collect() and continue chaining iterator methods',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_async_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect async/await performance issues."""
        findings = []
        
        # .await in loop without join/select
        pattern = r'for\s+\w+\s+in\s+[^{]+\{[^}]*\.await'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='performance',
                message='Sequential .await in loop - no concurrency',
                suggestion='Use join_all() or FuturesUnordered for concurrent execution',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Blocking operations in async context
        blocking_patterns = [
            (r'async\s+fn\s+\w+[^{]*\{[^}]*std::thread::sleep', 'thread::sleep in async function'),
            (r'async\s+fn\s+\w+[^{]*\{[^}]*\.lock\(\)\.unwrap\(\)', 'Mutex::lock in async (use tokio::sync::Mutex)'),
        ]
        
        for pattern, message in blocking_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='performance',
                    message=f'Blocking operation in async context: {message}',
                    suggestion='Use async-aware alternatives (tokio::time::sleep, tokio::sync::Mutex)',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_mutex_contention(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential mutex contention issues."""
        findings = []
        
        # Mutex lock held across await
        pattern = r'\.lock\(\)[^;]*\.await'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='performance',
                message='Mutex lock held across .await - can cause deadlocks',
                suggestion='Release lock before .await or use tokio::sync::Mutex',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_box_unnecessary(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary Box allocations."""
        findings = []
        
        # Box<T> for small types
        small_types = ['i32', 'u32', 'i64', 'u64', 'f32', 'f64', 'bool', 'char']
        
        for small_type in small_types:
            pattern = rf'Box<{small_type}>'
            
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message=f'Unnecessary Box<{small_type}> - adds heap allocation overhead',
                    suggestion=f'Use {small_type} directly unless trait object or recursive type',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_format_in_loops(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect format! macro in loops."""
        findings = []
        
        pattern = r'for\s+\w+\s+in\s+[^{]+\{[^}]*format!\('
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='format! macro in loop - allocates on each iteration',
                suggestion='Consider using write!() with a buffer or restructure',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings

