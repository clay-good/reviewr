"""
Demo: JavaScript/TypeScript Deep Code Analysis

Demonstrates the comprehensive analysis capabilities for JavaScript and TypeScript:
- Security vulnerabilities (XSS, SQL injection, command injection, etc.)
- Performance anti-patterns (DOM operations, memory leaks, N+1 queries)
- Type safety issues (TypeScript)
- Code quality (complexity, code smells, standards)
"""

from reviewr.analysis import (
    JavaScriptUnifiedAnalyzer,
    JavaScriptAnalyzerConfig,
    AnalyzerFactory
)


# Realistic problematic code
PROBLEMATIC_CODE = """
// E-commerce application with multiple issues

// Authentication handler with security vulnerabilities
async function handleLogin(req, res) {
    const { username, password } = req.body;
    
    // CRITICAL: SQL injection vulnerability
    const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
    const user = await db.query(query);
    
    // HIGH: Hardcoded secret
    const jwtSecret = 'super-secret-key-12345';
    const token = jwt.sign({ userId: user.id }, jwtSecret);
    
    // MEDIUM: Insecure randomness for session ID
    const sessionId = Math.random().toString(36);
    
    res.json({ token, sessionId });
}

// Product listing with performance issues
async function loadProducts(categoryId) {
    const products = await db.query('SELECT * FROM products WHERE category_id = ?', [categoryId]);
    
    // HIGH: N+1 query pattern
    for (const product of products) {
        const reviews = await db.query('SELECT * FROM reviews WHERE product_id = ?', [product.id]);
        product.reviews = reviews;
        
        const seller = await db.query('SELECT * FROM sellers WHERE id = ?', [product.seller_id]);
        product.seller = seller;
    }
    
    return products;
}

// UI rendering with DOM performance issues
function renderProductList(products) {
    const container = document.getElementById('products');
    
    // MEDIUM: DOM operations in loop
    for (let i = 0; i < products.length; i++) {
        const div = document.createElement('div');
        div.innerHTML = products[i].name;  // HIGH: XSS vulnerability
        container.appendChild(div);
    }
    
    // LOW: Multiple array iterations
    const activeProducts = products.filter(p => p.active).map(p => p.name);
}

// React component with performance issues
function ProductCard({ product, onAddToCart }) {
    // LOW: Inline function causes re-renders
    return (
        <div>
            <h3>{product.name}</h3>
            <button onClick={() => onAddToCart(product.id)}>
                Add to Cart
            </button>
        </div>
    );
}

// Memory leak example
function setupProductWatcher() {
    // MEDIUM: Event listener without cleanup
    document.addEventListener('scroll', () => {
        loadMoreProducts();
    });
    
    // HIGH: setInterval without clearInterval
    setInterval(() => {
        refreshPrices();
    }, 5000);
}

// Command injection vulnerability
async function generateReport(req, res) {
    const { format, filename } = req.query;
    
    // CRITICAL: Command injection
    const command = `convert report.pdf -format ${format} ${filename}`;
    exec(command, (error, stdout) => {
        res.send(stdout);
    });
}

// Complex function with high cyclomatic complexity
function calculateShipping(order, customer, address) {
    if (order.total > 100) {
        if (customer.isPremium) {
            if (address.country === 'US') {
                if (address.state === 'CA') {
                    return 0;
                } else if (address.state === 'NY') {
                    return 5;
                } else {
                    return 10;
                }
            } else if (address.country === 'CA') {
                return 15;
            } else {
                return 25;
            }
        } else {
            if (order.total > 200) {
                return 10;
            } else {
                return 15;
            }
        }
    } else {
        if (customer.isPremium) {
            return 5;
        } else {
            return 10;
        }
    }
}

// Code smells
console.log('Debug: Loading products');  // INFO: Console statement
var globalVar = 'bad practice';  // LOW: var usage

if (order.status == 'pending') {  // LOW: == instead of ===
    processOrder(order);
}
"""

TYPESCRIPT_CODE = """
// TypeScript code with type safety issues

interface User {
    id: number;
    name: string;
    email: string;
}

// MEDIUM: Missing return type
function fetchUser(id: number) {
    return fetch(`/api/users/${id}`).then(res => res.json());
}

// MEDIUM: any type usage
function processData(data: any) {
    return data.value.nested.property;
}

// MEDIUM: Missing parameter types
function calculateTotal(items, taxRate) {
    return items.reduce((sum, item) => sum + item.price, 0) * (1 + taxRate);
}

// MEDIUM: Non-null assertion
function getUserName(user: User | null) {
    return user!.name;  // Dangerous!
}

// LOW: Type assertion
function parseResponse(response: unknown) {
    const data = response as { value: string };
    return data.value;
}

// HIGH: Invalid typeof check
function validateInput(value: unknown) {
    if (typeof value === 'array') {  // Wrong! typeof never returns 'array'
        return value.length > 0;
    }
    return false;
}
"""


