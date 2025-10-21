"""
CLI commands for enterprise policy management.
"""

import sys
import json
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .policy import (
    PolicyManager,
    PolicyEnforcer,
    PolicyScope,
    PolicyAction,
    PolicyEnforcement,
    ENTERPRISE_POLICIES
)

console = Console()


@click.group(name='policy')
def policy_group():
    """
    Enterprise policy management and enforcement.
    
    Manage organization-wide policies for code quality, security, and compliance.
    Enforce policies at pre-commit, pull request, and merge stages.
    
    Examples:
        # List available policy templates
        reviewr policy list-templates
        
        # Create policy from template
        reviewr policy create security-critical my-security-policy
        
        # List active policies
        reviewr policy list
        
        # Check current code against policies
        reviewr policy check --scope pre-commit
        
        # Export policies for sharing
        reviewr policy export ./policies
    """
    pass


@policy_group.command(name='list-templates')
def list_templates():
    """List available policy templates."""
    console.print("\n[bold]Available Policy Templates:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Template ID", style="cyan", width=25)
    table.add_column("Name", style="white", width=25)
    table.add_column("Description", style="white")
    
    for template_id, config in ENTERPRISE_POLICIES.items():
        table.add_row(
            template_id,
            config.name,
            config.description
        )
    
    console.print(table)
    console.print("\n[dim]Use 'reviewr policy create <template> <policy-id>' to create a policy[/dim]")


@policy_group.command(name='create')
@click.argument('template')
@click.argument('policy_id')
@click.option('--save', is_flag=True, help='Save policy to file')
@click.option('--max-critical', type=int, help='Override max critical issues')
@click.option('--max-high', type=int, help='Override max high issues')
@click.option('--max-medium', type=int, help='Override max medium issues')
def create_policy(
    template: str,
    policy_id: str,
    save: bool,
    max_critical: Optional[int],
    max_high: Optional[int],
    max_medium: Optional[int]
):
    """
    Create a policy from a template.
    
    TEMPLATE: Template name (use list-templates to see available)
    POLICY_ID: Unique ID for the new policy
    
    Examples:
        reviewr policy create security-critical my-security
        reviewr policy create production-ready prod-policy --save
        reviewr policy create quality-gate qa-gate --max-high 5
    """
    try:
        manager = PolicyManager()
        
        # Build overrides
        overrides = {}
        if max_critical is not None:
            overrides['max_critical_issues'] = max_critical
        if max_high is not None:
            overrides['max_high_issues'] = max_high
        if max_medium is not None:
            overrides['max_medium_issues'] = max_medium
        
        # Create policy
        policy = manager.create_policy_from_template(template, policy_id, overrides)
        
        console.print(f"\n[green]✓ Created policy '{policy_id}' from template '{template}'[/green]")
        
        # Display policy details
        _display_policy(policy)
        
        # Save if requested
        if save:
            file_path = manager.save_policy(policy)
            console.print(f"\n[green]✓ Saved to {file_path}[/green]")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@policy_group.command(name='list')
