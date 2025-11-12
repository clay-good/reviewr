"""
Test suite for Go Unified Analyzer

Tests all Go analyzers:
- GoSecurityAnalyzer
- GoPerformanceAnalyzer
- GoQualityAnalyzer
- GoUnifiedAnalyzer
"""

from reviewr.analysis import AnalyzerFactory, GoUnifiedAnalyzer, GoAnalyzerConfig


# Test code with various issues
GO_CODE_WITH_ISSUES = """
package main

import (
	"database/sql"
	"fmt"
	"os/exec"
	"crypto/md5"
	"math/rand"
)

// CRITICAL: SQL injection
func getUser(username string) (*User, error) {
	query := "SELECT * FROM users WHERE name = '" + username + "'"
	row := db.Query(query)
	return parseUser(row)
}

// CRITICAL: Command injection
func runCommand(userInput string) error {
	cmd := exec.Command("sh", "-c", "echo " + userInput)
	return cmd.Run()
}

// HIGH: Weak cryptography
func hashPassword(password string) string {
	h := md5.New()
	h.Write([]byte(password))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// MEDIUM: Insecure random
func generateToken() string {
	return fmt.Sprintf("%d", rand.Int())
}

// CRITICAL: Hardcoded secret
const apiKey = "sk_live_1234567890abcdef"

// HIGH: Goroutine leak
func processItems(items []string) {
	for _, item := range items {
		go func(i string) {
			// No cancellation mechanism
			process(i)
		}(item)
	}
}

// HIGH: N+1 query pattern
func loadUsers(ids []int) ([]*User, error) {
	users := make([]*User, 0)
	for _, id := range ids {
		user, err := db.QueryRow("SELECT * FROM users WHERE id = ?", id)
		if err != nil {
			return nil, err
		}
		users = append(users, user)
	}
	return users, nil
}

// MEDIUM: String concatenation in loop
func buildMessage(parts []string) string {
	msg := ""
	for _, part := range parts {
		msg += part + " "
	}
	return msg
}

// MEDIUM: Ignored error
func saveData(data string) {
	file, _ := os.Create("data.txt")
	file.WriteString(data)
}

// HIGH: Panic without recover
func riskyOperation() {
	if someCondition {
		panic("something went wrong")
	}
}

// MEDIUM: Function with too many parameters
func complexFunction(a, b, c, d, e, f, g string) error {
	return nil
}
"""

GO_CODE_SECURITY_ONLY = """
package main

import (
	"database/sql"
	"os/exec"
	"crypto/md5"
)

// SQL injection
func query(input string) {
	db.Exec("DELETE FROM users WHERE id = " + input)
}

// Command injection
func execute(cmd string) {
	exec.Command("bash", "-c", cmd).Run()
}

// Weak crypto
func hash(data string) {
	md5.Sum([]byte(data))
}
"""

GO_CODE_PERFORMANCE_ONLY = """
package main

// Goroutine leak
func worker() {
	go func() {
		for {
			// Infinite loop without cancellation
			doWork()
		}
	}()
}

// N+1 queries
func loadData(ids []int) {
	for _, id := range ids {
		db.Query("SELECT * FROM items WHERE id = ?", id)
	}
}

// String concatenation
func build(items []string) string {
	result := ""
	for _, item := range items {
		result = result + item
	}
	return result
}
"""

GO_CODE_QUALITY_ONLY = """
package main

// Ignored error
func save() {
	file, _ := os.Create("test.txt")
	defer file.Close()
}

// Panic without recover
func dangerous() {
	panic("error")
}

// Too many parameters
func process(a, b, c, d, e, f int) {
	// ...
}

// TODO comment
// TODO: Fix this later
func incomplete() {
}
"""


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_findings(findings, title):
    """Print findings with formatting."""
    print(f"\n{title}: {len(findings)} issues found")
    
    if not findings:
        print("  ✅ No issues found!")
        return
    
    # Count by severity
    by_severity = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
    
    print("\n  By Severity:")
    severity_icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵',
        'info': '⚪'
    }
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = by_severity.get(severity, 0)
        if count > 0:
            icon = severity_icons.get(severity, '⚪')
            print(f"    {icon} {severity.upper()}: {count}")
    
    # Show top 3 issues
    print("\n  Top Issues:")
    for i, finding in enumerate(findings[:3], 1):
        print(f"\n    {i}. [{finding.severity.upper()}] {finding.category}")
        print(f"       Line {finding.line_start}: {finding.message}")
        if finding.suggestion:
            print(f"       💡 {finding.suggestion}")


