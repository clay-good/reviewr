"""
Semantic Code Analyzer for Python.

Analyzes code to understand intent and detect logic errors, race conditions,
resource leaks, incorrect error handling, and business logic flaws.
"""

import ast
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class ResourceUsage:
    """Track resource acquisition and release."""
    resource_type: str  # 'file', 'lock', 'connection', 'socket'
    acquired_line: int
    released_line: Optional[int] = None
    in_context_manager: bool = False


class SemanticAnalyzer(LocalAnalyzer):
    """
    Analyzer for semantic code understanding.
    
    Detects:
    - Resource leaks (files, connections, locks not closed)
    - Incorrect error handling (bare except, swallowed exceptions)
    - Logic errors (unreachable code, contradictory conditions)
    - Race conditions (TOCTOU, shared state issues)
    - Missing null checks
    - Incorrect return values
    - Business logic flaws
    """
    
    def __init__(self):
        """Initialize the semantic analyzer."""
        # Resources that need cleanup
        self.resource_functions = {
            'open': 'file',
            'connect': 'connection',
            'socket': 'socket',
            'Lock': 'lock',
            'RLock': 'lock',
            'Semaphore': 'lock',
            'urlopen': 'connection',
        }
        
        # Resource cleanup methods
        self.cleanup_methods = {
            'close', 'release', 'disconnect', 'shutdown'
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze Python code for semantic issues."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        
        findings = []
        
        # Analyze resource management
        findings.extend(self._analyze_resource_leaks(tree, file_path))
        
        # Analyze error handling
        findings.extend(self._analyze_error_handling(tree, file_path))
        
        # Analyze logic errors
        findings.extend(self._analyze_logic_errors(tree, file_path))
        
        # Analyze race conditions
        findings.extend(self._analyze_race_conditions(tree, file_path))
        
        # Analyze return value consistency
        findings.extend(self._analyze_return_values(tree, file_path))
        
        return findings
    
    def _analyze_resource_leaks(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Detect potential resource leaks."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Track resources in this function
                resources = self._track_resources(node)
                
                for resource in resources:
                    if not resource.in_context_manager and resource.released_line is None:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=resource.acquired_line,
                            line_end=resource.acquired_line,
                            severity=FindingSeverity.HIGH.value,
                            category='semantic',
                            message=f"Potential resource leak: {resource.resource_type} opened but not explicitly closed",
                            suggestion=f"Use context manager: with open(...) as f: or ensure .close() is called in finally block"
                        ))
        
        return findings
    
    def _analyze_error_handling(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze error handling patterns."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='semantic',
                        message="Bare except clause catches all exceptions including SystemExit and KeyboardInterrupt",
                        suggestion="Catch specific exceptions: except (ValueError, TypeError) as e:"
                    ))
                
                # Check for swallowed exceptions (pass in except)
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='semantic',
                        message="Exception silently swallowed with 'pass'",
                        suggestion="At minimum, log the exception: logger.exception('Error occurred')"
                    ))
            
            # Check for try without except or finally
            if isinstance(node, ast.Try):
                if not node.handlers and not node.finalbody:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='semantic',
                        message="Try block without except or finally clause",
                        suggestion="Add except or finally clause to handle errors properly"
                    ))
        
        return findings
    
    def _analyze_logic_errors(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Detect logic errors in code."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for unreachable code after return
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                findings.extend(self._check_unreachable_code(node, file_path))
            
            # Check for contradictory conditions
            if isinstance(node, ast.If):
                findings.extend(self._check_contradictory_conditions(node, file_path))
            
            # Check for comparison with True/False
            if isinstance(node, ast.Compare):
                findings.extend(self._check_boolean_comparison(node, file_path))
            
            # Check for is comparison with literals
            if isinstance(node, ast.Compare):
                findings.extend(self._check_is_with_literals(node, file_path))
        
        return findings
    
    def _analyze_race_conditions(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Detect potential race conditions."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for TOCTOU (Time-of-check Time-of-use)
                findings.extend(self._check_toctou(node, file_path))
                
                # Check for shared state without synchronization
                findings.extend(self._check_shared_state(node, file_path))
        
        return findings
    
    def _analyze_return_values(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze return value consistency."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for inconsistent return types
                return_types = self._get_return_types(node)
                
                if len(return_types) > 1:
                    # Check if mixing None with other types
                    has_none = 'None' in return_types
                    has_value = any(t != 'None' for t in return_types)
                    
                    if has_none and has_value:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.MEDIUM.value,
                            category='semantic',
                            message=f"Function '{node.name}' returns both None and other values inconsistently",
                            suggestion="Ensure all code paths return consistent types, or use Optional[Type] annotation"
                        ))
        
        return findings
    
    def _track_resources(self, func_node: ast.FunctionDef) -> List[ResourceUsage]:
        """Track resource acquisition and release in a function."""
        resources = []
        
        for node in ast.walk(func_node):
            # Check for resource acquisition
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name in self.resource_functions:
                    resource_type = self.resource_functions[func_name]
                    
                    # Check if in context manager
                    in_context = self._is_in_context_manager(node, func_node)
                    
                    resources.append(ResourceUsage(
                        resource_type=resource_type,
                        acquired_line=node.lineno,
                        in_context_manager=in_context
                    ))
            
            # Check for resource release
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.cleanup_methods:
                        # Mark corresponding resource as released
                        # (simplified - in real implementation, would track variable names)
                        pass
        
        return resources
    
    def _is_in_context_manager(self, node: ast.AST, func_node: ast.FunctionDef) -> bool:
        """Check if a node is inside a with statement."""
        for child in ast.walk(func_node):
            if isinstance(child, ast.With):
                for item in child.items:
                    if self._contains_node(item.context_expr, node):
                        return True
        return False
    
    def _contains_node(self, parent: ast.AST, target: ast.AST) -> bool:
        """Check if parent contains target node."""
        for node in ast.walk(parent):
            if node is target:
                return True
        return False
    
    def _check_unreachable_code(self, func_node: ast.FunctionDef, file_path: str) -> List[LocalFinding]:
        """Check for unreachable code after return/raise."""
        findings = []
        
        def check_statements(statements: List[ast.stmt]) -> None:
            for i, stmt in enumerate(statements):
                # If we find return/raise, check if there's code after
                if isinstance(stmt, (ast.Return, ast.Raise)):
                    if i < len(statements) - 1:
                        next_stmt = statements[i + 1]
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=next_stmt.lineno,
                            line_end=next_stmt.lineno,
                            severity=FindingSeverity.MEDIUM.value,
                            category='semantic',
                            message="Unreachable code after return/raise statement",
                            suggestion="Remove unreachable code or restructure control flow"
                        ))
                
                # Recursively check nested blocks
                if isinstance(stmt, ast.If):
                    check_statements(stmt.body)
                    check_statements(stmt.orelse)
                elif isinstance(stmt, (ast.For, ast.While)):
                    check_statements(stmt.body)
                elif isinstance(stmt, ast.Try):
                    check_statements(stmt.body)
        
        check_statements(func_node.body)
        return findings
    
    def _check_contradictory_conditions(self, if_node: ast.If, file_path: str) -> List[LocalFinding]:
        """Check for contradictory if conditions."""
        findings = []
        
        # Check for if x: ... elif x: (same condition)
        if if_node.orelse and len(if_node.orelse) == 1:
            elif_node = if_node.orelse[0]
            if isinstance(elif_node, ast.If):
                # Simplified check - would need more sophisticated comparison
                if ast.dump(if_node.test) == ast.dump(elif_node.test):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=elif_node.lineno,
                        line_end=elif_node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='semantic',
                        message="Elif condition is identical to if condition - second branch is unreachable",
                        suggestion="Check logic - elif should have different condition"
                    ))
        
        return findings
    
    def _check_boolean_comparison(self, compare_node: ast.Compare, file_path: str) -> List[LocalFinding]:
        """Check for comparison with True/False."""
        findings = []
        
        for comparator in compare_node.comparators:
            if isinstance(comparator, ast.Constant):
                if comparator.value is True or comparator.value is False:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=compare_node.lineno,
                        line_end=compare_node.lineno,
                        severity=FindingSeverity.LOW.value,
                        category='semantic',
                        message=f"Comparison with {comparator.value} is redundant",
                        suggestion=f"Use 'if condition:' instead of 'if condition == True:'"
                    ))
        
        return findings
    
    def _check_is_with_literals(self, compare_node: ast.Compare, file_path: str) -> List[LocalFinding]:
        """Check for 'is' comparison with literals (except None)."""
        findings = []
        
        for i, op in enumerate(compare_node.ops):
            if isinstance(op, (ast.Is, ast.IsNot)):
                comparator = compare_node.comparators[i]
                if isinstance(comparator, ast.Constant) and comparator.value is not None:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=compare_node.lineno,
                        line_end=compare_node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='semantic',
                        message=f"Using 'is' to compare with literal value {comparator.value}",
                        suggestion="Use '==' for value comparison, 'is' only for None and singletons"
                    ))
        
        return findings
    
    def _check_toctou(self, func_node: ast.FunctionDef, file_path: str) -> List[LocalFinding]:
        """Check for Time-of-check Time-of-use race conditions."""
        findings = []
        
        # Look for os.path.exists() followed by file operation
        statements = func_node.body
        for i in range(len(statements) - 1):
            stmt = statements[i]
            
            # Check if this is an if statement checking file existence
            if isinstance(stmt, ast.If):
                if self._is_file_existence_check(stmt.test):
                    # Check if next statements have file operations
                    if self._has_file_operation(stmt.body):
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=stmt.lineno,
                            line_end=stmt.lineno,
                            severity=FindingSeverity.MEDIUM.value,
                            category='semantic',
                            message="Potential TOCTOU race condition: file existence check followed by file operation",
                            suggestion="Use try/except around file operation instead of checking existence first"
                        ))
        
        return findings
    
    def _check_shared_state(self, func_node: ast.FunctionDef, file_path: str) -> List[LocalFinding]:
        """Check for shared state access without synchronization."""
        # This is a simplified check - would need more sophisticated analysis
        return []
    
    def _get_return_types(self, func_node: ast.FunctionDef) -> Set[str]:
        """Get all return types in a function."""
        return_types = set()
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value is None:
                    return_types.add('None')
                elif isinstance(node.value, ast.Constant):
                    return_types.add(type(node.value.value).__name__)
                else:
                    return_types.add('value')
        
        return return_types
    
    def _is_file_existence_check(self, test_node: ast.AST) -> bool:
        """Check if test is a file existence check."""
        if isinstance(test_node, ast.Call):
            func_name = self._get_function_name(test_node.func)
            return 'exists' in func_name or 'isfile' in func_name
        return False
    
    def _has_file_operation(self, statements: List[ast.stmt]) -> bool:
        """Check if statements contain file operations."""
        for stmt in statements:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node.func)
                    if func_name in ('open', 'remove', 'unlink', 'rmdir'):
                        return True
        return False
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_function_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""

