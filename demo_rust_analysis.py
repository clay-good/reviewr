"""
Interactive Demo: Rust Deep Code Analysis

Demonstrates the comprehensive Rust analysis capabilities of reviewr.
"""

from reviewr.analysis import AnalyzerFactory, RustUnifiedAnalyzer, RustAnalyzerConfig


def print_banner(title):
    """Print a formatted banner."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_code(code, title="Code"):
    """Print code with formatting."""
    print(f"\n{title}:")
    print("─" * 80)
    for i, line in enumerate(code.strip().split('\n'), 1):
        print(f"  {i:3} | {line}")
    print("─" * 80)


def print_findings(findings, analyzer_name="Rust"):
    """Print findings with rich formatting."""
    if not findings:
        print(f"\n✅ {analyzer_name} Analysis: No issues found!")
        return
    
    print(f"\n📊 {analyzer_name} Analysis: {len(findings)} issues found\n")
    
    # Count by severity
    by_severity = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
    
    # Print severity summary
    severity_icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵',
        'info': '⚪'
    }
    
    print("  Severity Breakdown:")
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = by_severity.get(severity, 0)
        if count > 0:
            icon = severity_icons.get(severity, '⚪')
            print(f"    {icon} {severity.upper()}: {count}")
    
    # Print detailed findings
    print("\n  Detailed Findings:")
    for i, finding in enumerate(findings, 1):
        icon = severity_icons.get(finding.severity, '⚪')
        print(f"\n    {i}. {icon} [{finding.severity.upper()}] {finding.category}")
        print(f"       📍 Line {finding.line_start}: {finding.message}")
        if finding.suggestion:
            print(f"       💡 Suggestion: {finding.suggestion}")
        if finding.code_snippet:
            print(f"       📝 Code: {finding.code_snippet.strip()}")


def demo_ownership_analysis():
    """Demo 1: Ownership and Borrowing Analysis."""
    print_banner("DEMO 1: Ownership & Borrowing Analysis")
    
    code = """
fn ownership_issues() {
    // Move after move
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s);  // Error: s was moved
    
    // Multiple mutable borrows
    let mut x = 5;
    let r1 = &mut x;
    let r2 = &mut x;  // Error: can't borrow x as mutable more than once
    
    // Dangling reference
    fn dangle() -> &String {
        let s = String::from("hello");
        &s  // Error: returns reference to local variable
    }
    
    // Unnecessary clone on Copy type
    let n: i32 = 42;
    let m = n.clone();  // Unnecessary: i32 implements Copy
}
"""
    
    print_code(code, "Rust Code with Ownership Issues")
    
    analyzer = AnalyzerFactory.get_analyzer('rust')
    findings = analyzer.analyze('ownership.rs', code)
    
    # Filter to ownership issues only
    ownership_findings = [f for f in findings if f.category == 'ownership']
    
    print_findings(ownership_findings, "Ownership")
    
    print("\n  💡 Key Insights:")
    print("     • Rust's ownership system prevents data races at compile time")
    print("     • Move semantics transfer ownership, making original variable invalid")
    print("     • Only one mutable borrow OR multiple immutable borrows allowed")
    print("     • References must not outlive the data they point to")


def demo_safety_analysis():
    """Demo 2: Safety Analysis."""
    print_banner("DEMO 2: Safety Analysis")
    
    code = """
use std::mem;

