"""
Policy manager for loading and managing policies.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .schema import Policy, PolicyConfig, ENTERPRISE_POLICIES
from .rules import (
    PolicyRule,
    SeverityRule,
    FilePatternRule,
    ComplexityRule,
    SecurityRule,
    LicenseRule,
    CoverageRule
)
from .engine import PolicyEngine


class PolicyManager:
    """Manages policies and rules."""
    
    def __init__(self, policy_dir: Optional[Path] = None):
        """
        Initialize policy manager.
        
        Args:
            policy_dir: Directory containing policy files
        """
        self.policy_dir = policy_dir or Path.home() / '.reviewr' / 'policies'
        self.engine = PolicyEngine()
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default rules."""
        # Severity rules
        self.engine.register_rule(SeverityRule(
            rule_id="severity-strict",
            max_critical=0,
            max_high=0,
            max_medium=5,
            max_low=20
        ))
        
        self.engine.register_rule(SeverityRule(
            rule_id="severity-moderate",
            max_critical=0,
            max_high=3,
            max_medium=10,
            max_low=50
        ))
        
        # Security rules
        self.engine.register_rule(SecurityRule(
            rule_id="security-zero-tolerance",
            max_issues=0,
            severity="critical"
        ))
        
        self.engine.register_rule(SecurityRule(
            rule_id="security-moderate",
            max_issues=3,
            severity="high"
        ))
        
        # Complexity rules
        self.engine.register_rule(ComplexityRule(
            rule_id="complexity-strict",
            max_complexity=10,
            severity="high"
        ))
        
        self.engine.register_rule(ComplexityRule(
            rule_id="complexity-moderate",
            max_complexity=15,
            severity="medium"
        ))
        
        # File pattern rules
        self.engine.register_rule(FilePatternRule(
            rule_id="security-files-zero-issues",
            name="Security Files Zero Issues",
            patterns=["**/auth/**", "**/security/**", "**/crypto/**"],
            max_issues=0,
            severity="critical"
        ))
        
        self.engine.register_rule(FilePatternRule(
            rule_id="api-files-low-issues",
            name="API Files Low Issues",
            patterns=["**/api/**", "**/endpoints/**"],
            max_issues=3,
            severity="high"
        ))
        
        # Coverage rules
        self.engine.register_rule(CoverageRule(
            rule_id="coverage-80",
            min_coverage=0.8,
            severity="medium"
        ))
        
        self.engine.register_rule(CoverageRule(
            rule_id="coverage-90",
            min_coverage=0.9,
            severity="high"
        ))
    
    def load_enterprise_policies(self) -> None:
        """Load predefined enterprise policies."""
        for policy_id, config in ENTERPRISE_POLICIES.items():
            policy = Policy(
                id=policy_id,
                config=config,
                rules=self._get_default_rules_for_policy(config),
                created_at=datetime.now().isoformat(),
                version=1
            )
            self.engine.register_policy(policy)
    
    def _get_default_rules_for_policy(self, config: PolicyConfig) -> List[str]:
        """Get default rules for a policy based on its configuration."""
        rules = []

        # Add severity rule
        if config.max_critical_issues == 0 and config.max_high_issues == 0:
            rules.append("severity-strict")
        else:
            rules.append("severity-moderate")

        # Add security rule if applicable
        if config.max_critical_issues == 0:
            rules.append("security-zero-tolerance")

        # Add complexity rule if specified
        if config.max_complexity:
            if config.max_complexity <= 10:
                rules.append("complexity-strict")
            else:
                rules.append("complexity-moderate")

        # Add coverage rule if specified
        if config.min_test_coverage:
            if config.min_test_coverage >= 0.9:
                rules.append("coverage-90")
            elif config.min_test_coverage >= 0.8:
                rules.append("coverage-80")

        # Add file pattern rules if applicable
        if config.file_patterns:
            if any(p in str(config.file_patterns) for p in ['auth', 'security', 'crypto']):
                rules.append("security-files-zero-issues")
            if any(p in str(config.file_patterns) for p in ['api', 'endpoints']):
                rules.append("api-files-low-issues")

        return rules
    
    def load_policy_file(self, file_path: Path) -> Policy:
        """
        Load a policy from a file.
        
        Args:
            file_path: Path to policy file (JSON or YAML)
            
        Returns:
            Loaded policy
        """
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        policy = Policy.from_dict(data)
        self.engine.register_policy(policy)
        return policy
    
    def load_policies_from_directory(self, directory: Optional[Path] = None) -> int:
        """
        Load all policies from a directory.
        
        Args:
            directory: Directory to load from (defaults to policy_dir)
            
        Returns:
            Number of policies loaded
        """
        directory = directory or self.policy_dir
        
        if not directory.exists():
            return 0
        
        count = 0
        for file_path in directory.glob('*.{json,yaml,yml}'):
            try:
                self.load_policy_file(file_path)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load policy from {file_path}: {e}")
        
        return count
    
    def save_policy(self, policy: Policy, file_path: Optional[Path] = None) -> Path:
        """
        Save a policy to a file.
        
        Args:
            policy: Policy to save
            file_path: Path to save to (defaults to policy_dir/policy_id.yaml)
            
        Returns:
            Path where policy was saved
        """
        if file_path is None:
            self.policy_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.policy_dir / f"{policy.id}.yaml"
        
        data = policy.to_dict()
        
        with open(file_path, 'w') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(data, f, indent=2)
        
        return file_path
    
    def create_policy_from_template(
        self,
        template_name: str,
        policy_id: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Policy:
        """
        Create a policy from a template.
        
        Args:
            template_name: Name of template (from ENTERPRISE_POLICIES)
            policy_id: ID for new policy
            overrides: Configuration overrides
            
        Returns:
            Created policy
        """
        if template_name not in ENTERPRISE_POLICIES:
            raise ValueError(f"Unknown template: {template_name}")
        
        config = ENTERPRISE_POLICIES[template_name]
        
        # Apply overrides
        if overrides:
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        policy = Policy(
            id=policy_id,
            config=config,
            rules=self._get_default_rules_for_policy(config),
            created_at=datetime.now().isoformat(),
            version=1
        )
        
        self.engine.register_policy(policy)
        return policy
    
    def get_engine(self) -> PolicyEngine:
        """Get the policy engine."""
        return self.engine
    
    def list_templates(self) -> List[str]:
        """List available policy templates."""
        return list(ENTERPRISE_POLICIES.keys())
    
    def export_policies(self, output_dir: Path) -> int:
        """
        Export all policies to a directory.
        
        Args:
            output_dir: Directory to export to
            
        Returns:
            Number of policies exported
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for policy in self.engine.list_policies():
            file_path = output_dir / f"{policy.id}.yaml"
            self.save_policy(policy, file_path)
            count += 1
        
        return count
    
    def import_policies(self, input_dir: Path) -> int:
        """
        Import policies from a directory.
        
        Args:
            input_dir: Directory to import from
            
        Returns:
            Number of policies imported
        """
        return self.load_policies_from_directory(input_dir)

