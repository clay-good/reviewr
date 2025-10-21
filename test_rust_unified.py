"""
Test suite for Rust Unified Analyzer

Tests all Rust analyzers:
- RustOwnershipAnalyzer
- RustSafetyAnalyzer
- RustPerformanceAnalyzer
- RustQualityAnalyzer
- RustUnifiedAnalyzer
"""

from reviewr.analysis import AnalyzerFactory, RustUnifiedAnalyzer, RustAnalyzerConfig


# Test code with various Rust issues
RUST_CODE_WITH_ISSUES = """
use std::collections::HashMap;

// CRITICAL: Potential move after move
fn move_issue() {
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s);  // Error: s moved
}

// HIGH: Unsafe block without SAFETY comment
fn unsafe_code() {
    unsafe {
        let x = 5;
        let r = &x as *const i32;
        println!("{}", *r);
    }
}

// MEDIUM: Excessive unwrap usage
fn unwrap_abuse(map: HashMap<String, i32>) {
    let value = map.get("key").unwrap();
    let other = map.get("other").unwrap();
}

// HIGH: Clone in loop
fn clone_in_loop(items: Vec<String>) {
    for item in &items {
        let owned = item.clone();
        process(owned);
    }
}

// MEDIUM: String allocation in loop
fn string_alloc_loop(count: usize) {
    for i in 0..count {
        let s = format!("Item {}", i);
        println!("{}", s);
    }
}

// CRITICAL: Sequential await in loop
async fn async_issue(urls: Vec<String>) {
    for url in urls {
        let response = fetch(&url).await;
        process(response);
    }
}

// MEDIUM: Function with too many parameters
fn too_many_params(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) {
    // ...
}

// LOW: Using .len() == 0 instead of .is_empty()
fn non_idiomatic(vec: Vec<i32>) {
    if vec.len() == 0 {
        println!("empty");
    }
}

// HIGH: panic! without proper error handling
fn panic_usage(value: Option<i32>) {
    if value.is_none() {
        panic!("Value is None!");
    }
}

// INFO: TODO comment
// TODO: Implement this function
fn incomplete() {
    unimplemented!()
}
"""

RUST_CODE_OWNERSHIP_ONLY = """
fn ownership_issues() {
    // Move after move
    let s = String::from("test");
    let s2 = s;
    println!("{}", s);
    
    // Multiple mutable borrows
    let mut x = 5;
    let r1 = &mut x;
    let r2 = &mut x;
    
    // Unnecessary clone on Copy type
    let n: i32 = 42;
    let m = n.clone();
}
"""

RUST_CODE_SAFETY_ONLY = """
fn safety_issues() {
    // Unsafe without comment
    unsafe {
        let x = std::mem::transmute::<i32, f32>(42);
    }
    
    // Unwrap abuse
    let opt: Option<i32> = Some(5);
    let val = opt.unwrap();
    
    // Panic
    panic!("Error occurred");
    
    // todo! macro
    todo!("Implement this");
}
"""

RUST_CODE_PERFORMANCE_ONLY = """
fn performance_issues() {
    // Clone in loop
    let items = vec![String::from("a"), String::from("b")];
    for item in &items {
        let owned = item.clone();
        process(owned);
    }
    
    // Vec without capacity
    let mut vec = Vec::new();
    for i in 0..100 {
        vec.push(i);
    }
    
    // String concatenation
    let s = "hello" + " " + "world";
}
"""

