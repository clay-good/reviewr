# Enterprise Policy Enforcement Engine

**Status**: ✅ **PRODUCTION READY**  
**Version**: 1.0.0  
**Date**: October 20, 2025

---

## Overview

The **Enterprise Policy Enforcement Engine** provides centralized policy management and enforcement for enterprise environments. It enables organizations to define, manage, and enforce code quality, security, and compliance policies across pre-commit hooks, pull requests, and merge operations.

### Key Features

✅ **Centralized Policy Management** - Define organization-wide policies  
✅ **Pre-commit Enforcement** - Block commits that violate policies  
✅ **PR/MR Approval Workflows** - Automated approval based on compliance  
✅ **Compliance Reporting** - Track violations across teams  
✅ **Custom Policy Rules** - Define organization-specific rules  
✅ **Flexible Enforcement** - Strict, flexible, or advisory modes  
✅ **Branch-specific Policies** - Different rules for different branches  
✅ **File Pattern Matching** - Target specific files or directories  

---

## Architecture

### Components

1. **PolicyEngine** - Core evaluation engine
2. **PolicyManager** - Policy lifecycle management
3. **PolicyEnforcer** - Enforcement in various contexts
4. **PolicyRules** - Reusable rule definitions
5. **PolicyConfig** - Policy configuration schema

### Policy Lifecycle

```
Define Policy → Register Rules → Evaluate Context → Enforce Action
```

---

## Quick Start

### 1. List Available Templates

```bash
reviewr policy list-templates
```

**Output:**
```
Available Policy Templates:

Template ID              Name                     Description
security-critical        Security Critical        Zero tolerance for critical security issues
production-ready         Production Ready         Strict quality requirements for production code
security-review-required Security Review Required Require security team approval for sensitive files
architecture-review      Architecture Review      Require architecture review for core changes
quality-gate             Quality Gate             Standard quality requirements for all code
```

### 2. Create a Policy

```bash
# Create from template
reviewr policy create security-critical my-security-policy --save

# Create with custom thresholds
reviewr policy create production-ready prod-policy \
  --max-critical 0 \
  --max-high 2 \
  --max-medium 10 \
  --save
```

### 3. Check Code Against Policies

```bash
# Pre-commit check
reviewr policy check --scope pre-commit

# Pull request check
reviewr policy check --scope pull-request --branch main

# Merge check
reviewr policy check --scope merge --branch main --verbose
```

### 4. List Active Policies

```bash
# List all policies
reviewr policy list

# List policies for specific scope
reviewr policy list --scope pre-commit
reviewr policy list --scope pull-request
```

---

## Policy Configuration

### Policy Scopes

Policies can be enforced at different stages:

- **`pre-commit`** - Before code is committed
- **`pre-push`** - Before code is pushed
- **`pull-request`** - During PR/MR review
- **`merge`** - Before merge to target branch
- **`post-merge`** - After merge (reporting only)
- **`continuous`** - Continuous monitoring

### Policy Actions

When a policy is violated:

- **`block`** - Block the operation (commit, push, merge)
- **`warn`** - Show warning but allow operation
- **`require-approval`** - Require manual approval
- **`notify`** - Send notification only
- **`report`** - Add to compliance report

### Enforcement Levels

- **`strict`** - No exceptions allowed
- **`flexible`** - Allow overrides with justification
- **`advisory`** - Informational only

---

## Predefined Enterprise Policies

### 1. Security Critical

**Use Case**: Zero tolerance for security issues

```yaml
name: Security Critical
scope: [pre-commit, pull-request]
action: block
enforcement: strict
max_critical_issues: 0
max_high_issues: 0
```

**When to Use**:
- Security-sensitive repositories
- Compliance-required projects
- Production systems

### 2. Production Ready

**Use Case**: Strict quality for production branches

```yaml
name: Production Ready
scope: [pull-request, merge]
action: block
enforcement: strict
branches: [main, master, production]
max_critical_issues: 0
max_high_issues: 0
max_medium_issues: 5
max_complexity: 15
min_test_coverage: 0.8
```

**When to Use**:
- Production branch protection
- Release branches
- Critical infrastructure

### 3. Security Review Required

**Use Case**: Require security team approval for sensitive files

```yaml
name: Security Review Required
scope: [pull-request]
action: require-approval
enforcement: strict
file_patterns:
  - "**/auth/**"
  - "**/security/**"
  - "**/crypto/**"
approval:
  required_approvers: 1
  required_teams: [security]
  allow_self_approval: false
```

**When to Use**:
- Authentication code changes
- Security module updates
- Cryptographic implementations

### 4. Architecture Review

**Use Case**: Require architect approval for core changes

```yaml
name: Architecture Review
scope: [pull-request]
action: require-approval
enforcement: flexible
file_patterns:
  - "**/core/**"
  - "**/api/**"
  - "**/database/**"
approval:
  required_approvers: 1
  required_roles: [architect, tech-lead]
  allow_self_approval: false
```

**When to Use**:
- Core system changes
- API modifications
- Database schema updates

### 5. Quality Gate

**Use Case**: Standard quality requirements

```yaml
name: Quality Gate
scope: [pull-request]
action: warn
enforcement: advisory
max_critical_issues: 0
max_high_issues: 3
max_medium_issues: 10
max_complexity: 20
```

**When to Use**:
- Feature branches
- Development workflow
- Code quality monitoring

---

## Custom Policy Rules

