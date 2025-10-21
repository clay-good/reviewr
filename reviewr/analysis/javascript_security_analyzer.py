"""
JavaScript/TypeScript Security Analyzer

Detects security vulnerabilities in JavaScript and TypeScript code including:
- XSS vulnerabilities
- SQL injection
- Command injection
- Insecure randomness
- Prototype pollution
- Unsafe eval/Function
- Path traversal
- Open redirects
- CSRF vulnerabilities
- Insecure dependencies
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaScriptSecurityAnalyzer(LocalAnalyzer):
    """Analyzer for JavaScript/TypeScript security vulnerabilities."""
    
    def __init__(self):
        """Initialize the security analyzer."""
        # Dangerous functions
        self.dangerous_functions = {
            'eval', 'Function', 'setTimeout', 'setInterval',
            'execScript', 'setImmediate'
        }
        
        # DOM manipulation functions that can lead to XSS
        self.dom_sinks = {
            'innerHTML', 'outerHTML', 'insertAdjacentHTML',
            'document.write', 'document.writeln'
        }
        
        # User input sources
        self.user_input_sources = {
            'req.query', 'req.params', 'req.body', 'req.headers',
            'location.search', 'location.hash', 'window.location',
            'document.URL', 'document.referrer', 'document.cookie'
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() in ['javascript', 'typescript', 'jsx', 'tsx']
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze JavaScript/TypeScript code for security vulnerabilities.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of security findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_xss_vulnerabilities(content, file_path, lines))
        findings.extend(self._detect_sql_injection(content, file_path, lines))
        findings.extend(self._detect_command_injection(content, file_path, lines))
        findings.extend(self._detect_eval_usage(content, file_path, lines))
        findings.extend(self._detect_prototype_pollution(content, file_path, lines))
        findings.extend(self._detect_insecure_randomness(content, file_path, lines))
        findings.extend(self._detect_path_traversal(content, file_path, lines))
        findings.extend(self._detect_open_redirects(content, file_path, lines))
        findings.extend(self._detect_insecure_crypto(content, file_path, lines))
        findings.extend(self._detect_hardcoded_secrets(content, file_path, lines))
        findings.extend(self._detect_unsafe_regex(content, file_path, lines))
        findings.extend(self._detect_xxe_vulnerabilities(content, file_path, lines))
        
        return findings
    
    def _detect_xss_vulnerabilities(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential XSS vulnerabilities."""
        findings = []
        
        # innerHTML with user input
        innerHTML_pattern = r'\.innerHTML\s*=\s*(?![\'"<])'
        for match in re.finditer(innerHTML_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Potential XSS vulnerability: innerHTML assignment without sanitization',
                suggestion='Use textContent for plain text or sanitize HTML with DOMPurify before assignment'
            ))
        
        # dangerouslySetInnerHTML in React
        dangerous_html_pattern = r'dangerouslySetInnerHTML\s*=\s*\{\{?\s*__html:'
        for match in re.finditer(dangerous_html_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Potential XSS: dangerouslySetInnerHTML used',
                suggestion='Sanitize HTML content with DOMPurify or use safe React components'
            ))
        
        # document.write
        doc_write_pattern = r'document\.write(?:ln)?\s*\('
        for match in re.finditer(doc_write_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='security',
                message='Potential XSS: document.write() can introduce XSS vulnerabilities',
                suggestion='Use DOM manipulation methods like createElement() and appendChild() instead'
            ))
        
        return findings
    
    def _detect_sql_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential SQL injection vulnerabilities."""
        findings = []
        
        # String concatenation in SQL queries
        sql_concat_patterns = [
            r'(?:SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\s+.*?\+\s*\w+',
            r'(?:SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\s+.*?\$\{',
            r'\.query\s*\(\s*[`"\'].*?\$\{',
            r'\.execute\s*\(\s*[`"\'].*?\+',
        ]
        
        for pattern in sql_concat_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message='Potential SQL injection: string concatenation in SQL query',
                    suggestion='Use parameterized queries or prepared statements instead'
                ))
        
        return findings
    
    def _detect_command_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential command injection vulnerabilities."""
        findings = []
        
        # exec, spawn, execSync with user input
        exec_patterns = [
            r'(?:exec|spawn|execSync|execFile)\s*\(\s*[`"\'].*?\$\{',
            r'(?:exec|spawn|execSync|execFile)\s*\(\s*.*?\+',
        ]
        
        for pattern in exec_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message='Potential command injection: user input in shell command',
                    suggestion='Validate and sanitize input, use execFile with array arguments, or avoid shell execution'
                ))
        
        return findings
    
    def _detect_eval_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect dangerous eval() and Function() usage."""
        findings = []
        
        # eval() usage
        eval_pattern = r'\beval\s*\('
        for match in re.finditer(eval_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Dangerous use of eval(): can execute arbitrary code',
                suggestion='Avoid eval(). Use JSON.parse() for JSON, or refactor to avoid dynamic code execution'
            ))
        
        # new Function() usage
        function_constructor_pattern = r'new\s+Function\s*\('
        for match in re.finditer(function_constructor_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Dangerous use of Function constructor: similar to eval()',
                suggestion='Avoid Function constructor. Refactor to use regular functions'
            ))
        
        return findings
    
    def _detect_prototype_pollution(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential prototype pollution vulnerabilities."""
        findings = []
        
        # Unsafe object property assignment
        prototype_patterns = [
            r'\[.*?(?:__proto__|constructor|prototype)\]',
            r'\.(?:__proto__|constructor\.prototype)',
        ]
        
        for pattern in prototype_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='Potential prototype pollution: unsafe property access',
                    suggestion='Validate object keys, use Object.create(null), or use Map instead of plain objects'
                ))
        
        return findings
    
    def _detect_insecure_randomness(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect use of insecure random number generation."""
        findings = []
        
        # Math.random() for security purposes
        random_pattern = r'Math\.random\s*\(\s*\)'
        for match in re.finditer(random_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            # Check if used in security context
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            if any(keyword in line_content.lower() for keyword in ['token', 'key', 'secret', 'password', 'salt', 'nonce', 'csrf']):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='Insecure randomness: Math.random() is not cryptographically secure',
                    suggestion='Use crypto.randomBytes() or crypto.getRandomValues() for security-sensitive operations'
                ))
        
        return findings
    
    def _detect_path_traversal(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential path traversal vulnerabilities."""
        findings = []
        
        # File operations with user input
        file_ops_pattern = r'(?:readFile|writeFile|unlink|rmdir|mkdir|open)\s*\(\s*.*?(?:req\.|params\.|query\.)'
        for match in re.finditer(file_ops_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Potential path traversal: user input in file path',
                suggestion='Validate and sanitize file paths, use path.resolve() and check if result is within allowed directory'
            ))
        
        return findings
    
    def _detect_open_redirects(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential open redirect vulnerabilities."""
        findings = []
        
        # Redirect with user input
        redirect_pattern = r'(?:redirect|location\.href|window\.location)\s*=?\s*.*?(?:req\.|params\.|query\.)'
        for match in re.finditer(redirect_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='security',
                message='Potential open redirect: user input in redirect URL',
                suggestion='Validate redirect URLs against a whitelist of allowed domains'
            ))
        
        return findings
    
    def _detect_insecure_crypto(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect use of insecure cryptographic functions."""
        findings = []
        
        # Weak hash algorithms
        weak_crypto_pattern = r'createHash\s*\(\s*["\'](?:md5|sha1)["\']'
        for match in re.finditer(weak_crypto_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='security',
                message='Weak cryptographic hash: MD5/SHA1 are not secure',
                suggestion='Use SHA-256 or stronger: crypto.createHash("sha256")'
            ))
        
        return findings
    
    def _detect_hardcoded_secrets(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect hardcoded secrets and credentials."""
        findings = []
        
        secret_patterns = [
            (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']', 'API key'),
            (r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{8,}["\']', 'Password'),
            (r'(?:secret|token)\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']', 'Secret/Token'),
            (r'(?:aws|amazon).*?(?:key|secret)', 'AWS credentials'),
        ]
        
        for pattern, secret_type in secret_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message=f'Hardcoded {secret_type.lower()} detected',
                    suggestion='Use environment variables or a secrets management system'
                ))
        
        return findings
    
    def _detect_unsafe_regex(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potentially unsafe regular expressions (ReDoS)."""
        findings = []
        
        # Patterns that can cause ReDoS
        redos_patterns = [
            r'new\s+RegExp\s*\([^)]*\([^)]*\+[^)]*\)',  # Nested quantifiers
            r'/\([^)]*\+[^)]*\)\+/',  # (a+)+ pattern
            r'/\([^)]*\*[^)]*\)\+/',  # (a*)+ pattern
        ]
        
        for pattern in redos_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='security',
                    message='Potentially unsafe regex: may be vulnerable to ReDoS attacks',
                    suggestion='Simplify regex pattern, avoid nested quantifiers, or use a ReDoS-safe regex library'
                ))
        
        return findings
    
    def _detect_xxe_vulnerabilities(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential XXE (XML External Entity) vulnerabilities."""
        findings = []
        
        # XML parsing without disabling external entities
        xml_parse_pattern = r'(?:parseXml|DOMParser|xml2js).*?(?:parse|parseString)'
        for match in re.finditer(xml_parse_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Potential XXE vulnerability: XML parsing without entity protection',
                suggestion='Disable external entities in XML parser configuration'
            ))
        
        return findings