def demo_comprehensive_analysis():
    """Demo comprehensive JavaScript analysis."""
    print("=" * 80)
    print("DEMO 1: Comprehensive JavaScript Analysis")
    print("=" * 80)
    
    analyzer = AnalyzerFactory.get_analyzer('javascript')
    findings = analyzer.analyze('ecommerce.js', PROBLEMATIC_CODE)
    
    print(f"\n📊 Analysis Results: {len(findings)} issues found\n")
    
    # Group by severity
    by_severity = {}
    for finding in findings:
        severity = finding.severity
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(finding)
    
    # Show critical and high severity issues
    for severity in ['critical', 'high']:
        issues = by_severity.get(severity, [])
        if issues:
            icon = '🔴' if severity == 'critical' else '🟠'
            print(f"\n{icon} {severity.upper()} SEVERITY ({len(issues)} issues):")
            print("-" * 80)
            for finding in issues:
                print(f"\n  Line {finding.line_start} [{finding.category}]:")
                print(f"  ⚠️  {finding.message}")
                print(f"  💡 {finding.suggestion}")
    
    # Summary by category
    by_category = {}
    for finding in findings:
        category = finding.category or 'other'
        by_category[category] = by_category.get(category, 0) + 1
    
    print(f"\n\n📈 Issues by Category:")
    print("-" * 80)
    for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
        icon = {'security': '🔒', 'performance': '⚡', 'smell': '👃', 'standards': '📏'}.get(category, '📋')
        print(f"  {icon} {category}: {count}")


def demo_typescript_analysis():
    """Demo TypeScript type safety analysis."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: TypeScript Type Safety Analysis")
    print("=" * 80)
    
    analyzer = AnalyzerFactory.get_analyzer('typescript')
    findings = analyzer.analyze('api.ts', TYPESCRIPT_CODE)
    
    type_issues = [f for f in findings if f.category == 'type_safety']
    
    print(f"\n📊 Type Safety Issues: {len(type_issues)} found\n")
    
    for i, finding in enumerate(type_issues, 1):
        severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}.get(finding.severity, '⚪')
        print(f"{i}. {severity_icon} Line {finding.line_start}:")
        print(f"   ⚠️  {finding.message}")
        print(f"   💡 {finding.suggestion}\n")


def demo_security_only():
    """Demo security-only analysis."""
    print("\n" + "=" * 80)
    print("DEMO 3: Security-Only Analysis")
    print("=" * 80)
    
    config = JavaScriptAnalyzerConfig(
        enable_security=True,
        enable_performance=False,
        enable_type_safety=False,
        enable_quality=False
    )
    
    analyzer = JavaScriptUnifiedAnalyzer(config)
    findings = analyzer.analyze('ecommerce.js', PROBLEMATIC_CODE)
    
    print(f"\n🔒 Security Issues: {len(findings)} found\n")
    
    for i, finding in enumerate(findings, 1):
        severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(finding.severity, '⚪')
        print(f"{i}. {severity_icon} {finding.severity.upper()} - Line {finding.line_start}:")
        print(f"   ⚠️  {finding.message}")
        print(f"   💡 {finding.suggestion}\n")


def demo_performance_only():
    """Demo performance-only analysis."""
    print("\n" + "=" * 80)
    print("DEMO 4: Performance-Only Analysis")
    print("=" * 80)
    
    config = JavaScriptAnalyzerConfig(
        enable_security=False,
        enable_performance=True,
        enable_type_safety=False,
        enable_quality=False
    )
    
    analyzer = JavaScriptUnifiedAnalyzer(config)
    findings = analyzer.analyze('ecommerce.js', PROBLEMATIC_CODE)
    
    print(f"\n⚡ Performance Issues: {len(findings)} found\n")
    
    for i, finding in enumerate(findings, 1):
        severity_icon = {'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(finding.severity, '⚪')
        print(f"{i}. {severity_icon} {finding.severity.upper()} - Line {finding.line_start}:")
        print(f"   ⚠️  {finding.message}")
        print(f"   💡 {finding.suggestion}\n")


def demo_custom_thresholds():
    """Demo custom complexity thresholds."""
    print("\n" + "=" * 80)
    print("DEMO 5: Custom Complexity Thresholds")
    print("=" * 80)
    
    config = JavaScriptAnalyzerConfig(
        enable_security=False,
        enable_performance=False,
        enable_type_safety=False,
        enable_quality=True,
        cyclomatic_threshold=5,  # Strict
        max_function_lines=30,
        max_function_params=3
    )
    
    analyzer = JavaScriptUnifiedAnalyzer(config)
    findings = analyzer.analyze('ecommerce.js', PROBLEMATIC_CODE)
    
    complexity_issues = [f for f in findings if f.category == 'complexity']
    
    print(f"\n🧩 Complexity Issues (strict thresholds): {len(complexity_issues)} found\n")
    
    for finding in complexity_issues:
        print(f"  Line {finding.line_start}:")
        print(f"  ⚠️  {finding.message}")
        if finding.metric_name and finding.metric_value:
            print(f"  📊 {finding.metric_name}: {finding.metric_value}")
        print()


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("🚀 JAVASCRIPT/TYPESCRIPT DEEP CODE ANALYSIS DEMO")
    print("=" * 80)
    print("\nDemonstrating world-class code analysis for JavaScript and TypeScript")
    print("Detects 50+ types of issues across 4 categories:")
    print("  🔒 Security: XSS, SQL injection, command injection, secrets, etc.")
    print("  ⚡ Performance: DOM operations, memory leaks, N+1 queries, React patterns")
    print("  🏷️  Type Safety: Missing types, any usage, unsafe assertions (TypeScript)")
    print("  ✨ Quality: Complexity, code smells, standards violations")
    
    try:
        demo_comprehensive_analysis()
        demo_typescript_analysis()
        demo_security_only()
        demo_performance_only()
        demo_custom_thresholds()
        
        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETE!")
        print("=" * 80)
        print("\nThe JavaScript/TypeScript analyzer is production-ready and can detect:")
        print("  • 12+ security vulnerability types")
        print("  • 9+ performance anti-patterns")
        print("  • 8+ type safety issues (TypeScript)")
        print("  • 10+ code quality issues")
        print("\nAll analysis is done locally with zero API calls! 🎉")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

