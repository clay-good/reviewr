"""
Enterprise Policy Enforcement Engine for reviewr.

This module provides centralized policy management and enforcement for enterprise
environments, including pre-commit hooks, PR/MR approval workflows, and compliance
reporting.
"""

from .engine import PolicyEngine, PolicyViolation, PolicyResult
from .rules import (
    PolicyRule,
    RuleViolation,
    SeverityRule,
    FilePatternRule,
    ComplexityRule,
    SecurityRule,
    LicenseRule,
    CoverageRule,
    CustomRule
)
from .schema import (
    Policy,
    PolicyConfig,
    PolicyScope,
    PolicyAction,
    PolicyEnforcement,
    ApprovalRequirement,
    ENTERPRISE_POLICIES
)
from .manager import PolicyManager
from .enforcer import PolicyEnforcer

__all__ = [
    # Core
    'PolicyEngine',
    'PolicyViolation',
    'PolicyResult',
    'PolicyManager',
    'PolicyEnforcer',

    # Rules
    'PolicyRule',
    'RuleViolation',
    'SeverityRule',
    'FilePatternRule',
    'ComplexityRule',
    'SecurityRule',
    'LicenseRule',
    'CoverageRule',
    'CustomRule',

    # Schema
    'Policy',
    'PolicyConfig',
    'PolicyScope',
    'PolicyAction',
    'PolicyEnforcement',
    'ApprovalRequirement',
    'ENTERPRISE_POLICIES',
]

