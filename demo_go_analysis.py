"""
Interactive Demo: Go Deep Code Analysis

Demonstrates the comprehensive Go analysis capabilities of reviewr.
"""

from reviewr.analysis import AnalyzerFactory, GoUnifiedAnalyzer, GoAnalyzerConfig


# Real-world Go code with various issues
REAL_WORLD_GO_CODE = """
package api

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
	"crypto/md5"
	"math/rand"
)

// UserAPI handles user-related HTTP requests
type UserAPI struct {
	db *sql.DB
}

// CRITICAL: SQL injection vulnerability
func (api *UserAPI) GetUser(w http.ResponseWriter, r *http.Request) {
	username := r.URL.Query().Get("username")
	query := "SELECT * FROM users WHERE username = '" + username + "'"
	
	rows, err := api.db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	
	// Process results...
}

// CRITICAL: Command injection
func (api *UserAPI) ExportData(w http.ResponseWriter, r *http.Request) {
	filename := r.URL.Query().Get("file")
	cmd := exec.Command("sh", "-c", "cat /data/" + filename)
	output, _ := cmd.Output()
	w.Write(output)
}

// HIGH: Weak cryptography
func hashPassword(password string) string {
	h := md5.New()
	h.Write([]byte(password))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// MEDIUM: Insecure random for tokens
func generateSessionToken() string {
	return fmt.Sprintf("%d-%d", rand.Int(), rand.Int())
}

// CRITICAL: Hardcoded credentials
const (
	dbPassword = "super_secret_password_123"
	apiKey     = "sk_live_abcdef1234567890"
)

// HIGH: Goroutine leak - no cancellation
func (api *UserAPI) ProcessOrders() {
	orders := api.getOrders()
	for _, order := range orders {
		go func(o Order) {
			// Long-running process without context
			api.processOrder(o)
		}(order)
	}
}

// HIGH: N+1 query pattern
func (api *UserAPI) LoadUsersWithProfiles(userIDs []int) ([]*User, error) {
	users := make([]*User, 0, len(userIDs))
	
	for _, id := range userIDs {
		// Separate query for each user
		row := api.db.QueryRow("SELECT * FROM users WHERE id = ?", id)
		var user User
		if err := row.Scan(&user); err != nil {
			return nil, err
		}
		
		// Another query for profile
		row = api.db.QueryRow("SELECT * FROM profiles WHERE user_id = ?", id)
		var profile Profile
		row.Scan(&profile)
		user.Profile = &profile
		
		users = append(users, &user)
	}
	
	return users, nil
}

// MEDIUM: String concatenation in loop
func buildReport(items []string) string {
	report := "Report:\\n"
	for _, item := range items {
		report += "- " + item + "\\n"
	}
	return report
}

// MEDIUM: Ignored error
func saveConfig(config *Config) {
	data, _ := json.Marshal(config)
	file, _ := os.Create("config.json")
	file.Write(data)
}

// HIGH: Panic without recover
func validateInput(input string) {
	if input == "" {
		panic("input cannot be empty")
	}
}

// LOW: Too many parameters
func createUser(firstName, lastName, email, phone, address, city, state, zip string) error {
	// ...
	return nil
}

// MEDIUM: Defer in loop
func processFiles(files []string) error {
	for _, filename := range files {
		f, err := os.Open(filename)
		if err != nil {
			return err
		}
		defer f.Close() // Defers accumulate!
		
		// Process file...
	}
	return nil
}
"""


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_findings_detailed(findings, title):
    """Print findings with detailed formatting."""
    print(f"\n{title}")
    print("=" * 80)
    
    if not findings:
        print("\n  ✅ No issues found!")
        return
    
    # Count by severity
    by_severity = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
    
    # Count by category
    by_category = {}
    for f in findings:
        cat = f.category or 'other'
        by_category[cat] = by_category.get(cat, 0) + 1
    
    print(f"\n📊 Found {len(findings)} issues")
    
    # Severity breakdown
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
    
    # Category breakdown
    print("\n  By Category:")
    category_icons = {
        'security': '🔒',
        'performance': '⚡',
        'quality': '✨'
    }
    for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
        icon = category_icons.get(category, '📋')
        print(f"    {icon} {category}: {count}")
    
    # Show all critical/high issues
    critical_high = [f for f in findings if f.severity in ['critical', 'high']]
    if critical_high:
        print(f"\n  🚨 Critical & High Severity Issues ({len(critical_high)}):")
        for i, finding in enumerate(critical_high, 1):
            print(f"\n    {i}. [{finding.severity.upper()}] {finding.category}")
            print(f"       📍 Line {finding.line_start}")
            print(f"       ⚠️  {finding.message}")
            if finding.suggestion:
                print(f"       💡 {finding.suggestion}")