fn safety_issues() {
    // Unsafe block without SAFETY comment
    unsafe {
        let x = 5;
        let r = &x as *const i32;
        println!("{}", *r);
    }
    
    // Unwrap abuse
    let opt: Option<i32> = Some(5);
    let val = opt.unwrap();  // Can panic!
    
    let result: Result<i32, &str> = Ok(10);
    let num = result.unwrap();  // Can panic!
    
    // Panic patterns
    if val < 0 {
        panic!("Negative value!");
    }
    
    // Transmute (extremely unsafe)
    unsafe {
        let f: f32 = mem::transmute(42i32);
    }
    
    // Index without bounds check
    let vec = vec![1, 2, 3];
    let x = vec[10];  // Can panic!
    
    // Unimplemented
    todo!("Implement this later");
}
"""
    
    print_code(code, "Rust Code with Safety Issues")
    
    analyzer = AnalyzerFactory.get_analyzer('rust')
    findings = analyzer.analyze('safety.rs', code)
    
    # Filter to safety issues only
    safety_findings = [f for f in findings if f.category == 'safety']
    
    print_findings(safety_findings, "Safety")
    
    print("\n  💡 Key Insights:")
    print("     • unsafe blocks should have SAFETY comments explaining invariants")
    print("     • Prefer ? operator over unwrap() for error propagation")
    print("     • Use Result<T, E> instead of panic! for recoverable errors")
    print("     • transmute is extremely dangerous - use safer alternatives")
    print("     • Use .get() instead of indexing to avoid panics")


def demo_performance_analysis():
    """Demo 3: Performance Analysis."""
    print_banner("DEMO 3: Performance Analysis")
    
    code = """
async fn performance_issues() {
    // Clone in loop
    let items = vec![String::from("a"), String::from("b"), String::from("c")];
    for item in &items {
        let owned = item.clone();  // Expensive!
        process(owned);
    }
    
    // Vec without capacity
    let mut vec = Vec::new();
    for i in 0..1000 {
        vec.push(i);  // Multiple reallocations
    }
    
    // String allocation in loop
    for i in 0..100 {
        let s = format!("Item {}", i);  // Allocates each iteration
        println!("{}", s);
    }
    
    // Sequential await in loop
    let urls = vec!["url1", "url2", "url3"];
    for url in urls {
        let response = fetch(url).await;  // No concurrency!
        process(response);
    }
    
    // Inefficient iterator
    let numbers: Vec<i32> = (0..100).collect();
    let doubled: Vec<i32> = numbers.iter().map(|x| x * 2).collect();
    
    // Unnecessary Box
    let x: Box<i32> = Box::new(42);  // i32 is small, no need for heap
}
"""
    
    print_code(code, "Rust Code with Performance Issues")
    
    analyzer = AnalyzerFactory.get_analyzer('rust')
    findings = analyzer.analyze('performance.rs', code)
    
    # Filter to performance issues only
    perf_findings = [f for f in findings if f.category == 'performance']
    
    print_findings(perf_findings, "Performance")
    
    print("\n  💡 Key Insights:")
    print("     • Avoid cloning in hot loops - use references when possible")
    print("     • Pre-allocate Vec with capacity to avoid reallocations")
    print("     • Use join_all() or FuturesUnordered for concurrent async operations")
    print("     • Minimize allocations in loops (format!, to_string(), etc.)")
    print("     • Use iterators efficiently - avoid unnecessary collect()")


def demo_quality_analysis():
    """Demo 4: Quality Analysis."""
    print_banner("DEMO 4: Quality Analysis")
    
    code = """
// Public function without documentation
pub fn process_data(input: String) -> Result<String, Error> {
    // Ignoring error
    let _ = std::fs::read_to_string("config.txt");
    
    // Non-idiomatic: .len() == 0
    if input.len() == 0 {
        return Err(Error::Empty);
    }
    
    // Non-idiomatic: comparing to true
    let is_valid = validate(&input);
    if is_valid == true {
        Ok(input)
    } else {
        Err(Error::Invalid)
    }
}

// Function with too many parameters
fn complex_function(
    a: i32, b: i32, c: i32, d: i32, 
    e: i32, f: i32, g: i32, h: i32
) {
    // Deep nesting
    if a > 0 {
        if b > 0 {
            if c > 0 {
                if d > 0 {
                    if e > 0 {
                        println!("Too deep!");
                    }
                }
            }
        }
    }
}

// TODO comments
// TODO: Refactor this function
// FIXME: Handle edge cases
fn incomplete() {
    let magic_number = 12345;  // Magic number
}
"""
    
    print_code(code, "Rust Code with Quality Issues")
    
    analyzer = AnalyzerFactory.get_analyzer('rust')
    findings = analyzer.analyze('quality.rs', code)
    
    # Filter to quality issues only
    quality_findings = [f for f in findings if f.category == 'quality']
    
    print_findings(quality_findings, "Quality")
    
    print("\n  💡 Key Insights:")
    print("     • Document public APIs with /// comments")
    print("     • Use .is_empty() instead of .len() == 0")
    print("     • Avoid comparing booleans to true/false")
    print("     • Limit function parameters (use structs for many params)")
    print("     • Avoid deep nesting - extract functions")
    print("     • Address TODO/FIXME comments or create issues")


def demo_unified_analysis():
    """Demo 5: Unified Analysis with Custom Configuration."""
    print_banner("DEMO 5: Unified Analysis with Custom Configuration")
    
    code = """