RUST_CODE_QUALITY_ONLY = """
fn quality_issues() {
    // Ignoring error
    let _ = std::fs::read_to_string("file.txt");
    
    // Function with too many params
    fn many_params(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32) {}
    
    // Non-idiomatic
    let vec = vec![1, 2, 3];
    if vec.len() == 0 {
        println!("empty");
    }
    
    // TODO comment
    // TODO: Fix this
    let x = 42;
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
    """Test all Rust analyzers with default configuration."""
    print_header("TEST 1: All Analyzers (Default Configuration)")
    
    analyzer = AnalyzerFactory.get_analyzer('rust')
    findings = analyzer.analyze('main.rs', RUST_CODE_WITH_ISSUES)
    
    print_findings(findings, "Rust Analysis")
    
    # Verify we found issues
    assert len(findings) > 0, "Should find issues in code with problems"
    
    # Verify we found critical issues
    critical = [f for f in findings if f.severity == 'critical']
    assert len(critical) > 0, "Should find critical issues"
    
    print("\n  ✅ Test passed!")
    return findings


def test_ownership_only():
    """Test ownership analyzer only."""
    print_header("TEST 2: Ownership Analysis Only")
    
    config = RustAnalyzerConfig(
        enable_ownership=True,
        enable_safety=False,
        enable_performance=False,
        enable_quality=False
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.rs', RUST_CODE_OWNERSHIP_ONLY)
    
    print_findings(findings, "Ownership Analysis")
    
    # Verify all findings are ownership-related
    for finding in findings:
        assert finding.category == 'ownership', f"Expected ownership, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_safety_only():
    """Test safety analyzer only."""
    print_header("TEST 3: Safety Analysis Only")
    
    config = RustAnalyzerConfig(
        enable_ownership=False,
        enable_safety=True,
        enable_performance=False,
        enable_quality=False
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.rs', RUST_CODE_SAFETY_ONLY)
    
    print_findings(findings, "Safety Analysis")
    
    # Verify all findings are safety-related
    for finding in findings:
        assert finding.category == 'safety', f"Expected safety, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_performance_only():
    """Test performance analyzer only."""
    print_header("TEST 4: Performance Analysis Only")
    
    config = RustAnalyzerConfig(
        enable_ownership=False,
        enable_safety=False,
        enable_performance=True,
        enable_quality=False
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.rs', RUST_CODE_PERFORMANCE_ONLY)
    
    print_findings(findings, "Performance Analysis")
    
    # Verify all findings are performance-related
    for finding in findings:
        assert finding.category == 'performance', f"Expected performance, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_quality_only():
    """Test quality analyzer only."""
    print_header("TEST 5: Quality Analysis Only")
    
    config = RustAnalyzerConfig(
        enable_ownership=False,
        enable_safety=False,
        enable_performance=False,
        enable_quality=True
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.rs', RUST_CODE_QUALITY_ONLY)
    
    print_findings(findings, "Quality Analysis")
    
    # Verify all findings are quality-related
    for finding in findings:
        assert finding.category == 'quality', f"Expected quality, got {finding.category}"
    
    print("\n  ✅ Test passed!")
    return findings


def test_severity_filter():
    """Test severity filtering."""
    print_header("TEST 6: Severity Filtering (High+ Only)")
    
    config = RustAnalyzerConfig(
        min_severity='high'
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('main.rs', RUST_CODE_WITH_ISSUES)
    
    print_findings(findings, "High+ Severity Issues")
    
    # Verify all findings are high or critical
    for finding in findings:
        assert finding.severity in ['high', 'critical'], f"Expected high+, got {finding.severity}"
    
    print("\n  ✅ Test passed!")
    return findings


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  🧪 RUST UNIFIED ANALYZER TEST SUITE")
    print("=" * 80)
    
    try:
        # Run all tests
        findings1 = test_all_analyzers()
        findings2 = test_ownership_only()
        findings3 = test_safety_only()
        findings4 = test_performance_only()
        findings5 = test_quality_only()
        findings6 = test_severity_filter()
        
        # Final summary
        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 80)
        
        print(f"\n  Test Results:")
        print(f"    • Test 1 (All analyzers): {len(findings1)} issues")
        print(f"    • Test 2 (Ownership only): {len(findings2)} issues")
        print(f"    • Test 3 (Safety only): {len(findings3)} issues")
        print(f"    • Test 4 (Performance only): {len(findings4)} issues")
        print(f"    • Test 5 (Quality only): {len(findings5)} issues")
        print(f"    • Test 6 (High+ severity): {len(findings6)} issues")
        
        print("\n  🎉 Rust analyzer is working perfectly!")
        
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

