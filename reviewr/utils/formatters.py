"""Output formatting utilities."""

import json
import hashlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Any
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


class SarifFormatter(OutputFormatter):
    """Format output as SARIF 2.1.0 JSON."""

    def format_result(self, result: 'ReviewResult') -> str:
        """Format result as SARIF 2.1.0 JSON."""
        sarif_log = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [self._create_run(result)]
        }

        return json.dumps(sarif_log, indent=2, ensure_ascii=False)

    def _create_run(self, result: 'ReviewResult') -> Dict[str, Any]:
        """Create a SARIF run object."""
        # Create rules from findings
        rules = self._create_rules(result.findings)

        # Create results
        sarif_results = []
        for finding in result.findings:
            sarif_results.append(self._create_result(finding))

        run = {
            "tool": {
                "driver": {
                    "name": "reviewr",
                    "version": "0.1.0",
                    "semanticVersion": "0.1.0",
                    "informationUri": "https://github.com/your-org/reviewr",
                    "rules": rules
                }
            },
            "results": sarif_results,
            "columnKind": "utf16CodeUnits"
        }

        # Add invocation info if we have stats
        if result.provider_stats:
            run["invocations"] = [{
                "executionSuccessful": True,
                "startTimeUtc": datetime.now(timezone.utc).isoformat(),
                "endTimeUtc": datetime.now(timezone.utc).isoformat(),
                "machine": "reviewr-cli"
            }]

        return run

    def _create_rules(self, findings: List) -> List[Dict[str, Any]]:
        """Create SARIF rules from findings."""
        rules_dict = {}

        for finding in findings:
            rule_id = self._get_rule_id(finding)
            if rule_id not in rules_dict:
                rules_dict[rule_id] = self._create_rule(finding)

        return list(rules_dict.values())

    def _create_rule(self, finding) -> Dict[str, Any]:
        """Create a SARIF rule from a finding."""
        from ..providers.base import ReviewType

        rule_id = self._get_rule_id(finding)

        # Map review types to descriptions
        descriptions = {
            ReviewType.SECURITY: {
                "short": "Security vulnerability detected",
                "full": "Identifies potential security vulnerabilities, injections, authentication issues, and other security concerns."
            },
            ReviewType.PERFORMANCE: {
                "short": "Performance issue detected",
                "full": "Identifies inefficient algorithms, bottlenecks, and optimization opportunities."
            },
            ReviewType.CORRECTNESS: {
                "short": "Correctness issue detected",
                "full": "Identifies logic errors, edge cases, and potential bugs."
            },
            ReviewType.MAINTAINABILITY: {
                "short": "Maintainability issue detected",
                "full": "Identifies code clarity, documentation, and naming convention issues."
            },
            ReviewType.ARCHITECTURE: {
                "short": "Architecture issue detected",
                "full": "Identifies design pattern violations, SOLID principle violations, and code structure issues."
            },
            ReviewType.STANDARDS: {
                "short": "Standards violation detected",
                "full": "Identifies language idiom violations, convention issues, and style guideline violations."
            },
            ReviewType.EXPLAIN: {
                "short": "Code explanation",
                "full": "Provides comprehensive code explanation and overview."
            }
        }

        desc = descriptions.get(finding.type, descriptions[ReviewType.CORRECTNESS])

        rule = {
            "id": rule_id,
            "name": f"{finding.type.value.title()}Rule",
            "shortDescription": {
                "text": desc["short"]
            },
            "fullDescription": {
                "text": desc["full"]
            },
            "defaultConfiguration": {
                "level": self._map_severity_to_level(finding.severity)
            },
            "properties": {
                "tags": [finding.type.value],
                "precision": self._map_confidence_to_precision(finding.confidence)
            }
        }

        # Add security-severity for security rules
        if finding.type == ReviewType.SECURITY:
            rule["properties"]["security-severity"] = self._map_severity_to_security_score(finding.severity)
        else:
            rule["properties"]["problem.severity"] = self._map_severity_to_problem_severity(finding.severity)

        return rule

    def _create_result(self, finding) -> Dict[str, Any]:
        """Create a SARIF result from a finding."""
        result = {
            "ruleId": self._get_rule_id(finding),
            "level": self._map_severity_to_level(finding.severity),
            "message": {
                "text": finding.message
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": finding.file_path
                    },
                    "region": {
                        "startLine": finding.line_start,
                        "endLine": finding.line_end
                    }
                }
            }],
            "partialFingerprints": {
                "primaryLocationLineHash": self._generate_fingerprint(finding)
            }
        }

        # Add suggestion as fix if available
        if finding.suggestion:
            result["fixes"] = [{
                "description": {
                    "text": finding.suggestion
                }
            }]

        return result

    def _get_rule_id(self, finding) -> str:
        """Generate a rule ID for a finding."""
        return f"reviewr-{finding.type.value}"

    def _map_severity_to_level(self, severity: str) -> str:
        """Map reviewr severity to SARIF level."""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note',
            'info': 'note'
        }
        return mapping.get(severity, 'warning')

    def _map_confidence_to_precision(self, confidence: float) -> str:
        """Map confidence score to SARIF precision."""
        if confidence >= 0.9:
            return "very-high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"

    def _map_severity_to_security_score(self, severity: str) -> str:
        """Map severity to security score (0.1-10.0)."""
        mapping = {
            'critical': '9.5',
            'high': '8.0',
            'medium': '5.5',
            'low': '3.0',
            'info': '1.0'
        }
        return mapping.get(severity, '5.5')

    def _map_severity_to_problem_severity(self, severity: str) -> str:
        """Map severity to problem severity."""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'recommendation',
            'info': 'recommendation'
        }
        return mapping.get(severity, 'warning')

    def _generate_fingerprint(self, finding) -> str:
        """Generate a fingerprint for the finding."""
        # Create a stable fingerprint based on file path, line, and message
        fingerprint_data = f"{finding.file_path}:{finding.line_start}:{finding.message}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]

