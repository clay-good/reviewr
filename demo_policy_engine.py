"""
Demo script for Enterprise Policy Enforcement Engine.

This script demonstrates the key features of the policy engine:
1. Creating policies from templates
2. Evaluating code against policies
3. Enforcing policies in different contexts
4. Generating compliance reports
"""

from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from reviewr.policy import (
    PolicyManager,
    PolicyEnforcer,
    PolicyScope,
    PolicyConfig,
    Policy,
    ApprovalRequirement
)

console = Console()


@dataclass
class MockFinding:
    """Mock finding for demo."""
    file_path: str
    line_start: int
    severity: str
    category: str
    message: str
    suggestion: str = ""
    metric_value: float = None


def print_section(title: str):
    """Print a section header."""
    console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 80}[/bold cyan]\n")


def demo_1_list_templates():
    """Demo 1: List available policy templates."""
    print_section("Demo 1: List Available Policy Templates")
    
    manager = PolicyManager()
    templates = manager.list_templates()
    
    table = Table(title="Available Policy Templates", show_header=True)
    table.add_column("Template ID", style="cyan", width=25)
    table.add_column("Description", style="white")
    
    from reviewr.policy.schema import ENTERPRISE_POLICIES
    for template_id in templates:
        config = ENTERPRISE_POLICIES[template_id]
        table.add_row(template_id, config.description)
    
    console.print(table)
    console.print(f"\n[green]✓ Found {len(templates)} policy templates[/green]")


def demo_2_create_policies():
    """Demo 2: Create policies from templates."""
    print_section("Demo 2: Create Policies from Templates")
    
    manager = PolicyManager()
    
    # Create security-critical policy
    console.print("[bold]Creating 'security-critical' policy...[/bold]")
    policy1 = manager.create_policy_from_template(
        "security-critical",
        "demo-security-policy"
    )
    console.print(f"[green]✓ Created policy: {policy1.config.name}[/green]")
    console.print(f"  - Max critical issues: {policy1.config.max_critical_issues}")
    console.print(f"  - Max high issues: {policy1.config.max_high_issues}")
    console.print(f"  - Action: {policy1.config.action.value}")
    
    # Create production-ready policy with overrides
    console.print("\n[bold]Creating 'production-ready' policy with custom thresholds...[/bold]")
    policy2 = manager.create_policy_from_template(
        "production-ready",
        "demo-prod-policy",
        overrides={'max_medium_issues': 3}
    )
    console.print(f"[green]✓ Created policy: {policy2.config.name}[/green]")
    console.print(f"  - Max medium issues: {policy2.config.max_medium_issues}")
    console.print(f"  - Min test coverage: {policy2.config.min_test_coverage}")
    console.print(f"  - Branches: {', '.join(policy2.config.branches)}")
    
    return manager


def demo_3_evaluate_clean_code(manager: PolicyManager):
    """Demo 3: Evaluate clean code (no violations)."""
    print_section("Demo 3: Evaluate Clean Code (No Violations)")
    
    enforcer = PolicyEnforcer(manager)
    
    # Clean code - no findings
    findings = []
    files = ["src/utils/helper.py"]
    
    console.print("[bold]Checking clean code against policies...[/bold]")
    result = enforcer.enforce_pre_commit(findings, files, verbose=False)
    
    if result:
        console.print("\n[green]✓ All policies passed![/green]")
        console.print("[dim]No violations found - commit allowed[/dim]")
    else:
        console.print("\n[red]✗ Policies failed[/red]")


def demo_4_evaluate_with_violations(manager: PolicyManager):
    """Demo 4: Evaluate code with violations."""
    print_section("Demo 4: Evaluate Code with Policy Violations")
    
    enforcer = PolicyEnforcer(manager)
    
    # Code with security issues
    findings = [
        MockFinding(
            file_path="src/api/auth.py",
            line_start=45,
            severity="critical",
            category="security",
            message="SQL injection vulnerability detected",
            suggestion="Use parameterized queries instead of string concatenation"
        ),
        MockFinding(
            file_path="src/api/auth.py",
            line_start=78,
            severity="high",
            category="security",
            message="Hardcoded credentials found",
            suggestion="Move credentials to environment variables"
        ),
        MockFinding(
            file_path="src/utils/parser.py",
            line_start=120,
            severity="medium",
            category="quality",
            message="High cyclomatic complexity (18)",
            suggestion="Refactor function to reduce complexity",
            metric_value=18
        )
    ]
    files = ["src/api/auth.py", "src/utils/parser.py"]
    
    console.print("[bold]Checking code with violations against policies...[/bold]")
    console.print(f"[dim]Files: {', '.join(files)}[/dim]")
    console.print(f"[dim]Findings: {len(findings)} issues detected[/dim]\n")
    
    result = enforcer.enforce_pre_commit(findings, files, verbose=True)
    
    if not result:
        console.print("\n[red]✗ Commit blocked by policy violations[/red]")
        console.print("[yellow]Fix the issues above before committing[/yellow]")


