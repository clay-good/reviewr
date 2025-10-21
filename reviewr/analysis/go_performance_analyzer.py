"""
Go Performance Analyzer

Detects performance anti-patterns in Go code including:
- Goroutine leaks
- Inefficient concurrency patterns
- Memory allocation issues
- N+1 query patterns
- Inefficient string operations
- Unnecessary allocations
- Blocking operations
- Channel misuse
- Defer in loops
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class GoPerformanceAnalyzer(LocalAnalyzer):
    """Analyzes Go code for performance issues."""

    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'go'

    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Go code for performance issues.
        
        Args:
            file_path: Path to the Go file
            content: File content
            
        Returns:
            List of performance findings
        """
        findings = []
        lines = content.split('\n')
        
        # Run all performance checks
        findings.extend(self._detect_goroutine_leaks(content, file_path, lines))
        findings.extend(self._detect_inefficient_concurrency(content, file_path, lines))
        findings.extend(self._detect_memory_issues(content, file_path, lines))
        findings.extend(self._detect_n_plus_one_queries(content, file_path, lines))
        findings.extend(self._detect_string_concatenation(content, file_path, lines))
        findings.extend(self._detect_defer_in_loops(content, file_path, lines))
        findings.extend(self._detect_blocking_operations(content, file_path, lines))
        findings.extend(self._detect_channel_misuse(content, file_path, lines))
        findings.extend(self._detect_inefficient_json(content, file_path, lines))
        
        return findings
    
    def _detect_goroutine_leaks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential goroutine leaks."""
        findings = []
        
        # Goroutines without context or cancellation
        for match in re.finditer(r'go\s+func\s*\([^)]*\)\s*\{', content):
            line_num = content[:match.start()].count('\n') + 1
            goroutine_start = match.start()
            # Find the end of the goroutine (simplified - look for closing brace)
            brace_count = 0
            goroutine_end = goroutine_start
            for i in range(goroutine_start, min(len(content), goroutine_start + 1000)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        goroutine_end = i
                        break
            
            goroutine_code = content[goroutine_start:goroutine_end]
            
            # Check for context, done channel, or timeout
            has_cancellation = any(keyword in goroutine_code for keyword in [
                'context.Context', 'ctx.Done()', '<-done', 'time.After', 'select'
            ])
            
            if not has_cancellation:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='performance',
                    message='Potential goroutine leak: No cancellation mechanism detected',
                    suggestion='Use context.Context or a done channel to allow goroutine cancellation',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_inefficient_concurrency(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient concurrency patterns."""
        findings = []
        
        # Goroutines in loops without rate limiting
        loop_patterns = [r'for\s+.*\{', r'for\s+range\s+']
        
        for loop_pattern in loop_patterns:
            for loop_match in re.finditer(loop_pattern, content):
                loop_line = content[:loop_match.start()].count('\n') + 1
                loop_start = loop_match.start()
                
                # Find goroutine within 200 chars of loop start
                goroutine_search = content[loop_start:min(len(content), loop_start + 200)]
                if 'go func' in goroutine_search or 'go ' in goroutine_search:
                    # Check for WaitGroup or rate limiting
                    context = content[max(0, loop_start - 100):min(len(content), loop_start + 300)]
                    has_control = any(keyword in context for keyword in [
                        'sync.WaitGroup', 'semaphore', 'rate.Limiter', 'time.Sleep'
                    ])
                    
                    if not has_control:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=loop_line,
                            line_end=loop_line,
                            severity='high',
                            category='performance',
                            message='Unbounded goroutine creation in loop: Can exhaust system resources',
                            suggestion='Use sync.WaitGroup, worker pools, or rate limiting: golang.org/x/time/rate',
                            code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                        ))
        
        return findings
    
    def _detect_memory_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect memory allocation issues."""
        findings = []
        
        # Slice/map growth in loops
        for match in re.finditer(r'for\s+.*\{', content):
            loop_line = content[:match.start()].count('\n') + 1
            loop_start = match.start()
            loop_end = min(len(content), loop_start + 500)
            loop_body = content[loop_start:loop_end]
            
            # Check for append without pre-allocation
            if 'append(' in loop_body:
                # Look for make() with capacity before the loop
                pre_loop = content[max(0, loop_start - 200):loop_start]
                if 'make(' not in pre_loop or ', ' not in pre_loop:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=loop_line,
                        line_end=loop_line,
                        severity='medium',
                        category='performance',
                        message='Inefficient slice growth: append() in loop without pre-allocation',
                        suggestion='Pre-allocate slice with known capacity: make([]Type, 0, expectedSize)',
                        code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                    ))
        
        # Large structs passed by value
        for match in re.finditer(r'func\s+\w+\s*\([^)]*\b(\w+)\s+(\w+)\s*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            param_type = match.group(2)
            
            # Check if it's a struct (capitalized) and not a pointer
            if param_type[0].isupper() and not match.group(0).startswith('*'):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message=f'Potential inefficiency: Struct "{param_type}" passed by value',
                    suggestion=f'Consider passing by pointer: *{param_type}',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_n_plus_one_queries(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect N+1 query patterns."""
        findings = []
        
        # Database queries in loops
        db_query_patterns = [
            r'\.Query\s*\(',
            r'\.QueryRow\s*\(',
            r'\.Exec\s*\(',
            r'\.Find\s*\(',  # GORM
            r'\.First\s*\(',  # GORM
        ]
        
        for loop_match in re.finditer(r'for\s+.*\{', content):
            loop_line = content[:loop_match.start()].count('\n') + 1
            loop_start = loop_match.start()
            loop_end = min(len(content), loop_start + 500)
            loop_body = content[loop_start:loop_end]
            
            for pattern in db_query_patterns:
                if re.search(pattern, loop_body):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=loop_line,
                        line_end=loop_line,
                        severity='high',
                        category='performance',
                        message='N+1 query pattern: Database query inside loop',
                        suggestion='Batch queries or use JOIN to fetch related data in a single query',
                        code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                    ))
                    break  # Only report once per loop
        
        return findings
    
    def _detect_string_concatenation(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient string operations."""
        findings = []
        
        # String concatenation in loops
        for loop_match in re.finditer(r'for\s+.*\{', content):
            loop_line = content[:loop_match.start()].count('\n') + 1
            loop_start = loop_match.start()
            loop_end = min(len(content), loop_start + 500)
            loop_body = content[loop_start:loop_end]
            
            # Check for += with strings
            if re.search(r'\w+\s*\+=\s*["\']', loop_body) or re.search(r'\w+\s*=\s*\w+\s*\+\s*["\']', loop_body):
                # Check if strings.Builder is used
                if 'strings.Builder' not in loop_body:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=loop_line,
                        line_end=loop_line,
                        severity='medium',
                        category='performance',
                        message='Inefficient string concatenation in loop',
                        suggestion='Use strings.Builder for efficient string building',
                        code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_defer_in_loops(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect defer statements in loops."""
        findings = []
        
        for loop_match in re.finditer(r'for\s+.*\{', content):
            loop_line = content[:loop_match.start()].count('\n') + 1
            loop_start = loop_match.start()
            loop_end = min(len(content), loop_start + 500)
            loop_body = content[loop_start:loop_end]
            
            if 'defer ' in loop_body:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=loop_line,
                    line_end=loop_line,
                    severity='medium',
                    category='performance',
                    message='defer in loop: Deferred functions accumulate until function returns',
                    suggestion='Move defer outside loop or use explicit cleanup in loop body',
                    code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_blocking_operations(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect blocking operations that could cause performance issues."""
        findings = []
        
        # Blocking channel operations without select/timeout
        for match in re.finditer(r'<-\s*\w+(?!\s*:)', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if it's in a select statement
            context_start = max(0, match.start() - 100)
            context = content[context_start:match.start()]
            
            if 'select' not in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='performance',
                    message='Blocking channel receive without timeout',
                    suggestion='Use select with time.After() for timeout or context cancellation',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_channel_misuse(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect channel misuse patterns."""
        findings = []
        
        # Unbuffered channels in synchronous code
        for match in re.finditer(r'make\s*\(\s*chan\s+\w+\s*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if goroutine is used nearby
            context_start = max(0, match.start() - 200)
            context_end = min(len(content), match.end() + 200)
            context = content[context_start:context_end]
            
            if 'go ' not in context and 'go func' not in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='performance',
                    message='Unbuffered channel without goroutine: May cause deadlock',
                    suggestion='Use buffered channel: make(chan Type, size) or ensure goroutine usage',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_inefficient_json(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient JSON operations."""
        findings = []
        
        # json.Marshal in loops
        for loop_match in re.finditer(r'for\s+.*\{', content):
            loop_line = content[:loop_match.start()].count('\n') + 1
            loop_start = loop_match.start()
            loop_end = min(len(content), loop_start + 500)
            loop_body = content[loop_start:loop_end]
            
            if 'json.Marshal' in loop_body or 'json.Unmarshal' in loop_body:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=loop_line,
                    line_end=loop_line,
                    severity='medium',
                    category='performance',
                    message='JSON marshaling in loop: Consider batching or streaming',
                    suggestion='Use json.Encoder/Decoder for streaming or batch operations outside loop',
                    code_snippet=lines[loop_line - 1].strip() if loop_line <= len(lines) else ''
                ))
        
        return findings