use std::collections::HashMap;

async fn complex_function(data: Vec<String>) -> Result<(), Error> {
    // Multiple issues in one function
    
    // SAFETY ISSUE: Unwrap
    let config = load_config().unwrap();
    
    // PERFORMANCE ISSUE: Clone in loop
    for item in &data {
        let owned = item.clone();
        
        // PERFORMANCE ISSUE: String allocation
        let key = format!("key_{}", owned);
        
        // SAFETY ISSUE: Unsafe without comment
        unsafe {
            process_raw(&key);
        }
    }
    
    // PERFORMANCE ISSUE: Sequential await
    for url in &data {
        let response = fetch(url).await;
        process(response);
    }
    
    // QUALITY ISSUE: Ignoring error
    let _ = save_results();
    
    Ok(())
}
"""
    
    print_code(code, "Complex Rust Code with Multiple Issues")
    
    # Create custom configuration
    config = RustAnalyzerConfig(
        enable_ownership=True,
        enable_safety=True,
        enable_performance=True,
        enable_quality=True,
        min_severity='medium'  # Only show medium+ issues
    )
    
    analyzer = RustUnifiedAnalyzer(config)
    findings = analyzer.analyze('complex.rs', code)
    
    print_findings(findings, "Unified (Medium+ Severity)")
    
    # Show summary
    summary = analyzer.get_summary(findings)
    
    print("\n  📊 Analysis Summary:")
    print(f"     • Total Issues: {summary['total_findings']}")
    print(f"     • By Category:")
    for category, count in sorted(summary['by_category'].items(), key=lambda x: -x[1]):
        print(f"       - {category}: {count}")
    
    # Show metrics
    metrics = analyzer.get_metrics(findings)
    print(f"\n  📈 Metrics:")
    print(f"     • Risk Score: {metrics['risk_score']}")
    print(f"     • Critical Issues: {metrics['critical_count']}")
    print(f"     • High Issues: {metrics['high_count']}")
    print(f"     • Medium Issues: {metrics['medium_count']}")
    
    print("\n  💡 Key Insights:")
    print("     • Unified analyzer combines all 4 specialized analyzers")
    print("     • Configurable severity filtering and analyzer selection")
    print("     • Comprehensive metrics and risk scoring")
    print("     • Production-ready for CI/CD integration")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  🦀 RUST DEEP CODE ANALYSIS - INTERACTIVE DEMO")
    print("  Built by a world-class software engineer")
    print("=" * 80)
    
    try:
        demo_ownership_analysis()
        input("\n  Press Enter to continue to next demo...")
        
        demo_safety_analysis()
        input("\n  Press Enter to continue to next demo...")
        
        demo_performance_analysis()
        input("\n  Press Enter to continue to next demo...")
        
        demo_quality_analysis()
        input("\n  Press Enter to continue to next demo...")
        
        demo_unified_analysis()
        
        # Final summary
        print("\n" + "=" * 80)
        print("  ✅ DEMO COMPLETE!")
        print("=" * 80)
        
        print("\n  🎉 Rust Deep Code Analysis Features:")
        print("     • 4 specialized analyzers (ownership, safety, performance, quality)")
        print("     • 35+ detection patterns")
        print("     • Configurable severity filtering")
        print("     • Comprehensive metrics and reporting")
        print("     • Zero API calls - all local analysis")
        print("     • Production-ready for CI/CD")
        
        print("\n  🚀 Try it yourself:")
        print("     from reviewr.analysis import AnalyzerFactory")
        print("     analyzer = AnalyzerFactory.get_analyzer('rust')")
        print("     findings = analyzer.analyze('main.rs', code)")
        
    except KeyboardInterrupt:
        print("\n\n  Demo interrupted by user.")
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