@click.option('--scope', type=click.Choice(['pre-commit', 'pull-request', 'merge', 'all']), default='all')
def list_policies(scope: str):
    """
    List active policies.
    
    Examples:
        reviewr policy list
        reviewr policy list --scope pre-commit
        reviewr policy list --scope pull-request
    """
    manager = PolicyManager()
    manager.load_enterprise_policies()
    manager.load_policies_from_directory()
    
    # Get policies
    if scope == 'all':
        policies = manager.get_engine().list_policies()
    else:
        scope_enum = PolicyScope(scope)
        policies = manager.get_engine().list_policies(scope_enum)
    
    if not policies:
        console.print("[yellow]No policies found[/yellow]")
        return
    
    console.print(f"\n[bold]Active Policies ({len(policies)}):[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=25)
    table.add_column("Name", style="white", width=25)
    table.add_column("Action", style="yellow", width=15)
    table.add_column("Scope", style="blue")
    
    for policy in policies:
        scopes = ", ".join(s.value for s in policy.config.scope)
        table.add_row(
            policy.id,
            policy.config.name,
            policy.config.action.value,
            scopes
        )
    
    console.print(table)


@policy_group.command(name='check')
@click.argument('path', type=click.Path(exists=True), required=False, default='.')
@click.option('--scope', type=click.Choice(['pre-commit', 'pull-request', 'merge']), 
              default='pre-commit', help='Enforcement scope')
@click.option('--branch', help='Target branch name')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def check_policies(path: str, scope: str, branch: Optional[str], verbose: bool):
    """
    Check code against active policies.
    
    PATH: Path to check (default: current directory)
    
    Examples:
        reviewr policy check
        reviewr policy check ./src --scope pull-request
        reviewr policy check --branch main --verbose
    """
    from .cli import run_review_internal
    import asyncio
    
    try:
        # Run review to get findings
        console.print("[dim]Running code review...[/dim]")
        findings = asyncio.run(run_review_internal(path, verbose=verbose))
        
        # Get files
        from pathlib import Path
        path_obj = Path(path)
        if path_obj.is_file():
            files = [str(path_obj)]
        else:
            files = [str(f) for f in path_obj.rglob('*.py')]
        
        # Initialize enforcer
        manager = PolicyManager()
        manager.load_enterprise_policies()
        manager.load_policies_from_directory()
        enforcer = PolicyEnforcer(manager)
        
        # Enforce based on scope
        scope_enum = PolicyScope(scope)
        
        if scope_enum == PolicyScope.PRE_COMMIT:
            passed = enforcer.enforce_pre_commit(findings, files, verbose=True)
            sys.exit(0 if passed else 1)
        elif scope_enum == PolicyScope.PULL_REQUEST:
            result = enforcer.enforce_pull_request(
                findings, files, branch or 'feature', 'main', verbose=True
            )
            sys.exit(0 if result.passed else 1)
        elif scope_enum == PolicyScope.MERGE:
            passed = enforcer.enforce_merge(findings, files, branch or 'main', verbose=True)
            sys.exit(0 if passed else 1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@policy_group.command(name='export')
@click.argument('output_dir', type=click.Path())
def export_policies(output_dir: str):
    """
    Export all policies to a directory.
    
    OUTPUT_DIR: Directory to export policies to
    
    Examples:
        reviewr policy export ./policies
        reviewr policy export /shared/team-policies
    """
    try:
        manager = PolicyManager()
        manager.load_enterprise_policies()
        manager.load_policies_from_directory()
        
        output_path = Path(output_dir)
        count = manager.export_policies(output_path)
        
        console.print(f"\n[green]✓ Exported {count} polic{'y' if count == 1 else 'ies'} to {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@policy_group.command(name='import')
@click.argument('input_dir', type=click.Path(exists=True))
def import_policies(input_dir: str):
    """
    Import policies from a directory.
    
    INPUT_DIR: Directory containing policy files
    
    Examples:
        reviewr policy import ./policies
        reviewr policy import /shared/team-policies
    """
    try:
        manager = PolicyManager()
        input_path = Path(input_dir)
        count = manager.import_policies(input_path)
        
        console.print(f"\n[green]✓ Imported {count} polic{'y' if count == 1 else 'ies'} from {input_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _display_policy(policy):
    """Display policy details."""
    content = []
    content.append(f"[bold]ID:[/bold] {policy.id}")
    content.append(f"[bold]Name:[/bold] {policy.config.name}")
    content.append(f"[bold]Description:[/bold] {policy.config.description}")
    content.append(f"[bold]Action:[/bold] {policy.config.action.value}")
    content.append(f"[bold]Enforcement:[/bold] {policy.config.enforcement.value}")
    content.append(f"[bold]Scope:[/bold] {', '.join(s.value for s in policy.config.scope)}")
    
    content.append(f"\n[bold]Thresholds:[/bold]")
    content.append(f"  • Max critical issues: {policy.config.max_critical_issues}")
    content.append(f"  • Max high issues: {policy.config.max_high_issues}")
    content.append(f"  • Max medium issues: {policy.config.max_medium_issues}")
    
    if policy.config.max_complexity:
        content.append(f"  • Max complexity: {policy.config.max_complexity}")
    if policy.config.min_test_coverage:
        content.append(f"  • Min test coverage: {policy.config.min_test_coverage * 100}%")
    
    if policy.rules:
        content.append(f"\n[bold]Rules ({len(policy.rules)}):[/bold]")
        for rule_id in policy.rules:
            content.append(f"  • {rule_id}")
    
    panel = Panel(
        "\n".join(content),
        title="[bold cyan]Policy Details[/bold cyan]",
        border_style="cyan"
    )
    console.print(panel)


if __name__ == '__main__':
    policy_group()

