"""
Advanced security scanning module.

Provides:
- Dependency vulnerability scanning
- SAST rule engine
- CWE/CVE mapping
- License compliance checking
- Security policy enforcement
"""

from .vulnerability_scanner import VulnerabilityScanner, Vulnerability
from .dependency_checker import DependencyChecker, Dependency
from .license_checker import LicenseChecker, License, LicensePolicy
from .sast_engine import SASTEngine, SASTRule, CWEMapping

__all__ = [
    'VulnerabilityScanner',
    'Vulnerability',
    'DependencyChecker',
    'Dependency',
    'LicenseChecker',
    'License',
    'LicensePolicy',
    'SASTEngine',
    'SASTRule',
    'CWEMapping',
]

