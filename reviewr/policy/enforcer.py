"""
Policy enforcer for pre-commit and PR workflows.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .engine import PolicyEngine, PolicyResult
from .schema import PolicyScope, PolicyAction
from .manager import PolicyManager


console = Console()


class PolicyEnforcer:
    """Enforces policies in various contexts."""
    
    def __init__(self, manager: Optional[PolicyManager] = None):
        """
        Initialize policy enforcer.
        
        Args:
            manager: PolicyManager instance (creates new one if not provided)
        """
        self.manager = manager or PolicyManager()
        self.engine = self.manager.get_engine()
    
    def enforce_pre_commit(
        self,
        findings: List[Any],
        files: List[str],
        verbose: bool = False
    ) -> bool:
        """
        Enforce policies for pre-commit hook.
        
        Args:
            findings: Review findings
            files: Files being committed
            verbose: Show detailed output
            
        Returns:
            True if commit should be allowed, False otherwise
        """
        # Get current branch
        branch = self._get_current_branch()
        
        # Build context
        context = {
            'findings': findings,
            'files': files,
            'branch': branch,
        }
        
        # Evaluate policies
        result = self.engine.evaluate(
            context=context,
            scope=PolicyScope.PRE_COMMIT,
            branch=branch,
            files=files
        )
        
        # Display results
        if verbose or not result.passed:
            self._display_result(result, "Pre-Commit Policy Check")
        
        if result.should_block:
            console.print("\n[red]❌ Commit blocked by policy violations[/red]")
            console.print("[yellow]Fix the issues above or use --no-verify to skip checks[/yellow]")
            return False
        
        if result.warnings:
            console.print("\n[yellow]⚠️  Policy warnings (commit allowed)[/yellow]")
        
        if verbose and result.passed:
            console.print("\n[green]✓ All policies passed[/green]")
        
        return True
    
    def enforce_pull_request(
        self,
        findings: List[Any],
        files: List[str],
        branch: str,
        target_branch: str = "main",
        verbose: bool = False
    ) -> PolicyResult:
        """
        Enforce policies for pull request.
        
        Args:
            findings: Review findings
            files: Files changed in PR
            branch: Source branch
            target_branch: Target branch
            verbose: Show detailed output
            
        Returns:
            PolicyResult with enforcement decision
        """
        # Build context
        context = {
            'findings': findings,
            'files': files,
            'branch': branch,
            'target_branch': target_branch,
        }
        
        # Evaluate policies
        result = self.engine.evaluate(
            context=context,
            scope=PolicyScope.PULL_REQUEST,
            branch=target_branch,  # Use target branch for policy selection
            files=files
        )
        
        # Display results
        if verbose or not result.passed:
            self._display_result(result, "Pull Request Policy Check")
        
        return result
    
    def enforce_merge(
        self,
        findings: List[Any],
        files: List[str],
        branch: str,
        verbose: bool = False
    ) -> bool:
        """
        Enforce policies for merge operation.
        
        Args:
            findings: Review findings
            files: Files being merged
            branch: Target branch
            verbose: Show detailed output
            
        Returns:
            True if merge should be allowed, False otherwise
        """
        # Build context
        context = {
            'findings': findings,
            'files': files,
            'branch': branch,
        }
        
        # Evaluate policies
        result = self.engine.evaluate(
            context=context,
            scope=PolicyScope.MERGE,
            branch=branch,
            files=files
        )
        
        # Display results
        if verbose or not result.passed:
            self._display_result(result, "Merge Policy Check")
        
        if result.should_block:
            console.print("\n[red]❌ Merge blocked by policy violations[/red]")
            return False
        
        if result.requires_approval:
            console.print("\n[yellow]⚠️  Manual approval required[/yellow]")
            if result.approval_teams:
                console.print(f"Required teams: {', '.join(result.approval_teams)}")
            if result.approval_roles:
                console.print(f"Required roles: {', '.join(result.approval_roles)}")
        
        return True
    
    def _display_result(self, result: PolicyResult, title: str) -> None:
        """Display policy result in a formatted way."""
        # Create summary table
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Status", style="cyan", width=12)
        table.add_column("Details", style="white")
        
        # Overall status
        status_icon = "✓" if result.passed else "✗"
        status_color = "green" if result.passed else "red"
        table.add_row(
            f"[{status_color}]{status_icon} Overall[/{status_color}]",
            f"{'Passed' if result.passed else 'Failed'}"
        )
        
        # Violations
        if result.violations:
            table.add_row(
                "[red]Violations[/red]",
                f"{len(result.violations)} polic{'y' if len(result.violations) == 1 else 'ies'} violated"
            )
        
        # Warnings
        if result.warnings:
            table.add_row(
                "[yellow]Warnings[/yellow]",
                f"{len(result.warnings)} warning(s)"
            )
        
        # Approval required
        if result.requires_approval:
            approval_info = []
            if result.approval_teams:
                approval_info.append(f"Teams: {', '.join(result.approval_teams)}")
            if result.approval_roles:
                approval_info.append(f"Roles: {', '.join(result.approval_roles)}")
            table.add_row(
                "[yellow]Approval[/yellow]",
                " | ".join(approval_info) if approval_info else "Required"
            )
        
        console.print(table)
        
        # Display violations in detail
        if result.violations:
            console.print("\n[bold]Policy Violations:[/bold]")
            for violation in result.violations:
                self._display_violation(violation)
        
        # Display warnings
        if result.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")
    
    def _display_violation(self, violation) -> None:
        """Display a single policy violation."""
        # Create violation panel
        severity_colors = {
            'critical': 'red',
            'high': 'red',
            'medium': 'yellow',
            'low': 'blue',
        }
        color = severity_colors.get(violation.severity, 'white')

        content = []
        content.append(f"[bold]Policy:[/bold] {violation.policy_name}")

        # Handle action being either enum or string
        action_str = violation.action.value if hasattr(violation.action, 'value') else str(violation.action)
        content.append(f"[bold]Action:[/bold] {action_str}")
        content.append(f"[bold]Severity:[/bold] [{color}]{violation.severity}[/{color}]")
        
        if violation.can_override:
            content.append("[yellow]Can be overridden with justification[/yellow]")
        
        if violation.requires_approval:
            content.append("[yellow]Requires manual approval[/yellow]")
        
        # Add rule violations
        if violation.rule_violations:
            content.append(f"\n[bold]Rule Violations ({len(violation.rule_violations)}):[/bold]")
            for rv in violation.rule_violations[:5]:  # Show first 5
                content.append(f"  • {rv.message}")
                if rv.suggestion:
                    content.append(f"    → {rv.suggestion}")
            
            if len(violation.rule_violations) > 5:
                content.append(f"  ... and {len(violation.rule_violations) - 5} more")
        
        panel = Panel(
            "\n".join(content),
            title=f"[{color}]Policy Violation[/{color}]",
            border_style=color
        )
        console.print(panel)
    
    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def generate_compliance_report(
        self,
        results: List[PolicyResult],
        output_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report from policy results.
        
        Args:
            results: List of policy results
            output_file: Optional file to write report to
            
        Returns:
            Compliance report data
        """
        report = {
            'total_evaluations': len(results),
            'passed': sum(1 for r in results if r.passed),
            'failed': sum(1 for r in results if not r.passed),
            'blocked': sum(1 for r in results if r.should_block),
            'requires_approval': sum(1 for r in results if r.requires_approval),
            'total_violations': sum(len(r.violations) for r in results),
            'violations_by_severity': {
                'critical': sum(len(r.critical_violations) for r in results),
                'high': sum(len(r.high_violations) for r in results),
            },
            'results': [r.to_dict() for r in results],
        }
        
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report

