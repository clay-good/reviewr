"""
Policy schema definitions for enterprise policy enforcement.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class PolicyScope(str, Enum):
    """Scope where policy applies."""
    PRE_COMMIT = "pre-commit"  # Enforced before commit
    PRE_PUSH = "pre-push"  # Enforced before push
    PULL_REQUEST = "pull-request"  # Enforced on PR/MR
    MERGE = "merge"  # Enforced before merge
    POST_MERGE = "post-merge"  # Enforced after merge (reporting only)
    CONTINUOUS = "continuous"  # Continuous monitoring


class PolicyAction(str, Enum):
    """Action to take when policy is violated."""
    BLOCK = "block"  # Block the operation (commit, push, merge)
    WARN = "warn"  # Show warning but allow operation
    REQUIRE_APPROVAL = "require-approval"  # Require manual approval
    NOTIFY = "notify"  # Send notification only
    REPORT = "report"  # Add to compliance report


class PolicyEnforcement(str, Enum):
    """Enforcement level for policy."""
    STRICT = "strict"  # No exceptions allowed
    FLEXIBLE = "flexible"  # Allow overrides with justification
    ADVISORY = "advisory"  # Informational only


@dataclass
class ApprovalRequirement:
    """Requirements for manual approval."""
    required_approvers: int = 1
    required_roles: Set[str] = field(default_factory=set)  # e.g., "security-team", "tech-lead"
    required_teams: Set[str] = field(default_factory=set)  # e.g., "security", "architecture"
    allow_self_approval: bool = False
    timeout_hours: Optional[int] = None  # Auto-reject after timeout


@dataclass
class PolicyConfig:
    """Configuration for a policy."""
    name: str
    description: str
    enabled: bool = True
    scope: List[PolicyScope] = field(default_factory=lambda: [PolicyScope.PULL_REQUEST])
    action: PolicyAction = PolicyAction.BLOCK
    enforcement: PolicyEnforcement = PolicyEnforcement.STRICT
    
    # Conditions
    file_patterns: List[str] = field(default_factory=list)  # Glob patterns
    exclude_patterns: List[str] = field(default_factory=list)
    branches: List[str] = field(default_factory=list)  # Apply to specific branches
    exclude_branches: List[str] = field(default_factory=list)
    
    # Thresholds
    max_critical_issues: int = 0
    max_high_issues: int = 0
    max_medium_issues: int = 10
    max_complexity: Optional[int] = None
    min_test_coverage: Optional[float] = None
    
    # Approval requirements
    approval: Optional[ApprovalRequirement] = None
    
    # Custom rules
    custom_rules: List[str] = field(default_factory=list)  # Rule IDs
    
    # Metadata
    owner: Optional[str] = None  # Team or person responsible
    tags: List[str] = field(default_factory=list)
    priority: int = 100  # Higher = more important
    
    # Notifications
    notify_on_violation: List[str] = field(default_factory=list)  # Email/Slack channels
    notify_on_override: List[str] = field(default_factory=list)


@dataclass
class Policy:
    """A complete policy definition."""
    id: str
    config: PolicyConfig
    rules: List[str] = field(default_factory=list)  # Rule IDs to apply
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'config': {
                'name': self.config.name,
                'description': self.config.description,
                'enabled': self.config.enabled,
                'scope': [s.value for s in self.config.scope],
                'action': self.config.action.value,
                'enforcement': self.config.enforcement.value,
                'file_patterns': self.config.file_patterns,
                'exclude_patterns': self.config.exclude_patterns,
                'branches': self.config.branches,
                'exclude_branches': self.config.exclude_branches,
                'max_critical_issues': self.config.max_critical_issues,
                'max_high_issues': self.config.max_high_issues,
                'max_medium_issues': self.config.max_medium_issues,
                'max_complexity': self.config.max_complexity,
                'min_test_coverage': self.config.min_test_coverage,
                'approval': {
                    'required_approvers': self.config.approval.required_approvers,
                    'required_roles': list(self.config.approval.required_roles),
                    'required_teams': list(self.config.approval.required_teams),
                    'allow_self_approval': self.config.approval.allow_self_approval,
                    'timeout_hours': self.config.approval.timeout_hours,
                } if self.config.approval else None,
                'custom_rules': self.config.custom_rules,
                'owner': self.config.owner,
                'tags': self.config.tags,
                'priority': self.config.priority,
                'notify_on_violation': self.config.notify_on_violation,
                'notify_on_override': self.config.notify_on_override,
            },
            'rules': self.rules,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'version': self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Create from dictionary."""
        config_data = data['config']
        
        approval = None
        if config_data.get('approval'):
            approval_data = config_data['approval']
            approval = ApprovalRequirement(
                required_approvers=approval_data.get('required_approvers', 1),
                required_roles=set(approval_data.get('required_roles', [])),
                required_teams=set(approval_data.get('required_teams', [])),
                allow_self_approval=approval_data.get('allow_self_approval', False),
                timeout_hours=approval_data.get('timeout_hours'),
            )
        
        config = PolicyConfig(
            name=config_data['name'],
            description=config_data['description'],
            enabled=config_data.get('enabled', True),
            scope=[PolicyScope(s) for s in config_data.get('scope', ['pull-request'])],
            action=PolicyAction(config_data.get('action', 'block')),
            enforcement=PolicyEnforcement(config_data.get('enforcement', 'strict')),
            file_patterns=config_data.get('file_patterns', []),
            exclude_patterns=config_data.get('exclude_patterns', []),
            branches=config_data.get('branches', []),
            exclude_branches=config_data.get('exclude_branches', []),
            max_critical_issues=config_data.get('max_critical_issues', 0),
            max_high_issues=config_data.get('max_high_issues', 0),
            max_medium_issues=config_data.get('max_medium_issues', 10),
            max_complexity=config_data.get('max_complexity'),
            min_test_coverage=config_data.get('min_test_coverage'),
            approval=approval,
            custom_rules=config_data.get('custom_rules', []),
            owner=config_data.get('owner'),
            tags=config_data.get('tags', []),
            priority=config_data.get('priority', 100),
            notify_on_violation=config_data.get('notify_on_violation', []),
            notify_on_override=config_data.get('notify_on_override', []),
        )
        
        return cls(
            id=data['id'],
            config=config,
            rules=data.get('rules', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            created_by=data.get('created_by'),
            version=data.get('version', 1),
        )


# Predefined enterprise policies
ENTERPRISE_POLICIES = {
    "security-critical": PolicyConfig(
        name="Security Critical",
        description="Zero tolerance for critical security issues",
        scope=[PolicyScope.PRE_COMMIT, PolicyScope.PULL_REQUEST],
        action=PolicyAction.BLOCK,
        enforcement=PolicyEnforcement.STRICT,
        max_critical_issues=0,
        max_high_issues=0,
    ),
    
    "production-ready": PolicyConfig(
        name="Production Ready",
        description="Strict quality requirements for production code",
        scope=[PolicyScope.PULL_REQUEST, PolicyScope.MERGE],
        action=PolicyAction.BLOCK,
        enforcement=PolicyEnforcement.STRICT,
        max_critical_issues=0,
        max_high_issues=0,
        max_medium_issues=5,
        max_complexity=15,
        min_test_coverage=0.8,
        branches=["main", "master", "production"],
    ),
    
    "security-review-required": PolicyConfig(
        name="Security Review Required",
        description="Require security team approval for sensitive files",
        scope=[PolicyScope.PULL_REQUEST],
        action=PolicyAction.REQUIRE_APPROVAL,
        enforcement=PolicyEnforcement.STRICT,
        file_patterns=["**/auth/**", "**/security/**", "**/crypto/**"],
        approval=ApprovalRequirement(
            required_approvers=1,
            required_teams={"security"},
            allow_self_approval=False,
        ),
    ),
    
    "architecture-review": PolicyConfig(
        name="Architecture Review",
        description="Require architecture review for core changes",
        scope=[PolicyScope.PULL_REQUEST],
        action=PolicyAction.REQUIRE_APPROVAL,
        enforcement=PolicyEnforcement.FLEXIBLE,
        file_patterns=["**/core/**", "**/api/**", "**/database/**"],
        approval=ApprovalRequirement(
            required_approvers=1,
            required_roles={"architect", "tech-lead"},
            allow_self_approval=False,
        ),
    ),
    
    "quality-gate": PolicyConfig(
        name="Quality Gate",
        description="Standard quality requirements for all code",
        scope=[PolicyScope.PULL_REQUEST],
        action=PolicyAction.WARN,
        enforcement=PolicyEnforcement.ADVISORY,
        max_critical_issues=0,
        max_high_issues=3,
        max_medium_issues=10,
        max_complexity=20,
    ),
}

