"""
Advanced security analysis for Python code.

This module provides deep security analysis including:
- SQL injection detection
- Command injection detection
- Path traversal vulnerabilities
- Insecure deserialization
- SSRF (Server-Side Request Forgery)
- XXE (XML External Entity) attacks
- Cryptographic issues
- Authentication/authorization flaws
"""

import ast
import re
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class TaintSource:
    """Represents a source of potentially untrusted data."""
    name: str
    node: ast.AST
    line: int
    category: str  # 'user_input', 'file', 'network', 'environment'


@dataclass
class TaintSink:
    """Represents a dangerous operation that could be exploited."""
    name: str
    node: ast.AST
    line: int
    category: str  # 'sql', 'command', 'file', 'network', 'eval'


class SecurityAnalyzer(LocalAnalyzer):
    """Advanced security analyzer for Python code."""
    
    def __init__(self):
        """Initialize the security analyzer."""
        # Taint sources - where untrusted data comes from
        self.taint_sources = {
            # User input
            'input', 'raw_input', 'sys.stdin', 'sys.argv',
            # Web frameworks
            'request.args', 'request.form', 'request.data', 'request.json',
            'request.get_json', 'request.values', 'request.cookies',
            'request.headers', 'request.query_params', 'request.POST',
            'request.GET', 'request.FILES', 'request.body',
            # Environment
            'os.environ', 'os.getenv', 'environ.get',
            # Files
            'open', 'read', 'readlines', 'file.read',
        }
        
        # SQL-related functions (potential injection points)
        self.sql_sinks = {
            'execute', 'executemany', 'raw', 'cursor.execute',
            'connection.execute', 'session.execute', 'query',
            'filter', 'filter_by', 'raw_sql', 'exec_driver_sql',
        }
        
        # Command execution functions
        self.command_sinks = {
            'os.system', 'os.popen', 'os.exec', 'os.execl', 'os.execle',
            'os.execlp', 'os.execlpe', 'os.execv', 'os.execve', 'os.execvp',
            'os.execvpe', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
            'subprocess.check_call', 'subprocess.check_output', 'eval', 'exec',
            'compile', '__import__',
        }
        
        # File operation functions (path traversal)
        self.file_sinks = {
            'open', 'file', 'os.open', 'os.remove', 'os.unlink', 'os.rmdir',
            'os.rename', 'os.chmod', 'os.chown', 'shutil.copy', 'shutil.move',
            'shutil.rmtree', 'pathlib.Path',
        }
        
        # Network functions (SSRF)
        self.network_sinks = {
            'requests.get', 'requests.post', 'requests.put', 'requests.delete',
            'requests.request', 'urllib.request.urlopen', 'urllib.request.urlretrieve',
            'httplib.request', 'http.client.request', 'socket.connect',
        }
        
        # Insecure deserialization
        self.deserialization_funcs = {
            'pickle.loads', 'pickle.load', 'cPickle.loads', 'cPickle.load',
            'yaml.load', 'marshal.loads', 'marshal.load', 'shelve.open',
        }
        
        # Weak cryptographic functions
        self.weak_crypto = {
            'md5', 'sha1', 'DES', 'RC4', 'Random', 'random.random',
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports Python."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Perform comprehensive security analysis.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            return findings
        except Exception:
            return findings
        
        # Run security analyses
        findings.extend(self._detect_sql_injection(tree, file_path, content))
        findings.extend(self._detect_command_injection(tree, file_path, content))
        findings.extend(self._detect_path_traversal(tree, file_path, content))
        findings.extend(self._detect_insecure_deserialization(tree, file_path, content))
        findings.extend(self._detect_ssrf(tree, file_path, content))
        findings.extend(self._detect_xxe(tree, file_path, content))
        findings.extend(self._detect_weak_crypto(tree, file_path, content))
        findings.extend(self._detect_hardcoded_secrets(tree, file_path, content))
        findings.extend(self._detect_insecure_random(tree, file_path, content))
        findings.extend(self._detect_timing_attacks(tree, file_path, content))
        findings.extend(self._detect_race_conditions(tree, file_path, content))
        findings.extend(self._detect_insecure_temp_files(tree, file_path, content))
        
        return findings
    
    def _detect_sql_injection(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential SQL injection vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            # Check for string formatting in SQL queries (in execute calls)
            if isinstance(node, ast.Call):
                # Check if it's a SQL execution call
                func_name = self._get_function_name(node.func)

                if any(sink in func_name for sink in self.sql_sinks):
                    # Check if the query uses string formatting
                    if node.args:
                        query_arg = node.args[0]
                        findings.extend(self._check_sql_string_formatting(query_arg, file_path, node.lineno))

            # Also check assignments that look like SQL queries
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        # Check if variable name suggests it's a SQL query
                        if any(keyword in var_name for keyword in ['query', 'sql', 'select', 'insert', 'update', 'delete']):
                            findings.extend(self._check_sql_string_formatting(node.value, file_path, node.lineno))

        return findings

    def _check_sql_string_formatting(self, node: ast.AST, file_path: str, line_num: int) -> List[LocalFinding]:
        """Check if a node contains SQL string formatting."""
        findings = []

        # Detect f-strings
        if isinstance(node, ast.JoinedStr):
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.CRITICAL.value,
                category='security',
                message="Potential SQL injection: f-string used in SQL query",
                suggestion="Use parameterized queries instead: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
            ))

        # Detect % formatting
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=FindingSeverity.CRITICAL.value,
                category='security',
                message="Potential SQL injection: % formatting used in SQL query",
                suggestion="Use parameterized queries with placeholders instead of string formatting"
            ))

        # Detect .format()
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'format':
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity=FindingSeverity.CRITICAL.value,
                        category='security',
                        message="Potential SQL injection: .format() used in SQL query",
                        suggestion="Use parameterized queries instead of .format()"
                    ))

        # Detect string concatenation
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._contains_variable(node):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity=FindingSeverity.CRITICAL.value,
                    category='security',
                    message="Potential SQL injection: string concatenation in SQL query",
                    suggestion="Use parameterized queries instead of string concatenation"
                ))

        return findings
    
    def _detect_command_injection(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential command injection vulnerabilities."""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if any(sink in func_name for sink in self.command_sinks):
                    # Check if shell=True is used
                    shell_true = False
                    for keyword in node.keywords:
                        if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is True:
                                shell_true = True
                    
                    if shell_true:
                        # Check if command contains variables
                        if node.args and self._contains_variable(node.args[0]):
                            findings.append(LocalFinding(
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                severity=FindingSeverity.CRITICAL.value,
                                category='security',
                                message="Command injection risk: shell=True with variable input",
                                suggestion="Use shell=False and pass command as a list, or use shlex.quote() to sanitize input"
                            ))
                    
                    # Check for eval/exec with user input
                    if 'eval' in func_name or 'exec' in func_name:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.CRITICAL.value,
                            category='security',
                            message=f"Dangerous use of {func_name}(): can execute arbitrary code",
                            suggestion="Avoid eval/exec. Use safer alternatives like ast.literal_eval() for data, or refactor to avoid dynamic code execution"
                        ))

        return findings

    def _detect_path_traversal(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential path traversal vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                if any(sink in func_name for sink in self.file_sinks):
                    # Check if path contains user input without validation
                    if node.args and self._contains_variable(node.args[0]):
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.HIGH.value,
                            category='security',
                            message="Potential path traversal: file operation with variable path",
                            suggestion="Validate and sanitize file paths. Use os.path.abspath() and check if path starts with allowed directory"
                        ))

        return findings

    def _detect_insecure_deserialization(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect insecure deserialization vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for pickle.loads/load
                if 'pickle.load' in func_name or 'cPickle.load' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='security',
                        message="Insecure deserialization: pickle can execute arbitrary code",
                        suggestion="Use JSON or other safe serialization formats. If pickle is necessary, only deserialize from trusted sources"
                    ))

                # Check for yaml.load without Loader
                if 'yaml.load' in func_name:
                    has_safe_loader = False
                    for keyword in node.keywords:
                        if keyword.arg == 'Loader':
                            if isinstance(keyword.value, ast.Attribute):
                                if 'SafeLoader' in ast.unparse(keyword.value):
                                    has_safe_loader = True

                    if not has_safe_loader:
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.HIGH.value,
                            category='security',
                            message="Insecure YAML deserialization: yaml.load() without SafeLoader",
                            suggestion="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)"
                        ))

        return findings

    def _detect_ssrf(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential SSRF (Server-Side Request Forgery) vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                if any(sink in func_name for sink in self.network_sinks):
                    # Check if URL contains user input
                    if node.args and self._contains_variable(node.args[0]):
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            severity=FindingSeverity.HIGH.value,
                            category='security',
                            message="Potential SSRF: HTTP request with user-controlled URL",
                            suggestion="Validate URLs against an allowlist. Block private IP ranges (127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)"
                        ))

        return findings

    def _detect_xxe(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential XXE (XML External Entity) vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for XML parsing without disabling external entities
                if 'xml.etree' in func_name or 'lxml' in func_name or 'minidom.parse' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='security',
                        message="Potential XXE vulnerability: XML parsing without entity protection",
                        suggestion="Use defusedxml library or disable external entity processing: parser.setFeature(feature_external_ges, False)"
                    ))

        return findings

    def _detect_weak_crypto(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect use of weak cryptographic algorithms."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for MD5/SHA1
                if 'hashlib.md5' in func_name or '.md5(' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='security',
                        message="Weak cryptographic hash: MD5 is cryptographically broken",
                        suggestion="Use SHA-256 or SHA-3 for cryptographic purposes. MD5 is only acceptable for non-security checksums"
                    ))

                if 'hashlib.sha1' in func_name or '.sha1(' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='security',
                        message="Weak cryptographic hash: SHA-1 is deprecated for security",
                        suggestion="Use SHA-256, SHA-384, or SHA-512 for cryptographic purposes"
                    ))

        return findings

    def _detect_hardcoded_secrets(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect hardcoded secrets and credentials."""
        findings = []

        # Patterns for secrets
        secret_patterns = [
            (r'password\s*=\s*["\'](?!.*\{)[^"\']{8,}["\']', 'Hardcoded password'),
            (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', 'Hardcoded API key'),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{20,}["\']', 'Hardcoded secret key'),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', 'Hardcoded token'),
            (r'aws[_-]?access[_-]?key', 'AWS access key'),
            (r'private[_-]?key\s*=\s*["\']', 'Private key'),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        severity=FindingSeverity.CRITICAL.value,
                        category='security',
                        message=f"{message} detected in code",
                        suggestion="Use environment variables or a secrets management system (e.g., AWS Secrets Manager, HashiCorp Vault)"
                    ))

        return findings

    def _detect_insecure_random(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect use of insecure random number generation for security purposes."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for random.random() in security contexts
                if 'random.random' in func_name or 'random.randint' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.MEDIUM.value,
                        category='security',
                        message="Insecure random number generation",
                        suggestion="Use secrets module for cryptographic purposes: secrets.token_bytes(), secrets.token_hex(), or secrets.SystemRandom()"
                    ))

        return findings

    def _detect_timing_attacks(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential timing attack vulnerabilities."""
        findings = []

        for node in ast.walk(tree):
            # Check for string comparison in authentication/security contexts
            if isinstance(node, ast.Compare):
                # Look for comparisons that might be passwords/tokens
                if isinstance(node.left, ast.Name):
                    var_name = node.left.id.lower()
                    if any(keyword in var_name for keyword in ['password', 'token', 'secret', 'key', 'hash']):
                        # Check if using == instead of secrets.compare_digest
                        if any(isinstance(op, ast.Eq) for op in node.ops):
                            findings.append(LocalFinding(
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                severity=FindingSeverity.MEDIUM.value,
                                category='security',
                                message="Potential timing attack: string comparison on sensitive data",
                                suggestion="Use secrets.compare_digest() for constant-time comparison of secrets"
                            ))

        return findings

    def _detect_race_conditions(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect potential race condition vulnerabilities."""
        findings = []

        # Track file operations
        file_checks = []
        file_operations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Track file existence checks
                if 'os.path.exists' in func_name or 'os.path.isfile' in func_name:
                    file_checks.append(node)

                # Track file operations
                elif any(op in func_name for op in ['open', 'os.remove', 'os.rename']):
                    file_operations.append(node)

        # If we have both checks and operations, warn about TOCTOU
        if file_checks and file_operations:
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=file_checks[0].lineno,
                line_end=file_checks[0].end_lineno or file_checks[0].lineno,
                severity=FindingSeverity.MEDIUM.value,
                category='security',
                message="Potential TOCTOU (Time-of-check Time-of-use) race condition",
                suggestion="Use atomic operations or file locking. For file creation, use open() with 'x' mode instead of checking existence first"
            ))

        return findings

    def _detect_insecure_temp_files(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Detect insecure temporary file creation."""
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)

                # Check for insecure temp file creation
                if 'tempfile.mktemp' in func_name:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        severity=FindingSeverity.HIGH.value,
                        category='security',
                        message="Insecure temporary file creation: mktemp() is vulnerable to race conditions",
                        suggestion="Use tempfile.NamedTemporaryFile() or tempfile.mkstemp() instead"
                    ))

        return findings

    # Helper methods

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from a call node."""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                # Recursively build the full name
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

    def _contains_variable(self, node: ast.AST) -> bool:
        """Check if an AST node contains variables (not just constants)."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                return True
        return False

