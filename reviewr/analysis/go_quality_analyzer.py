"""
Go Code Quality Analyzer

Detects code quality issues in Go code including:
- Error handling anti-patterns
- Defer misuse
- Panic/recover patterns
- Nil pointer dereferences
- Unused variables
- Shadowed variables
- Complexity issues
- Code smells
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class GoQualityAnalyzer(LocalAnalyzer):
    """Analyzes Go code for quality issues."""

    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'go'

    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Go code for quality issues.
        
        Args:
            file_path: Path to the Go file
            content: File content
            
        Returns:
            List of quality findings
        """
        findings = []
        lines = content.split('\n')
        
        # Run all quality checks
        findings.extend(self._detect_error_handling_issues(content, file_path, lines))
        findings.extend(self._detect_defer_issues(content, file_path, lines))
        findings.extend(self._detect_panic_recover_issues(content, file_path, lines))
        findings.extend(self._detect_nil_checks(content, file_path, lines))
        findings.extend(self._detect_shadowed_variables(content, file_path, lines))
        findings.extend(self._detect_complexity_issues(content, file_path, lines))
        findings.extend(self._detect_code_smells(content, file_path, lines))
        findings.extend(self._detect_context_issues(content, file_path, lines))
        
        return findings
    
    def _detect_error_handling_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect error handling anti-patterns."""
        findings = []
        
        # Ignored errors
        for match in re.finditer(r'_\s*[,:]?=\s*\w+\([^)]*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Check if it's likely an error return
            if 'err' in line_content.lower() or re.search(r'\w+\s*,\s*_\s*:?=', line_content):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='Ignored error: Error return value discarded with _',
                    suggestion='Handle errors explicitly or use // nolint comment if intentional',
                    code_snippet=line_content.strip()
                ))
        
        # Error without context
        for match in re.finditer(r'return\s+err\b', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if error is wrapped
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start()]
            
            if 'fmt.Errorf' not in context and 'errors.Wrap' not in context and 'errors.New' not in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message='Error returned without context',
                    suggestion='Wrap error with context: fmt.Errorf("operation failed: %w", err)',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        # Empty error checks
        for match in re.finditer(r'if\s+err\s*!=\s*nil\s*\{\s*\}', content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='quality',
                message='Empty error check: Error is checked but not handled',
                suggestion='Handle the error or remove the check',
                code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_defer_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect defer misuse patterns."""
        findings = []
        
        # Defer with function call that returns error
        for match in re.finditer(r'defer\s+\w+\.Close\s*\(\s*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Deferred Close() error ignored',
                suggestion='Check error: defer func() { if err := f.Close(); err != nil { ... } }()',
                code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
            ))
        
        # Multiple defers in wrong order
        defer_pattern = r'defer\s+'
        defer_matches = list(re.finditer(defer_pattern, content))
        
        if len(defer_matches) > 3:
            # Check if they're in a small function (potential LIFO confusion)
            for i in range(len(defer_matches) - 1):
                match1 = defer_matches[i]
                match2 = defer_matches[i + 1]
                
                if match2.start() - match1.start() < 100:  # Close together
                    line_num = content[:match1.start()].count('\n') + 1
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='info',
                        category='quality',
                        message='Multiple defer statements: Remember LIFO execution order',
                        suggestion='Ensure defer order matches intended cleanup sequence',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
                    break  # Only report once
        
        return findings
    
    def _detect_panic_recover_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect panic/recover anti-patterns."""
        findings = []
        
        # Panic without recover
        for match in re.finditer(r'\bpanic\s*\(', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if there's a recover in the function
            func_start = content.rfind('func ', 0, match.start())
            func_end = min(len(content), match.end() + 1000)
            func_body = content[func_start:func_end] if func_start != -1 else ''
            
            if 'recover()' not in func_body:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='panic without recover: Can crash the program',
                    suggestion='Use error returns instead of panic, or add recover() in defer',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        # Recover not in defer
        for match in re.finditer(r'\brecover\s*\(\s*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if it's in a defer
            line_start = content.rfind('\n', 0, match.start())
            line_content = content[line_start:match.start()]
            
            if 'defer' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='quality',
                    message='recover() not in defer: Will not catch panics',
                    suggestion='Use recover() only in deferred functions',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_nil_checks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect missing nil checks."""
        findings = []
        
        # Pointer dereference without nil check
        for match in re.finditer(r'(\w+)\s*:=\s*.*\n.*\1\.', content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)
            
            # Check if there's a nil check between assignment and usage
            assignment_pos = match.start()
            usage_pos = match.end()
            between = content[assignment_pos:usage_pos]
            
            if f'{var_name} != nil' not in between and f'{var_name} == nil' not in between:
                # Check if it's a pointer type
                if '*' in between or 'new(' in between:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='medium',
                        category='quality',
                        message=f'Potential nil pointer dereference: {var_name} used without nil check',
                        suggestion=f'Add nil check: if {var_name} != nil {{ ... }}',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_shadowed_variables(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect shadowed variables."""
        findings = []
        
        # err := shadowing
        for match in re.finditer(r'if\s+.*err\s*:=', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if err already exists in outer scope
            before = content[:match.start()]
            if 'err :=' in before or 'var err' in before:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message='Variable shadowing: err redeclared with :=',
                    suggestion='Use = instead of := to assign to existing variable',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_complexity_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect complexity issues."""
        findings = []
        
        # Functions with too many parameters
        for match in re.finditer(r'func\s+\w+\s*\(([^)]+)\)', content):
            line_num = content[:match.start()].count('\n') + 1
            params = match.group(1)
            param_count = len([p for p in params.split(',') if p.strip()])
            
            if param_count > 5:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Function has {param_count} parameters (> 5)',
                    suggestion='Consider using a struct to group related parameters',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else '',
                    metric_name='parameter_count',
                    metric_value=param_count
                ))
        
        # Deep nesting
        for i, line in enumerate(lines):
            indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indent
            
            if indent_level > 4:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    severity='low',
                    category='quality',
                    message=f'Deep nesting: {indent_level} levels',
                    suggestion='Extract nested logic into separate functions',
                    code_snippet=line.strip(),
                    metric_name='nesting_level',
                    metric_value=indent_level
                ))
        
        return findings
    
    def _detect_code_smells(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect code smells."""
        findings = []
        
        # Empty interfaces
        for match in re.finditer(r'interface\s*\{\s*\}', content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='quality',
                message='Empty interface: Consider using generics (Go 1.18+) or specific types',
                suggestion='Use type parameters or concrete types for better type safety',
                code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
            ))
        
        # TODO/FIXME comments
        for match in re.finditer(r'//\s*(TODO|FIXME|HACK|XXX):', content, re.IGNORECASE):
            line_num = content[:match.start()].count('\n') + 1
            comment_type = match.group(1).upper()
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='quality',
                message=f'{comment_type} comment found',
                suggestion='Address the comment or create a tracking issue',
                code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
            ))
        
        # Magic numbers
        for match in re.finditer(r'(?<![a-zA-Z0-9_])((?!0|1|2|10|100|1000)\d{3,})(?![a-zA-Z0-9_])', content):
            line_num = content[:match.start()].count('\n') + 1
            number = match.group(1)
            
            # Skip if it's in a comment or string
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            if '//' not in line_content[:line_content.find(number)] and '"' not in line_content[:line_content.find(number)]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='info',
                    category='quality',
                    message=f'Magic number: {number}',
                    suggestion='Define as a named constant for better readability',
                    code_snippet=line_content.strip()
                ))
        
        return findings
    
    def _detect_context_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect context usage issues."""
        findings = []
        
        # context.Background() in non-main functions
        for match in re.finditer(r'context\.Background\s*\(\s*\)', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if it's in main function
            func_start = content.rfind('func ', 0, match.start())
            if func_start != -1:
                func_line = content[func_start:match.start()]
                if 'func main' not in func_line:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='low',
                        category='quality',
                        message='context.Background() in non-main function',
                        suggestion='Accept context.Context as parameter or use context.TODO()',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
        
        # Functions that should accept context
        for match in re.finditer(r'func\s+(\w+)\s*\(([^)]*)\)', content):
            line_num = content[:match.start()].count('\n') + 1
            func_name = match.group(1)
            params = match.group(2)
            
            # Skip if already has context
            if 'context.Context' in params or 'ctx ' in params:
                continue
            
            # Check if function makes HTTP requests or DB calls
            func_start = match.start()
            func_end = min(len(content), func_start + 1000)
            func_body = content[func_start:func_end]
            
            needs_context = any(keyword in func_body for keyword in [
                'http.Get', 'http.Post', 'http.NewRequest',
                '.Query(', '.Exec(', '.QueryRow(',
                'time.Sleep'
            ])
            
            if needs_context and not func_name.startswith('Test'):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Function {func_name} should accept context.Context',
                    suggestion='Add ctx context.Context as first parameter for cancellation support',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings

