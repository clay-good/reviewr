"""
JavaScript/TypeScript Type Safety Analyzer

Detects type safety issues including:
- Missing TypeScript types
- Use of 'any' type
- Implicit any
- Type assertions
- Non-null assertions
- Unsafe type coercion
- Missing null checks
- Incorrect type guards
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaScriptTypeAnalyzer(LocalAnalyzer):
    """Analyzer for JavaScript/TypeScript type safety."""
    
    def __init__(self):
        """Initialize the type analyzer."""
        pass
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() in ['typescript', 'tsx']
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze TypeScript code for type safety issues.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of type safety findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_any_usage(content, file_path, lines))
        findings.extend(self._detect_type_assertions(content, file_path, lines))
        findings.extend(self._detect_non_null_assertions(content, file_path, lines))
        findings.extend(self._detect_missing_return_types(content, file_path, lines))
        findings.extend(self._detect_missing_parameter_types(content, file_path, lines))
        findings.extend(self._detect_unsafe_type_coercion(content, file_path, lines))
        findings.extend(self._detect_missing_null_checks(content, file_path, lines))
        findings.extend(self._detect_incorrect_type_guards(content, file_path, lines))
        
        return findings
    
    def _detect_any_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect usage of 'any' type."""
        findings = []
        
        # Explicit 'any' type
        any_pattern = r':\s*any\b'
        for match in re.finditer(any_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='type_safety',
                message='Use of "any" type defeats TypeScript type checking',
                suggestion='Use specific type or "unknown" if type is truly unknown'
            ))
        
        # Array of any
        any_array_pattern = r':\s*any\[\]'
        for match in re.finditer(any_array_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='type_safety',
                message='Array of "any" type: no type safety for array elements',
                suggestion='Use specific array type: T[] or Array<T>'
            ))
        
        return findings
    
    def _detect_type_assertions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect type assertions (casts)."""
        findings = []
        
        # as Type assertions
        as_pattern = r'\bas\s+\w+'
        for match in re.finditer(as_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Skip 'as const' which is safe
            if 'as const' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='type_safety',
                    message='Type assertion bypasses type checking',
                    suggestion='Prefer type guards or proper typing over assertions'
                ))
        
        # <Type> assertions (old style)
        angle_bracket_pattern = r'<\w+>'
        for match in re.finditer(angle_bracket_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Skip JSX/TSX tags
            if not any(jsx_indicator in line_content for jsx_indicator in ['</', 'return <', '= <']):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='type_safety',
                    message='Old-style type assertion: use "as Type" instead',
                    suggestion='Replace <Type>value with value as Type'
                ))
        
        return findings
    
    def _detect_non_null_assertions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect non-null assertions (!)."""
        findings = []
        
        # Non-null assertion operator
        non_null_pattern = r'\w+!'
        for match in re.finditer(non_null_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            
            # Skip if it's part of !== or !=
            if '!=' not in line_content[max(0, match.start()-1):match.end()+1]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='type_safety',
                    message='Non-null assertion (!) can cause runtime errors if value is null/undefined',
                    suggestion='Add explicit null check or use optional chaining (?.) instead'
                ))
        
        return findings
    
    def _detect_missing_return_types(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect functions without return type annotations."""
        findings = []
        
        # Function declarations without return type
        func_patterns = [
            r'function\s+\w+\s*\([^)]*\)\s*\{',  # function foo() {
            r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{',  # const foo = () => {
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # Check if return type is specified
                if ')' in line_content and ':' not in line_content[line_content.rindex(')'):]:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='low',
                        category='type_safety',
                        message='Function missing return type annotation',
                        suggestion='Add return type: function foo(): ReturnType { ... }'
                    ))
        
        return findings
    
    def _detect_missing_parameter_types(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect function parameters without type annotations."""
        findings = []
        
        # Parameters without types
        param_pattern = r'function\s+\w+\s*\(([^)]+)\)'
        for match in re.finditer(param_pattern, content):
            params = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if parameters have type annotations
            if params.strip() and ':' not in params:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='type_safety',
                    message='Function parameters missing type annotations',
                    suggestion='Add type annotations: function foo(param: Type) { ... }'
                ))
        
        return findings
    
    def _detect_unsafe_type_coercion(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unsafe type coercion."""
        findings = []
        
        # Implicit string to number coercion
        for i, line in enumerate(lines):
            # + operator with mixed types
            if re.search(r'\+\s*["\']', line) or re.search(r'["\'].*?\+', line):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    severity='low',
                    category='type_safety',
                    message='Potential unsafe type coercion with + operator',
                    suggestion='Use explicit conversion: Number(str) or String(num)'
                ))
        
        # Double negation for boolean coercion
        double_neg_pattern = r'!!\w+'
        for match in re.finditer(double_neg_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='type_safety',
                message='Double negation (!!) for boolean coercion is unclear',
                suggestion='Use explicit Boolean(value) for clarity'
            ))
        
        return findings
    
    def _detect_missing_null_checks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential null/undefined access without checks."""
        findings = []
        
        # Property access without optional chaining
        for i, line in enumerate(lines):
            # Look for property access that might be null
            if re.search(r'\w+\.\w+\.\w+', line) and '?.' not in line:
                # Check if there's a null check nearby
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                if 'if' not in context and '&&' not in context:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1,
                        severity='low',
                        category='type_safety',
                        message='Nested property access without null check',
                        suggestion='Use optional chaining: obj?.prop?.nested'
                    ))
        
        return findings
    
    def _detect_incorrect_type_guards(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect incorrect or weak type guards."""
        findings = []
        
        # typeof checks with wrong values
        typeof_pattern = r'typeof\s+\w+\s*===?\s*["\'](\w+)["\']'
        valid_typeof_values = {'undefined', 'boolean', 'number', 'string', 'symbol', 'function', 'object', 'bigint'}
        
        for match in re.finditer(typeof_pattern, content):
            typeof_value = match.group(1)
            if typeof_value not in valid_typeof_values:
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='type_safety',
                    message=f'Invalid typeof check: "{typeof_value}" is not a valid typeof result',
                    suggestion=f'Valid typeof values: {", ".join(sorted(valid_typeof_values))}'
                ))
        
        # Array.isArray for array checks
        instanceof_array_pattern = r'instanceof\s+Array'
        for match in re.finditer(instanceof_array_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='type_safety',
                message='Use Array.isArray() instead of instanceof Array',
                suggestion='Array.isArray() is more reliable for array type checking'
            ))
        
        return findings

