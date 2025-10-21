"""
Rust Quality Analyzer

Detects code quality issues in Rust including error handling patterns,
code smells, complexity, and idiomatic Rust patterns.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class RustQualityAnalyzer(LocalAnalyzer):
    """Analyzes Rust code for quality issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'rust'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Rust code for quality issues.
        
        Args:
            file_path: Path to the Rust file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_error_handling_issues(content, file_path, lines))
        findings.extend(self._detect_option_handling(content, file_path, lines))
        findings.extend(self._detect_match_patterns(content, file_path, lines))
        findings.extend(self._detect_complexity_issues(content, file_path, lines))
        findings.extend(self._detect_naming_conventions(content, file_path, lines))
        findings.extend(self._detect_documentation_issues(content, file_path, lines))
        findings.extend(self._detect_idiomatic_issues(content, file_path, lines))
        findings.extend(self._detect_code_smells(content, file_path, lines))
        
        return findings
    
    def _detect_error_handling_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect error handling anti-patterns."""
        findings = []
        
        # Ignoring errors with let _ =
        pattern = r'let\s+_\s*=\s*\w+\([^)]*\)\s*;'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Check if it's likely a Result
            if 'Result' in line_content or '?' in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='Ignoring potential error with let _ =',
                    suggestion='Handle errors explicitly or use .ok() if intentionally ignoring',
                    code_snippet=line_content
                ))
        
        # Using .ok() without handling None
        pattern = r'\.ok\(\)\s*;'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Converting Result to Option with .ok() and ignoring',
                suggestion='Consider handling the error or documenting why it can be ignored',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # match with only Ok arm
        pattern = r'match\s+[^{]+\{[^}]*Ok\([^)]*\)\s*=>[^}]*\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            match_text = match.group()
            if 'Err' not in match_text:
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='quality',
                    message='match on Result without handling Err case',
                    suggestion='Handle Err case or use if let Ok(...) = ... pattern',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_option_handling(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect Option handling issues."""
        findings = []
        
        # if let Some(...) without else
        pattern = r'if\s+let\s+Some\([^)]*\)\s*=\s*[^{]+\{[^}]+\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            match_text = match.group()
            if 'else' not in match_text:
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='info',
                    category='quality',
                    message='if let Some without else - consider if None case needs handling',
                    suggestion='Add else branch if None case is significant',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # .is_some() followed by .unwrap()
        pattern = r'if\s+\w+\.is_some\(\)[^}]*\w+\.unwrap\(\)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='quality',
                message='.is_some() check followed by .unwrap() - use if let instead',
                suggestion='Replace with: if let Some(value) = option { ... }',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_match_patterns(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect match pattern issues."""
        findings = []
        
        # match with single arm
        pattern = r'match\s+[^{]+\{[^}]*=>[^,}]*\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            match_text = match.group()
            if match_text.count('=>') == 1:
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message='match with single arm - consider if let instead',
                    suggestion='Use if let for single pattern matching',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Catch-all pattern _ => without comment
        pattern = r'_\s*=>\s*\{[^}]*\}'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for comment
            context_start = max(0, match.start() - 100)
            context = content[context_start:match.start()]
            has_comment = '//' in context or '/*' in context
            
            if not has_comment:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='info',
                    category='quality',
                    message='Catch-all pattern _ => without comment',
                    suggestion='Add comment explaining why other cases are not handled',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_complexity_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect complexity issues."""
        findings = []
        
        # Functions with too many parameters
        pattern = r'fn\s+\w+\s*\([^)]{100,}\)'
        
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
                    message=f'Function has {param_count} parameters (> 5)',
                    suggestion='Consider using a struct to group related parameters',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Deep nesting (4+ levels)
        for i, line in enumerate(lines, 1):
            indent_level = (len(line) - len(line.lstrip())) // 4
            
            if indent_level >= 4 and line.strip() and not line.strip().startswith('//'):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i,
                    line_end=i,
                    severity='medium',
                    category='quality',
                    message=f'Deep nesting detected (level {indent_level})',
                    suggestion='Extract nested logic into separate functions',
                    code_snippet=line
                ))
        
        # Long functions (> 50 lines)
        fn_pattern = r'fn\s+\w+[^{]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(fn_pattern, content, re.DOTALL):
            fn_body = match.group(1)
            line_count = fn_body.count('\n')
            
            if line_count > 50:
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Long function ({line_count} lines > 50)',
                    suggestion='Consider breaking into smaller functions',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_naming_conventions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect naming convention violations."""
        findings = []
        
        # Non-snake_case function names
        pattern = r'fn\s+([A-Z]\w+|[a-z]+[A-Z]\w*)\s*\('
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            fn_name = match.group(1)
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message=f'Function name "{fn_name}" not in snake_case',
                suggestion='Use snake_case for function names (Rust convention)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Non-CamelCase type names
        pattern = r'(?:struct|enum|trait)\s+([a-z_]\w+)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            type_name = match.group(1)
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message=f'Type name "{type_name}" not in CamelCase',
                suggestion='Use CamelCase for type names (Rust convention)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_documentation_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect documentation issues."""
        findings = []
        
        # Public functions without doc comments
        pattern = r'pub\s+fn\s+\w+'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for doc comment above
            if line_num > 1:
                prev_line = lines[line_num - 2] if line_num - 2 < len(lines) else ''
                if not prev_line.strip().startswith('///'):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='info',
                        category='quality',
                        message='Public function without documentation comment',
                        suggestion='Add /// doc comment describing function purpose',
                        code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_idiomatic_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect non-idiomatic Rust patterns."""
        findings = []
        
        # Using .len() == 0 instead of .is_empty()
        pattern = r'\.len\(\)\s*==\s*0'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Use .is_empty() instead of .len() == 0',
                suggestion='Replace with .is_empty() for better readability',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Using if x == true instead of if x
        pattern = r'if\s+\w+\s*==\s*true'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='quality',
                message='Comparing boolean to true is redundant',
                suggestion='Use if x instead of if x == true',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Using return at end of function
        pattern = r'\n\s+return\s+[^;]+;\s*\n\s*\}'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 2
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='quality',
                message='Unnecessary return at end of function',
                suggestion='Remove return keyword - Rust returns last expression',
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
            
            # Skip if in const or let binding
            if 'const' not in line_content and 'let' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='quality',
                    message=f'Magic number detected: {match.group()}',
                    suggestion='Extract to named constant for clarity',
                    code_snippet=line_content
                ))
        
        return findings

