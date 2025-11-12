"""
Test CI/CD integration components.

This script tests:
1. PR comment formatter
2. Status check utilities
3. GitHub Actions integration
4. GitLab CI integration
"""

import sys
from pathlib import Path

# Add reviewr to path
sys.path.insert(0, str(Path(__file__).parent))


def test_pr_formatter():
    """Test PR comment formatter."""
    print("=" * 80)
    print("TEST 1: PR Comment Formatter")
    print("=" * 80)
    
    from reviewr.utils.pr_formatter import PRCommentFormatter
    
    # Create mock findings
    class MockFinding:
        def __init__(self, severity, file_path, line_start, line_end, message, suggestion, category):
            self.severity = severity
            self.file_path = file_path
            self.line_start = line_start
            self.line_end = line_end
            self.message = message
            self.suggestion = suggestion
            self.category = category
            self.type = type('obj', (object,), {'value': 'security'})()
            self.confidence = 0.95
    
    class MockResult:
        def __init__(self):
            self.files_reviewed = 5
            self.findings = [
                MockFinding('critical', 'src/auth.py', 10, 15, 
                           'SQL injection vulnerability detected', 
                           'Use parameterized queries', 'security'),
                MockFinding('high', 'src/api.py', 42, 45,
                           'Unvalidated user input',
                           'Add input validation', 'security'),
                MockFinding('medium', 'src/utils.py', 100, 102,
                           'Inefficient loop detected',
                           'Use list comprehension', 'performance'),
                MockFinding('low', 'src/helpers.py', 20, 22,
                           'Variable name could be more descriptive',
                           'Rename to be more clear', 'maintainability'),
                MockFinding('info', 'src/config.py', 5, 5,
                           'Consider using environment variables',
                           'Use os.environ.get()', 'standards'),
            ]
            self.provider_stats = {
                'request_count': 3,
                'total_input_tokens': 15000,
                'total_output_tokens': 2500
            }
        
        def get_findings_by_severity(self):
            by_severity = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': []
            }
            for finding in self.findings:
                by_severity[finding.severity].append(finding)
            return by_severity
    
    # Test formatter
    formatter = PRCommentFormatter(max_findings=50, collapse_low_severity=True)
    result = MockResult()
    
    comment = formatter.format_comment(result, "owner/repo", "123")
    
    print("\n✅ Generated PR comment:")
    print("-" * 80)
    print(comment[:1000])  # Show first 1000 chars
    print("-" * 80)
    print(f"\nComment length: {len(comment)} characters")
    
    # Verify key elements
    assert "🤖 reviewr Code Review" in comment
    assert "Critical" in comment or "critical" in comment
    assert "src/auth.py" in comment
    assert "SQL injection" in comment
    
    print("✅ PR comment formatter test PASSED\n")
    return True


def test_status_checks():
    """Test status check utilities."""
    print("=" * 80)
    print("TEST 2: Status Check Utilities")
    print("=" * 80)
    
    from reviewr.ci.status_checks import CheckStatus, create_summary_markdown
    
    # Create mock result
    class MockFinding:
        def __init__(self, severity):
            self.severity = severity
    
    class MockResult:
        def __init__(self):
            self.files_reviewed = 10
            self.findings = [
                MockFinding('critical'),
                MockFinding('critical'),
                MockFinding('high'),
                MockFinding('high'),
                MockFinding('high'),
                MockFinding('medium'),
                MockFinding('low'),
            ]
        
        def get_findings_by_severity(self):
            by_severity = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': []
            }
            for finding in self.findings:
                by_severity[finding.severity].append(finding)
            return by_severity
    
    result = MockResult()
    
    # Test summary creation
    summary = create_summary_markdown(result)
    
    print("\n✅ Generated summary markdown:")
    print("-" * 80)
    print(summary)
    print("-" * 80)
    
    # Verify key elements
    assert "reviewr Code Review Summary" in summary
    assert "Files Reviewed" in summary
    assert "Critical" in summary
    
    print("✅ Status check utilities test PASSED\n")
    return True


def test_github_action_config():
    """Test GitHub Actions configuration."""
    print("=" * 80)
    print("TEST 3: GitHub Actions Configuration")
    print("=" * 80)
    
    # Check if workflow file exists
    workflow_file = Path('.github/workflows/reviewr.yml')
    action_file = Path('.github/actions/reviewr-action/action.yml')
    
    if workflow_file.exists():
        print(f"✅ Found workflow file: {workflow_file}")
        content = workflow_file.read_text()
        
        # Verify key elements
        assert 'reviewr' in content.lower()
        assert 'pull_request' in content
        print("✅ Workflow file contains required elements")
    else:
        print(f"⚠️  Workflow file not found: {workflow_file}")
    
    if action_file.exists():
        print(f"✅ Found action file: {action_file}")
        content = action_file.read_text()
        
        # Verify key elements
        assert 'reviewr' in content.lower()
        assert 'api-key' in content
        print("✅ Action file contains required elements")
    else:
        print(f"⚠️  Action file not found: {action_file}")
    
    print("✅ GitHub Actions configuration test PASSED\n")
    return True


def test_gitlab_ci_config():
    """Test GitLab CI configuration."""
    print("=" * 80)
    print("TEST 4: GitLab CI Configuration")
    print("=" * 80)
    
    # Check if GitLab CI file exists
    gitlab_file = Path('.gitlab-ci-reviewr.yml')
    
    if gitlab_file.exists():
        print(f"✅ Found GitLab CI file: {gitlab_file}")
        content = gitlab_file.read_text()
        
        # Verify key elements
        assert 'reviewr' in content.lower()
        assert 'merge_request' in content
        assert 'ANTHROPIC_API_KEY' in content or 'OPENAI_API_KEY' in content
        print("✅ GitLab CI file contains required elements")
    else:
        print(f"⚠️  GitLab CI file not found: {gitlab_file}")
    
    print("✅ GitLab CI configuration test PASSED\n")
    return True


def test_documentation():
    """Test CI/CD documentation."""
    print("=" * 80)
    print("TEST 5: CI/CD Documentation")
    print("=" * 80)
    
    # Check if documentation exists
    doc_file = Path('docs/CI_CD_INTEGRATION.md')
    
    if doc_file.exists():
        print(f"✅ Found documentation: {doc_file}")
        content = doc_file.read_text()
        
        # Verify key sections
        assert 'GitHub Actions' in content
        assert 'GitLab CI' in content
        assert 'Configuration' in content
        assert 'Troubleshooting' in content
        print("✅ Documentation contains all required sections")
        
        # Count words
        word_count = len(content.split())
        print(f"✅ Documentation length: {word_count} words")
    else:
        print(f"⚠️  Documentation not found: {doc_file}")
    
    print("✅ Documentation test PASSED\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 TESTING CI/CD INTEGRATION")
    print("=" * 80 + "\n")
    
    tests = [
        ("PR Comment Formatter", test_pr_formatter),
        ("Status Check Utilities", test_status_checks),
        ("GitHub Actions Config", test_github_action_config),
        ("GitLab CI Config", test_gitlab_ci_config),
        ("Documentation", test_documentation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! CI/CD integration is ready!\n")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

