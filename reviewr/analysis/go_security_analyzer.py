"""
Go Security Analyzer

Detects security vulnerabilities in Go code including:
- SQL injection
- Command injection
- Path traversal
- Unsafe cryptography
- Race conditions
- Hardcoded secrets
- Unsafe deserialization
- SSRF vulnerabilities
- XML external entity (XXE)
- Insecure random number generation
- Unsafe reflection
- Directory traversal
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class GoSecurityAnalyzer(LocalAnalyzer):
    """Analyzes Go code for security vulnerabilities."""

    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'go'

    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Go code for security issues.
        
        Args:
            file_path: Path to the Go file
            content: File content
            
        Returns:
            List of security findings
        """
        findings = []
        lines = content.split('\n')
        
        # Run all security checks
        findings.extend(self._detect_sql_injection(content, file_path, lines))
        findings.extend(self._detect_command_injection(content, file_path, lines))
        findings.extend(self._detect_path_traversal(content, file_path, lines))
        findings.extend(self._detect_weak_crypto(content, file_path, lines))
        findings.extend(self._detect_race_conditions(content, file_path, lines))
        findings.extend(self._detect_hardcoded_secrets(content, file_path, lines))
        findings.extend(self._detect_unsafe_deserialization(content, file_path, lines))
        findings.extend(self._detect_ssrf(content, file_path, lines))
        findings.extend(self._detect_xxe(content, file_path, lines))
        findings.extend(self._detect_insecure_random(content, file_path, lines))
        findings.extend(self._detect_unsafe_reflection(content, file_path, lines))
        findings.extend(self._detect_tls_issues(content, file_path, lines))
        
        return findings
    
    def _detect_sql_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect SQL injection vulnerabilities."""
        findings = []
        
        # String concatenation or formatting in SQL queries
        sql_concat_patterns = [
            (r'(Query|Exec|QueryRow)\s*\([^)]*\+\s*\w+', 'String concatenation in SQL query'),
            (r'(Query|Exec|QueryRow)\s*\([^)]*fmt\.Sprintf', 'fmt.Sprintf in SQL query'),
            (r'(Query|Exec|QueryRow)\s*\([^)]*fmt\.Sprint', 'fmt.Sprint in SQL query'),
            (r'"(?:SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)[^"]*"\s*\+', 'SQL query with string concatenation'),
        ]
        
        for pattern, message in sql_concat_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message=f'Potential SQL injection: {message}',
                    suggestion='Use parameterized queries with placeholders: db.Query("SELECT * FROM users WHERE id = $1", userID)',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_command_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect command injection vulnerabilities."""
        findings = []
        
        # exec.Command with string concatenation or user input
        cmd_patterns = [
            (r'exec\.Command\s*\([^)]*\+\s*\w+', 'String concatenation in exec.Command'),
            (r'exec\.Command\s*\([^)]*fmt\.Sprintf', 'fmt.Sprintf in exec.Command'),
            (r'exec\.CommandContext\s*\([^)]*\+\s*\w+', 'String concatenation in exec.CommandContext'),
            (r'syscall\.Exec\s*\([^)]*\+\s*\w+', 'String concatenation in syscall.Exec'),
        ]
        
        for pattern, message in cmd_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message=f'Potential command injection: {message}',
                    suggestion='Pass arguments as separate parameters: exec.Command("git", "clone", userRepo)',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_path_traversal(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect path traversal vulnerabilities."""
        findings = []
        
        # File operations with user input without validation
        file_patterns = [
            (r'os\.Open\s*\([^)]*\+\s*\w+', 'os.Open with string concatenation'),
            (r'ioutil\.ReadFile\s*\([^)]*\+\s*\w+', 'ioutil.ReadFile with string concatenation'),
            (r'os\.ReadFile\s*\([^)]*\+\s*\w+', 'os.ReadFile with string concatenation'),
            (r'filepath\.Join\s*\([^)]*\w+\s*\)', 'filepath.Join without path validation'),
        ]
        
        for pattern, message in file_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                # Check if filepath.Clean is used nearby
                context_start = max(0, match.start() - 200)
                context_end = min(len(content), match.end() + 200)
                context = content[context_start:context_end]
                
                if 'filepath.Clean' not in context and 'path.Clean' not in context:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='high',
                        category='security',
                        message=f'Potential path traversal: {message}',
                        suggestion='Validate and sanitize file paths: filepath.Clean(filepath.Join(baseDir, userPath))',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_weak_crypto(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect weak cryptography usage."""
        findings = []
        
        # Weak hash algorithms
        weak_hash_patterns = [
            (r'md5\.New\s*\(', 'MD5 is cryptographically broken', 'Use SHA-256 or SHA-3: sha256.New()'),
            (r'sha1\.New\s*\(', 'SHA-1 is cryptographically weak', 'Use SHA-256 or SHA-3: sha256.New()'),
            (r'crypto/des', 'DES is insecure', 'Use AES: aes.NewCipher()'),
            (r'crypto/rc4', 'RC4 is insecure', 'Use AES-GCM or ChaCha20-Poly1305'),
        ]
        
        for pattern, message, suggestion in weak_hash_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message=f'Weak cryptography: {message}',
                    suggestion=suggestion,
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_race_conditions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential race conditions."""
        findings = []
        
        # Shared variable access without synchronization
        # Look for global variables accessed in goroutines
        global_var_pattern = r'var\s+(\w+)\s+(?:int|string|bool|map|slice|\[\])'
        goroutine_pattern = r'go\s+(?:func\s*\(|(\w+)\()'
        
        global_vars = set(re.findall(global_var_pattern, content))
        
        for match in re.finditer(goroutine_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            # Check if goroutine accesses global variables
            goroutine_start = match.start()
            # Find the end of the goroutine (simplified)
            goroutine_end = min(len(content), goroutine_start + 500)
            goroutine_code = content[goroutine_start:goroutine_end]
            
            # Check for mutex usage
            has_mutex = 'sync.Mutex' in goroutine_code or 'sync.RWMutex' in goroutine_code or '.Lock()' in goroutine_code
            
            if not has_mutex:
                for var in global_vars:
                    if re.search(rf'\b{var}\b', goroutine_code):
                        findings.append(LocalFinding(
                            file_path=file_path,
                            line_start=line_num,
                            line_end=line_num,
                            severity='high',
                            category='security',
                            message=f'Potential race condition: goroutine accesses shared variable "{var}" without synchronization',
                            suggestion='Use sync.Mutex or sync.RWMutex to protect shared data, or use channels for communication',
                            code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                        ))
                        break  # Only report once per goroutine
        
        return findings
    
    def _detect_hardcoded_secrets(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect hardcoded secrets."""
        findings = []
        
        # Common secret patterns
        secret_patterns = [
            (r'(?:password|passwd|pwd)\s*[:=]\s*["\'](?!.*\$\{)([^"\']{8,})["\']', 'Hardcoded password'),
            (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Hardcoded API key'),
            (r'(?:secret[_-]?key|secretkey)\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Hardcoded secret key'),
            (r'(?:access[_-]?token|accesstoken)\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Hardcoded access token'),
            (r'(?:private[_-]?key|privatekey)\s*[:=]\s*["\']([^"\']{20,})["\']', 'Hardcoded private key'),
        ]
        
        for pattern, message in secret_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='security',
                    message=f'{message} detected',
                    suggestion='Use environment variables: os.Getenv("API_KEY") or a secrets management service',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_unsafe_deserialization(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unsafe deserialization."""
        findings = []
        
        # gob.Decode without validation
        if 'gob.Decode' in content or 'gob.NewDecoder' in content:
            for match in re.finditer(r'gob\.(?:Decode|NewDecoder)', content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='security',
                    message='Unsafe deserialization: gob.Decode can execute arbitrary code',
                    suggestion='Validate input before deserialization and use JSON for untrusted data',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_ssrf(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect SSRF vulnerabilities."""
        findings = []
        
        # HTTP requests with user-controlled URLs
        http_patterns = [
            r'http\.Get\s*\([^)]*\+\s*\w+',
            r'http\.Post\s*\([^)]*\+\s*\w+',
            r'http\.NewRequest\s*\([^)]*\+\s*\w+',
        ]
        
        for pattern in http_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='Potential SSRF: HTTP request with user-controlled URL',
                    suggestion='Validate and whitelist URLs before making requests',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_xxe(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect XXE vulnerabilities."""
        findings = []
        
        # XML parsing without disabling external entities
        if 'xml.Unmarshal' in content or 'xml.NewDecoder' in content:
            for match in re.finditer(r'xml\.(?:Unmarshal|NewDecoder)', content):
                line_num = content[:match.start()].count('\n') + 1
                # Check if external entities are disabled
                context_start = max(0, match.start() - 300)
                context_end = min(len(content), match.end() + 300)
                context = content[context_start:context_end]
                
                if 'DisallowUnknownFields' not in context:
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='high',
                        category='security',
                        message='Potential XXE vulnerability: XML parsing without proper configuration',
                        suggestion='Use encoding/xml with DisallowUnknownFields or validate XML input',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_insecure_random(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect insecure random number generation."""
        findings = []
        
        # math/rand used for security purposes
        if 'math/rand' in content:
            for match in re.finditer(r'rand\.(?:Int|Intn|Float|Read)', content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='security',
                    message='Insecure random: math/rand is not cryptographically secure',
                    suggestion='Use crypto/rand for security-sensitive operations: crypto/rand.Read()',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_unsafe_reflection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unsafe reflection usage."""
        findings = []
        
        # reflect.ValueOf with user input
        if 'reflect.' in content:
            unsafe_reflect_patterns = [
                r'reflect\.ValueOf\s*\([^)]*\+\s*\w+',
                r'reflect\.Call\s*\(',
            ]
            
            for pattern in unsafe_reflect_patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='medium',
                        category='security',
                        message='Unsafe reflection: Can lead to arbitrary code execution',
                        suggestion='Avoid reflection with user input or validate types strictly',
                        code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_tls_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect TLS/SSL configuration issues."""
        findings = []
        
        # InsecureSkipVerify
        if 'InsecureSkipVerify' in content:
            for match in re.finditer(r'InsecureSkipVerify\s*:\s*true', content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='Insecure TLS: InsecureSkipVerify disables certificate validation',
                    suggestion='Remove InsecureSkipVerify or use proper certificate validation',
                    code_snippet=lines[line_num - 1].strip() if line_num <= len(lines) else ''
                ))
        
        return findings