### Built-in Rules

1. **SeverityRule** - Check issue severity thresholds
2. **FilePatternRule** - Check issues in specific files
3. **ComplexityRule** - Check code complexity
4. **SecurityRule** - Check security issues
5. **LicenseRule** - Check license compliance
6. **CoverageRule** - Check test coverage
7. **CustomRule** - Define custom logic

### Creating Custom Rules

```python
from reviewr.policy import PolicyRule, RuleViolation

class MyCustomRule(PolicyRule):
    def __init__(self):
        super().__init__(
            rule_id="my-custom-rule",
            name="My Custom Rule",
            description="Custom validation logic",
            severity="high"
        )
    
    def evaluate(self, context):
        violations = []
        
        # Your custom logic here
        findings = context.get('findings', [])
        
        for finding in findings:
            if self._should_flag(finding):
                violations.append(RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    message="Custom violation detected",
                    file_path=finding.file_path,
                    suggestion="Fix the issue"
                ))
        
        return violations
```

---

## Integration Examples

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run policy check
reviewr policy check --scope pre-commit

# Exit with policy result
exit $?
```

### GitHub Actions

```yaml
name: Policy Enforcement

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install reviewr
        run: pip install reviewr
      
      - name: Check Policies
        run: |
          reviewr policy check \
            --scope pull-request \
            --branch ${{ github.base_ref }}
```

### GitLab CI

```yaml
policy-check:
  stage: test
  script:
    - pip install reviewr
    - reviewr policy check --scope pull-request --branch $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
  only:
    - merge_requests
```

---

## Policy File Format

### YAML Format

```yaml
id: my-policy
config:
  name: My Policy
  description: Custom policy for my team
  enabled: true
  scope:
    - pull-request
    - merge
  action: block
  enforcement: strict
  
  # File filters
  file_patterns:
    - "src/**/*.py"
    - "lib/**/*.js"
  exclude_patterns:
    - "**/*_test.py"
    - "**/vendor/**"
  
  # Branch filters
  branches:
    - main
    - release/*
  exclude_branches:
    - feature/*
  
  # Thresholds
  max_critical_issues: 0
  max_high_issues: 2
  max_medium_issues: 10
  max_complexity: 15
  min_test_coverage: 0.8
  
  # Approval requirements
  approval:
    required_approvers: 2
    required_roles:
      - tech-lead
      - architect
    required_teams:
      - security
    allow_self_approval: false
    timeout_hours: 48
  
  # Metadata
  owner: security-team
  tags:
    - security
    - compliance
  priority: 100
  
  # Notifications
  notify_on_violation:
    - security@company.com
    - slack://security-channel
  notify_on_override:
    - audit@company.com

rules:
  - severity-strict
  - security-zero-tolerance
  - complexity-strict
  - coverage-80

created_at: "2025-10-20T10:00:00Z"
version: 1
```

---

## CLI Reference

### `reviewr policy list-templates`

List available policy templates.

### `reviewr policy create <template> <policy-id>`

Create a policy from a template.

**Options:**
- `--save` - Save policy to file
- `--max-critical <n>` - Override max critical issues
- `--max-high <n>` - Override max high issues
- `--max-medium <n>` - Override max medium issues

### `reviewr policy list`

List active policies.

**Options:**
- `--scope <scope>` - Filter by scope (pre-commit, pull-request, merge, all)

### `reviewr policy check [path]`

Check code against active policies.

**Options:**
- `--scope <scope>` - Enforcement scope (default: pre-commit)
- `--branch <name>` - Target branch name
- `--verbose, -v` - Verbose output

### `reviewr policy export <output-dir>`

Export all policies to a directory.

### `reviewr policy import <input-dir>`

Import policies from a directory.

---

## Best Practices

### 1. Start with Templates

Use predefined templates and customize as needed:

```bash
reviewr policy create security-critical team-security --save
```

### 2. Use Branch-Specific Policies

Apply stricter policies to production branches:

```yaml
branches: [main, master, production]
max_critical_issues: 0
max_high_issues: 0
```

### 3. Require Approval for Sensitive Changes

```yaml
file_patterns: ["**/auth/**", "**/security/**"]
action: require-approval
approval:
  required_teams: [security]
```

### 4. Use Advisory Mode for New Policies

Test policies in advisory mode before enforcing:

```yaml
enforcement: advisory
action: warn
```

### 5. Share Policies Across Teams

Export and share policies:

```bash
reviewr policy export /shared/team-policies
```

---

## Troubleshooting

### Policy Not Applying

**Check:**
1. Policy scope matches current context
2. Branch filters are correct
3. File patterns match target files
4. Policy is enabled

### False Positives

**Solutions:**
1. Adjust thresholds
2. Add exclude patterns
3. Use flexible enforcement
4. Create custom rules

### Performance Issues

**Optimizations:**
1. Limit file patterns
2. Use pre-commit scope for fast checks
3. Cache policy evaluations
4. Run in parallel

---

## Future Enhancements

- [ ] Policy versioning and rollback
- [ ] Policy inheritance and composition
- [ ] Machine learning for policy tuning
- [ ] Integration with SIEM systems
- [ ] Policy compliance dashboards
- [ ] Automated policy suggestions

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/reviewr/reviewr/issues
- Documentation: https://reviewr.dev/docs/policy-engine
- Email: support@reviewr.dev

---

**Built with ❤️ for enterprise teams**

