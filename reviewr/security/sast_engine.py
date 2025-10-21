"""
SAST (Static Application Security Testing) rule engine.

Provides:
- Security rule definitions
- CWE (Common Weakness Enumeration) mapping
- OWASP Top 10 coverage
- Pattern-based vulnerability detection
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Callable
from pathlib import Path
from enum import Enum


class OWASPCategory(Enum):
    """OWASP Top 10 categories."""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021 - Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_DATA_INTEGRITY_FAILURES = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"


@dataclass
class CWEMapping:
    """CWE (Common Weakness Enumeration) mapping."""
    cwe_id: str
    name: str
    description: str
    owasp_category: Optional[OWASPCategory] = None
    severity: str = "medium"
    
    @property
    def cwe_url(self) -> str:
        """Get CWE reference URL."""
        cwe_num = self.cwe_id.replace("CWE-", "")
        return f"https://cwe.mitre.org/data/definitions/{cwe_num}.html"


@dataclass
class SASTRule:
    """A SAST security rule."""
    id: str
    name: str
    description: str
    cwe_mapping: CWEMapping
    severity: str
    pattern: str
    languages: List[str]
    fix_guidance: str
    examples: List[str] = field(default_factory=list)
    
    def matches(self, code: str, language: str) -> bool:
        """Check if rule matches code."""
        if language not in self.languages:
            return False
        
        return bool(re.search(self.pattern, code, re.MULTILINE | re.IGNORECASE))
    
    def find_matches(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Find all matches in code."""
        if language not in self.languages:
            return []
        
        matches = []
        for match in re.finditer(self.pattern, code, re.MULTILINE | re.IGNORECASE):
            # Calculate line number
            line_num = code[:match.start()].count('\n') + 1
            
            matches.append({
                "line": line_num,
                "match": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        
        return matches


class SASTEngine:
    """SAST rule engine for security analysis."""
    
    # CWE Mappings
    CWE_MAPPINGS = {
        "CWE-89": CWEMapping(
            cwe_id="CWE-89",
            name="SQL Injection",
            description="Improper neutralization of special elements used in an SQL command",
            owasp_category=OWASPCategory.A03_INJECTION,
            severity="critical"
        ),
        "CWE-79": CWEMapping(
            cwe_id="CWE-79",
            name="Cross-site Scripting (XSS)",
            description="Improper neutralization of input during web page generation",
            owasp_category=OWASPCategory.A03_INJECTION,
            severity="high"
        ),
        "CWE-78": CWEMapping(
            cwe_id="CWE-78",
            name="OS Command Injection",
            description="Improper neutralization of special elements used in an OS command",
            owasp_category=OWASPCategory.A03_INJECTION,
            severity="critical"
        ),
        "CWE-22": CWEMapping(
            cwe_id="CWE-22",
            name="Path Traversal",
            description="Improper limitation of a pathname to a restricted directory",
            owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            severity="high"
        ),
        "CWE-798": CWEMapping(
            cwe_id="CWE-798",
            name="Hard-coded Credentials",
            description="Use of hard-coded credentials",
            owasp_category=OWASPCategory.A07_AUTH_FAILURES,
            severity="critical"
        ),
        "CWE-327": CWEMapping(
            cwe_id="CWE-327",
            name="Weak Cryptography",
            description="Use of a broken or risky cryptographic algorithm",
            owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
            severity="high"
        ),
        "CWE-502": CWEMapping(
            cwe_id="CWE-502",
            name="Deserialization of Untrusted Data",
            description="Deserialization of untrusted data",
            owasp_category=OWASPCategory.A08_DATA_INTEGRITY_FAILURES,
            severity="critical"
        ),
        "CWE-918": CWEMapping(
            cwe_id="CWE-918",
            name="Server-Side Request Forgery (SSRF)",
            description="Server-side request forgery",
            owasp_category=OWASPCategory.A10_SSRF,
            severity="high"
        ),
        "CWE-611": CWEMapping(
            cwe_id="CWE-611",
            name="XML External Entity (XXE)",
            description="Improper restriction of XML external entity reference",
            owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
            severity="high"
        ),
        "CWE-352": CWEMapping(
            cwe_id="CWE-352",
            name="Cross-Site Request Forgery (CSRF)",
            description="Cross-site request forgery",
            owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            severity="medium"
        ),
    }
    
    def __init__(self):
        """Initialize SAST engine."""
        self.rules: List[SASTRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default security rules."""
        
        # SQL Injection rules
        self.rules.append(SASTRule(
            id="SAST-001",
            name="SQL Injection via String Concatenation",
            description="SQL query constructed using string concatenation with user input",
            cwe_mapping=self.CWE_MAPPINGS["CWE-89"],
            severity="critical",
            pattern=r'(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*\+',
            languages=["python", "javascript", "typescript", "java", "php"],
            fix_guidance="Use parameterized queries or prepared statements instead of string concatenation",
            examples=[
                'cursor.execute("SELECT * FROM users WHERE id = " + user_id)',
                'query("SELECT * FROM products WHERE name = \'" + name + "\'")'
            ]
        ))

        # XSS rules
        self.rules.append(SASTRule(
            id="SAST-002",
            name="Cross-Site Scripting (XSS)",
            description="Unescaped user input rendered in HTML",
            cwe_mapping=self.CWE_MAPPINGS["CWE-79"],
            severity="high",
            pattern=r'(innerHTML|outerHTML|document\.write)\s*=',
            languages=["javascript", "typescript"],
            fix_guidance="Use textContent instead of innerHTML, or sanitize user input",
            examples=[
                'element.innerHTML = userInput',
                'document.write("<div>" + data + "</div>")'
            ]
        ))
        
        # Command Injection rules
        self.rules.append(SASTRule(
            id="SAST-003",
            name="OS Command Injection",
            description="OS command executed with user-controlled input",
            cwe_mapping=self.CWE_MAPPINGS["CWE-78"],
            severity="critical",
            pattern=r'(os\.system|subprocess\.call|exec|eval|shell_exec)\s*\(.*\+',
            languages=["python", "javascript", "typescript", "php"],
            fix_guidance="Avoid executing OS commands with user input. Use safe alternatives or validate input strictly",
            examples=[
                'os.system("ls " + user_path)',
                'exec("rm -rf " + directory)'
            ]
        ))
        
        # Path Traversal rules
        self.rules.append(SASTRule(
            id="SAST-004",
            name="Path Traversal",
            description="File path constructed with user input without validation",
            cwe_mapping=self.CWE_MAPPINGS["CWE-22"],
            severity="high",
            pattern=r'(open|read|readFile|File)\s*\(.*\+',
            languages=["python", "javascript", "typescript", "java"],
            fix_guidance="Validate and sanitize file paths. Use Path.resolve() and check if path is within allowed directory",
            examples=[
                'open("/var/data/" + filename)',
                'fs.readFile(basePath + userFile)'
            ]
        ))
        
        # Hard-coded credentials
        self.rules.append(SASTRule(
            id="SAST-005",
            name="Hard-coded Credentials",
            description="Hard-coded password or API key detected",
            cwe_mapping=self.CWE_MAPPINGS["CWE-798"],
            severity="critical",
            pattern=r'(password|passwd|pwd|api_key|apikey|secret|token)\s*=\s*["\'][^"\']{8,}["\']',
            languages=["python", "javascript", "typescript", "java", "go", "rust"],
            fix_guidance="Use environment variables or secure credential management systems",
            examples=[
                'password = "MySecretPassword123"',
                'api_key = "sk-1234567890abcdef"'
            ]
        ))
        
        # Weak cryptography
        self.rules.append(SASTRule(
            id="SAST-006",
            name="Weak Cryptographic Algorithm",
            description="Use of weak or deprecated cryptographic algorithm",
            cwe_mapping=self.CWE_MAPPINGS["CWE-327"],
            severity="high",
            pattern=r'(MD5|SHA1|DES|RC4|ECB)\s*\(',
            languages=["python", "javascript", "typescript", "java", "go"],
            fix_guidance="Use strong cryptographic algorithms like SHA-256, AES-256, or modern alternatives",
            examples=[
                'hashlib.md5(data)',
                'crypto.createHash("sha1")'
            ]
        ))
        
        # Insecure deserialization
        self.rules.append(SASTRule(
            id="SAST-007",
            name="Insecure Deserialization",
            description="Deserialization of untrusted data",
            cwe_mapping=self.CWE_MAPPINGS["CWE-502"],
            severity="critical",
            pattern=r'(pickle\.loads|yaml\.load|unserialize|ObjectInputStream)\s*\(',
            languages=["python", "java", "php"],
            fix_guidance="Avoid deserializing untrusted data. Use safe alternatives like JSON",
            examples=[
                'pickle.loads(user_data)',
                'yaml.load(untrusted_input)'
            ]
        ))
        
        # SSRF
        self.rules.append(SASTRule(
            id="SAST-008",
            name="Server-Side Request Forgery (SSRF)",
            description="HTTP request with user-controlled URL",
            cwe_mapping=self.CWE_MAPPINGS["CWE-918"],
            severity="high",
            pattern=r'(requests\.get|fetch|urllib\.request|http\.get)\s*\(.*\+',
            languages=["python", "javascript", "typescript"],
            fix_guidance="Validate and whitelist allowed URLs. Avoid using user input directly in URLs",
            examples=[
                'requests.get(user_url)',
                'fetch(baseUrl + userPath)'
            ]
        ))
        
        # XXE
        self.rules.append(SASTRule(
            id="SAST-009",
            name="XML External Entity (XXE)",
            description="XML parser configured to process external entities",
            cwe_mapping=self.CWE_MAPPINGS["CWE-611"],
            severity="high",
            pattern=r'(XMLParser|DocumentBuilder|SAXParser).*(?!.*setFeature.*disallow)',
            languages=["python", "java"],
            fix_guidance="Disable external entity processing in XML parsers",
            examples=[
                'parser = etree.XMLParser()',
                'DocumentBuilderFactory.newInstance()'
            ]
        ))
        
        # CSRF
        self.rules.append(SASTRule(
            id="SAST-010",
            name="Missing CSRF Protection",
            description="Form or state-changing endpoint without CSRF protection",
            cwe_mapping=self.CWE_MAPPINGS["CWE-352"],
            severity="medium",
            pattern=r'@(app\.route|post|put|delete).*(?!.*csrf)',
            languages=["python"],
            fix_guidance="Implement CSRF tokens for all state-changing operations",
            examples=[
                '@app.route("/transfer", methods=["POST"])'
            ]
        ))
    
    def scan_code(self, code: str, language: str, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Scan code for security vulnerabilities.
        
        Args:
            code: Source code to scan
            language: Programming language
            file_path: Optional file path for context
            
        Returns:
            List of findings
        """
        findings = []
        
        for rule in self.rules:
            matches = rule.find_matches(code, language)
            
            for match in matches:
                findings.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "cwe_id": rule.cwe_mapping.cwe_id,
                    "cwe_name": rule.cwe_mapping.name,
                    "cwe_url": rule.cwe_mapping.cwe_url,
                    "owasp_category": rule.cwe_mapping.owasp_category.value if rule.cwe_mapping.owasp_category else None,
                    "line": match["line"],
                    "match": match["match"],
                    "fix_guidance": rule.fix_guidance,
                    "file": str(file_path) if file_path else "unknown"
                })
        
        return findings
    
    def get_owasp_coverage(self) -> Dict[str, int]:
        """Get OWASP Top 10 coverage statistics."""
        coverage = {}
        
        for rule in self.rules:
            if rule.cwe_mapping.owasp_category:
                category = rule.cwe_mapping.owasp_category.value
                coverage[category] = coverage.get(category, 0) + 1
        
        return coverage
    
    def add_custom_rule(self, rule: SASTRule):
        """Add a custom security rule."""
        self.rules.append(rule)
    
    def get_rules_by_severity(self, severity: str) -> List[SASTRule]:
        """Get rules by severity level."""
        return [rule for rule in self.rules if rule.severity == severity]
    
    def get_rules_by_cwe(self, cwe_id: str) -> List[SASTRule]:
        """Get rules by CWE ID."""
        return [rule for rule in self.rules if rule.cwe_mapping.cwe_id == cwe_id]

