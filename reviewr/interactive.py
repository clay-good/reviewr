from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, Confirm

from .providers.base import ReviewFinding


class FindingAction(Enum):
    """Actions that can be taken on a finding."""
    ACCEPT = "accept"
    REJECT = "reject"
    APPLY_FIX = "apply_fix"
    SKIP = "skip"


@dataclass
class FindingDecision:
    """A decision made about a finding."""
    finding: ReviewFinding
    action: FindingAction
    note: Optional[str] = None


class InteractiveReviewer:
    """Interactive review mode for accepting/rejecting findings."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the interactive reviewer.
        
        Args:
            console: Rich console for output
        """
        self.console = console or Console()
        self.decisions: List[FindingDecision] = []
    
    def review_findings(
        self,
        findings: List[ReviewFinding],
        show_code: bool = True,
        auto_apply_fixes: bool = False
    ) -> List[FindingDecision]:
        """
        Interactively review findings.
        
        Args:
            findings: List of findings to review
            show_code: Whether to show code snippets
            auto_apply_fixes: Whether to automatically apply fixes
            
        Returns:
            List of decisions made
        """
        self.decisions = []
        
        if not findings:
            self.console.print("[yellow]No findings to review.[/yellow]")
            return self.decisions
        
        self.console.print(f"\n[bold cyan]Interactive Review Mode[/bold cyan]")
        self.console.print(f"Found {len(findings)} issue(s) to review\n")
        
        for i, finding in enumerate(findings, 1):
            self.console.print(f"\n[bold]Finding {i}/{len(findings)}[/bold]")
            self._display_finding(finding, show_code)
            
            decision = self._prompt_for_decision(finding, auto_apply_fixes)
            self.decisions.append(decision)
            
            if decision.action == FindingAction.APPLY_FIX:
                self._apply_fix(finding)
        
        self._display_summary()
        return self.decisions
    
    def _display_finding(self, finding: ReviewFinding, show_code: bool = True):
        """Display a finding to the user."""
        # Severity color mapping
        severity_colors = {
            'critical': 'red',
            'high': 'orange1',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'cyan'
        }
        color = severity_colors.get(finding.severity, 'white')
        
        # Create finding panel
        content = []
        content.append(f"[bold {color}]{finding.severity.upper()}[/bold {color}]")
        content.append(f"[bold]File:[/bold] {finding.file_path}")
        content.append(f"[bold]Lines:[/bold] {finding.line_start}-{finding.line_end}")
        content.append(f"[bold]Type:[/bold] {finding.type.value if hasattr(finding.type, 'value') else finding.type}")
        content.append(f"\n[bold]Message:[/bold]\n{finding.message}")
        
        if finding.suggestion:
            content.append(f"\n[bold]Suggestion:[/bold]\n{finding.suggestion}")
        
        if finding.confidence < 1.0:
            content.append(f"\n[bold]Confidence:[/bold] {finding.confidence:.0%}")
        
        panel = Panel(
            "\n".join(content),
            title=f"Issue in {Path(finding.file_path).name}",
            border_style=color
        )
        self.console.print(panel)
        
        # Show code snippet if available
        if show_code and finding.code_snippet:
            self.console.print("\n[bold]Code:[/bold]")
            try:
                # Try to detect language from file extension
                file_ext = Path(finding.file_path).suffix.lstrip('.')
                syntax = Syntax(
                    finding.code_snippet,
                    file_ext or "text",
                    theme="monokai",
                    line_numbers=True,
                    start_line=finding.line_start
                )
                self.console.print(syntax)
            except Exception:
                self.console.print(finding.code_snippet)
    
    def _prompt_for_decision(
        self,
        finding: ReviewFinding,
        auto_apply_fixes: bool = False
    ) -> FindingDecision:
        """Prompt user for a decision on a finding."""
        choices = {
            'a': FindingAction.ACCEPT,
            'r': FindingAction.REJECT,
            's': FindingAction.SKIP,
        }
        
        # Add apply fix option if suggestion is available
        if finding.suggestion and not auto_apply_fixes:
            choices['f'] = FindingAction.APPLY_FIX
        
        # Build prompt
        prompt_parts = []
        prompt_parts.append("[a]ccept")
        prompt_parts.append("[r]eject")
        if 'f' in choices:
            prompt_parts.append("[f]ix")
        prompt_parts.append("[s]kip")
        
        prompt_text = f"Action ({', '.join(prompt_parts)})"
        
        while True:
            choice = Prompt.ask(
                prompt_text,
                choices=list(choices.keys()),
                default='s'
            ).lower()
            
            if choice in choices:
                action = choices[choice]
                
                # Ask for note if rejecting
                note = None
                if action == FindingAction.REJECT:
                    if Confirm.ask("Add a note?", default=False):
                        note = Prompt.ask("Note")
                
                return FindingDecision(
                    finding=finding,
                    action=action,
                    note=note
                )
    
    def _apply_fix(self, finding: ReviewFinding):
        """Apply a suggested fix to a file."""
        try:
            file_path = Path(finding.file_path)
            
            if not file_path.exists():
                self.console.print(f"[red]Error:[/red] File not found: {file_path}")
                return
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Show what will be changed
            self.console.print("\n[bold yellow]Applying fix...[/bold yellow]")
            self.console.print(f"This is a suggestion only. Manual review recommended.")
            
            if not Confirm.ask("Proceed with applying fix?", default=False):
                self.console.print("[yellow]Fix not applied.[/yellow]")
                return
            
            # Note: Actual fix application would require more sophisticated logic
            # For now, we just show the suggestion
            self.console.print(f"\n[bold]Suggested fix:[/bold]")
            self.console.print(finding.suggestion)
            self.console.print("\n[yellow]Automatic fix application not yet implemented.[/yellow]")
            self.console.print("[yellow]Please apply the fix manually.[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]Error applying fix:[/red] {e}")
    
    def _display_summary(self):
        """Display summary of decisions made."""
        if not self.decisions:
            return
        
        self.console.print("\n[bold cyan]Review Summary[/bold cyan]")
        
        # Count actions
        action_counts = {
            FindingAction.ACCEPT: 0,
            FindingAction.REJECT: 0,
            FindingAction.APPLY_FIX: 0,
            FindingAction.SKIP: 0,
        }
        
        for decision in self.decisions:
            action_counts[decision.action] += 1
        
        # Create summary table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Action", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        for action, count in action_counts.items():
            if count > 0:
                table.add_row(action.value.title(), str(count))
        
        self.console.print(table)
        
        # Show rejected findings with notes
        rejected_with_notes = [
            d for d in self.decisions
            if d.action == FindingAction.REJECT and d.note
        ]
        
        if rejected_with_notes:
            self.console.print("\n[bold]Rejected findings with notes:[/bold]")
            for decision in rejected_with_notes:
                self.console.print(
                    f"  - {Path(decision.finding.file_path).name}:"
                    f"{decision.finding.line_start}: {decision.note}"
                )
    
    def get_accepted_findings(self) -> List[ReviewFinding]:
        """Get list of accepted findings."""
        return [
            d.finding for d in self.decisions
            if d.action == FindingAction.ACCEPT
        ]
    
    def get_rejected_findings(self) -> List[ReviewFinding]:
        """Get list of rejected findings."""
        return [
            d.finding for d in self.decisions
            if d.action == FindingAction.REJECT
        ]
    
    def export_decisions(self, output_path: str):
        """Export decisions to a file."""
        import json
        
        decisions_data = []
        for decision in self.decisions:
            decisions_data.append({
                'file': decision.finding.file_path,
                'line': decision.finding.line_start,
                'severity': decision.finding.severity,
                'message': decision.finding.message,
                'action': decision.action.value,
                'note': decision.note
            })
        
        with open(output_path, 'w') as f:
            json.dump(decisions_data, f, indent=2)
        
        self.console.print(f"[green]Decisions exported to:[/green] {output_path}")


def filter_findings_by_decisions(
    findings: List[ReviewFinding],
    decisions: List[FindingDecision]
) -> List[ReviewFinding]:
    """
    Filter findings based on decisions.
    
    Args:
        findings: Original list of findings
        decisions: List of decisions made
        
    Returns:
        Filtered list of findings (accepted only)
    """
    accepted_findings = set()
    
    for decision in decisions:
        if decision.action == FindingAction.ACCEPT:
            # Match by file path and line number
            key = (decision.finding.file_path, decision.finding.line_start)
            accepted_findings.add(key)
    
    return [
        f for f in findings
        if (f.file_path, f.line_start) in accepted_findings
    ]

