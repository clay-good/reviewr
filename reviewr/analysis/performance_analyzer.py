"""
Performance Pattern Analyzer for Python code.

Detects performance anti-patterns and suggests optimizations.
"""

import ast
from typing import List, Set, Dict, Optional
from dataclasses import dataclass

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class LoopInfo:
    """Information about a loop."""
    node: ast.AST
    line: int
    nesting_level: int
    has_db_call: bool = False
    has_network_call: bool = False
    has_string_concat: bool = False


class PerformanceAnalyzer(LocalAnalyzer):
    """
    Analyzer for Python performance patterns.
    
    Detects:
    - Inefficient loops (nested loops, repeated computations)
    - String concatenation in loops
    - Unnecessary object creation
    - Missing caching opportunities
    - N+1 query patterns
    - Inefficient data structure usage
    - Repeated function calls with same arguments
    """
    
    def __init__(self):
        """Initialize the performance analyzer."""
        # Database operation patterns
        self.db_operations = {
            'execute', 'query', 'filter', 'get', 'all', 'first',
            'save', 'update', 'delete', 'insert', 'select',
            'find', 'find_one', 'find_many', 'fetch', 'fetchone', 'fetchall'
        }
        
        # Network operation patterns
        self.network_operations = {
            'get', 'post', 'put', 'delete', 'patch', 'request',
            'urlopen', 'urlretrieve', 'fetch', 'download'
        }
        
        # Expensive operations
        self.expensive_operations = {
            'compile', 'search', 'match', 'findall',  # regex
            'loads', 'dumps',  # json/pickle
            'parse', 'fromstring',  # xml/html
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze Python code for performance issues."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        
        findings = []
        
        # Analyze loops
        findings.extend(self._analyze_loops(tree, file_path))
        
        # Analyze string operations
        findings.extend(self._analyze_string_operations(tree, file_path))
        
        # Analyze repeated computations
        findings.extend(self._analyze_repeated_computations(tree, file_path))
        
        # Analyze data structure usage
        findings.extend(self._analyze_data_structures(tree, file_path))
        
        # Analyze comprehensions vs loops
        findings.extend(self._analyze_comprehension_opportunities(tree, file_path))
        
        return findings
    
    def _analyze_loops(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze loops for performance issues."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check for database calls in loops (N+1 pattern)
                db_calls = self._find_db_calls_in_loop(node)
                if db_calls:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='performance',
                        message=f"Potential N+1 query pattern: database call inside loop",
                        suggestion="Consider using bulk operations or prefetching: Model.objects.filter(id__in=ids) or use select_related()/prefetch_related()"
                    ))
                
                # Check for network calls in loops
                network_calls = self._find_network_calls_in_loop(node)
                if network_calls:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='performance',
                        message="Network call inside loop can cause performance issues",
                        suggestion="Consider batching requests or using async/concurrent execution"
                    ))
                
                # Check for string concatenation in loops
                if self._has_string_concatenation(node):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='performance',
                        message="String concatenation in loop is inefficient",
                        suggestion="Use list.append() and ''.join(list) or io.StringIO for better performance"
                    ))
                
                # Check for repeated expensive operations
                expensive_ops = self._find_expensive_operations(node)
                if expensive_ops:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='performance',
                        message=f"Expensive operation in loop: {expensive_ops[0]}",
                        suggestion="Consider moving expensive operations outside the loop or caching results"
                    ))
                
                # Check for nested loops
                nesting_level = self._get_loop_nesting_level(node)
                if nesting_level >= 3:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='performance',
                        message=f"Deeply nested loops (level {nesting_level}) can cause O(n^{nesting_level}) complexity",
                        suggestion="Consider using more efficient algorithms or data structures"
                    ))
        
        return findings
    
    def _analyze_string_operations(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze string operations for performance issues."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for repeated string concatenation
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                # Check if it's string concatenation
                if self._is_string_operation(node):
                    # Count consecutive concatenations
                    concat_count = self._count_string_concatenations(node)
                    if concat_count >= 3:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.LOW.value,
                            category='performance',
                            message=f"Multiple string concatenations ({concat_count}) can be inefficient",
                            suggestion="Use f-strings or ''.join() for better performance"
                        ))
        
        return findings
    
    def _analyze_repeated_computations(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze for repeated computations that could be cached."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Look for repeated function calls with same arguments
                call_counts = {}
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_sig = self._get_call_signature(child)
                        if call_sig:
                            call_counts[call_sig] = call_counts.get(call_sig, 0) + 1
                
                # Report repeated calls
                for call_sig, count in call_counts.items():
                    if count >= 3:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.LOW.value,
                            category='performance',
                            message=f"Function '{call_sig}' called {count} times with same arguments",
                            suggestion="Consider caching the result or storing in a variable"
                        ))
        
        return findings
    
    def _analyze_data_structures(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze data structure usage for performance issues."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for 'in' operator on lists (should use sets)
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        # Check if comparing against a list
                        for comparator in node.comparators:
                            if isinstance(comparator, ast.List):
                                if len(comparator.elts) > 5:
                                    findings.append(LocalFinding(
                                        file_path=file_path,
                                        line_start=node.lineno,
                                        line_end=node.lineno,
                                        severity=FindingSeverity.MEDIUM.value,
                                        category='performance',
                                        message="Using 'in' operator on list is O(n), consider using set for O(1) lookup",
                                        suggestion="Convert list to set: if item in {1, 2, 3, ...}"
                                    ))
            
            # Check for list.append() in comprehension-like patterns
            if isinstance(node, ast.For):
                has_append = False
                appended_var = None
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr == 'append':
                                has_append = True
                                if isinstance(child.func.value, ast.Name):
                                    appended_var = child.func.value.id
                
                if has_append and appended_var:
                    # Check if this could be a list comprehension
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.LOW.value,
                        category='performance',
                        message="Loop with append() could potentially be a list comprehension",
                        suggestion="Consider using list comprehension for better performance: result = [item for item in iterable]"
                    ))
        
        return findings
    
    def _analyze_comprehension_opportunities(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze opportunities to use comprehensions instead of loops."""
        findings = []
        
        # This is handled in _analyze_data_structures
        # Could be expanded with more sophisticated pattern matching
        
        return findings
    
    def _find_db_calls_in_loop(self, loop_node: ast.AST) -> List[ast.Call]:
        """Find database calls inside a loop."""
        db_calls = []
        
        for node in ast.walk(loop_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if any(op in func_name.lower() for op in self.db_operations):
                    db_calls.append(node)
        
        return db_calls
    
    def _find_network_calls_in_loop(self, loop_node: ast.AST) -> List[ast.Call]:
        """Find network calls inside a loop."""
        network_calls = []
        
        for node in ast.walk(loop_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if any(op in func_name.lower() for op in self.network_operations):
                    # Check if it's likely a network call (requests.get, urllib.request, etc.)
                    if 'request' in func_name.lower() or 'http' in func_name.lower() or 'url' in func_name.lower():
                        network_calls.append(node)
        
        return network_calls
    
    def _find_expensive_operations(self, loop_node: ast.AST) -> List[str]:
        """Find expensive operations inside a loop."""
        expensive_ops = []
        
        for node in ast.walk(loop_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if any(op in func_name for op in self.expensive_operations):
                    expensive_ops.append(func_name)
        
        return expensive_ops
    
    def _has_string_concatenation(self, loop_node: ast.AST) -> bool:
        """Check if loop contains string concatenation."""
        for node in ast.walk(loop_node):
            if isinstance(node, ast.AugAssign):
                if isinstance(node.op, ast.Add):
                    # Check if it's likely string concatenation
                    return True
        return False
    
    def _get_loop_nesting_level(self, loop_node: ast.AST, current_level: int = 1) -> int:
        """Get the nesting level of loops."""
        max_level = current_level
        
        for node in ast.walk(loop_node):
            if isinstance(node, (ast.For, ast.While)) and node != loop_node:
                level = self._get_loop_nesting_level(node, current_level + 1)
                max_level = max(max_level, level)
        
        return max_level
    
    def _is_string_operation(self, node: ast.BinOp) -> bool:
        """Check if binary operation is likely a string operation."""
        # Simplified check - in real implementation, would need type inference
        return True
    
    def _count_string_concatenations(self, node: ast.BinOp) -> int:
        """Count consecutive string concatenations."""
        count = 1
        
        if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Add):
            count += self._count_string_concatenations(node.left)
        
        if isinstance(node.right, ast.BinOp) and isinstance(node.right.op, ast.Add):
            count += self._count_string_concatenations(node.right)
        
        return count
    
    def _get_call_signature(self, call_node: ast.Call) -> Optional[str]:
        """Get a signature for a function call."""
        func_name = self._get_function_name(call_node.func)
        
        # Only track calls with constant arguments
        args = []
        for arg in call_node.args:
            if isinstance(arg, ast.Constant):
                args.append(str(arg.value))
            else:
                return None  # Variable arguments, can't track
        
        if args:
            return f"{func_name}({', '.join(args)})"
        return None
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_function_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""

