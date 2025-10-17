import re
from typing import List, Set, Dict, Optional
from collections import defaultdict

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


class JavaScriptAnalyzer(LocalAnalyzer):
    """Analyzer for JavaScript and TypeScript code using regex patterns."""
    
    def __init__(self):
        """Initialize the JavaScript/TypeScript analyzer."""
        self.complexity_threshold = 10
        self.max_function_lines = 50
        self.max_function_params = 5
        self.max_nesting_depth = 4
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports JavaScript or TypeScript."""
        return language.lower() in ['javascript', 'typescript', 'jsx', 'tsx']
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze JavaScript/TypeScript code and return findings.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of local findings
        """
        findings = []
        lines = content.split('\n')
        
        # Run various analyses
        findings.extend(self._analyze_complexity(content, file_path, lines))
        findings.extend(self._analyze_function_length(content, file_path, lines))
        findings.extend(self._analyze_code_smells(content, file_path, lines))
        findings.extend(self._analyze_console_statements(content, file_path, lines))
        findings.extend(self._analyze_var_usage(content, file_path, lines))
        findings.extend(self._analyze_equality_operators(content, file_path, lines))
        findings.extend(self._analyze_unused_variables(content, file_path, lines))
        findings.extend(self._analyze_callback_hell(content, file_path, lines))
        findings.extend(self._analyze_magic_numbers(content, file_path, lines))
        
        return findings
    
    def _analyze_complexity(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Analyze cyclomatic complexity of functions."""
        findings = []
        
        # Find function definitions
        function_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2)
            start_pos = match.start()
            line_num = content[:start_pos].count('\n') + 1
            
            # Find function body
            func_start = content.find('{', start_pos)
            if func_start == -1:
                continue
            
            # Find matching closing brace
            func_end = self._find_matching_brace(content, func_start)
            if func_end == -1:
                continue
            
            func_body = content[func_start:func_end]
            complexity = self._calculate_complexity(func_body)
            
            if complexity > self.complexity_threshold:
                severity = FindingSeverity.LOW.value
                if complexity > 20:
                    severity = FindingSeverity.HIGH.value
                elif complexity > 15:
                    severity = FindingSeverity.MEDIUM.value
                
                end_line = content[:func_end].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=end_line,
                    severity=severity,
                    category='complexity',
                    message=f"Function '{func_name}' has high cyclomatic complexity ({complexity})",
                    suggestion=f"Consider breaking this function into smaller functions. Target complexity: <{self.complexity_threshold}",
                    metric_value=float(complexity),
                    metric_name='cyclomatic_complexity'
                ))
        
        return findings
    
    def _calculate_complexity(self, func_body: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        
        # Decision points
        decision_keywords = [
            r'\bif\b', r'\belse\s+if\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\b\?\s*[^:]+:', r'\|\|', r'&&'
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, func_body))
        
        return complexity
    
    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find the matching closing brace."""
        count = 1
        i = start + 1
        
        while i < len(content) and count > 0:
            if content[i] == '{':
                count += 1
            elif content[i] == '}':
                count -= 1
            i += 1
        
        return i - 1 if count == 0 else -1
    
    def _analyze_function_length(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Analyze function length."""
        findings = []
        
        function_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2)
            start_pos = match.start()
            line_num = content[:start_pos].count('\n') + 1
            
            func_start = content.find('{', start_pos)
            if func_start == -1:
                continue
            
            func_end = self._find_matching_brace(content, func_start)
            if func_end == -1:
                continue
            
            func_lines = content[func_start:func_end].count('\n')
            
            if func_lines > self.max_function_lines:
                severity = FindingSeverity.LOW.value
                if func_lines > 100:
                    severity = FindingSeverity.MEDIUM.value
                
                end_line = content[:func_end].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=end_line,
                    severity=severity,
                    category='complexity',
                    message=f"Function '{func_name}' is too long ({func_lines} lines)",
                    suggestion=f"Consider breaking this function into smaller functions. Target: <{self.max_function_lines} lines",
                    metric_value=float(func_lines),
                    metric_name='function_length'
                ))
        
        return findings
    
    def _analyze_code_smells(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Analyze common code smells."""
        findings = []

        # Empty catch blocks - more flexible pattern
        empty_catch_pattern = r'catch\s*\([^)]*\)\s*\{\s*\}'
        for match in re.finditer(empty_catch_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.MEDIUM.value,
                category='smell',
                message="Empty catch block swallows exceptions",
                suggestion="Handle the exception appropriately or at least log it"
            ))

        # Nested ternary operators - improved pattern
        nested_ternary_pattern = r'\?[^:?\n]+\?[^:\n]+:[^:\n]+:'
        for match in re.finditer(nested_ternary_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.LOW.value,
                category='smell',
                message="Nested ternary operators reduce readability",
                suggestion="Use if-else statements for better clarity"
            ))

        return findings
    
    def _analyze_console_statements(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect console.log and similar debugging statements."""
        findings = []
        
        console_pattern = r'\bconsole\.(log|debug|info|warn|error)\s*\('
        for match in re.finditer(console_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.INFO.value,
                category='smell',
                message=f"Console statement found: console.{match.group(1)}()",
                suggestion="Remove console statements before production or use a proper logging library"
            ))
        
        return findings
    
    def _analyze_var_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect usage of 'var' instead of 'let' or 'const'."""
        findings = []
        
        var_pattern = r'\bvar\s+\w+'
        for match in re.finditer(var_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.LOW.value,
                category='standards',
                message="Use 'let' or 'const' instead of 'var'",
                suggestion="Replace 'var' with 'const' (if not reassigned) or 'let' (if reassigned)"
            ))
        
        return findings
    
    def _analyze_equality_operators(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect usage of == instead of ===."""
        findings = []
        
        # Match == but not === or ==
        equality_pattern = r'(?<![=!])={2}(?!=)'
        for match in re.finditer(equality_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Skip if in comments
            if '//' in line_content and line_content.index('//') < line_content.find('=='):
                continue
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.LOW.value,
                category='standards',
                message="Use '===' instead of '==' for strict equality",
                suggestion="Replace '==' with '===' to avoid type coercion issues"
            ))
        
        return findings
    
    def _analyze_unused_variables(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potentially unused variables (basic heuristic)."""
        findings = []
        
        # Find variable declarations
        var_declarations = re.finditer(r'(?:const|let|var)\s+(\w+)\s*=', content)
        
        for match in var_declarations:
            var_name = match.group(1)
            declaration_pos = match.start()
            
            # Check if variable is used after declaration
            after_declaration = content[declaration_pos + len(match.group(0)):]
            
            # Simple heuristic: if variable name appears less than 2 times after declaration
            usage_count = len(re.findall(r'\b' + re.escape(var_name) + r'\b', after_declaration))
            
            if usage_count == 0:
                line_num = content[:declaration_pos].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity=FindingSeverity.INFO.value,
                    category='dead_code',
                    message=f"Variable '{var_name}' appears to be unused",
                    suggestion="Remove unused variables to improve code clarity"
                ))
        
        return findings
    
    def _analyze_callback_hell(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect deeply nested callbacks."""
        findings = []
        
        for i, line in enumerate(lines):
            # Count nesting level by counting leading spaces/tabs and looking for callback patterns
            indent_level = len(line) - len(line.lstrip())
            
            if re.search(r'function\s*\(|=>\s*\{', line) and indent_level > 16:  # 4+ levels of nesting
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    severity=FindingSeverity.MEDIUM.value,
                    category='smell',
                    message="Deeply nested callback detected (callback hell)",
                    suggestion="Consider using async/await or Promises to flatten the callback structure"
                ))
        
        return findings
    
    def _analyze_magic_numbers(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect magic numbers in code."""
        findings = []
        
        # Find numeric literals that aren't 0, 1, -1, or in obvious contexts
        magic_number_pattern = r'(?<![a-zA-Z0-9_])(?<![\[\.])-?(?!0\b|1\b|-1\b)\d{2,}(?:\.\d+)?(?![a-zA-Z0-9_])'
        
        for match in re.finditer(magic_number_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Skip if in comments or strings
            if '//' in line_content or '/*' in line_content:
                continue
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.INFO.value,
                category='smell',
                message=f"Magic number detected: {match.group(0)}",
                suggestion="Consider extracting this number into a named constant"
            ))
        
        return findings

