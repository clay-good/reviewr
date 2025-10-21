"""
Test suite for JavaScript/TypeScript Unified Analyzer

Tests all specialized analyzers:
- Security
- Performance
- Type Safety (TypeScript)
- Code Quality
"""

from reviewr.analysis import (
    JavaScriptUnifiedAnalyzer,
    JavaScriptAnalyzerConfig,
    AnalyzerFactory
)


# Test code with various issues
TEST_JS_CODE = """
// Security issues
function handleLogin(username, password) {
    // SQL injection vulnerability
    const query = "SELECT * FROM users WHERE username = '" + username + "'";
    db.query(query);
    
    // XSS vulnerability
    document.getElementById('welcome').innerHTML = username;
    
    // Hardcoded secret
    const apiKey = 'sk_live_1234567890abcdefghijklmnop';
    
    // eval usage
    eval('console.log("dangerous")');
}

// Performance issues
function renderList(items) {
    // DOM operations in loop
    for (let i = 0; i < items.length; i++) {
        document.getElementById('list').appendChild(createItem(items[i]));
    }
    
    // Multiple array iterations
    const result = items.filter(x => x.active).map(x => x.name);
    
    // N+1 query pattern
    for (const item of items) {
        fetch('/api/details/' + item.id);
    }
}

// Memory leak
function setupListener() {
    document.addEventListener('click', handleClick);
    // No cleanup!
}

// React performance issues
function MyComponent({ data }) {
    // Inline function in JSX
    return <button onClick={() => console.log('clicked')}>Click</button>;
}

// Code quality issues
function complexFunction(a, b, c, d, e, f) {
    if (a) {
        if (b) {
            if (c) {
                if (d) {
                    if (e) {
                        return f;
                    }
                }
            }
        }
    }
    return null;
}

// Console statements
console.log('Debug info');

// var usage
var oldStyle = 'bad';

// == instead of ===
if (value == 5) {
    console.log('loose equality');
}
"""

TEST_TS_CODE = """
// TypeScript type safety issues

// Missing type annotations
function calculate(x, y) {
    return x + y;
}

// any type usage
function processData(data: any) {
    return data.value;
}

// Non-null assertion
function getValue(obj: any) {
    return obj.value!;
}

// Type assertion
const value = someValue as string;

// Missing return type
function fetchData(id: number) {
    return fetch('/api/' + id);
}

// Unsafe type coercion
const result = "5" + 10;

// Missing null check
function process(obj) {
    return obj.nested.value;
}
"""


def test_all_analyzers():
    """Test all analyzers with default configuration."""
    print("=" * 70)
    print("TEST 1: All Analyzers (JavaScript)")
    print("=" * 70)
    
    analyzer = AnalyzerFactory.get_analyzer('javascript')
    findings = analyzer.analyze('test.js', TEST_JS_CODE)
    
    print(f"\n✓ Found {len(findings)} issues")
    
    # Group by category
    by_category = {}
    by_severity = {}
    for finding in findings:
        category = finding.category or 'other'
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(finding)
        
        if finding.severity not in by_severity:
            by_severity[finding.severity] = []
        by_severity[finding.severity].append(finding)
    
    print("\nBy Category:")
    for category, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  {category}: {len(items)}")
    
    print("\nBy Severity:")
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = len(by_severity.get(severity, []))
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    # Show first 5 findings
    print("\nSample Findings:")
    for i, finding in enumerate(findings[:5], 1):
        print(f"\n{i}. [{finding.severity.upper()}] {finding.category}")
        print(f"   Line {finding.line_start}: {finding.message}")
        if finding.suggestion:
            print(f"   → {finding.suggestion}")
    
    assert len(findings) > 0, "Should find issues in test code"
    print("\n✓ Test passed!")


def test_typescript_analysis():
    """Test TypeScript-specific analysis."""
    print("\n" + "=" * 70)
    print("TEST 2: TypeScript Type Safety")
    print("=" * 70)
    
    analyzer = AnalyzerFactory.get_analyzer('typescript')
    findings = analyzer.analyze('test.ts', TEST_TS_CODE)
    
    print(f"\n✓ Found {len(findings)} issues")
    
    # Count type safety issues
    type_issues = [f for f in findings if f.category == 'type_safety']
    print(f"  Type safety issues: {len(type_issues)}")
    
    # Show type safety findings
    print("\nType Safety Findings:")
    for i, finding in enumerate(type_issues[:5], 1):
        print(f"\n{i}. [{finding.severity.upper()}]")
        print(f"   Line {finding.line_start}: {finding.message}")
        if finding.suggestion:
            print(f"   → {finding.suggestion}")
    
    assert len(type_issues) > 0, "Should find type safety issues"
    print("\n✓ Test passed!")


def test_selective_analyzers():
    """Test with selective analyzers enabled."""
    print("\n" + "=" * 70)
    print("TEST 3: Security Only")
    print("=" * 70)
    
    config = JavaScriptAnalyzerConfig(
        enable_security=True,
        enable_performance=False,
        enable_type_safety=False,
        enable_quality=False
    )
    
    analyzer = JavaScriptUnifiedAnalyzer(config)
    findings = analyzer.analyze('test.js', TEST_JS_CODE)
    
    print(f"\n✓ Found {len(findings)} security issues")
    
    # All should be security issues
    security_issues = [f for f in findings if f.category == 'security']
    print(f"  Security issues: {len(security_issues)}")
    
    # Show findings
    print("\nSecurity Findings:")
    for i, finding in enumerate(security_issues[:5], 1):
        print(f"\n{i}. [{finding.severity.upper()}]")
        print(f"   Line {finding.line_start}: {finding.message}")
    
    assert len(security_issues) > 0, "Should find security issues"
    print("\n✓ Test passed!")


def test_severity_filter():
    """Test severity filtering."""
    print("\n" + "=" * 70)
    print("TEST 4: High Severity Only")
    print("=" * 70)
    
    config = JavaScriptAnalyzerConfig(
        min_severity='high'
    )
    
    analyzer = JavaScriptUnifiedAnalyzer(config)
    findings = analyzer.analyze('test.js', TEST_JS_CODE)
    
    print(f"\n✓ Found {len(findings)} high+ severity issues")
    
    # Check severities
    for finding in findings:
        assert finding.severity in ['high', 'critical'], \
            f"Should only have high/critical, got {finding.severity}"
    
    print("\nHigh Severity Findings:")
    for i, finding in enumerate(findings[:5], 1):
        print(f"\n{i}. [{finding.severity.upper()}] {finding.category}")
        print(f"   Line {finding.line_start}: {finding.message}")
    
    print("\n✓ Test passed!")


def test_summary_generation():
    """Test summary generation."""
    print("\n" + "=" * 70)
    print("TEST 5: Summary Generation")
    print("=" * 70)
    
    analyzer = JavaScriptUnifiedAnalyzer()
    findings = analyzer.analyze('test.js', TEST_JS_CODE)
    
    summary = analyzer.get_summary(findings)
    print("\n" + summary)
    
    assert "Found" in summary, "Summary should contain findings count"
    assert "By Severity:" in summary, "Summary should contain severity breakdown"
    assert "By Category:" in summary, "Summary should contain category breakdown"
    
    print("\n✓ Test passed!")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("JAVASCRIPT/TYPESCRIPT UNIFIED ANALYZER TEST SUITE")
    print("=" * 70)
    
    try:
        test_all_analyzers()
        test_typescript_analysis()
        test_selective_analyzers()
        test_severity_filter()
        test_summary_generation()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

