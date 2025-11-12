"""
Comprehensive tests for Enterprise Policy Enforcement Engine.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass

from reviewr.policy import (
    PolicyEngine,
    PolicyManager,
    PolicyEnforcer,
    Policy,
    PolicyConfig,
    PolicyScope,
    PolicyAction,
    PolicyEnforcement,
    ApprovalRequirement,
    SeverityRule,
    FilePatternRule,
    ComplexityRule,
    SecurityRule,
    RuleViolation
)


# Mock finding class for testing
@dataclass
class MockFinding:
    """Mock finding for testing."""
    file_path: str
    line_start: int
    severity: str
    category: str
    message: str
    metric_value: float = None


class TestPolicyEngine:
    """Test PolicyEngine core functionality."""
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = PolicyEngine()
        assert engine is not None
        assert len(engine.policies) == 0
        assert len(engine.rules) == 0
    
    def test_register_policy(self):
        """Test registering a policy."""
        engine = PolicyEngine()
        
        config = PolicyConfig(
            name="Test Policy",
            description="Test description",
            max_critical_issues=0
        )
        policy = Policy(id="test-policy", config=config)
        
        engine.register_policy(policy)
        assert "test-policy" in engine.policies
        assert engine.get_policy("test-policy") == policy
    
    def test_register_rule(self):
        """Test registering a rule."""
        engine = PolicyEngine()
        
        rule = SeverityRule(rule_id="test-rule", max_critical=0)
        engine.register_rule(rule)
        
        assert "test-rule" in engine.rules
    
    def test_evaluate_no_violations(self):
        """Test evaluation with no violations."""
        engine = PolicyEngine()
        
        # Register rule
        rule = SeverityRule(rule_id="severity-rule", max_critical=5)
        engine.register_rule(rule)
        
        # Register policy
        config = PolicyConfig(
            name="Test Policy",
            description="Test",
            scope=[PolicyScope.PRE_COMMIT]
        )
        policy = Policy(id="test-policy", config=config, rules=["severity-rule"])
        engine.register_policy(policy)
        
        # Evaluate with no findings
        context = {'findings': []}
        result = engine.evaluate(context, PolicyScope.PRE_COMMIT)
        
        assert result.passed is True
        assert len(result.violations) == 0
    
    def test_evaluate_with_violations(self):
        """Test evaluation with violations."""
        engine = PolicyEngine()
        
        # Register rule
        rule = SeverityRule(rule_id="severity-rule", max_critical=0)
        engine.register_rule(rule)
        
        # Register policy
        config = PolicyConfig(
            name="Test Policy",
            description="Test",
            scope=[PolicyScope.PRE_COMMIT],
            action=PolicyAction.BLOCK
        )
        policy = Policy(id="test-policy", config=config, rules=["severity-rule"])
        engine.register_policy(policy)
        
        # Evaluate with critical findings
        findings = [
            MockFinding(
                file_path="test.py",
                line_start=10,
                severity="critical",
                category="security",
                message="SQL injection"
            )
        ]
        context = {'findings': findings}
        result = engine.evaluate(context, PolicyScope.PRE_COMMIT)
        
        assert result.passed is False
        assert len(result.violations) > 0
        assert result.should_block is True
    
    def test_scope_filtering(self):
        """Test policies are filtered by scope."""
        engine = PolicyEngine()
        
        # Register rule
        rule = SeverityRule(rule_id="severity-rule", max_critical=0)
        engine.register_rule(rule)
        
        # Register policy for pre-commit only
        config = PolicyConfig(
            name="Pre-commit Policy",
            description="Test",
            scope=[PolicyScope.PRE_COMMIT]
        )
        policy = Policy(id="precommit-policy", config=config, rules=["severity-rule"])
        engine.register_policy(policy)
        
        # Evaluate in PR scope (should not apply)
        findings = [
            MockFinding(
                file_path="test.py",
                line_start=10,
                severity="critical",
                category="security",
                message="Issue"
            )
        ]
        context = {'findings': findings}
        result = engine.evaluate(context, PolicyScope.PULL_REQUEST)
        
        assert len(result.violations) == 0  # Policy doesn't apply to PR scope
    
    def test_branch_filtering(self):
        """Test policies are filtered by branch."""
        engine = PolicyEngine()
        
        # Register rule
        rule = SeverityRule(rule_id="severity-rule", max_critical=0)
        engine.register_rule(rule)
        
        # Register policy for main branch only
        config = PolicyConfig(
            name="Main Branch Policy",
            description="Test",
            scope=[PolicyScope.PULL_REQUEST],
            branches=["main", "master"]
        )
        policy = Policy(id="main-policy", config=config, rules=["severity-rule"])
        engine.register_policy(policy)
        
        # Evaluate on feature branch (should not apply)
        findings = [
            MockFinding(
                file_path="test.py",
                line_start=10,
                severity="critical",
                category="security",
                message="Issue"
            )
        ]
        context = {'findings': findings}
        result = engine.evaluate(context, PolicyScope.PULL_REQUEST, branch="feature")
        
        assert len(result.violations) == 0  # Policy doesn't apply to feature branch


class TestPolicyRules:
    """Test individual policy rules."""
    
    def test_severity_rule_pass(self):
        """Test severity rule passes with low counts."""
        rule = SeverityRule(max_critical=1, max_high=2)
        
        findings = [
            MockFinding("test.py", 10, "medium", "quality", "Issue")
        ]
        context = {'findings': findings}
        
        violations = rule.evaluate(context)
        assert len(violations) == 0
    
    def test_severity_rule_fail(self):
        """Test severity rule fails with high counts."""
        rule = SeverityRule(max_critical=0, max_high=0)
        
        findings = [
            MockFinding("test.py", 10, "critical", "security", "SQL injection"),
            MockFinding("test.py", 20, "high", "security", "XSS")
        ]
        context = {'findings': findings}
        
        violations = rule.evaluate(context)
        assert len(violations) == 2  # One for critical, one for high
    
    def test_file_pattern_rule(self):
        """Test file pattern rule."""
        rule = FilePatternRule(
            rule_id="security-files",
            name="Security Files",
            patterns=["**/auth/**", "**/security/**"],
            max_issues=0
        )
        
        findings = [
            MockFinding("src/auth/login.py", 10, "high", "security", "Issue"),
            MockFinding("src/utils/helper.py", 10, "high", "security", "Issue")
        ]
        context = {'findings': findings}
        
        violations = rule.evaluate(context)
        assert len(violations) == 1  # Only auth file matches pattern
    
    def test_complexity_rule(self):
        """Test complexity rule."""
        rule = ComplexityRule(max_complexity=10)
        
        findings = [
            MockFinding(
                "test.py", 10, "medium", "complexity",
                "High complexity", metric_value=15
            )
        ]
        context = {'findings': findings}
        
        violations = rule.evaluate(context)
        assert len(violations) == 1
        assert violations[0].metadata['complexity'] == 15
    
    def test_security_rule(self):
        """Test security rule."""
        rule = SecurityRule(max_issues=0)
        
        findings = [
            MockFinding("test.py", 10, "critical", "security", "SQL injection"),
            MockFinding("test.py", 20, "high", "performance", "Slow loop")
        ]
        context = {'findings': findings}
        
        violations = rule.evaluate(context)
        assert len(violations) == 1  # Only security finding counts


class TestPolicyManager:
    """Test PolicyManager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initializes with default rules."""
        manager = PolicyManager()
        engine = manager.get_engine()
        
        # Should have default rules registered
        assert len(engine.rules) > 0
    
    def test_load_enterprise_policies(self):
        """Test loading enterprise policies."""
        manager = PolicyManager()
        manager.load_enterprise_policies()
        
        engine = manager.get_engine()
        policies = engine.list_policies()
        
        assert len(policies) > 0
        assert any(p.id == "security-critical" for p in policies)
    
    def test_create_from_template(self):
        """Test creating policy from template."""
        manager = PolicyManager()
        
        policy = manager.create_policy_from_template(
            "security-critical",
            "my-security-policy"
        )
        
        assert policy.id == "my-security-policy"
        assert policy.config.name == "Security Critical"
        assert len(policy.rules) > 0
    
    def test_create_with_overrides(self):
        """Test creating policy with overrides."""
        manager = PolicyManager()
        
        policy = manager.create_policy_from_template(
            "quality-gate",
            "custom-gate",
            overrides={'max_high_issues': 10}
        )
        
        assert policy.config.max_high_issues == 10
    
    def test_list_templates(self):
        """Test listing templates."""
        manager = PolicyManager()
        templates = manager.list_templates()
        
        assert len(templates) > 0
        assert "security-critical" in templates
        assert "production-ready" in templates


class TestPolicyEnforcer:
    """Test PolicyEnforcer functionality."""
    
    def test_enforcer_initialization(self):
        """Test enforcer initializes correctly."""
        enforcer = PolicyEnforcer()
        assert enforcer.manager is not None
        assert enforcer.engine is not None
    
    def test_enforce_pre_commit_pass(self):
        """Test pre-commit enforcement passes with no issues."""
        manager = PolicyManager()
        manager.load_enterprise_policies()
        enforcer = PolicyEnforcer(manager)
        
        findings = []
        files = ["test.py"]
        
        result = enforcer.enforce_pre_commit(findings, files, verbose=False)
        assert result is True
    
    def test_enforce_pre_commit_fail(self):
        """Test pre-commit enforcement fails with critical issues."""
        manager = PolicyManager()
        manager.load_enterprise_policies()
        enforcer = PolicyEnforcer(manager)
        
        findings = [
            MockFinding("test.py", 10, "critical", "security", "SQL injection")
        ]
        files = ["test.py"]
        
        result = enforcer.enforce_pre_commit(findings, files, verbose=False)
        assert result is False
    
    def test_enforce_pull_request(self):
        """Test pull request enforcement."""
        manager = PolicyManager()
        manager.load_enterprise_policies()
        enforcer = PolicyEnforcer(manager)
        
        findings = [
            MockFinding("test.py", 10, "high", "security", "XSS vulnerability")
        ]
        files = ["test.py"]
        
        result = enforcer.enforce_pull_request(
            findings, files, "feature", "main", verbose=False
        )
        
        assert result is not None
        assert hasattr(result, 'passed')
        assert hasattr(result, 'violations')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

