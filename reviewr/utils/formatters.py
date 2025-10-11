"""Output formatting utilities."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

if TYPE_CHECKING:
    from ..review.orchestrator import ReviewResult


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""
    
    @abstractmethod
    def format_result(self, result: 'ReviewResult') -> str:
        """Format a review result."""
        pass


class TerminalFormatter(OutputFormatter):
    """Format output for terminal display using Rich."""
    
    def __init__(self):
        """Initialize terminal formatter."""
        self.console = Console()
    
    def format_result(self, result: 'ReviewResult') -> str:
        """Format result for terminal display."""
        from io import StringIO
        from rich.console import Console
        
        # Create a string buffer to capture output
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        
        # Summary section
        console.print("\n[bold cyan]═══ Code Review Summary ═══[/bold cyan]\n")
        
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Label", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Files Reviewed", str(result.files_reviewed))
        summary_table.add_row("Total Findings", str(len(result.findings)))
        
        # Count by severity
        by_severity = result.get_findings_by_severity()
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                emoji = self._get_severity_emoji(severity)
                summary_table.add_row(f"{emoji} {severity.title()}", str(count))
        
        console.print(summary_table)
        console.print()
        
        # Findings section
        if result.findings:
            console.print("[bold cyan]═══ Findings ═══[/bold cyan]\n")
            
            # Group by severity and display
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                findings = by_severity[severity]
                if not findings:
                    continue
                
                emoji = self._get_severity_emoji(severity)
                console.print(f"\n[bold]{emoji} {severity.upper()} ({len(findings)})[/bold]\n")
                
                for i, finding in enumerate(findings, 1):
                    self._format_finding(console, finding, i)
        else:
            console.print("[green]✓ No issues found![/green]\n")
        
        # Stats section
        if result.provider_stats:
            console.print("\n[bold cyan]═══ Statistics ═══[/bold cyan]\n")
            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="yellow")
            
            stats_table.add_row("API Requests", str(result.provider_stats.get('request_count', 0)))
            stats_table.add_row("Input Tokens", str(result.provider_stats.get('total_input_tokens', 0)))
            stats_table.add_row("Output Tokens", str(result.provider_stats.get('total_output_tokens', 0)))
            
            console.print(stats_table)
            console.print()
        
        return buffer.getvalue()
    
    def _format_finding(self, console: Console, finding, index: int) -> None:
        """Format a single finding."""
        from ..providers.base import ReviewType

        # Special formatting for explain type
        if finding.type == ReviewType.EXPLAIN:
            console.print(f"[bold cyan]Code Explanation[/bold cyan]")
            console.print(f"   [dim]File:[/dim] {finding.file_path}")
            console.print(f"   [dim]Lines:[/dim] {finding.line_start}-{finding.line_end}")
            console.print()

            # Format the explanation with better readability
            console.print(Panel(finding.message, title="Overview", border_style="cyan"))
            console.print()

            if finding.suggestion:
                console.print(Panel(finding.suggestion, title="Additional Context", border_style="blue"))
                console.print()
            return

        # Standard formatting for other types
        # Header
        console.print(f"[bold]{index}. {finding.type.value.title()}[/bold]")
        console.print(f"   [dim]File:[/dim] {finding.file_path}")
        console.print(f"   [dim]Lines:[/dim] {finding.line_start}-{finding.line_end}")
        console.print(f"   [dim]Confidence:[/dim] {finding.confidence:.0%}")
        console.print()

        # Message
        console.print(f"   {finding.message}")
        console.print()

        # Suggestion
        if finding.suggestion:
            console.print(f"   [cyan]Suggestion:[/cyan]")
            console.print(f"   {finding.suggestion}")
            console.print()
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get symbol for severity level."""
        symbols = {
            'critical': '[CRITICAL]',
            'high': '[HIGH]',
            'medium': '[MEDIUM]',
            'low': '[LOW]',
            'info': '[INFO]',
        }
        return symbols.get(severity, '[INFO]')


class MarkdownFormatter(OutputFormatter):
    """Format output as Markdown."""
    
    def format_result(self, result: 'ReviewResult') -> str:
        """Format result as Markdown."""
        lines = []
        
        lines.append("# Code Review Report\n")
        
        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Files Reviewed**: {result.files_reviewed}")
        lines.append(f"- **Total Issues**: {len(result.findings)}\n")
        
        # Count by severity
        by_severity = result.get_findings_by_severity()
        severity_counts = []
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                severity_counts.append(f"**{severity.title()}**: {count}")
        
        if severity_counts:
            lines.append("- " + " | ".join(severity_counts))
        
        lines.append("")
        
        # Findings
        if result.findings:
            lines.append("## Findings\n")
            
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                findings = by_severity[severity]
                if not findings:
                    continue
                
                emoji = self._get_severity_emoji(severity)
                lines.append(f"### {emoji} {severity.upper()}\n")
                
                for finding in findings:
                    lines.append(f"#### {finding.type.value.title()}")
                    lines.append(f"**File**: `{finding.file_path}` | **Lines**: {finding.line_start}-{finding.line_end}\n")
                    lines.append(f"**Description**: {finding.message}\n")
                    
                    if finding.suggestion:
                        lines.append(f"**Suggestion**: {finding.suggestion}\n")
                    
                    lines.append("")
        else:
            lines.append("## ✓ No Issues Found\n")
        
        # Statistics
        if result.provider_stats:
            lines.append("## Statistics\n")
            lines.append(f"- API Requests: {result.provider_stats.get('request_count', 0)}")
            lines.append(f"- Input Tokens: {result.provider_stats.get('total_input_tokens', 0)}")
            lines.append(f"- Output Tokens: {result.provider_stats.get('total_output_tokens', 0)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get symbol for severity level."""
        symbols = {
            'critical': '[CRITICAL]',
            'high': '[HIGH]',
            'medium': '[MEDIUM]',
            'low': '[LOW]',
            'info': '[INFO]',
        }
        return symbols.get(severity, '[INFO]')

