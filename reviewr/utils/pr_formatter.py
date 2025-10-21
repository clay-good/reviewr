"""
PR/MR Comment Formatter for GitHub and GitLab.

This module provides specialized formatters for creating beautiful,
actionable comments on Pull Requests and Merge Requests.
"""

from typing import TYPE_CHECKING, Dict, List, Optional
from collections import defaultdict

if TYPE_CHECKING:
    from ..review.orchestrator import ReviewResult


class PRCommentFormatter:
    """Format review results as GitHub/GitLab PR/MR comments."""
    
    def __init__(self, max_findings: int = 50, collapse_low_severity: bool = True):
        """
        Initialize PR comment formatter.
        
        Args:
            max_findings: Maximum number of findings to show (prevents huge comments)
            collapse_low_severity: Whether to collapse low/info severity findings
        """
        self.max_findings = max_findings
        self.collapse_low_severity = collapse_low_severity
    
    def format_comment(self, result: 'ReviewResult', repo_name: str = "", pr_number: str = "") -> str:
        """
        Format review result as a PR/MR comment.
        
        Args:
            result: Review result to format
            repo_name: Repository name (e.g., "owner/repo")
            pr_number: PR/MR number
            
        Returns:
            Formatted markdown comment
        """
        lines = []
        
        # Header with branding
        lines.append("## 🤖 reviewr Code Review")
        if repo_name and pr_number:
            lines.append(f"*Automated review for `{repo_name}` PR #{pr_number}*")
        lines.append("")
        
        # Quick summary with badges
        by_severity = result.get_findings_by_severity()
        critical_count = len(by_severity['critical'])
        high_count = len(by_severity['high'])
        medium_count = len(by_severity['medium'])
        low_count = len(by_severity['low'])
        info_count = len(by_severity['info'])
        total_count = len(result.findings)
        
        # Overall status badge
        if critical_count > 0:
            status = "🔴 **Action Required**"
        elif high_count > 0:
            status = "🟠 **Review Recommended**"
        elif medium_count > 0:
            status = "🟡 **Minor Issues Found**"
        elif total_count > 0:
            status = "🔵 **Looks Good**"
        else:
            status = "✅ **All Clear**"
        
        lines.append(f"### {status}")
        lines.append("")
        
        # Summary table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Files Reviewed | {result.files_reviewed} |")
        lines.append(f"| Total Issues | {total_count} |")
        
        if critical_count > 0:
            lines.append(f"| 🔴 Critical | {critical_count} |")
        if high_count > 0:
            lines.append(f"| 🟠 High | {high_count} |")
        if medium_count > 0:
            lines.append(f"| 🟡 Medium | {medium_count} |")
        if low_count > 0:
            lines.append(f"| 🔵 Low | {low_count} |")
        if info_count > 0:
            lines.append(f"| ⚪ Info | {info_count} |")
        
        lines.append("")
        
        # No issues found - early return
        if total_count == 0:
            lines.append("### ✨ Excellent Work!")
            lines.append("")
            lines.append("No issues detected. Your code looks great! 🎉")
            lines.append("")
            self._add_footer(lines, result)
            return "\n".join(lines)
        
        # Group findings by severity and file
        findings_by_severity = self._group_by_severity_and_file(result.findings)
        
        # Show critical and high severity findings first (always expanded)
        if critical_count > 0 or high_count > 0:
            lines.append("### 🚨 Critical & High Severity Issues")
            lines.append("")
            lines.append("These issues should be addressed before merging:")
            lines.append("")
            
            shown = 0
            for severity in ['critical', 'high']:
                for file_path, findings in findings_by_severity[severity].items():
                    for finding in findings:
                        if shown >= self.max_findings:
                            break
                        lines.extend(self._format_finding(finding, severity))
                        shown += 1
                    if shown >= self.max_findings:
                        break
                if shown >= self.max_findings:
                    break
            
            if shown >= self.max_findings and (critical_count + high_count) > shown:
                remaining = (critical_count + high_count) - shown
                lines.append(f"*... and {remaining} more critical/high severity issues*")
                lines.append("")
        
        # Show medium severity findings (always expanded)
        if medium_count > 0:
            lines.append("### ⚠️ Medium Severity Issues")
            lines.append("")
            lines.append("Consider addressing these issues:")
            lines.append("")
            
            shown = 0
            max_medium = self.max_findings - (critical_count + high_count)
            for file_path, findings in findings_by_severity['medium'].items():
                for finding in findings:
                    if shown >= max_medium:
                        break
                    lines.extend(self._format_finding(finding, 'medium'))
                    shown += 1
                if shown >= max_medium:
                    break
            
            if shown >= max_medium and medium_count > shown:
                remaining = medium_count - shown
                lines.append(f"*... and {remaining} more medium severity issues*")
                lines.append("")
        
        # Show low and info findings (collapsed if enabled)
        if low_count > 0 or info_count > 0:
            if self.collapse_low_severity:
                lines.append("<details>")
                lines.append(f"<summary>🔵 Low & Info Issues ({low_count + info_count})</summary>")
                lines.append("")
            else:
                lines.append("### 🔵 Low & Info Issues")
                lines.append("")
            
            shown = 0
            max_low = 20  # Limit low/info findings
            for severity in ['low', 'info']:
                for file_path, findings in findings_by_severity[severity].items():
                    for finding in findings:
                        if shown >= max_low:
                            break
                        lines.extend(self._format_finding(finding, severity))
                        shown += 1
                    if shown >= max_low:
                        break
                if shown >= max_low:
                    break
            
            if shown >= max_low and (low_count + info_count) > shown:
                remaining = (low_count + info_count) - shown
                lines.append(f"*... and {remaining} more low/info issues*")
                lines.append("")
            
            if self.collapse_low_severity:
                lines.append("</details>")
                lines.append("")
        
        # Add footer
        self._add_footer(lines, result)
        
        return "\n".join(lines)
    
    def _format_finding(self, finding, severity: str) -> List[str]:
        """Format a single finding as markdown."""
        lines = []
        
        # Severity emoji
        emoji = self._get_severity_emoji(severity)
        
        # Category icon
        category_icon = ""
        if hasattr(finding, 'category') and finding.category:
            category_icon = self._get_category_icon(finding.category) + " "
        
        # Finding type
        finding_type = finding.type.value if hasattr(finding.type, 'value') else str(finding.type)
        finding_type = finding_type.replace('_', ' ').title()
        
        # Header
        lines.append(f"#### {emoji} {category_icon}{finding_type}")
        lines.append("")
        
        # Location
        lines.append(f"**📄 File:** `{finding.file_path}` (Lines {finding.line_start}-{finding.line_end})")
        lines.append("")
        
        # Message
        lines.append(f"**Issue:** {finding.message}")
        lines.append("")
        
        # Suggestion
        if finding.suggestion:
            lines.append(f"💡 **Suggestion:** {finding.suggestion}")
            lines.append("")
        
        # Confidence
        if hasattr(finding, 'confidence'):
            confidence_pct = int(finding.confidence * 100)
            lines.append(f"*Confidence: {confidence_pct}%*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return lines
    
    def _group_by_severity_and_file(self, findings: List) -> Dict[str, Dict[str, List]]:
        """Group findings by severity and then by file."""
        grouped = {
            'critical': defaultdict(list),
            'high': defaultdict(list),
            'medium': defaultdict(list),
            'low': defaultdict(list),
            'info': defaultdict(list)
        }
        
        for finding in findings:
            severity = finding.severity.lower() if hasattr(finding, 'severity') else 'info'
            file_path = finding.file_path if hasattr(finding, 'file_path') else 'unknown'
            grouped[severity][file_path].append(finding)
        
        return grouped
    
    def _add_footer(self, lines: List[str], result: 'ReviewResult') -> None:
        """Add footer with stats and branding."""
        lines.append("---")
        lines.append("")
        
        # Performance stats
        if result.provider_stats:
            lines.append("<details>")
            lines.append("<summary>📊 Analysis Statistics</summary>")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| API Requests | {result.provider_stats.get('request_count', 0)} |")
            lines.append(f"| Input Tokens | {result.provider_stats.get('total_input_tokens', 0):,} |")
            lines.append(f"| Output Tokens | {result.provider_stats.get('total_output_tokens', 0):,} |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Branding
        lines.append("*Powered by [reviewr](https://github.com/clay-good/reviewr) - AI-powered code review* 🚀")
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emojis = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '⚪'
        }
        return emojis.get(severity, '⚪')
    
    def _get_category_icon(self, category: str) -> str:
        """Get icon for finding category."""
        icons = {
            'security': '🔒',
            'dataflow': '🌊',
            'complexity': '🧩',
            'type_safety': '🏷️',
            'performance': '⚡',
            'semantic': '🧠',
            'technical_debt': '💳',
            'syntax': '❌',
            'smell': '👃',
            'dead_code': '💀',
            'imports': '📦',
        }
        return icons.get(category, '📋')

