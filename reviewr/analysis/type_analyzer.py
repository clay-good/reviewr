"""
Type Safety Analyzer for Python code.

Analyzes type hints, detects missing annotations, type inconsistencies,
and potential runtime type errors.
"""

import ast
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class TypeInfo:
    """Information about a type annotation."""
    name: str
    annotation: Optional[ast.AST]
    line: int
    is_parameter: bool = False
    is_return: bool = False


class TypeAnalyzer(LocalAnalyzer):
    """
    Analyzer for Python type safety.
    
    Detects:
    - Missing type annotations on functions and methods
    - Missing return type annotations
    - Inconsistent type usage
    - Potential type errors (e.g., None checks)
    - Mutable default arguments
    - Type annotation best practices
    """
    
    def __init__(self):
        """Initialize the type analyzer."""
        self.builtin_types = {
            'int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple',
            'bytes', 'bytearray', 'None', 'type', 'object', 'Any'
        }
        
        # Common typing module types
        self.typing_types = {
            'List', 'Dict', 'Set', 'Tuple', 'Optional', 'Union', 'Any',
            'Callable', 'Iterable', 'Iterator', 'Sequence', 'Mapping'
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze Python code for type safety issues."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        
        findings = []
        
        # Analyze functions and methods
        findings.extend(self._analyze_functions(tree, file_path, content))
        
        # Analyze class attributes
        findings.extend(self._analyze_class_attributes(tree, file_path))
        
        # Analyze variable assignments
        findings.extend(self._analyze_assignments(tree, file_path))
        
        # Analyze None checks and type guards
        findings.extend(self._analyze_none_checks(tree, file_path))
        
        # Analyze mutable defaults
        findings.extend(self._analyze_mutable_defaults(tree, file_path))
        
        return findings
    
    def _analyze_functions(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze function and method type annotations."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods (except __init__)
                if node.name.startswith('__') and node.name.endswith('__') and node.name != '__init__':
                    continue
                
                # Check for missing return type annotation
                if node.returns is None and node.name != '__init__':
                    # Check if function actually returns something
                    has_return = self._has_return_value(node)
                    if has_return:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.LOW.value,
                            category='type_safety',
                            message=f"Function '{node.name}' is missing return type annotation",
                            suggestion="Add return type annotation: def func() -> ReturnType:"
                        ))
                
                # Check for missing parameter annotations
                missing_params = []
                for arg in node.args.args:
                    # Skip 'self' and 'cls'
                    if arg.arg in ('self', 'cls'):
                        continue
                    
                    if arg.annotation is None:
                        missing_params.append(arg.arg)
                
                if missing_params:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.LOW.value,
                        category='type_safety',
                        message=f"Function '{node.name}' has parameters without type annotations: {', '.join(missing_params)}",
                        suggestion="Add type annotations to parameters: def func(param: Type) -> ReturnType:"
                    ))
                
                # Check for inconsistent annotation style
                annotated_params = [arg for arg in node.args.args if arg.annotation is not None and arg.arg not in ('self', 'cls')]
                unannotated_params = [arg for arg in node.args.args if arg.annotation is None and arg.arg not in ('self', 'cls')]
                
                if annotated_params and unannotated_params:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='type_safety',
                        message=f"Function '{node.name}' has inconsistent type annotations (some parameters annotated, some not)",
                        suggestion="Either annotate all parameters or none for consistency"
                    ))
                
                # Check for Any type usage
                findings.extend(self._check_any_usage(node, file_path))
        
        return findings
    
    def _analyze_class_attributes(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze class attribute type annotations."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for class attributes without annotations
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                # Class attribute without annotation
                                findings.append(LocalFinding(
                                    file_path=file_path,
                                    line_start=item.lineno,
                                    line_end=item.lineno,
                                    severity=FindingSeverity.INFO.value,
                                    category='type_safety',
                                    message=f"Class attribute '{target.id}' in '{node.name}' lacks type annotation",
                                    suggestion="Use annotated assignment: attribute: Type = value"
                                ))
        
        return findings
    
    def _analyze_assignments(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze variable assignments for type issues."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for type narrowing opportunities
            if isinstance(node, ast.Assign):
                # Check for None assignments that could use Optional
                if isinstance(node.value, ast.Constant) and node.value.value is None:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            findings.append(LocalFinding(
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.lineno,
                                severity=FindingSeverity.INFO.value,
                                category='type_safety',
                                message=f"Variable '{target.id}' initialized to None without type annotation",
                                suggestion="Consider adding type annotation: var: Optional[Type] = None"
                            ))
        
        return findings
    
    def _analyze_none_checks(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Analyze None checks and potential None dereferences."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for attribute access without None check
            if isinstance(node, ast.Attribute):
                # Look for patterns like: obj.attr where obj might be None
                if isinstance(node.value, ast.Name):
                    # This is a simplified check - in real implementation,
                    # we'd need data flow analysis to track None values
                    pass
            
            # Check for comparison with None using == instead of is
            if isinstance(node, ast.Compare):
                if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                    # Check if comparing with None
                    is_none_comparison = False
                    if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                        is_none_comparison = True
                    elif isinstance(node.left, ast.Constant) and node.left.value is None:
                        is_none_comparison = True
                    
                    if is_none_comparison:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.LOW.value,
                            category='type_safety',
                            message="Use 'is None' or 'is not None' instead of '==' or '!=' for None checks",
                            suggestion="Replace '== None' with 'is None' and '!= None' with 'is not None'"
                        ))
        
        return findings
    
    def _analyze_mutable_defaults(self, tree: ast.AST, file_path: str) -> List[LocalFinding]:
        """Detect mutable default arguments."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    # Check for mutable defaults: [], {}, set()
                    is_mutable = False
                    mutable_type = ""
                    
                    if isinstance(default, ast.List):
                        is_mutable = True
                        mutable_type = "list"
                    elif isinstance(default, ast.Dict):
                        is_mutable = True
                        mutable_type = "dict"
                    elif isinstance(default, ast.Set):
                        is_mutable = True
                        mutable_type = "set"
                    elif isinstance(default, ast.Call):
                        if isinstance(default.func, ast.Name):
                            if default.func.id in ('list', 'dict', 'set'):
                                is_mutable = True
                                mutable_type = default.func.id
                    
                    if is_mutable:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            severity=FindingSeverity.HIGH.value,
                            category='type_safety',
                            message=f"Function '{node.name}' has mutable default argument ({mutable_type})",
                            suggestion=f"Use None as default and create {mutable_type} inside function: def func(arg=None): arg = arg if arg is not None else {mutable_type}()"
                        ))
        
        return findings
    
    def _check_any_usage(self, func_node: ast.FunctionDef, file_path: str) -> List[LocalFinding]:
        """Check for usage of Any type."""
        findings = []
        
        # Check return type
        if func_node.returns:
            if self._is_any_type(func_node.returns):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=func_node.lineno,
                    line_end=func_node.lineno,
                    severity=FindingSeverity.INFO.value,
                    category='type_safety',
                    message=f"Function '{func_node.name}' uses 'Any' return type, which bypasses type checking",
                    suggestion="Consider using a more specific type if possible"
                ))
        
        # Check parameter types
        for arg in func_node.args.args:
            if arg.annotation and self._is_any_type(arg.annotation):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=func_node.lineno,
                    line_end=func_node.lineno,
                    severity=FindingSeverity.INFO.value,
                    category='type_safety',
                    message=f"Parameter '{arg.arg}' in function '{func_node.name}' uses 'Any' type",
                    suggestion="Consider using a more specific type if possible"
                ))
        
        return findings
    
    def _is_any_type(self, annotation: ast.AST) -> bool:
        """Check if annotation is Any type."""
        if isinstance(annotation, ast.Name):
            return annotation.id == 'Any'
        return False
    
    def _has_return_value(self, func_node: ast.FunctionDef) -> bool:
        """Check if function returns a value (not just None or no return)."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                # If return has a value that's not None
                if node.value is not None:
                    if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                        return True
        return False