def demo_comprehensive_analysis():
    """Demo comprehensive Go analysis."""
    print_header("DEMO 1: Comprehensive Go Analysis")
    
    print("\n  Analyzing real-world Go API code with all analyzers:")
    print("    • GoSecurityAnalyzer (12 vulnerability types)")
    print("    • GoPerformanceAnalyzer (9 anti-patterns)")
    print("    • GoQualityAnalyzer (8 quality issues)")
    
    analyzer = AnalyzerFactory.get_analyzer('go')
    findings = analyzer.analyze('api/user.go', REAL_WORLD_GO_CODE)
    
    print_findings_detailed(findings, "\n📊 Analysis Results")
    
    return findings


def demo_security_focus():
    """Demo security-focused analysis."""
    print_header("DEMO 2: Security-Focused Analysis")
    
    print("\n  Running security analysis only...")
    print("  Detecting:")
    print("    • SQL injection")
    print("    • Command injection")
    print("    • Weak cryptography")
    print("    • Hardcoded secrets")
    print("    • Insecure random")
    
    config = GoAnalyzerConfig(
        enable_security=True,
        enable_performance=False,
        enable_quality=False
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('api/user.go', REAL_WORLD_GO_CODE)
    
    print_findings_detailed(findings, "\n🔒 Security Issues")
    
    return findings


def demo_performance_focus():
    """Demo performance-focused analysis."""
    print_header("DEMO 3: Performance-Focused Analysis")
    
    print("\n  Running performance analysis only...")
    print("  Detecting:")
    print("    • Goroutine leaks")
    print("    • N+1 query patterns")
    print("    • String concatenation in loops")
    print("    • Defer in loops")
    
    config = GoAnalyzerConfig(
        enable_security=False,
        enable_performance=True,
        enable_quality=False
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('api/user.go', REAL_WORLD_GO_CODE)
    
    print_findings_detailed(findings, "\n⚡ Performance Issues")
    
    return findings


def demo_quality_focus():
    """Demo quality-focused analysis."""
    print_header("DEMO 4: Quality-Focused Analysis")
    
    print("\n  Running quality analysis only...")
    print("  Detecting:")
    print("    • Ignored errors")
    print("    • Panic without recover")
    print("    • Too many parameters")
    print("    • Defer misuse")
    
    config = GoAnalyzerConfig(
        enable_security=False,
        enable_performance=False,
        enable_quality=True
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('api/user.go', REAL_WORLD_GO_CODE)
    
    print_findings_detailed(findings, "\n✨ Quality Issues")
    
    return findings


def demo_critical_only():
    """Demo critical issues only."""
    print_header("DEMO 5: Critical Issues Only")
    
    print("\n  Filtering for critical severity only...")
    
    config = GoAnalyzerConfig(
        min_severity='critical'
    )
    
    analyzer = GoUnifiedAnalyzer(config)
    findings = analyzer.analyze('api/user.go', REAL_WORLD_GO_CODE)
    
    print_findings_detailed(findings, "\n🔴 Critical Issues")
    
    return findings


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  🚀 GO DEEP CODE ANALYSIS - INTERACTIVE DEMO")
    print("=" * 80)
    print("\n  Demonstrating world-class Go analysis capabilities")
    
    try:
        # Run all demos
        findings1 = demo_comprehensive_analysis()
        findings2 = demo_security_focus()
        findings3 = demo_performance_focus()
        findings4 = demo_quality_focus()
        findings5 = demo_critical_only()
        
        # Final summary
        print("\n" + "=" * 80)
        print("  ✅ DEMO COMPLETE!")
        print("=" * 80)
        
        print(f"\n  📊 Summary:")
        print(f"     • Demo 1 (Comprehensive): {len(findings1)} issues")
        print(f"     • Demo 2 (Security): {len(findings2)} issues")
        print(f"     • Demo 3 (Performance): {len(findings3)} issues")
        print(f"     • Demo 4 (Quality): {len(findings4)} issues")
        print(f"     • Demo 5 (Critical only): {len(findings5)} issues")
        
        print("\n  🎯 Key Capabilities:")
        print("     • 12 security vulnerability types")
        print("     • 9 performance anti-patterns")
        print("     • 8 code quality issues")
        print("     • Flexible configuration")
        print("     • Severity filtering")
        print("     • Fast local analysis (< 0.1s)")
        
        print("\n  🚀 Ready for Production:")
        print("     reviewr analyze main.go --all")
        print("     reviewr-github --all --approve-if-no-issues")
        print("     reviewr-gitlab --all")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

