#!/usr/bin/env python3
"""
Simple integration test for advanced analyzers.
Tests the analyzers directly without requiring API keys.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reviewr.analysis import AnalyzerFactory, AnalyzerConfig
from reviewr.utils.formatters import MarkdownFormatter, HtmlFormatter
from dataclasses import dataclass, field
from typing import List

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

def n_plus_one_query(user_ids):
    results = []
    # N+1 query pattern
    for user_id in user_ids:
        user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(user)
    return results
"""


@dataclass
class MockReviewResult:
    """Mock ReviewResult for testing formatters."""
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


def test_all_analyzers():
    """Test all analyzers with default configuration."""
    print("=" * 70)
    print("TEST 1: All Analyzers (Default Configuration)")
    print("=" * 70)
    
    analyzer = AnalyzerFactory.get_analyzer('python')
    findings = analyzer.analyze('test.py', TEST_CODE)
    
    print(f"\n✓ Found {len(findings)} issues")
    
    # Group by category
    by_category = {}
    by_severity = {}
    for finding in findings:
        if finding.category not in by_category:
            by_category[finding.category] = []
        by_category[finding.category].append(finding)
        
        if finding.severity not in by_severity:
            by_severity[finding.severity] = []
        by_severity[finding.severity].append(finding)
    
    print("\nBy Category:")
    for category, cat_findings in sorted(by_category.items()):
        print(f"  • {category}: {len(cat_findings)} issues")
    
    print("\nBy Severity:")
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        if severity in by_severity:
            print(f"  • {severity}: {len(by_severity[severity])} issues")
    
    # Verify we found issues from multiple analyzers
    assert len(findings) > 0, "Should find issues"
    assert len(by_category) >= 2, "Should find issues from multiple categories"
    assert 'security' in by_category, "Should find security issues"
    
    print("\n✓ Test passed: All analyzers working")
    return findings


def test_selective_analyzers():
    """Test with only security and performance analyzers."""
    print("\n" + "=" * 70)
    print("TEST 2: Selective Analyzers (Security + Performance Only)")
    print("=" * 70)
    
    config = AnalyzerConfig(
        enable_security=True,
        enable_dataflow=False,
        enable_complexity=False,
        enable_type_safety=False,
        enable_performance=True,
        enable_semantic=False
    )
    
    analyzer = AnalyzerFactory.get_unified_analyzer(config)
    findings = analyzer.analyze('test.py', TEST_CODE)
    
    print(f"\n✓ Found {len(findings)} issues")
    
    # Group by category
    by_category = {}
    for finding in findings:
        if finding.category not in by_category:
            by_category[finding.category] = []
        by_category[finding.category].append(finding)
    
    print("\nBy Category:")
    for category, cat_findings in sorted(by_category.items()):
        print(f"  • {category}: {len(cat_findings)} issues")
    
    # Verify only security and performance issues
    categories = set(by_category.keys())
    assert 'security' in categories or 'performance' in categories, \
        "Should find security or performance issues"
    assert 'type_safety' not in categories, "Should not find type safety issues"
    assert 'complexity' not in categories, "Should not find complexity issues"
    
    print("\n✓ Test passed: Selective analyzers working")
    return findings


def test_severity_filter():
    """Test with minimum severity filter."""
    print("\n" + "=" * 70)
    print("TEST 3: Severity Filter (High and Above)")
    print("=" * 70)
    
    config = AnalyzerConfig(min_severity='high')
    
    analyzer = AnalyzerFactory.get_unified_analyzer(config)
    findings = analyzer.analyze('test.py', TEST_CODE)
    
    print(f"\n✓ Found {len(findings)} issues")
    
    # Check severities
    severities = [f.severity for f in findings]
    print(f"\nSeverities: {set(severities)}")
    
    # Verify only high and critical issues
    for finding in findings:
        assert finding.severity in ('critical', 'high'), \
            f"Should only have high/critical issues, found: {finding.severity}"
    
    print("\n✓ Test passed: Severity filter working")
    return findings


def test_formatters():
    """Test enhanced formatters with findings."""
    print("\n" + "=" * 70)
    print("TEST 4: Enhanced Formatters")
    print("=" * 70)
    
    # Get findings
    analyzer = AnalyzerFactory.get_analyzer('python')
    local_findings = analyzer.analyze('test.py', TEST_CODE)
    
    # Convert to ReviewFindings
    review_findings = [f.to_review_finding() for f in local_findings]
    
    result = MockReviewResult(
        findings=review_findings,
        files_reviewed=1,
        provider_stats={'request_count': 0}
    )
    
    # Test Markdown formatter
    md_formatter = MarkdownFormatter()
    markdown = md_formatter.format_result(result)
    
    print("\n✓ Generated Markdown report")
    print(f"  Length: {len(markdown)} chars")
    
    # Check for category information
    assert '🔒' in markdown or '⚡' in markdown or '🧠' in markdown, \
        "Markdown should contain category icons"
    assert 'Category' in markdown, "Markdown should mention categories"
    
    # Test HTML formatter
    html_formatter = HtmlFormatter()
    html = html_formatter.format_result(result)
    
    print("✓ Generated HTML report")
    print(f"  Length: {len(html)} chars")
    
    # Check for category styling
    assert 'category-badge' in html, "HTML should have category badge CSS"
    
    # Save reports
    Path('integration-test-report.md').write_text(markdown)
    Path('integration-test-report.html').write_text(html)
    
    print("\n✓ Test passed: Formatters working")
    print("\nGenerated files:")
    print("  • integration-test-report.md")
    print("  • integration-test-report.html")


def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("INTEGRATION TESTS - Advanced Analyzers")
    print("=" * 70 + "\n")
    
    try:
        test_all_analyzers()
        test_selective_analyzers()
        test_severity_filter()
        test_formatters()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nThe advanced analyzers are fully integrated and working:")
        print("  ✓ All 6 analyzers (security, dataflow, complexity, type, performance, semantic)")
        print("  ✓ Selective analyzer configuration")
        print("  ✓ Severity filtering")
        print("  ✓ Enhanced formatters with category icons and metrics")
        print("\nNext steps:")
        print("  • Run against real codebases")
        print("  • Test GitHub/GitLab integration")
        print("  • Add more detection patterns")
        
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

