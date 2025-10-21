#!/usr/bin/env python3
"""
Test the enhanced formatters with findings from advanced analyzers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reviewr.analysis import AnalyzerFactory
from reviewr.utils.formatters import MarkdownFormatter, HtmlFormatter

# Test code with multiple issues
TEST_CODE = """
import os
import pickle

def vulnerable_function(user_id):
    # SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    # Command injection
    os.system(f"echo {user_id}")
    
    # High complexity
    if user_id > 0:
        if user_id < 100:
            if user_id % 2 == 0:
                if user_id % 3 == 0:
                    return "complex"
    
    # Resource leak
    f = open('data.txt', 'r')
    data = f.read()
    return data
"""

def test_markdown_formatter():
    """Test Markdown formatter with advanced analyzer findings."""
    print("=" * 60)
    print("TEST: Markdown Formatter with Advanced Analyzers")
    print("=" * 60)
    
    # Get analyzer and analyze code
    analyzer = AnalyzerFactory.get_analyzer('python')
    findings = analyzer.analyze('test.py', TEST_CODE)
    
    print(f"\nFound {len(findings)} issues")
    
    # Create a mock ReviewResult
    from dataclasses import dataclass, field
    from typing import List
    
    @dataclass
    class MockReviewResult:
        findings: List = field(default_factory=list)
        files_reviewed: int = 1
        total_chunks: int = 1
        provider_stats: dict = field(default_factory=dict)
        
        def get_findings_by_severity(self):
            by_severity = {'critical': [], 'high': [], 'medium': [], 'low': [], 'info': []}
            for finding in self.findings:
                if finding.severity in by_severity:
                    by_severity[finding.severity].append(finding)
            return by_severity
        
        def get_findings_by_type(self):
            return {}
        
        def has_critical_issues(self):
            return any(f.severity in ('critical', 'high') for f in self.findings)
    
    # Convert LocalFindings to ReviewFindings
    review_findings = [f.to_review_finding() for f in findings]
    
    result = MockReviewResult(
        findings=review_findings,
        files_reviewed=1,
        provider_stats={'request_count': 0}
    )
    
    # Format as Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format_result(result)
    
    print("\n" + "=" * 60)
    print("MARKDOWN OUTPUT (first 2000 chars):")
    print("=" * 60)
    print(markdown[:2000])
    
    # Check for category icons
    assert '🔒' in markdown or '⚡' in markdown or '🧠' in markdown, \
        "Should contain category icons"
    assert 'Category' in markdown or 'category' in markdown, \
        "Should mention categories"
    
    # Save to file
    output_path = Path('test-report.md')
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"\n✓ Markdown report saved to: {output_path}")
    print("✓ Markdown formatter test passed")


def test_html_formatter():
    """Test HTML formatter with advanced analyzer findings."""
    print("\n" + "=" * 60)
    print("TEST: HTML Formatter with Advanced Analyzers")
    print("=" * 60)
    
    # Get analyzer and analyze code
    analyzer = AnalyzerFactory.get_analyzer('python')
    findings = analyzer.analyze('test.py', TEST_CODE)
    
    # Create a mock ReviewResult
    from dataclasses import dataclass, field
    from typing import List
    
    @dataclass
    class MockReviewResult:
        findings: List = field(default_factory=list)
        files_reviewed: int = 1
        total_chunks: int = 1
        provider_stats: dict = field(default_factory=dict)
        
        def get_findings_by_severity(self):
            by_severity = {'critical': [], 'high': [], 'medium': [], 'low': [], 'info': []}
            for finding in self.findings:
                if finding.severity in by_severity:
                    by_severity[finding.severity].append(finding)
            return by_severity
        
        def get_findings_by_type(self):
            return {}
        
        def has_critical_issues(self):
            return any(f.severity in ('critical', 'high') for f in self.findings)
    
    # Convert LocalFindings to ReviewFindings
    review_findings = [f.to_review_finding() for f in findings]
    
    result = MockReviewResult(
        findings=review_findings,
        files_reviewed=1,
        provider_stats={'request_count': 0}
    )
    
    # Format as HTML
    formatter = HtmlFormatter()
    html = formatter.format_result(result)
    
    print(f"\nGenerated HTML report ({len(html)} chars)")
    
    # Check for category styling
    assert 'category-badge' in html, "Should have category badge CSS"
    assert 'metric-info' in html, "Should have metric info CSS"
    
    # Save to file
    output_path = Path('test-report.html')
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ HTML report saved to: {output_path}")
    print("✓ HTML formatter test passed")
    print("\n💡 Open test-report.html in a browser to see the enhanced formatting!")


def main():
    """Run all formatter tests."""
    print("\n" + "=" * 60)
    print("ENHANCED FORMATTER TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_markdown_formatter()
        test_html_formatter()
        
        print("\n" + "=" * 60)
        print("✅ ALL FORMATTER TESTS PASSED!")
        print("=" * 60)
        print("\nThe formatters now display:")
        print("  • Category icons (🔒 security, ⚡ performance, etc.)")
        print("  • Category badges and grouping")
        print("  • Metric information for complexity findings")
        print("  • Enhanced severity indicators")
        print("\nCheck the generated files:")
        print("  - test-report.md (Markdown)")
        print("  - test-report.html (HTML - open in browser)")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