def demo_5_pull_request_enforcement(manager: PolicyManager):
    """Demo 5: Pull request enforcement with approval requirements."""
    print_section("Demo 5: Pull Request Enforcement")
    
    # Add a policy that requires approval
    approval_policy = Policy(
        id="demo-approval-policy",
        config=PolicyConfig(
            name="Security Review Required",
            description="Require security team approval",
            scope=[PolicyScope.PULL_REQUEST],
            action="require-approval",
            enforcement="strict",
            file_patterns=["**/auth/**", "**/security/**"],
            approval=ApprovalRequirement(
                required_approvers=1,
                required_teams={"security"},
                allow_self_approval=False
            )
        ),
        rules=["security-files-zero-issues"]
    )
    manager.get_engine().register_policy(approval_policy)
    
    enforcer = PolicyEnforcer(manager)
    
    # Changes to security-sensitive files
    findings = [
        MockFinding(
            file_path="src/auth/login.py",
            line_start=30,
            severity="medium",
            category="security",
            message="Weak password validation",
            suggestion="Implement stronger password requirements"
        )
    ]
    files = ["src/auth/login.py"]
    
    console.print("[bold]Checking pull request with changes to security files...[/bold]")
    console.print(f"[dim]Files: {', '.join(files)}[/dim]\n")
    
    result = enforcer.enforce_pull_request(
        findings, files, "feature/auth-update", "main", verbose=True
    )
    
    if result.requires_approval:
        console.print("\n[yellow]⚠️  Manual approval required[/yellow]")
        console.print(f"[yellow]Required teams: {', '.join(result.approval_teams)}[/yellow]")


def demo_6_compliance_report():
    """Demo 6: Generate compliance report."""
    print_section("Demo 6: Generate Compliance Report")
    
    from reviewr.policy import PolicyResult, PolicyViolation
    from reviewr.policy.rules import RuleViolation
    
    # Simulate multiple policy evaluations
    results = []
    
    # Result 1: Passed
    results.append(PolicyResult(passed=True, violations=[]))
    
    # Result 2: Failed with violations
    violation = PolicyViolation(
        policy_id="security-critical",
        policy_name="Security Critical",
        action="block",
        enforcement="strict",
        rule_violations=[
            RuleViolation(
                rule_id="severity-rule",
                rule_name="Severity Threshold",
                severity="critical",
                message="Found 2 critical issues",
                suggestion="Fix critical issues"
            )
        ]
    )
    results.append(PolicyResult(passed=False, violations=[violation]))
    
    # Result 3: Requires approval
    results.append(PolicyResult(
        passed=True,
        requires_approval=True,
        approval_teams=["security"]
    ))
    
    # Generate report
    enforcer = PolicyEnforcer()
    report = enforcer.generate_compliance_report(results)
    
    console.print("[bold]Compliance Report Summary:[/bold]\n")
    
    table = Table(show_header=True)
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="white")
    
    table.add_row("Total Evaluations", str(report['total_evaluations']))
    table.add_row("Passed", f"[green]{report['passed']}[/green]")
    table.add_row("Failed", f"[red]{report['failed']}[/red]")
    table.add_row("Blocked", f"[red]{report['blocked']}[/red]")
    table.add_row("Requires Approval", f"[yellow]{report['requires_approval']}[/yellow]")
    table.add_row("Total Violations", str(report['total_violations']))
    
    console.print(table)
    console.print(f"\n[green]✓ Compliance report generated[/green]")


def main():
    """Run all demos."""
    console.print(Panel.fit(
        "[bold cyan]Enterprise Policy Enforcement Engine Demo[/bold cyan]\n"
        "[white]Demonstrating centralized policy management and enforcement[/white]",
        border_style="cyan"
    ))
    
    try:
        # Demo 1: List templates
        demo_1_list_templates()
        
        # Demo 2: Create policies
        manager = demo_2_create_policies()
        
        # Demo 3: Clean code
        demo_3_evaluate_clean_code(manager)
        
        # Demo 4: Code with violations
        demo_4_evaluate_with_violations(manager)
        
        # Demo 5: Pull request enforcement
        demo_5_pull_request_enforcement(manager)
        
        # Demo 6: Compliance report
        demo_6_compliance_report()
        
        # Summary
        print_section("Demo Complete!")
        console.print("[bold green]✓ All demos completed successfully![/bold green]\n")
        console.print("[bold]Key Features Demonstrated:[/bold]")
        console.print("  ✓ Policy template management")
        console.print("  ✓ Custom policy creation")
        console.print("  ✓ Pre-commit enforcement")
        console.print("  ✓ Pull request enforcement")
        console.print("  ✓ Approval workflows")
        console.print("  ✓ Compliance reporting")
        
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        console.print("  1. Try: reviewr policy list-templates")
        console.print("  2. Try: reviewr policy create security-critical my-policy --save")
        console.print("  3. Try: reviewr policy check --scope pre-commit")
        console.print("  4. Read: ENTERPRISE_POLICY_ENGINE.md for full documentation")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == '__main__':
    main()

