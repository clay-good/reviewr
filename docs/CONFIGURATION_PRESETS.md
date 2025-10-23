# Configuration Presets Guide

reviewr provides **configuration presets** - predefined configurations for common use cases that make it easy to get started without manually configuring every option.

---

## Table of Contents

- [Overview](#overview)
- [Built-in Presets](#built-in-presets)
- [Using Presets](#using-presets)
- [Custom Presets](#custom-presets)
- [Preset Management](#preset-management)
- [Examples](#examples)

---

## Overview

Configuration presets provide:

- **Quick Start** - Get started with sensible defaults
- **Best Practices** - Configurations tuned for specific use cases
- **Consistency** - Standardize reviews across your team
- **Flexibility** - Override preset values as needed
- **Extensibility** - Create custom presets for your team

---

## Built-in Presets

### **security**

**Focus:** Security vulnerabilities, injections, authentication issues

```bash
reviewr app.py --preset security
```

**Configuration:**
- Review Types: `security`
- Min Severity: `medium`
- Enabled Analyzers: `security`, `dataflow`, `semantic`
- Fail on Critical: `true`
- Fail on High Threshold: `0` (fail on any high severity issue)
- Additional: Secrets detection enabled

**Use Cases:**
- Security audits
- Pre-deployment security checks
- Compliance reviews

---

### **performance**

**Focus:** Performance bottlenecks, inefficiencies, optimization opportunities

```bash
reviewr app.py --preset performance
```

**Configuration:**
- Review Types: `performance`
- Min Severity: `medium`
- Enabled Analyzers: `performance`, `complexity`, `dataflow`
- Fail on Critical: `false`
- Fail on High Threshold: `5`
- Additional: Profiling and algorithmic complexity checks enabled

**Use Cases:**
- Performance optimization
- Identifying bottlenecks
- Scalability reviews

---

### **quick**

**Focus:** Fast review focusing on critical issues only

```bash
reviewr app.py --preset quick
```

**Configuration:**
- Review Types: `security`, `correctness`
- Min Severity: `high`
- Enabled Analyzers: `security`
- Max Findings: `20`
- Fail on Critical: `true`
- Additional: Fast mode enabled

**Use Cases:**
- Pre-commit hooks
- Quick sanity checks
- Developer workflow integration

---

### **comprehensive**

**Focus:** All review types and analyzers

```bash
reviewr app.py --preset comprehensive
```

**Configuration:**
- Review Types: `security`, `performance`, `correctness`, `maintainability`, `architecture`, `standards`
- Min Severity: `info`
- Enabled Analyzers: All analyzers
- Fail on Critical: `true`
- Fail on High Threshold: `10`
- Additional: All checks enabled, detailed reports

**Use Cases:**
- Major releases
- Code quality audits
- Comprehensive reviews

---

### **maintainability**

**Focus:** Code quality, complexity, documentation, best practices

```bash
reviewr app.py --preset maintainability
```

**Configuration:**
- Review Types: `maintainability`, `standards`
- Min Severity: `low`
- Enabled Analyzers: `complexity`, `semantic`, `type`
- Fail on Critical: `false`
- Additional: Documentation and test coverage checks enabled

**Use Cases:**
- Code quality reviews
- Technical debt assessment
- Refactoring planning

---

### **pre-commit**

**Focus:** Fast, focused on blocking issues for pre-commit hooks

```bash
reviewr app.py --preset pre-commit
```

**Configuration:**
- Review Types: `security`, `correctness`
- Min Severity: `high`
- Enabled Analyzers: `security`, `dataflow`
- Max Findings: `10`
- Fail on Critical: `true`
- Output Format: `sarif`
- Additional: Fast mode, 30-second timeout

**Use Cases:**
- Git pre-commit hooks
- Developer workflow
- Fast feedback loop

---

### **ci-cd**

**Focus:** Balanced review for CI/CD pipelines and pull requests

```bash
reviewr app.py --preset ci-cd
```

**Configuration:**
- Review Types: `security`, `performance`, `correctness`, `maintainability`
- Min Severity: `medium`
- Enabled Analyzers: `security`, `dataflow`, `complexity`, `performance`
- Max Findings: `50`
- Fail on Critical: `true`
- Fail on High Threshold: `5`
- Output Format: `sarif`
- Additional: PR comment posting, status check updates

**Use Cases:**
- GitHub Actions
- GitLab CI
- Pull request reviews

---

### **strict**

**Focus:** Zero tolerance for issues

```bash
reviewr app.py --preset strict
```

**Configuration:**
- Review Types: All types
- Min Severity: `low`
- Enabled Analyzers: All analyzers
- Fail on Critical: `true`
- Fail on High Threshold: `0`
- Additional: Strict mode, fail on warnings

**Use Cases:**
- Critical systems
- High-security environments
- Quality gates

---

## Using Presets

### Basic Usage

```bash
# Use a preset
reviewr <file_or_dir> --preset <preset_name>

# Examples
reviewr app.py --preset security
reviewr src/ --preset performance
reviewr . --preset comprehensive
```

### Combining with Other Options

Presets can be combined with other CLI options. CLI options override preset values:

```bash
# Use security preset but change output format
reviewr app.py --preset security --output-format html

# Use quick preset but increase max findings
reviewr app.py --preset quick --max-findings 50

# Use ci-cd preset with custom provider
reviewr app.py --preset ci-cd --provider openai
```

### In Configuration Files

You can reference presets in your `.reviewr.yml` configuration:

```yaml
# .reviewr.yml
preset: security

# Override specific values
min_severity: high
output_format: html
```

---

## Custom Presets

### Creating Custom Presets

Create custom presets for your team's specific needs:

```bash
reviewr preset create my-team-standard \
 --description "Team standard review configuration" \
 --review-types security,maintainability,standards \
 --min-severity medium \
 --fail-on-critical \
 --fail-on-high-threshold 3 \
 --enabled-analyzers security,complexity,semantic \
 --output-format markdown \
 --output ./presets/my-team-standard.yml
```

### Custom Preset File Format

**YAML Format:**

```yaml
name: my-team-standard
description: Team standard review configuration
review_types:
 - security
 - maintainability
 - standards
min_severity: medium
enabled_analyzers:
 - security
 - complexity
 - semantic
disabled_analyzers: []
max_findings: null
fail_on_critical: true
fail_on_high_threshold: 3
custom_rules: null
output_format: markdown
additional_options:
 check_documentation: true
 check_test_coverage: true
```

**JSON Format:**

```json
{
 "name": "my-team-standard",
 "description": "Team standard review configuration",
 "review_types": ["security", "maintainability", "standards"],
 "min_severity": "medium",
 "enabled_analyzers": ["security", "complexity", "semantic"],
 "fail_on_critical": true,
 "fail_on_high_threshold": 3,
 "output_format": "markdown"
}
```

### Using Custom Presets

```bash
# Use custom preset from directory
reviewr app.py --preset my-team-standard --custom-presets-dir ./presets

# Or set environment variable
export REVIEWR_PRESETS_DIR=./presets
reviewr app.py --preset my-team-standard
```

---

## Preset Management

### List Available Presets

```bash
# List all built-in presets
reviewr preset list

# List including custom presets
reviewr preset list --custom-dir ./presets
```

### Show Preset Details

```bash
# Show detailed information about a preset
reviewr preset show security

# Show custom preset
reviewr preset show my-team-standard --custom-dir ./presets
```

### Compare Presets

```bash
# Compare two presets side-by-side
reviewr preset compare security performance

# Compare with custom preset
reviewr preset compare security my-team-standard --custom-dir ./presets
```

### Export Presets

```bash
# Export built-in preset to file
reviewr preset export security --output ./my-security.yml

# Modify and use as custom preset
reviewr app.py --preset my-security --custom-presets-dir .
```

---

## Examples

### Example 1: Security Audit

```bash
# Run comprehensive security audit
reviewr . --preset security --output-format html > security-report.html
```

### Example 2: Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
reviewr $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$') \
 --preset pre-commit \
 --output-format sarif
```

### Example 3: CI/CD Pipeline

```yaml
# .github/workflows/review.yml
- name: Code Review
 run: |
 reviewr . --preset ci-cd --output-format sarif > results.sarif
```

### Example 4: Team Standard

```bash
# Create team preset
reviewr preset create team-standard \
 --description "Our team's standard review" \
 --review-types security,performance,maintainability \
 --min-severity medium \
 --fail-on-critical \
 --output .reviewr/team-standard.yml

# Use in reviews
reviewr . --preset team-standard --custom-presets-dir .reviewr
```

---

## Best Practices

1. **Start with Built-in Presets** - Use built-in presets as starting points
2. **Create Team Presets** - Standardize reviews across your team
3. **Version Control Presets** - Commit custom presets to your repository
4. **Document Presets** - Add clear descriptions to custom presets
5. **Test Presets** - Validate presets before rolling out to team
6. **Review Regularly** - Update presets as your needs evolve

---

## Troubleshooting

### Preset Not Found

```bash
# Error: Unknown preset 'my-preset'
# Solution: Check preset name and custom presets directory
reviewr preset list --custom-dir ./presets
```

### Preset Override Not Working

```bash
# CLI options override preset values
# Make sure you're using the correct option name
reviewr app.py --preset security --min-severity high
```

### Custom Preset Not Loading

```bash
# Check file format and location
# Ensure file has .yml, .yaml, or .json extension
# Verify file is in the custom presets directory
```

---

## Next Steps

- See [CI/CD Integration Guide](CI_CD_INTEGRATION.md) for using presets in pipelines
- See [Configuration Guide](../README.md#configuration) for full configuration options
- See [Auto-Fix Guide](AUTO_FIX_GUIDE.md) for automatic code fixing

---

**Built by a world-class software engineer** 