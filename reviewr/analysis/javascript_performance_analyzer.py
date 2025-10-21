"""
JavaScript/TypeScript Performance Analyzer

Detects performance anti-patterns including:
- Inefficient DOM operations
- Memory leaks
- Unnecessary re-renders (React)
- Blocking operations
- Inefficient loops
- Large bundle sizes
- Unoptimized images/assets
- N+1 query patterns
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaScriptPerformanceAnalyzer(LocalAnalyzer):
    """Analyzer for JavaScript/TypeScript performance issues."""
    
    def __init__(self):
        """Initialize the performance analyzer."""
        self.dom_query_methods = {
            'querySelector', 'querySelectorAll', 'getElementById',
            'getElementsByClassName', 'getElementsByTagName'
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() in ['javascript', 'typescript', 'jsx', 'tsx']
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze JavaScript/TypeScript code for performance issues.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of performance findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_dom_operations_in_loops(content, file_path, lines))
        findings.extend(self._detect_memory_leaks(content, file_path, lines))
        findings.extend(self._detect_inefficient_react_patterns(content, file_path, lines))
        findings.extend(self._detect_blocking_operations(content, file_path, lines))
        findings.extend(self._detect_inefficient_array_operations(content, file_path, lines))
        findings.extend(self._detect_unnecessary_computations(content, file_path, lines))
        findings.extend(self._detect_large_dependencies(content, file_path, lines))
        findings.extend(self._detect_n_plus_one_patterns(content, file_path, lines))
        findings.extend(self._detect_string_concatenation_in_loops(content, file_path, lines))
        
        return findings
    
    def _detect_dom_operations_in_loops(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect DOM operations inside loops."""
        findings = []
        
        # Find loops
        loop_patterns = [
            r'for\s*\([^)]+\)\s*\{',
            r'while\s*\([^)]+\)\s*\{',
            r'\.forEach\s*\(',
            r'\.map\s*\(',
        ]
        
        for loop_pattern in loop_patterns:
            for loop_match in re.finditer(loop_pattern, content):
                loop_start = loop_match.start()
                loop_line = content[:loop_start].count('\n') + 1
                
                # Find the loop body
                brace_start = content.find('{', loop_start)
                if brace_start == -1:
                    continue
                
                brace_end = self._find_matching_brace(content, brace_start)
                if brace_end == -1:
                    continue
                
                loop_body = content[brace_start:brace_end]
                
                # Check for DOM operations in loop body
                dom_operations = [
                    'appendChild', 'removeChild', 'insertBefore',
                    'innerHTML', 'outerHTML', 'textContent',
                    'querySelector', 'querySelectorAll',
                    'getElementById', 'getElementsByClassName'
                ]
                
                for dom_op in dom_operations:
                    if dom_op in loop_body:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=loop_line,
                            line_end=loop_line,
                            severity='medium',
                            category='performance',
                            message=f'DOM operation "{dom_op}" inside loop causes reflow/repaint on each iteration',
                            suggestion='Batch DOM operations: build HTML string or DocumentFragment, then insert once'
                        ))
                        break  # Only report once per loop
        
        return findings
    
    def _detect_memory_leaks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential memory leaks."""
        findings = []
        
        # Event listeners without cleanup
        add_listener_pattern = r'addEventListener\s*\('
        for match in re.finditer(add_listener_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if there's a corresponding removeEventListener
            # This is a heuristic - not perfect but catches common cases
            func_start = content.rfind('function', 0, match.start())
            func_end = content.find('}', match.end())
            
            if func_start != -1 and func_end != -1:
                func_body = content[func_start:func_end]
                if 'removeEventListener' not in func_body and 'cleanup' not in func_body.lower():
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='medium',
                        category='performance',
                        message='Event listener added without cleanup: potential memory leak',
                        suggestion='Remove event listener in cleanup function or useEffect return'
                    ))
        
        # setInterval without clearInterval
        set_interval_pattern = r'setInterval\s*\('
        for match in re.finditer(set_interval_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for clearInterval in same scope
            func_start = content.rfind('function', 0, match.start())
            func_end = content.find('}', match.end())
            
            if func_start != -1 and func_end != -1:
                func_body = content[func_start:func_end]
                if 'clearInterval' not in func_body:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='high',
                        category='performance',
                        message='setInterval without clearInterval: memory leak',
                        suggestion='Store interval ID and call clearInterval in cleanup'
                    ))
        
        return findings
    
    def _detect_inefficient_react_patterns(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient React patterns."""
        findings = []
        
        # Inline function definitions in JSX
        inline_func_pattern = r'(?:onClick|onChange|onSubmit|on\w+)\s*=\s*\{(?:\([^)]*\)\s*=>|\s*function)'
        for match in re.finditer(inline_func_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Inline function in JSX prop causes unnecessary re-renders',
                suggestion='Define function outside render or use useCallback hook'
            ))
        
        # Missing dependency array in useEffect
        use_effect_pattern = r'useEffect\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\}\s*\)'
        for match in re.finditer(use_effect_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='useEffect without dependency array runs on every render',
                suggestion='Add dependency array to useEffect: useEffect(() => {...}, [deps])'
            ))
        
        # Large component without React.memo
        component_pattern = r'(?:function|const)\s+(\w+)\s*(?:=\s*)?(?:\([^)]*\))?\s*(?:=>)?\s*\{[^}]{500,}\}'
        for match in re.finditer(component_pattern, content, re.DOTALL):
            component_name = match.group(1)
            if component_name and component_name[0].isupper():  # React component
                line_num = content[:match.start()].count('\n') + 1
                if 'React.memo' not in content[match.start():match.end()]:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='low',
                        category='performance',
                        message=f'Large component "{component_name}" without React.memo may re-render unnecessarily',
                        suggestion='Wrap component with React.memo() to prevent unnecessary re-renders'
                    ))
        
        return findings
    
    def _detect_blocking_operations(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect blocking operations."""
        findings = []
        
        # Synchronous file operations
        sync_ops = ['readFileSync', 'writeFileSync', 'readdirSync', 'statSync']
        for sync_op in sync_ops:
            pattern = rf'\b{sync_op}\s*\('
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='performance',
                    message=f'Blocking operation: {sync_op} blocks event loop',
                    suggestion=f'Use async version: {sync_op.replace("Sync", "")} with await'
                ))
        
        # Large synchronous JSON parsing
        json_parse_pattern = r'JSON\.parse\s*\([^)]{100,}\)'
        for match in re.finditer(json_parse_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Large JSON.parse() operation may block event loop',
                suggestion='Consider streaming JSON parser for large payloads'
            ))
        
        return findings
    
    def _detect_inefficient_array_operations(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect inefficient array operations."""
        findings = []
        
        # Multiple array iterations
        for i, line in enumerate(lines):
            if '.map(' in line and '.filter(' in line:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    severity='low',
                    category='performance',
                    message='Multiple array iterations: .map().filter() iterates twice',
                    suggestion='Combine operations: use .reduce() or single .map() with conditional logic'
                ))
            
            if '.filter(' in line and '.map(' in line:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    severity='low',
                    category='performance',
                    message='Multiple array iterations: .filter().map() iterates twice',
                    suggestion='Combine operations: use .reduce() or single .map() with conditional logic'
                ))
        
        # Array.push in loop
        push_in_loop_pattern = r'for\s*\([^)]+\)\s*\{[^}]*\.push\s*\('
        for match in re.finditer(push_in_loop_pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='Array.push() in loop: consider using array spread or map()',
                suggestion='Use array methods: arr.map(), arr.filter(), or spread operator'
            ))
        
        return findings
    
    def _detect_unnecessary_computations(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary computations."""
        findings = []
        
        # Repeated expensive operations in loops
        for i, line in enumerate(lines):
            if any(loop_keyword in line for loop_keyword in ['for', 'while', 'forEach']):
                # Check next few lines for expensive operations
                loop_body = '\n'.join(lines[i:min(i+20, len(lines))])
                
                expensive_ops = [
                    ('new RegExp', 'Compile regex outside loop'),
                    ('JSON.parse', 'Parse JSON outside loop'),
                    ('JSON.stringify', 'Stringify outside loop'),
                    ('.split(', 'Split string outside loop if possible'),
                ]
                
                for op, suggestion in expensive_ops:
                    if loop_body.count(op) > 1:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=i + 1,
                            line_end=i + 1,
                            severity='medium',
                            category='performance',
                            message=f'Expensive operation "{op}" repeated in loop',
                            suggestion=suggestion
                        ))
                        break
        
        return findings
    
    def _detect_large_dependencies(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect large dependency imports."""
        findings = []
        
        # Importing entire lodash instead of specific functions
        lodash_pattern = r'import\s+(?:_|\*\s+as\s+_)\s+from\s+["\']lodash["\']'
        for match in re.finditer(lodash_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='Importing entire lodash library increases bundle size',
                suggestion='Import specific functions: import { map, filter } from "lodash"'
            ))
        
        # Importing entire moment.js
        moment_pattern = r'import\s+moment\s+from\s+["\']moment["\']'
        for match in re.finditer(moment_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='low',
                category='performance',
                message='moment.js is large (67KB): consider lighter alternatives',
                suggestion='Use date-fns or day.js (2KB) for better bundle size'
            ))
        
        return findings
    
    def _detect_n_plus_one_patterns(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect N+1 query patterns."""
        findings = []
        
        # Database/API calls in loops
        query_patterns = [
            r'for\s*\([^)]+\)\s*\{[^}]*(?:fetch|axios|query|findOne|findById)\s*\(',
            r'\.forEach\s*\([^)]*\{[^}]*(?:fetch|axios|query|findOne|findById)\s*\(',
            r'\.map\s*\([^)]*\{[^}]*(?:fetch|axios|query|findOne|findById)\s*\(',
        ]
        
        for pattern in query_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='performance',
                    message='Potential N+1 query: database/API call inside loop',
                    suggestion='Batch queries: fetch all data at once or use Promise.all()'
                ))
        
        return findings
    
    def _detect_string_concatenation_in_loops(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect string concatenation in loops."""
        findings = []
        
        concat_in_loop_pattern = r'for\s*\([^)]+\)\s*\{[^}]*\+=\s*["\']'
        for match in re.finditer(concat_in_loop_pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='performance',
                message='String concatenation in loop creates new string each iteration',
                suggestion='Use array.join() or template literals: arr.map().join("")'
            ))
        
        return findings
    
    def _find_matching_brace(self, content: str, start_pos: int) -> int:
        """Find the matching closing brace."""
        count = 1
        pos = start_pos + 1
        
        while pos < len(content) and count > 0:
            if content[pos] == '{':
                count += 1
            elif content[pos] == '}':
                count -= 1
            pos += 1
        
        return pos - 1 if count == 0 else -1

