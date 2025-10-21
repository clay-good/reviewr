"""
Tests for security module.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from reviewr.security.vulnerability_scanner import (
    VulnerabilityScanner,
    Vulnerability,
    VulnerabilitySeverity
)
from reviewr.security.dependency_checker import (
    DependencyChecker,
    Dependency,
    DependencyHealth
)
from reviewr.security.license_checker import (
    LicenseChecker,
    License,
    LicenseCategory,
    LicensePolicy,
    LicenseRisk
)
from reviewr.security.sast_engine import (
    SASTEngine,
    SASTRule,
    CWEMapping,
    OWASPCategory
)


class TestVulnerabilityScanner:
    """Test vulnerability scanner."""
    
    def test_init(self):
        """Test scanner initialization."""
        scanner = VulnerabilityScanner()
        assert scanner.cache_dir.exists()
    
    def test_parse_requirements_txt(self, tmp_path):
        """Test parsing requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
# Test requirements
requests==2.28.0
flask>=2.0.0
django==3.2.0
""")
        
        scanner = VulnerabilityScanner()
        deps = scanner._parse_requirements_txt(req_file)
        
        assert "requests" in deps
        assert deps["requests"] == "2.28.0"
        assert "flask" in deps
        assert "django" in deps
    
    def test_parse_package_json(self, tmp_path):
        """Test parsing package.json."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text("""
{
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "~4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
""")
        
        scanner = VulnerabilityScanner()
        deps = scanner._parse_package_json(pkg_file)
        
        assert "express" in deps
        assert deps["express"] == "4.18.0"
        assert "lodash" in deps
        assert "jest" in deps
    
    def test_parse_go_mod(self, tmp_path):
        """Test parsing go.mod."""
        go_file = tmp_path / "go.mod"
        go_file.write_text("""
module example.com/myapp

go 1.19

require (
    github.com/gin-gonic/gin v1.8.1
    github.com/stretchr/testify v1.8.0
)
""")
        
        scanner = VulnerabilityScanner()
        deps = scanner._parse_go_mod(go_file)
        
        assert "github.com/gin-gonic/gin" in deps
        assert deps["github.com/gin-gonic/gin"] == "1.8.1"
    
    def test_parse_cargo_toml(self, tmp_path):
        """Test parsing Cargo.toml."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "myapp"
version = "0.1.0"

[dependencies]
serde = "1.0.0"
tokio = { version = "1.20.0", features = ["full"] }
""")
        
        scanner = VulnerabilityScanner()
        deps = scanner._parse_cargo_toml(cargo_file)
        
        assert "serde" in deps
        assert deps["serde"] == "1.0.0"
        assert "tokio" in deps
    
    def test_vulnerability_properties(self):
        """Test vulnerability properties."""
        vuln = Vulnerability(
            id="CVE-2023-1234",
            package="test-package",
            version="1.0.0",
            severity=VulnerabilitySeverity.CRITICAL,
            summary="Test vulnerability",
            details="Details",
            fixed_versions=["1.0.1", "1.1.0"]
        )
        
        assert vuln.is_critical
        assert not vuln.is_high
        assert vuln.has_fix
        assert "1.0.1" in vuln.get_remediation()


class TestDependencyChecker:
    """Test dependency checker."""
    
    def test_init(self):
        """Test checker initialization."""
        checker = DependencyChecker()
        assert len(checker.dependencies) == 0
    
    def test_analyze_requirements_txt(self, tmp_path):
        """Test analyzing requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
requests==2.28.0
flask==2.0.0
""")
        
        checker = DependencyChecker()
        deps = checker.analyze_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].ecosystem == "PyPI"
        assert deps[0].is_direct
    
    def test_analyze_package_json(self, tmp_path):
        """Test analyzing package.json."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text("""
{
  "dependencies": {
    "express": "4.18.0"
  }
}
""")
        
        checker = DependencyChecker()
        deps = checker.analyze_package_json(pkg_file)
        
        assert len(deps) == 1
        assert deps[0].name == "express"
        assert deps[0].ecosystem == "npm"
    
    def test_dependency_properties(self):
        """Test dependency properties."""
        dep = Dependency(
            name="test-package",
            version="1.0.0",
            ecosystem="PyPI",
            health=DependencyHealth.OUTDATED,
            latest_version="2.0.0"
        )
        
        assert dep.is_outdated
        assert not dep.is_unmaintained
        assert dep.version_lag == "1.0.0 → 2.0.0"
    
    def test_get_dependency_summary(self):
        """Test dependency summary."""
        checker = DependencyChecker()
        checker.dependencies = {
            "pkg1": Dependency("pkg1", "1.0.0", "PyPI", health=DependencyHealth.HEALTHY),
            "pkg2": Dependency("pkg2", "1.0.0", "PyPI", health=DependencyHealth.OUTDATED),
        }
        
        summary = checker.get_dependency_summary()
        
        assert summary["total_dependencies"] == 2
        assert summary["outdated"] == 1
        assert "health_score" in summary


class TestLicenseChecker:
    """Test license checker."""
    
    def test_init(self):
        """Test checker initialization."""
        checker = LicenseChecker()
        assert checker.policy is not None
    
    def test_identify_mit_license(self):
        """Test MIT license identification."""
        checker = LicenseChecker()
        license_text = """
MIT License

Copyright (c) 2023 Test

Permission is hereby granted...
"""
        
        license = checker.identify_license(license_text)
        
        assert license is not None
        assert license.spdx_id == "MIT"
        assert license.is_permissive
    
    def test_identify_gpl_license(self):
        """Test GPL license identification."""
        checker = LicenseChecker()
        license_text = """
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
"""
        
        license = checker.identify_license(license_text)
        
        assert license is not None
        assert license.spdx_id == "GPL-3.0"
        assert license.is_copyleft
    
    def test_license_properties(self):
        """Test license properties."""
        license = License(
            spdx_id="MIT",
            name="MIT License",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True
        )
        
        assert license.is_permissive
        assert not license.is_copyleft
        assert license.is_compatible_with_proprietary
    
    def test_permissive_policy(self):
        """Test permissive license policy."""
        policy = LicenseChecker.PERMISSIVE_POLICY
        
        mit_license = LicenseChecker.KNOWN_LICENSES["MIT"]
        gpl_license = LicenseChecker.KNOWN_LICENSES["GPL-3.0"]
        
        assert policy.is_license_allowed(mit_license)
        assert not policy.is_license_allowed(gpl_license)
    
    def test_check_compliance(self):
        """Test license compliance checking."""
        checker = LicenseChecker(LicenseChecker.PERMISSIVE_POLICY)
        
        licenses = [
            LicenseChecker.KNOWN_LICENSES["MIT"],
            LicenseChecker.KNOWN_LICENSES["Apache-2.0"],
            LicenseChecker.KNOWN_LICENSES["GPL-3.0"]
        ]
        
        report = checker.check_compliance(licenses)
        
        assert not report["compliant"]
        assert len(report["violations"]) > 0
        assert report["total_licenses"] == 3


class TestSASTEngine:
    """Test SAST engine."""
    
    def test_init(self):
        """Test engine initialization."""
        engine = SASTEngine()
        assert len(engine.rules) > 0
    
    def test_sql_injection_detection(self):
        """Test SQL injection detection."""
        engine = SASTEngine()
        
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
'''
        
        findings = engine.scan_code(code, "python")
        
        assert len(findings) > 0
        assert any("SQL" in f["rule_name"] for f in findings)
        assert any(f["severity"] == "critical" for f in findings)
    
    def test_xss_detection(self):
        """Test XSS detection."""
        engine = SASTEngine()
        
        code = '''
function displayMessage(msg) {
    document.getElementById("output").innerHTML = msg;
}
'''
        
        findings = engine.scan_code(code, "javascript")
        
        assert len(findings) > 0
        assert any("XSS" in f["rule_name"] for f in findings)
    
    def test_command_injection_detection(self):
        """Test command injection detection."""
        engine = SASTEngine()
        
        code = '''
import os
def run_command(cmd):
    os.system("ls " + cmd)
'''
        
        findings = engine.scan_code(code, "python")
        
        assert len(findings) > 0
        assert any("Command" in f["rule_name"] for f in findings)
    
    def test_hardcoded_credentials_detection(self):
        """Test hard-coded credentials detection."""
        engine = SASTEngine()
        
        code = '''
api_key = "sk-1234567890abcdef"
password = "MySecretPassword123"
'''
        
        findings = engine.scan_code(code, "python")
        
        assert len(findings) > 0
        assert any("Credential" in f["rule_name"] for f in findings)
    
    def test_weak_crypto_detection(self):
        """Test weak cryptography detection."""
        engine = SASTEngine()
        
        code = '''
import hashlib
hash = hashlib.md5(data)
'''
        
        findings = engine.scan_code(code, "python")
        
        assert len(findings) > 0
        assert any("Crypto" in f["rule_name"] for f in findings)
    
    def test_cwe_mapping(self):
        """Test CWE mapping."""
        engine = SASTEngine()
        
        code = '''
cursor.execute("SELECT * FROM users WHERE id = " + user_id)
'''
        
        findings = engine.scan_code(code, "python")
        
        assert len(findings) > 0
        finding = findings[0]
        assert "cwe_id" in finding
        assert "CWE-" in finding["cwe_id"]
        assert "cwe_url" in finding
    
    def test_owasp_coverage(self):
        """Test OWASP Top 10 coverage."""
        engine = SASTEngine()
        coverage = engine.get_owasp_coverage()
        
        assert len(coverage) > 0
        assert any("Injection" in cat for cat in coverage.keys())
    
    def test_custom_rule(self):
        """Test adding custom rule."""
        engine = SASTEngine()
        
        custom_cwe = CWEMapping(
            cwe_id="CWE-999",
            name="Custom Weakness",
            description="Test weakness",
            severity="medium"
        )
        
        custom_rule = SASTRule(
            id="CUSTOM-001",
            name="Custom Rule",
            description="Test rule",
            cwe_mapping=custom_cwe,
            severity="medium",
            pattern=r"dangerous_function\(",
            languages=["python"],
            fix_guidance="Don't use dangerous_function"
        )
        
        initial_count = len(engine.rules)
        engine.add_custom_rule(custom_rule)
        
        assert len(engine.rules) == initial_count + 1
    
    def test_get_rules_by_severity(self):
        """Test getting rules by severity."""
        engine = SASTEngine()
        critical_rules = engine.get_rules_by_severity("critical")
        
        assert len(critical_rules) > 0
        assert all(rule.severity == "critical" for rule in critical_rules)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

