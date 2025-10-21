"""
Core policy enforcement engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import fnmatch

from .schema import Policy, PolicyConfig, PolicyScope, PolicyAction, PolicyEnforcement
from .rules import PolicyRule, RuleViolation


@dataclass
class PolicyViolation:
    """A violation of a policy."""
    policy_id: str
    policy_name: str
    action: PolicyAction
    enforcement: PolicyEnforcement
    rule_violations: List[RuleViolation] = field(default_factory=list)
    can_override: bool = False
    requires_approval: bool = False
    approval_teams: List[str] = field(default_factory=list)
    approval_roles: List[str] = field(default_factory=list)
    
    @property
    def severity(self) -> str:
        """Get highest severity from rule violations."""
        if not self.rule_violations:
            return "low"
        
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}
        max_severity = max(
            (severity_order.get(v.severity, 0) for v in self.rule_violations),
            default=0
        )
        
        for sev, order in severity_order.items():
            if order == max_severity:
                return sev
        return "low"
    
    @property
    def should_block(self) -> bool:
        """Check if this violation should block the operation."""
        if self.action == PolicyAction.BLOCK:
            if self.enforcement == PolicyEnforcement.STRICT:
                return True
            elif self.enforcement == PolicyEnforcement.FLEXIBLE and not self.can_override:
                return True
        return False


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    passed: bool
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    requires_approval: bool = False
    approval_teams: List[str] = field(default_factory=list)
    approval_roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def should_block(self) -> bool:
        """Check if any violation should block the operation."""
        return any(v.should_block for v in self.violations)
    
    @property
    def critical_violations(self) -> List[PolicyViolation]:
        """Get critical violations."""
        return [v for v in self.violations if v.severity == 'critical']
    
    @property
    def high_violations(self) -> List[PolicyViolation]:
        """Get high severity violations."""
        return [v for v in self.violations if v.severity == 'high']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'passed': self.passed,
            'should_block': self.should_block,
            'requires_approval': self.requires_approval,
            'approval_teams': self.approval_teams,
            'approval_roles': self.approval_roles,
            'violations': [
                {
                    'policy_id': v.policy_id,
                    'policy_name': v.policy_name,
                    'action': v.action.value if hasattr(v.action, 'value') else str(v.action),
                    'enforcement': v.enforcement.value if hasattr(v.enforcement, 'value') else str(v.enforcement),
                    'severity': v.severity,
                    'can_override': v.can_override,
                    'requires_approval': v.requires_approval,
                    'rule_violations': [
                        {
                            'rule_id': rv.rule_id,
                            'rule_name': rv.rule_name,
                            'severity': rv.severity,
                            'message': rv.message,
                            'file_path': rv.file_path,
                            'line_number': rv.line_number,
                            'suggestion': rv.suggestion,
                            'metadata': rv.metadata,
                        }
                        for rv in v.rule_violations
                    ]
                }
                for v in self.violations
            ],
            'warnings': self.warnings,
            'metadata': self.metadata,
        }


class PolicyEngine:
    """Core policy enforcement engine."""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.rules: Dict[str, PolicyRule] = {}
    
    def register_policy(self, policy: Policy) -> None:
        """Register a policy."""
        self.policies[policy.id] = policy
    
    def register_rule(self, rule: PolicyRule) -> None:
        """Register a rule."""
        self.rules[rule.rule_id] = rule
    
    def evaluate(
        self,
        context: Dict[str, Any],
        scope: PolicyScope,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> PolicyResult:
        """
        Evaluate policies against the given context.
        
        Args:
            context: Context containing findings, metrics, etc.
            scope: Scope to evaluate (pre-commit, pull-request, etc.)
            branch: Current branch name
            files: List of files being evaluated
            
        Returns:
            PolicyResult with violations and recommendations
        """
        result = PolicyResult(passed=True)
        
        # Get applicable policies
        applicable_policies = self._get_applicable_policies(scope, branch, files)
        
        # Sort by priority (higher first)
        applicable_policies.sort(key=lambda p: p.config.priority, reverse=True)
        
        # Evaluate each policy
        for policy in applicable_policies:
            if not policy.config.enabled:
                continue
            
            violation = self._evaluate_policy(policy, context)
            
            if violation and violation.rule_violations:
                result.violations.append(violation)
                
                if violation.should_block:
                    result.passed = False
                
                if violation.requires_approval:
                    result.requires_approval = True
                    result.approval_teams.extend(violation.approval_teams)
                    result.approval_roles.extend(violation.approval_roles)
                
                if violation.action == PolicyAction.WARN:
                    result.warnings.append(
                        f"Policy '{policy.config.name}' has {len(violation.rule_violations)} violation(s)"
                    )
        
        # Add metadata
        result.metadata['evaluated_policies'] = len(applicable_policies)
        result.metadata['total_violations'] = len(result.violations)
        result.metadata['scope'] = scope.value
        
        return result
    
    def _get_applicable_policies(
        self,
        scope: PolicyScope,
        branch: Optional[str],
        files: Optional[List[str]]
    ) -> List[Policy]:
        """Get policies applicable to the current context."""
        applicable = []
        
        for policy in self.policies.values():
            # Check scope
            if scope not in policy.config.scope:
                continue
            
            # Check branch filters
            if branch:
                if policy.config.branches and branch not in policy.config.branches:
                    continue
                if policy.config.exclude_branches and branch in policy.config.exclude_branches:
                    continue
            
            # Check file filters
            if files and (policy.config.file_patterns or policy.config.exclude_patterns):
                if not self._matches_file_filters(files, policy.config):
                    continue
            
            applicable.append(policy)
        
        return applicable
    
    def _matches_file_filters(self, files: List[str], config: PolicyConfig) -> bool:
        """Check if any file matches the policy's file filters."""
        for file_path in files:
            # Check include patterns
            if config.file_patterns:
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in config.file_patterns):
                    continue
            
            # Check exclude patterns
            if config.exclude_patterns:
                if any(fnmatch.fnmatch(file_path, pattern) for pattern in config.exclude_patterns):
                    continue
            
            # File matches filters
            return True
        
        return False
    
    def _evaluate_policy(self, policy: Policy, context: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Evaluate a single policy."""
        rule_violations = []
        
        # Evaluate each rule in the policy
        for rule_id in policy.rules:
            rule = self.rules.get(rule_id)
            if not rule:
                continue
            
            violations = rule.evaluate(context)
            rule_violations.extend(violations)
        
        # If no violations, policy passes
        if not rule_violations:
            return None
        
        # Create policy violation
        violation = PolicyViolation(
            policy_id=policy.id,
            policy_name=policy.config.name,
            action=policy.config.action,
            enforcement=policy.config.enforcement,
            rule_violations=rule_violations,
            can_override=(policy.config.enforcement == PolicyEnforcement.FLEXIBLE),
        )
        
        # Check if approval is required
        if policy.config.action == PolicyAction.REQUIRE_APPROVAL and policy.config.approval:
            violation.requires_approval = True
            violation.approval_teams = list(policy.config.approval.required_teams)
            violation.approval_roles = list(policy.config.approval.required_roles)
        
        return violation
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self.policies.get(policy_id)
    
    def list_policies(self, scope: Optional[PolicyScope] = None) -> List[Policy]:
        """List all policies, optionally filtered by scope."""
        if scope:
            return [p for p in self.policies.values() if scope in p.config.scope]
        return list(self.policies.values())
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy."""
        if policy_id in self.policies:
            del self.policies[policy_id]
            return True
        return False

