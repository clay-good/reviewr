"""
Java Security Analyzer

Detects security vulnerabilities in Java code including SQL injection, XXE,
deserialization attacks, SSRF, path traversal, and cryptographic issues.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaSecurityAnalyzer(LocalAnalyzer):
    """Analyzes Java code for security vulnerabilities."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'java'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Java code for security issues.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_sql_injection(content, file_path, lines))
        findings.extend(self._detect_xxe_vulnerabilities(content, file_path, lines))
        findings.extend(self._detect_deserialization(content, file_path, lines))
        findings.extend(self._detect_path_traversal(content, file_path, lines))
        findings.extend(self._detect_ssrf(content, file_path, lines))
        findings.extend(self._detect_crypto_issues(content, file_path, lines))
        findings.extend(self._detect_command_injection(content, file_path, lines))
        findings.extend(self._detect_ldap_injection(content, file_path, lines))
        findings.extend(self._detect_xpath_injection(content, file_path, lines))
        findings.extend(self._detect_insecure_random(content, file_path, lines))
        findings.extend(self._detect_hardcoded_secrets(content, file_path, lines))
        
        return findings
    
    def _detect_sql_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect SQL injection vulnerabilities."""
        findings = []
        
        # String concatenation in SQL queries
        pattern = r'(Statement|createStatement|executeQuery|executeUpdate|execute)\s*\([^)]*\+[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Potential SQL injection: String concatenation in SQL query',
                suggestion='Use PreparedStatement with parameterized queries instead',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Direct string formatting in queries
        pattern = r'(executeQuery|executeUpdate|execute)\s*\(\s*String\.format\s*\('
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Potential SQL injection: String.format() in SQL query',
                suggestion='Use PreparedStatement with ? placeholders',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_xxe_vulnerabilities(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect XML External Entity (XXE) vulnerabilities."""
        findings = []
        
        # DocumentBuilderFactory without secure processing
        pattern = r'DocumentBuilderFactory\.newInstance\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if secure features are set nearby
            context_start = max(0, match.start() - 500)
            context_end = min(len(content), match.end() + 500)
            context = content[context_start:context_end]
            
            has_secure_processing = 'setFeature' in context and 'XMLConstants.FEATURE_SECURE_PROCESSING' in context
            
            if not has_secure_processing:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='XXE vulnerability: DocumentBuilderFactory without secure processing',
                    suggestion='Set factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true) and disable external entities',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # SAXParserFactory without secure processing
        pattern = r'SAXParserFactory\.newInstance\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            context_start = max(0, match.start() - 500)
            context_end = min(len(content), match.end() + 500)
            context = content[context_start:context_end]
            
            has_secure_processing = 'setFeature' in context and 'disallow-doctype-decl' in context
            
            if not has_secure_processing:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='XXE vulnerability: SAXParserFactory without secure processing',
                    suggestion='Disable external entities and DTDs',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_deserialization(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect insecure deserialization."""
        findings = []
        
        # ObjectInputStream.readObject() without validation
        pattern = r'ObjectInputStream\s*\([^)]*\)\.readObject\(\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Insecure deserialization: readObject() without validation',
                suggestion='Validate object types before deserialization or use safer alternatives like JSON',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # XMLDecoder usage
        pattern = r'new\s+XMLDecoder\s*\('
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Insecure deserialization: XMLDecoder can execute arbitrary code',
                suggestion='Avoid XMLDecoder or use with extreme caution and input validation',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_path_traversal(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect path traversal vulnerabilities."""
        findings = []
        
        # File operations with user input
        pattern = r'new\s+File\s*\([^)]*request\.getParameter[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Path traversal: File path from user input without validation',
                suggestion='Validate and sanitize file paths, use whitelist of allowed paths',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # FileInputStream with user input
        pattern = r'new\s+FileInputStream\s*\([^)]*request\.'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Path traversal: FileInputStream with user-controlled path',
                suggestion='Validate file paths against whitelist before opening',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_ssrf(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect Server-Side Request Forgery (SSRF) vulnerabilities."""
        findings = []
        
        # URL connections with user input
        pattern = r'new\s+URL\s*\([^)]*request\.getParameter[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='SSRF: URL constructed from user input',
                suggestion='Validate URLs against whitelist of allowed domains',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # HttpClient with user input
        pattern = r'HttpClient.*\.execute\s*\([^)]*request\.'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='SSRF: HTTP request with user-controlled URL',
                suggestion='Implement URL validation and whitelist allowed destinations',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_crypto_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect cryptographic issues."""
        findings = []
        
        # Weak algorithms
        weak_algos = ['MD5', 'SHA1', 'DES', 'RC4']
        
        for algo in weak_algos:
            pattern = rf'MessageDigest\.getInstance\s*\(\s*["\']({algo})["\']'
            
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message=f'Weak cryptographic algorithm: {algo}',
                    suggestion='Use SHA-256 or stronger algorithms',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # Insecure SSL/TLS
        pattern = r'SSLContext\.getInstance\s*\(\s*["\']SSL["\']'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Insecure SSL/TLS: Using deprecated SSL protocol',
                suggestion='Use TLSv1.2 or TLSv1.3 instead',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_command_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect command injection vulnerabilities."""
        findings = []
        
        # Runtime.exec with string concatenation
        pattern = r'Runtime\.getRuntime\(\)\.exec\s*\([^)]*\+[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Command injection: Runtime.exec() with string concatenation',
                suggestion='Use ProcessBuilder with array of arguments, validate all inputs',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_ldap_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect LDAP injection vulnerabilities."""
        findings = []
        
        # LDAP search with string concatenation
        pattern = r'search\s*\([^)]*\+[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            if 'ldap' in line_content.lower() or 'DirContext' in content[max(0, match.start()-200):match.end()]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='LDAP injection: Search filter with string concatenation',
                    suggestion='Use parameterized LDAP queries and escape special characters',
                    code_snippet=line_content
                ))
        
        return findings
    
    def _detect_xpath_injection(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect XPath injection vulnerabilities."""
        findings = []
        
        # XPath with string concatenation
        pattern = r'(compile|evaluate)\s*\([^)]*\+[^)]*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            if 'xpath' in line_content.lower() or 'XPath' in content[max(0, match.start()-200):match.end()]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='security',
                    message='XPath injection: XPath expression with string concatenation',
                    suggestion='Use parameterized XPath queries',
                    code_snippet=line_content
                ))
        
        return findings
    
    def _detect_insecure_random(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect insecure random number generation."""
        findings = []
        
        # java.util.Random for security purposes
        pattern = r'new\s+Random\s*\('
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check context for security-related usage
            context = content[max(0, match.start()-300):min(len(content), match.end()+300)]
            security_keywords = ['token', 'password', 'key', 'secret', 'session', 'crypto']
            
            if any(keyword in context.lower() for keyword in security_keywords):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='security',
                    message='Insecure random: java.util.Random for security-sensitive operation',
                    suggestion='Use SecureRandom for cryptographic operations',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_hardcoded_secrets(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect hardcoded secrets and credentials."""
        findings = []
        
        # Hardcoded passwords
        pattern = r'(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='security',
                message='Hardcoded password detected',
                suggestion='Use environment variables or secure configuration management',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # API keys
        pattern = r'(api[_-]?key|apikey|access[_-]?key)\s*=\s*["\'][A-Za-z0-9]{20,}["\']'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='security',
                message='Hardcoded API key detected',
                suggestion='Use environment variables or secrets management service',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings

