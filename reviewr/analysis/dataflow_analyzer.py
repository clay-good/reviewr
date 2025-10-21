"""
Data flow analysis for Python code.

This module implements taint analysis to track data flow from sources
(user input, files, network) to sinks (database queries, system calls, file operations)
to detect security vulnerabilities.
"""

import ast
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class TaintedVariable:
    """Represents a variable that contains tainted (untrusted) data."""
    name: str
    source: str  # Where the taint came from
    line: int
    taint_type: str  # 'user_input', 'file', 'network', 'environment'


@dataclass
class DataFlowPath:
    """Represents a path from source to sink."""
    source_line: int
    source_var: str
    source_type: str
    sink_line: int
    sink_func: str
    sink_type: str
    intermediate_vars: List[str] = field(default_factory=list)


class DataFlowAnalyzer(LocalAnalyzer):
    """Analyzes data flow to detect taint propagation."""
    
    def __init__(self):
        """Initialize the data flow analyzer."""
        # Taint sources - where untrusted data originates
        self.taint_sources = {
            # User input
            'input': 'user_input',
            'raw_input': 'user_input',
            'sys.stdin.read': 'user_input',
            'sys.stdin.readline': 'user_input',
            # Web frameworks - Flask
            'request.args.get': 'user_input',
            'request.form.get': 'user_input',
            'request.data': 'user_input',
            'request.json': 'user_input',
            'request.get_json': 'user_input',
            'request.values': 'user_input',
            'request.cookies': 'user_input',
            'request.headers': 'user_input',
            # Web frameworks - Django
            'request.GET.get': 'user_input',
            'request.POST.get': 'user_input',
            'request.body': 'user_input',
            # Environment
            'os.environ.get': 'environment',
            'os.getenv': 'environment',
            # Files
            'open': 'file',
            'file.read': 'file',
            'Path.read_text': 'file',
            # Network
            'requests.get': 'network',
            'requests.post': 'network',
            'urllib.request.urlopen': 'network',
            'socket.recv': 'network',
        }
        
        # Dangerous sinks - operations that should not receive tainted data
        self.dangerous_sinks = {
            # SQL
            'execute': 'sql',
            'executemany': 'sql',
            'cursor.execute': 'sql',
            'connection.execute': 'sql',
            # Command execution
            'os.system': 'command',
            'subprocess.call': 'command',
            'subprocess.run': 'command',
            'subprocess.Popen': 'command',
            'eval': 'eval',
            'exec': 'eval',
            # File operations
            'open': 'file',
            'os.remove': 'file',
            'os.unlink': 'file',
            'shutil.rmtree': 'file',
            # Network
            'requests.get': 'network',
            'requests.post': 'network',
            'urllib.request.urlopen': 'network',
        }
        
        # Sanitization functions - these clean tainted data
        self.sanitizers = {
            'html.escape',
            'urllib.parse.quote',
            'shlex.quote',
            'bleach.clean',
            'int',  # Type conversion can sanitize
            'float',
            'str.isalnum',  # Validation
            'str.isdigit',
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports Python."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Perform data flow analysis to detect taint propagation.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            tree = ast.parse(content, filename=file_path)
        except (SyntaxError, Exception):
            return findings
        
        # Track tainted variables throughout the code
        tainted_vars: Dict[str, TaintedVariable] = {}
        
        # Analyze each function separately
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_findings, func_tainted = self._analyze_function(node, file_path, content)
                findings.extend(func_findings)
                tainted_vars.update(func_tainted)
        
        # Also analyze module-level code
        module_findings, module_tainted = self._analyze_statements(tree.body, file_path, content, {})
        findings.extend(module_findings)
        
        return findings
    
    def _analyze_function(
        self, 
        func_node: ast.FunctionDef, 
        file_path: str, 
        content: str
    ) -> Tuple[List[LocalFinding], Dict[str, TaintedVariable]]:
        """Analyze a single function for taint flow."""
        findings = []
        tainted_vars: Dict[str, TaintedVariable] = {}
        
        # Check if function parameters are tainted (e.g., from web framework)
        for arg in func_node.args.args:
            arg_name = arg.arg
            # Common parameter names that indicate user input
            if arg_name in ['request', 'req', 'data', 'input', 'params']:
                tainted_vars[arg_name] = TaintedVariable(
                    name=arg_name,
                    source='function_parameter',
                    line=func_node.lineno,
                    taint_type='user_input'
                )
        
        # Analyze function body
        func_findings, func_tainted = self._analyze_statements(
            func_node.body, file_path, content, tainted_vars
        )
        findings.extend(func_findings)
        tainted_vars.update(func_tainted)
        
        return findings, tainted_vars
    
    def _analyze_statements(
        self,
        statements: List[ast.stmt],
        file_path: str,
        content: str,
        tainted_vars: Dict[str, TaintedVariable]
    ) -> Tuple[List[LocalFinding], Dict[str, TaintedVariable]]:
        """Analyze a list of statements for taint flow."""
        findings = []
        
        for stmt in statements:
            # Track assignments
            if isinstance(stmt, ast.Assign):
                findings.extend(self._analyze_assignment(stmt, file_path, tainted_vars))
            
            # Track augmented assignments (+=, etc.)
            elif isinstance(stmt, ast.AugAssign):
                findings.extend(self._analyze_aug_assignment(stmt, file_path, tainted_vars))
            
            # Check function calls for sinks
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                findings.extend(self._check_sink(stmt.value, file_path, tainted_vars))
            
            # Recursively analyze control flow
            elif isinstance(stmt, (ast.If, ast.While, ast.For)):
                if hasattr(stmt, 'body'):
                    body_findings, _ = self._analyze_statements(stmt.body, file_path, content, tainted_vars)
                    findings.extend(body_findings)
                if hasattr(stmt, 'orelse'):
                    else_findings, _ = self._analyze_statements(stmt.orelse, file_path, content, tainted_vars)
                    findings.extend(else_findings)
            
            # Analyze try-except blocks
            elif isinstance(stmt, ast.Try):
                body_findings, _ = self._analyze_statements(stmt.body, file_path, content, tainted_vars)
                findings.extend(body_findings)
                for handler in stmt.handlers:
                    handler_findings, _ = self._analyze_statements(handler.body, file_path, content, tainted_vars)
                    findings.extend(handler_findings)
        
        return findings, tainted_vars
    
    def _analyze_assignment(
        self,
        assign_node: ast.Assign,
        file_path: str,
        tainted_vars: Dict[str, TaintedVariable]
    ) -> List[LocalFinding]:
        """Analyze an assignment for taint propagation."""
        findings = []
        
        # Check if the right-hand side is a taint source
        if isinstance(assign_node.value, ast.Call):
            func_name = self._get_function_name(assign_node.value.func)
            
            # Check if it's a taint source
            for source_pattern, taint_type in self.taint_sources.items():
                if source_pattern in func_name:
                    # Mark all targets as tainted
                    for target in assign_node.targets:
                        if isinstance(target, ast.Name):
                            tainted_vars[target.id] = TaintedVariable(
                                name=target.id,
                                source=func_name,
                                line=assign_node.lineno,
                                taint_type=taint_type
                            )
                    break
            
            # Check if it's a sink with tainted input
            findings.extend(self._check_sink(assign_node.value, file_path, tainted_vars))
        
        # Check if assigning from a tainted variable
        elif isinstance(assign_node.value, ast.Name):
            if assign_node.value.id in tainted_vars:
                # Propagate taint to new variable
                for target in assign_node.targets:
                    if isinstance(target, ast.Name):
                        original_taint = tainted_vars[assign_node.value.id]
                        tainted_vars[target.id] = TaintedVariable(
                            name=target.id,
                            source=original_taint.source,
                            line=assign_node.lineno,
                            taint_type=original_taint.taint_type
                        )
        
        # Check if using tainted variable in operations
        elif isinstance(assign_node.value, (ast.BinOp, ast.JoinedStr)):
            if self._contains_tainted_var(assign_node.value, tainted_vars):
                # Propagate taint
                for target in assign_node.targets:
                    if isinstance(target, ast.Name):
                        tainted_vars[target.id] = TaintedVariable(
                            name=target.id,
                            source='derived',
                            line=assign_node.lineno,
                            taint_type='user_input'
                        )
        
        return findings
    
    def _analyze_aug_assignment(
        self,
        aug_assign_node: ast.AugAssign,
        file_path: str,
        tainted_vars: Dict[str, TaintedVariable]
    ) -> List[LocalFinding]:
        """Analyze augmented assignment (+=, etc.) for taint propagation."""
        findings = []
        
        # If adding tainted data to a variable, the variable becomes tainted
        if isinstance(aug_assign_node.target, ast.Name):
            if self._contains_tainted_var(aug_assign_node.value, tainted_vars):
                tainted_vars[aug_assign_node.target.id] = TaintedVariable(
                    name=aug_assign_node.target.id,
                    source='augmented_assignment',
                    line=aug_assign_node.lineno,
                    taint_type='user_input'
                )

        return findings

    def _check_sink(
        self,
        call_node: ast.Call,
        file_path: str,
        tainted_vars: Dict[str, TaintedVariable]
    ) -> List[LocalFinding]:
        """Check if a function call is a dangerous sink with tainted input."""
        findings = []

        func_name = self._get_function_name(call_node.func)

        # Check if this is a dangerous sink
        sink_type = None
        for sink_pattern, s_type in self.dangerous_sinks.items():
            if sink_pattern in func_name:
                sink_type = s_type
                break

        if not sink_type:
            return findings

        # Check if any arguments are tainted
        tainted_args = []
        for arg in call_node.args:
            if self._is_tainted(arg, tainted_vars):
                tainted_source = self._get_taint_source(arg, tainted_vars)
                tainted_args.append((arg, tainted_source))

        # Check keyword arguments
        for keyword in call_node.keywords:
            if self._is_tainted(keyword.value, tainted_vars):
                tainted_source = self._get_taint_source(keyword.value, tainted_vars)
                tainted_args.append((keyword.value, tainted_source))

        # Report findings for tainted sinks
        for arg, source in tainted_args:
            severity = self._get_severity_for_sink(sink_type)
            message = self._get_message_for_sink(sink_type, func_name, source)
            suggestion = self._get_suggestion_for_sink(sink_type)

            findings.append(LocalFinding(
                file_path=file_path,
                line_start=call_node.lineno,
                line_end=call_node.end_lineno or call_node.lineno,
                severity=severity,
                category='dataflow',
                message=message,
                suggestion=suggestion
            ))

        return findings

    def _is_tainted(self, node: ast.AST, tainted_vars: Dict[str, TaintedVariable]) -> bool:
        """Check if an AST node contains tainted data."""
        # Direct variable reference
        if isinstance(node, ast.Name):
            return node.id in tainted_vars

        # Attribute access (e.g., request.args)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return node.value.id in tainted_vars
            return self._is_tainted(node.value, tainted_vars)

        # Binary operations (concatenation, etc.)
        elif isinstance(node, ast.BinOp):
            return (self._is_tainted(node.left, tainted_vars) or
                    self._is_tainted(node.right, tainted_vars))

        # F-strings
        elif isinstance(node, ast.JoinedStr):
            return any(self._is_tainted(val, tainted_vars) for val in node.values
                      if isinstance(val, ast.FormattedValue))

        # Function calls
        elif isinstance(node, ast.Call):
            # Check if any argument is tainted
            for arg in node.args:
                if self._is_tainted(arg, tainted_vars):
                    return True
            for keyword in node.keywords:
                if self._is_tainted(keyword.value, tainted_vars):
                    return True
            return False

        return False

    def _get_taint_source(self, node: ast.AST, tainted_vars: Dict[str, TaintedVariable]) -> Optional[TaintedVariable]:
        """Get the taint source for a node."""
        if isinstance(node, ast.Name) and node.id in tainted_vars:
            return tainted_vars[node.id]
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in tainted_vars:
                return tainted_vars[node.value.id]
        return None

    def _contains_tainted_var(self, node: ast.AST, tainted_vars: Dict[str, TaintedVariable]) -> bool:
        """Check if a node contains any tainted variables."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in tainted_vars:
                return True
        return False

    def _get_severity_for_sink(self, sink_type: str) -> str:
        """Get severity level for a sink type."""
        severity_map = {
            'sql': FindingSeverity.CRITICAL.value,
            'command': FindingSeverity.CRITICAL.value,
            'eval': FindingSeverity.CRITICAL.value,
            'file': FindingSeverity.HIGH.value,
            'network': FindingSeverity.HIGH.value,
        }
        return severity_map.get(sink_type, FindingSeverity.MEDIUM.value)

    def _get_message_for_sink(self, sink_type: str, func_name: str, source: Optional[TaintedVariable]) -> str:
        """Get message for a tainted sink."""
        source_desc = f" from {source.source}" if source else ""

        messages = {
            'sql': f"SQL injection risk: tainted data{source_desc} flows to {func_name}",
            'command': f"Command injection risk: tainted data{source_desc} flows to {func_name}",
            'eval': f"Code injection risk: tainted data{source_desc} flows to {func_name}",
            'file': f"Path traversal risk: tainted data{source_desc} flows to {func_name}",
            'network': f"SSRF risk: tainted data{source_desc} flows to {func_name}",
        }
        return messages.get(sink_type, f"Tainted data{source_desc} flows to {func_name}")

    def _get_suggestion_for_sink(self, sink_type: str) -> str:
        """Get suggestion for fixing a tainted sink."""
        suggestions = {
            'sql': "Use parameterized queries or an ORM to prevent SQL injection",
            'command': "Validate and sanitize input, use shell=False, or use shlex.quote()",
            'eval': "Avoid eval/exec. Use ast.literal_eval() for data or refactor to avoid dynamic code",
            'file': "Validate file paths against an allowlist and use os.path.abspath()",
            'network': "Validate URLs against an allowlist and block private IP ranges",
        }
        return suggestions.get(sink_type, "Validate and sanitize all user input before use")

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from a call node."""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                parts = []
                current = node
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                return '.'.join(reversed(parts))
            return ''
        except:
            return ''