def test_all_analyzers():
    """Test all Go analyzers with default configuration."""
    print_header("TEST 1: All Analyzers (Default Configuration)")
    
    analyzer = AnalyzerFactory.get_analyzer('go')
    findings = analyzer.analyze('main.go', GO_CODE_WITH_ISSUES)
    
    print_findings(findings, "Go Analysis")
    
    # Verify we found issues
    assert len(findings) > 0, "Should find issues in code with problems"
    
    # Verify we found critical issues
    critical = [f for f in findings if f.severity == 'critical']
    assert len(critical) > 0, "Should find critical issues"
    
    print("\n  ✅ Test passed!")
    return findings


def test_security_only():
    """Test security analyzer only."""
    print_header("TEST 2: Security Analysis Only")
    
    config = GoAnalyzerConfig(
        enable_security=True,
        enable_performance=False,
        enable_quality=False
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.go', GO_CODE_SECURITY_ONLY)
    
    print_findings(findings, "Security Analysis")
    
    # Verify all findings are security-related
    for finding in findings:
        assert finding.category == 'security', f"Expected security, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_performance_only():
    """Test performance analyzer only."""
    print_header("TEST 3: Performance Analysis Only")
    
    config = GoAnalyzerConfig(
        enable_security=False,
        enable_performance=True,
        enable_quality=False
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.go', GO_CODE_PERFORMANCE_ONLY)
    
    print_findings(findings, "Performance Analysis")
    
    # Verify all findings are performance-related
    for finding in findings:
        assert finding.category == 'performance', f"Expected performance, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_quality_only():
    """Test quality analyzer only."""
    print_header("TEST 4: Quality Analysis Only")
    
    config = GoAnalyzerConfig(
        enable_security=False,
        enable_performance=False,
        enable_quality=True
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.go', GO_CODE_QUALITY_ONLY)
    
    print_findings(findings, "Quality Analysis")
    
    # Verify all findings are quality-related
    for finding in findings:
        assert finding.category == 'quality', f"Expected quality, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_severity_filter():
    """Test severity filtering."""
    print_header("TEST 5: Severity Filtering (High+ Only)")
    
    config = GoAnalyzerConfig(
        min_severity='high'
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.go', GO_CODE_WITH_ISSUES)
    
    print_findings(findings, "High+ Severity Issues")
    
    # Verify all findings are high or critical
    for finding in findings:
        assert finding.severity in ['high', 'critical'], f"Expected high+, got {finding.severity}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_summary_generation():
    """Test summary generation."""
    print_header("TEST 6: Summary Generation")
    
    analyzer = GoUnifiedAnalyzer()
    findings = analyzer.analyze('main.go', GO_CODE_WITH_ISSUES)
    
    # Get summary
    summary = analyzer.get_summary(findings)
    
    print(f"\n  Total findings: {summary['total_findings']}")
    print(f"  By severity: {summary['by_severity']}")
    print(f"  By category: {summary['by_category']}")
    print(f"  By analyzer: {summary['by_analyzer']}")
    
    # Format summary
    formatted = analyzer.format_summary(findings)
    print(formatted)
    
    # Verify summary structure
    assert 'total_findings' in summary
    assert 'by_severity' in summary
    assert 'by_category' in summary
    assert 'by_analyzer' in summary
    
    print("\n  ✅ Test passed!")
    return summary


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  🧪 GO UNIFIED ANALYZER TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        findings1 = test_all_analyzers()
        findings2 = test_security_only()
        findings3 = test_performance_only()
        findings4 = test_quality_only()
        findings5 = test_severity_filter()
        summary = test_summary_generation()
        
        # Final summary
        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 80)
        
        print(f"\n  Test Results:")
        print(f"    • Test 1 (All analyzers): {len(findings1)} issues")
        print(f"    • Test 2 (Security only): {len(findings2)} issues")
        print(f"    • Test 3 (Performance only): {len(findings3)} issues")
        print(f"    • Test 4 (Quality only): {len(findings4)} issues")
        print(f"    • Test 5 (High+ severity): {len(findings5)} issues")
        print(f"    • Test 6 (Summary): {summary['total_findings']} issues")
        
        print("\n  🎉 Go analyzer is working perfectly!")
        
    except AssertionError as e:
        print(f"\n  ❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

