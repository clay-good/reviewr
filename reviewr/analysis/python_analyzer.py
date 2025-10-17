import ast
from typing import List, Set, Dict, Optional, Any
from collections import defaultdict
from pathlib import Path

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


class PythonAnalyzer(LocalAnalyzer):
    """Analyzer for Python code using AST."""
    
    def __init__(self):
        """Initialize the Python analyzer."""
        self.complexity_threshold = 10
        self.max_function_lines = 50
        self.max_function_params = 5
        self.max_nesting_depth = 4
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports Python."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Python code and return findings.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of local findings
        """
        findings = []
        
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            # Syntax error - report it
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=e.lineno or 1,
                line_end=e.lineno or 1,
                severity=FindingSeverity.CRITICAL.value,
                category='syntax',
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before proceeding with analysis."
            ))
            return findings
        except Exception as e:
            # Other parsing errors
            return findings
        
        # Run various analyses
        findings.extend(self._analyze_complexity(tree, file_path, content))
        findings.extend(self._analyze_function_length(tree, file_path, content))
        findings.extend(self._analyze_dead_code(tree, file_path, content))
        findings.extend(self._analyze_imports(tree, file_path, content))
        findings.extend(self._analyze_code_smells(tree, file_path, content))
        findings.extend(self._analyze_nesting_depth(tree, file_path, content))
        
        return findings
    
    def _analyze_complexity(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze cyclomatic complexity of functions."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                
                if complexity > self.complexity_threshold:
                    severity = FindingSeverity.MEDIUM.value
                    if complexity > 20:
                        severity = FindingSeverity.HIGH.value
                    elif complexity > 15:
                        severity = FindingSeverity.MEDIUM.value
                    else:
                        severity = FindingSeverity.LOW.value
                    
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=severity,
                        category='complexity',
                        message=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                        suggestion=f"Consider breaking this function into smaller functions. Target complexity: <{self.complexity_threshold}",
                        metric_value=float(complexity),
                        metric_name='cyclomatic_complexity'
                    ))
        
        return findings
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds complexity
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                # Add complexity for filters in comprehensions
                complexity += len(child.ifs)
        
        return complexity
    
    def _analyze_function_length(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze function length."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.end_lineno:
                    length = node.end_lineno - node.lineno + 1
                    
                    if length > self.max_function_lines:
                        severity = FindingSeverity.LOW.value
                        if length > 100:
                            severity = FindingSeverity.MEDIUM.value
                        
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            severity=severity,
                            category='maintainability',
                            message=f"Function '{node.name}' is too long ({length} lines)",
                            suggestion=f"Consider breaking this function into smaller functions. Target: <{self.max_function_lines} lines",
                            metric_value=float(length),
                            metric_name='function_length'
                        ))
                
                # Check parameter count
                param_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1
                
                if param_count > self.max_function_params:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.LOW.value,
                        category='maintainability',
                        message=f"Function '{node.name}' has too many parameters ({param_count})",
                        suggestion=f"Consider using a configuration object or reducing parameters. Target: <{self.max_function_params}",
                        metric_value=float(param_count),
                        metric_name='parameter_count'
                    ))
        
        return findings
    
    def _analyze_dead_code(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential dead code."""
        findings = []
        
        # Track defined and used names
        defined_functions = set()
        defined_classes = set()
        used_names = set()
        
        # First pass: collect definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Ignore private functions
                    defined_functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    defined_classes.add(node.name)
        
        # Second pass: collect usages
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used_names.add(node.func.id)
        
        # Find unused functions (potential dead code)
        unused_functions = defined_functions - used_names
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in unused_functions:
                # Skip if it's a special method or test function
                if node.name.startswith('test_') or node.name in ('main', '__init__', '__str__', '__repr__'):
                    continue
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    severity=FindingSeverity.INFO.value,
                    category='dead_code',
                    message=f"Function '{node.name}' appears to be unused",
                    suggestion="Consider removing this function if it's truly unused, or mark it as private with '_' prefix if it's part of the API."
                ))
        
        # Check for unreachable code after return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_unreachable_code(node, file_path, findings)
        
        return findings
    
    def _check_unreachable_code(self, func_node: ast.AST, file_path: str, findings: List[LocalFinding]):
        """Check for unreachable code after return statements."""
        for i, stmt in enumerate(func_node.body):
            if isinstance(stmt, ast.Return):
                # Check if there are more statements after this return
                if i < len(func_node.body) - 1:
                    next_stmt = func_node.body[i + 1]
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=next_stmt.lineno,
                        line_end=next_stmt.end_lineno or next_stmt.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='dead_code',
                        message="Unreachable code after return statement",
                        suggestion="Remove the unreachable code or restructure the function logic."
                    ))
                    break

    def _analyze_imports(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze import statements."""
        findings = []

        imported_names = set()
        used_names = set()
        import_nodes = {}

        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
                    import_nodes[name] = node
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':
                        name = alias.asname if alias.asname else alias.name
                        imported_names.add(name)
                        import_nodes[name] = node

        # Collect usages
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # Find unused imports
        unused_imports = imported_names - used_names
        for name in unused_imports:
            if name in import_nodes:
                node = import_nodes[name]
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    severity=FindingSeverity.INFO.value,
                    category='imports',
                    message=f"Unused import: '{name}'",
                    suggestion="Remove unused imports to keep the code clean."
                ))

        # Check for wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.LOW.value,
                            category='imports',
                            message=f"Wildcard import from '{node.module}'",
                            suggestion="Use explicit imports instead of wildcard imports to avoid namespace pollution."
                        ))

        return findings

    def _analyze_code_smells(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect common code smells."""
        findings = []

        for node in ast.walk(tree):
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='smell',
                        message="Bare except clause catches all exceptions",
                        suggestion="Catch specific exceptions instead of using bare 'except:'. Use 'except Exception:' at minimum."
                    ))

            # Check for pass in except blocks (swallowing exceptions)
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='smell',
                        message="Exception silently swallowed with 'pass'",
                        suggestion="At minimum, log the exception. Silently swallowing exceptions makes debugging difficult."
                    ))

            # Check for mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.HIGH.value,
                            category='smell',
                            message=f"Function '{node.name}' has mutable default argument",
                            suggestion="Use None as default and initialize inside the function: def func(arg=None): arg = arg or []"
                        ))

            # Check for TODO/FIXME comments
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    comment = node.value.value.upper()
                    if 'TODO' in comment or 'FIXME' in comment:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.INFO.value,
                            category='smell',
                            message="TODO/FIXME comment found",
                            suggestion="Address the TODO/FIXME or create a ticket to track it."
                        ))

        # Check for duplicate code patterns
        findings.extend(self._check_duplicate_code(tree, file_path))

        return findings

    def _check_duplicate_code(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Check for duplicate code patterns."""
        findings = []

        # Collect all function bodies as strings
        function_bodies = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_str = ast.dump(node)
                if body_str in function_bodies:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.LOW.value,
                        category='smell',
                        message=f"Function '{node.name}' appears to be duplicate of '{function_bodies[body_str]}'",
                        suggestion="Consider extracting common logic into a shared function."
                    ))
                else:
                    function_bodies[body_str] = node.name

        return findings

    def _analyze_nesting_depth(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze nesting depth of code blocks."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                max_depth = self._calculate_nesting_depth(node)

                if max_depth > self.max_nesting_depth:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='complexity',
                        message=f"Function '{node.name}' has deep nesting (depth: {max_depth})",
                        suggestion=f"Reduce nesting depth by extracting nested logic into separate functions. Target: <{self.max_nesting_depth}",
                        metric_value=float(max_depth),
                        metric_name='nesting_depth'
                    ))

        return findings

    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in a node."""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

