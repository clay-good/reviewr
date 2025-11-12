"""
Enhanced HTML formatter with interactive filtering and navigation for reviewers.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..review.orchestrator import ReviewResult


class EnhancedHtmlFormatter:
    """Enhanced HTML formatter with filtering, navigation, and quick summary."""
    
    def format_result(self, result: 'ReviewResult') -> str:
        """Format result as enhanced interactive HTML."""
        # Get quick summary for triage
        quick_summary = result.get_quick_summary()
        by_severity = result.get_findings_by_severity()
        by_file = result.get_findings_by_file()
        by_category = result.get_findings_by_category()
        prioritized = result.get_prioritized_findings()
        
        html_parts = []
        
        # HTML header with enhanced styles and JavaScript
        html_parts.append(self._get_html_header())
        
        # Quick triage summary at the top
        html_parts.append(self._format_quick_summary(quick_summary, result))
        
        # Filter controls
        html_parts.append(self._format_filter_controls(by_severity, by_category, by_file))
        
        # Navigation tabs
        html_parts.append(self._format_navigation_tabs())
        
        # Tab content: Priority view
        html_parts.append(self._format_priority_view(prioritized))
        
        # Tab content: By severity view
        html_parts.append(self._format_severity_view(by_severity))
        
        # Tab content: By file view
        html_parts.append(self._format_file_view(by_file))
        
        # Tab content: By category view
        html_parts.append(self._format_category_view(by_category))
        
        # Statistics
        if result.provider_stats:
            html_parts.append(self._format_stats(result.provider_stats))
        
        # Footer
        html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _get_html_header(self) -> str:
        """Get HTML header with styles and JavaScript."""
        return """<!DOCTYPE html>
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
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; margin-bottom: 10px; font-size: 2em; }
        h2 { color: #34495e; margin-top: 30px; margin-bottom: 15px; font-size: 1.5em; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
        h3 { color: #7f8c8d; margin-top: 20px; margin-bottom: 10px; font-size: 1.2em; }
        
        /* Quick Summary */
        .quick-summary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; }
        .quick-summary h2 { color: white; border-bottom: 2px solid rgba(255,255,255,0.3); }
        .quick-summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 15px; }
        .quick-summary-item { background: rgba(255,255,255,0.15); padding: 15px; border-radius: 5px; text-align: center; backdrop-filter: blur(10px); }
        .quick-summary-item .label { font-size: 0.9em; margin-bottom: 5px; opacity: 0.9; }
        .quick-summary-item .value { font-size: 2em; font-weight: bold; }
        .alert-badge { background: #e74c3c; padding: 5px 10px; border-radius: 15px; font-size: 0.9em; display: inline-block; margin-top: 10px; }
        
        /* Filters */
        .filters { background: #ecf0f1; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .filter-group { display: inline-block; margin-right: 20px; margin-bottom: 10px; }
        .filter-group label { font-weight: bold; margin-right: 10px; }
        .filter-group select, .filter-group input { padding: 5px 10px; border: 1px solid #bdc3c7; border-radius: 4px; }
        
        /* Navigation Tabs */
        .tabs { display: flex; border-bottom: 2px solid #3498db; margin-bottom: 20px; }
        .tab { padding: 12px 24px; cursor: pointer; background: #ecf0f1; margin-right: 5px; border-radius: 5px 5px 0 0; transition: all 0.3s; }
        .tab:hover { background: #d5dbdb; }
        .tab.active { background: #3498db; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* Findings */
        .finding { background: #fff; border-left: 4px solid #3498db; padding: 15px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.3s; }
        .finding:hover { box-shadow: 0 3px 8px rgba(0,0,0,0.15); transform: translateY(-2px); }
        .finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .finding-title { font-weight: bold; font-size: 1.1em; color: #2c3e50; }
        .finding-meta { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }
        .finding-message { margin-bottom: 10px; line-height: 1.6; }
        .finding-suggestion { background: #e8f5e9; padding: 10px; border-radius: 4px; margin-top: 10px; border-left: 3px solid #4caf50; }
        .priority-score { background: #f39c12; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: bold; }
        .priority-reasons { font-size: 0.85em; color: #7f8c8d; margin-top: 5px; }
        
        /* Severity colors */
        .severity-critical { border-left-color: #e74c3c; }
        .severity-high { border-left-color: #e67e22; }
        .severity-medium { border-left-color: #f39c12; }
        .severity-low { border-left-color: #3498db; }
        .severity-info { border-left-color: #95a5a6; }
        
        /* Badges */
        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 0.85em; font-weight: bold; text-transform: uppercase; margin-left: 5px; }
        .badge-critical { background: #e74c3c; color: white; }
        .badge-high { background: #e67e22; color: white; }
        .badge-medium { background: #f39c12; color: white; }
        .badge-low { background: #3498db; color: white; }
        .badge-info { background: #95a5a6; color: white; }
        .category-badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 0.75em; background: #ecf0f1; color: #2c3e50; margin-left: 5px; }
        
        /* File groups */
        .file-group { margin-bottom: 30px; }
        .file-header { background: #34495e; color: white; padding: 12px 15px; border-radius: 5px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .file-header:hover { background: #2c3e50; }
        .file-count { background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 15px; font-size: 0.9em; }
        
        /* Stats */
        .stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .stat-item { text-align: center; }
        .stat-label { font-size: 0.85em; color: #7f8c8d; }
        .stat-value { font-size: 1.3em; font-weight: bold; color: #2c3e50; }
        
        .no-issues { text-align: center; padding: 40px; color: #27ae60; font-size: 1.2em; }
        .timestamp { text-align: right; color: #7f8c8d; font-size: 0.9em; margin-top: 20px; }
        .hidden { display: none !important; }
    </style>
    <script>
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
        }
        
        function filterFindings() {
            const severityFilter = document.getElementById('severity-filter').value;
            const categoryFilter = document.getElementById('category-filter').value;
            const searchText = document.getElementById('search-filter').value.toLowerCase();
            
            document.querySelectorAll('.finding').forEach(finding => {
                let show = true;
                
                // Severity filter
                if (severityFilter && !finding.classList.contains(`severity-${severityFilter}`)) {
                    show = false;
                }
                
                // Category filter
                if (categoryFilter && !finding.dataset.category?.includes(categoryFilter)) {
                    show = false;
                }
                
                // Search filter
                if (searchText && !finding.textContent.toLowerCase().includes(searchText)) {
                    show = false;
                }
                
                finding.style.display = show ? 'block' : 'none';
            });
        }
        
        function toggleFileGroup(fileId) {
            const content = document.getElementById(fileId);
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🔍 Code Review Report</h1>
        <p style="color: #7f8c8d; margin-bottom: 20px;">Generated by reviewr - Enhanced Interactive Report</p>
"""
    
    def _format_quick_summary(self, summary: dict, result: 'ReviewResult') -> str:
        """Format quick triage summary."""
        parts = ['        <div class="quick-summary">']
        parts.append('            <h2>⚡ Quick Triage Summary</h2>')
        parts.append('            <div class="quick-summary-grid">')
        
        parts.append(f'                <div class="quick-summary-item">')
        parts.append(f'                    <div class="label">Total Findings</div>')
        parts.append(f'                    <div class="value">{summary["total_findings"]}</div>')
        parts.append(f'                </div>')
        
        parts.append(f'                <div class="quick-summary-item">')
        parts.append(f'                    <div class="label">Files Affected</div>')
        parts.append(f'                    <div class="value">{summary["files_affected"]}</div>')
        parts.append(f'                </div>')
        
        parts.append(f'                <div class="quick-summary-item">')
        parts.append(f'                    <div class="label">High Confidence Critical</div>')
        parts.append(f'                    <div class="value">{summary["high_confidence_critical"]}</div>')
        parts.append(f'                </div>')
        
        parts.append(f'                <div class="quick-summary-item">')
        parts.append(f'                    <div class="label">Actionable Findings</div>')
        parts.append(f'                    <div class="value">{summary["actionable_findings"]}</div>')
        parts.append(f'                </div>')
        
        parts.append('            </div>')
        
        if summary["needs_immediate_attention"]:
            parts.append('            <div class="alert-badge">⚠️ Needs Immediate Attention</div>')
        
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_filter_controls(self, by_severity: dict, by_category: dict, by_file: dict) -> str:
        """Format filter controls."""
        parts = ['        <div class="filters">']
        parts.append('            <div class="filter-group">')
        parts.append('                <label for="severity-filter">Severity:</label>')
        parts.append('                <select id="severity-filter" onchange="filterFindings()">')
        parts.append('                    <option value="">All</option>')
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if by_severity.get(severity):
                parts.append(f'                    <option value="{severity}">{severity.title()} ({len(by_severity[severity])})</option>')
        parts.append('                </select>')
        parts.append('            </div>')
        
        parts.append('            <div class="filter-group">')
        parts.append('                <label for="category-filter">Category:</label>')
        parts.append('                <select id="category-filter" onchange="filterFindings()">')
        parts.append('                    <option value="">All</option>')
        for category in sorted(by_category.keys()):
            parts.append(f'                    <option value="{category}">{category.title()} ({len(by_category[category])})</option>')
        parts.append('                </select>')
        parts.append('            </div>')
        
        parts.append('            <div class="filter-group">')
        parts.append('                <label for="search-filter">Search:</label>')
        parts.append('                <input type="text" id="search-filter" placeholder="Search findings..." oninput="filterFindings()">')
        parts.append('            </div>')
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_navigation_tabs(self) -> str:
        """Format navigation tabs."""
        return """        <div class="tabs">
            <div class="tab active" onclick="switchTab('priority-view')">🎯 Priority View</div>
            <div class="tab" onclick="switchTab('severity-view')">⚠️ By Severity</div>
            <div class="tab" onclick="switchTab('file-view')">📁 By File</div>
            <div class="tab" onclick="switchTab('category-view')">🏷️ By Category</div>
        </div>
"""
    
    def _format_priority_view(self, prioritized: list) -> str:
        """Format priority view tab."""
        parts = ['        <div id="priority-view" class="tab-content active">']
        parts.append('            <h2>Findings by Priority</h2>')
        parts.append('            <p style="color: #7f8c8d; margin-bottom: 15px;">Findings are sorted by impact and importance. Focus on the top items first.</p>')
        
        if not prioritized:
            parts.append('            <div class="no-issues">✅ No issues found!</div>')
        else:
            for i, fp in enumerate(prioritized[:50], 1):  # Show top 50
                finding = fp.finding
                parts.append(self._format_finding(finding, i, fp.priority_score, fp.reasons))
        
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_severity_view(self, by_severity: dict) -> str:
        """Format severity view tab."""
        parts = ['        <div id="severity-view" class="tab-content">']
        parts.append('            <h2>Findings by Severity</h2>')
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            findings = by_severity.get(severity, [])
            if findings:
                parts.append(f'            <h3>{severity.upper()} ({len(findings)})</h3>')
                for i, finding in enumerate(findings, 1):
                    parts.append(self._format_finding(finding, i))
        
        if not any(by_severity.values()):
            parts.append('            <div class="no-issues">✅ No issues found!</div>')
        
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_file_view(self, by_file: dict) -> str:
        """Format file view tab."""
        parts = ['        <div id="file-view" class="tab-content">']
        parts.append('            <h2>Findings by File</h2>')
        
        for file_path, findings in sorted(by_file.items()):
            file_id = f"file-{hash(file_path)}"
            parts.append(f'            <div class="file-group">')
            parts.append(f'                <div class="file-header" onclick="toggleFileGroup(\'{file_id}-content\')">')
            parts.append(f'                    <span>📄 {self._escape_html(file_path)}</span>')
            parts.append(f'                    <span class="file-count">{len(findings)} finding(s)</span>')
            parts.append(f'                </div>')
            parts.append(f'                <div id="{file_id}-content" style="margin-top: 10px;">')
            for i, finding in enumerate(findings, 1):
                parts.append(self._format_finding(finding, i))
            parts.append(f'                </div>')
            parts.append(f'            </div>')
        
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_category_view(self, by_category: dict) -> str:
        """Format category view tab."""
        parts = ['        <div id="category-view" class="tab-content">']
        parts.append('            <h2>Findings by Category</h2>')
        
        for category, findings in sorted(by_category.items()):
            parts.append(f'            <h3>{category.title()} ({len(findings)})</h3>')
            for i, finding in enumerate(findings, 1):
                parts.append(self._format_finding(finding, i))
        
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _format_finding(self, finding, index: int, priority_score: float = None, reasons: list = None) -> str:
        """Format a single finding."""
        category = finding.category or finding.type.value
        severity = finding.severity
        
        parts = [f'            <div class="finding severity-{severity}" data-category="{category}">']
        parts.append('                <div class="finding-header">')
        parts.append(f'                    <div class="finding-title">#{index} {self._escape_html(finding.type.value.replace("_", " ").title())}</div>')
        parts.append(f'                    <div>')
        if priority_score:
            parts.append(f'                        <span class="priority-score">Priority: {priority_score:.0f}</span>')
        parts.append(f'                        <span class="badge badge-{severity}">{severity}</span>')
        parts.append(f'                    </div>')
        parts.append('                </div>')
        
        if reasons:
            parts.append(f'                <div class="priority-reasons">📌 {", ".join(reasons)}</div>')
        
        parts.append(f'                <div class="finding-meta">📄 {self._escape_html(finding.file_path)} | Lines {finding.line_start}-{finding.line_end} | Confidence: {finding.confidence:.0%}</div>')
        parts.append(f'                <div class="finding-message">{self._escape_html(finding.message)}</div>')
        
        if finding.suggestion:
            parts.append(f'                <div class="finding-suggestion"><strong>💡 Suggestion:</strong> {self._escape_html(finding.suggestion)}</div>')
        
        parts.append('            </div>')
        return '\n'.join(parts)
    
    def _format_stats(self, stats: dict) -> str:
        """Format statistics section."""
        parts = ['        <div class="stats">']
        parts.append('            <h2>Statistics</h2>')
        parts.append('            <div class="stats-grid">')
        parts.append(f'                <div class="stat-item"><div class="stat-label">API Requests</div><div class="stat-value">{stats.get("request_count", 0)}</div></div>')
        parts.append(f'                <div class="stat-item"><div class="stat-label">Input Tokens</div><div class="stat-value">{stats.get("total_input_tokens", 0):,}</div></div>')
        parts.append(f'                <div class="stat-item"><div class="stat-label">Output Tokens</div><div class="stat-value">{stats.get("total_output_tokens", 0):,}</div></div>')
        parts.append('            </div>')
        parts.append('        </div>')
        return '\n'.join(parts)
    
    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return f"""        <div class="timestamp">Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</div>
    </div>
</body>
</html>"""
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

