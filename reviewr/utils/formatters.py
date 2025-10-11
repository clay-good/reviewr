
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


class HtmlFormatter(OutputFormatter):
    """Format output as HTML."""

    def format_result(self, result: 'ReviewResult') -> str:
        """Format result as HTML."""
        html_parts = []

        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report - reviewr</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; margin-bottom: 10px; font-size: 2em; }
        h2 { color: #34495e; margin-top: 30px; margin-bottom: 15px; font-size: 1.5em; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
        h3 { color: #7f8c8d; margin-top: 20px; margin-bottom: 10px; font-size: 1.2em; }
        .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .summary-item { background: white; padding: 15px; border-radius: 5px; text-align: center; }
        .summary-item .label { font-size: 0.9em; color: #7f8c8d; margin-bottom: 5px; }
        .summary-item .value { font-size: 1.8em; font-weight: bold; color: #2c3e50; }
        .finding { background: #fff; border-left: 4px solid #3498db; padding: 15px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .finding-title { font-weight: bold; font-size: 1.1em; color: #2c3e50; }
        .finding-meta { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }
        .finding-message { margin-bottom: 10px; line-height: 1.6; }
        .finding-suggestion { background: #e8f5e9; padding: 10px; border-radius: 4px; margin-top: 10px; border-left: 3px solid #4caf50; }
        .severity-critical { border-left-color: #e74c3c; }
        .severity-high { border-left-color: #e67e22; }
        .severity-medium { border-left-color: #f39c12; }
        .severity-low { border-left-color: #3498db; }
        .severity-info { border-left-color: #95a5a6; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; font-weight: bold; text-transform: uppercase; }
        .badge-critical { background: #e74c3c; color: white; }
        .badge-high { background: #e67e22; color: white; }
        .badge-medium { background: #f39c12; color: white; }
        .badge-low { background: #3498db; color: white; }
        .badge-info { background: #95a5a6; color: white; }
        .stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .stat-item { text-align: center; }
        .stat-label { font-size: 0.85em; color: #7f8c8d; }
        .stat-value { font-size: 1.3em; font-weight: bold; color: #2c3e50; }
        .no-issues { text-align: center; padding: 40px; color: #27ae60; font-size: 1.2em; }
        .timestamp { text-align: right; color: #7f8c8d; font-size: 0.9em; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Code Review Report</h1>
        <p style="color: #7f8c8d; margin-bottom: 20px;">Generated by reviewr</p>
""")

        # Summary section
        by_severity = result.get_findings_by_severity()
        html_parts.append('        <div class="summary">')
        html_parts.append('            <h2>Summary</h2>')
        html_parts.append('            <div class="summary-grid">')
        html_parts.append(f'                <div class="summary-item"><div class="label">Files Reviewed</div><div class="value">{result.files_reviewed}</div></div>')
        html_parts.append(f'                <div class="summary-item"><div class="label">Total Findings</div><div class="value">{len(result.findings)}</div></div>')

        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                html_parts.append(f'                <div class="summary-item"><div class="label">{severity.title()}</div><div class="value">{count}</div></div>')

        html_parts.append('            </div>')
        html_parts.append('        </div>')

        # Findings section
        if result.findings:
            html_parts.append('        <h2>Findings</h2>')

            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                findings = by_severity[severity]
                if not findings:
                    continue

                html_parts.append(f'        <h3>{severity.upper()} ({len(findings)})</h3>')

                for finding in findings:
                    html_parts.append(f'        <div class="finding severity-{severity}">')
                    html_parts.append('            <div class="finding-header">')
                    html_parts.append(f'                <div class="finding-title">{self._escape_html(finding.type.value.title())}</div>')
                    html_parts.append(f'                <span class="badge badge-{severity}">{severity}</span>')
                    html_parts.append('            </div>')
                    html_parts.append(f'            <div class="finding-meta">📄 {self._escape_html(finding.file_path)} | Lines {finding.line_start}-{finding.line_end} | Confidence: {finding.confidence:.0%}</div>')
                    html_parts.append(f'            <div class="finding-message">{self._escape_html(finding.message)}</div>')

                    if finding.suggestion:
                        html_parts.append(f'            <div class="finding-suggestion"><strong>💡 Suggestion:</strong> {self._escape_html(finding.suggestion)}</div>')

                    html_parts.append('        </div>')
        else:
            html_parts.append('        <div class="no-issues">✅ No issues found!</div>')

        # Stats section
        if result.provider_stats:
            html_parts.append('        <div class="stats">')
            html_parts.append('            <h2>Statistics</h2>')
            html_parts.append('            <div class="stats-grid">')
            html_parts.append(f'                <div class="stat-item"><div class="stat-label">API Requests</div><div class="stat-value">{result.provider_stats.get("request_count", 0)}</div></div>')
            html_parts.append(f'                <div class="stat-item"><div class="stat-label">Input Tokens</div><div class="stat-value">{result.provider_stats.get("total_input_tokens", 0):,}</div></div>')
            html_parts.append(f'                <div class="stat-item"><div class="stat-label">Output Tokens</div><div class="stat-value">{result.provider_stats.get("total_output_tokens", 0):,}</div></div>')
            html_parts.append('            </div>')
            html_parts.append('        </div>')

        # Footer
        html_parts.append(f'        <div class="timestamp">Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</div>')
        html_parts.append('    </div>')
        html_parts.append('</body>')
        html_parts.append('</html>')

        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


class JunitFormatter(OutputFormatter):
    """Format output as JUnit XML."""

    def format_result(self, result: 'ReviewResult') -> str:
        """Format result as JUnit XML."""
        import xml.etree.ElementTree as ET
        from xml.dom import minidom

        # Create root testsuite element
        testsuite = ET.Element('testsuite')
        testsuite.set('name', 'reviewr Code Review')
        testsuite.set('tests', str(len(result.findings)))

        # Count failures (critical and high severity)
        by_severity = result.get_findings_by_severity()
        failures = len(by_severity['critical']) + len(by_severity['high'])
        testsuite.set('failures', str(failures))
        testsuite.set('errors', '0')
        testsuite.set('skipped', '0')
        testsuite.set('timestamp', datetime.now(timezone.utc).isoformat())

        # Group findings by file
        findings_by_file: Dict[str, List] = {}
        for finding in result.findings:
            if finding.file_path not in findings_by_file:
                findings_by_file[finding.file_path] = []
            findings_by_file[finding.file_path].append(finding)

        # Create testcase for each file
        for file_path, findings in findings_by_file.items():
            testcase = ET.SubElement(testsuite, 'testcase')
            testcase.set('name', file_path)
            testcase.set('classname', f'reviewr.{file_path.replace("/", ".").replace(".py", "")}')
            testcase.set('time', '0')

            # Add failures for critical and high severity findings
            for finding in findings:
                if finding.severity in ['critical', 'high']:
                    failure = ET.SubElement(testcase, 'failure')
                    failure.set('message', f'{finding.type.value}: {finding.message}')
                    failure.set('type', finding.severity)

                    # Add detailed information in failure text
                    failure_text = []
                    failure_text.append(f'File: {finding.file_path}')
                    failure_text.append(f'Lines: {finding.line_start}-{finding.line_end}')
                    failure_text.append(f'Severity: {finding.severity}')
                    failure_text.append(f'Type: {finding.type.value}')
                    failure_text.append(f'Confidence: {finding.confidence:.0%}')
                    failure_text.append(f'\nMessage: {finding.message}')

                    if finding.suggestion:
                        failure_text.append(f'\nSuggestion: {finding.suggestion}')

                    failure.text = '\n'.join(failure_text)

            # Add system-out for all findings (including warnings)
            if findings:
                system_out = ET.SubElement(testcase, 'system-out')
                out_lines = []
                out_lines.append(f'Review findings for {file_path}:')
                out_lines.append('')

                for finding in findings:
                    out_lines.append(f'[{finding.severity.upper()}] {finding.type.value}')
                    out_lines.append(f'  Lines: {finding.line_start}-{finding.line_end}')
                    out_lines.append(f'  Confidence: {finding.confidence:.0%}')
                    out_lines.append(f'  Message: {finding.message}')
                    if finding.suggestion:
                        out_lines.append(f'  Suggestion: {finding.suggestion}')
                    out_lines.append('')

                system_out.text = '\n'.join(out_lines)

        # Add properties with summary information
        properties = ET.SubElement(testsuite, 'properties')

        prop = ET.SubElement(properties, 'property')
        prop.set('name', 'files_reviewed')
        prop.set('value', str(result.files_reviewed))

        prop = ET.SubElement(properties, 'property')
        prop.set('name', 'total_findings')
        prop.set('value', str(len(result.findings)))

        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            prop = ET.SubElement(properties, 'property')
            prop.set('name', f'{severity}_findings')
            prop.set('value', str(count))

        if result.provider_stats:
            prop = ET.SubElement(properties, 'property')
            prop.set('name', 'api_requests')
            prop.set('value', str(result.provider_stats.get('request_count', 0)))

            prop = ET.SubElement(properties, 'property')
            prop.set('name', 'total_tokens')
            prop.set('value', str(result.provider_stats.get('total_input_tokens', 0) + result.provider_stats.get('total_output_tokens', 0)))

        # Convert to pretty-printed XML string
        xml_str = ET.tostring(testsuite, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')

