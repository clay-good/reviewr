"""
Interactive Demo: Java Deep Code Analysis

Demonstrates the capabilities of the Java unified analyzer with real-world examples.
"""

from reviewr.analysis import JavaUnifiedAnalyzer, JavaAnalyzerConfig


def print_banner(title):
    """Print a formatted banner."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_findings(findings, show_code=True):
    """Print findings in a formatted way."""
    if not findings:
        print("✅ No issues found!\n")
        return
    
    print(f"Found {len(findings)} issues:\n")
    
    for i, finding in enumerate(findings, 1):
        emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '⚪'
        }
        
        print(f"{i}. {emoji.get(finding.severity, '•')} [{finding.severity.upper()}] Line {finding.line_start}")
        print(f"   Category: {finding.category}")
        print(f"   Message: {finding.message}")
        print(f"   Suggestion: {finding.suggestion}")
        
        if show_code and finding.code_snippet:
            print(f"   Code: {finding.code_snippet.strip()}")
        
        print()


def demo_1_security_vulnerabilities():
    """Demo 1: Security Vulnerabilities"""
    print_banner("DEMO 1: Security Vulnerabilities")
    
    code = '''
public class PaymentService {
    private static final String API_KEY = "sk_live_1234567890abcdefghijklmnop";
    
    public Payment processPayment(String userId, String cardNumber) {
        // SQL Injection vulnerability
        String query = "SELECT * FROM payments WHERE user_id = '" + userId + "'";
        Statement stmt = connection.createStatement();
        ResultSet rs = stmt.executeQuery(query);
        
        // Weak cryptography
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] hash = md.digest(cardNumber.getBytes());
        
        // Command injection
        Runtime.getRuntime().exec("process_payment.sh " + userId);
        
        return new Payment(rs);
    }
}
'''
    
    analyzer = JavaUnifiedAnalyzer()
    findings = analyzer.analyze('PaymentService.java', code)
    
    print("Analyzing payment processing code for security vulnerabilities...\n")
    print_findings(findings)


def demo_2_concurrency_issues():
    """Demo 2: Concurrency Issues"""
    print_banner("DEMO 2: Concurrency Issues")
    
    code = '''
public class UserCache {
    private static Map<String, User> cache = new HashMap<>();
    private static SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
    
    public void addUser(User user) {
        cache.put(user.getId(), user);
    }
    
    public User getUser(String id) {
        return cache.get(id);
    }
    
    public String formatDate(Date date) {
        return dateFormat.format(date);
    }
    
    // Broken double-checked locking
    private static UserCache instance;
    
    public static UserCache getInstance() {
        if (instance == null) {
            synchronized (UserCache.class) {
                if (instance == null) {
                    instance = new UserCache();
                }
            }
        }
        return instance;
    }
}
'''
    
    analyzer = JavaUnifiedAnalyzer()
    findings = analyzer.analyze('UserCache.java', code)
    
    print("Analyzing multi-threaded cache implementation...\n")
    print_findings(findings)


def demo_3_performance_issues():
    """Demo 3: Performance Issues"""
    print_banner("DEMO 3: Performance Issues")
    
    code = '''
public class ReportGenerator {
    public String generateReport(List<Transaction> transactions) {
        String report = "";
        
        // String concatenation in loop
        for (Transaction tx : transactions) {
            report += "Transaction: " + tx.getId() + ", Amount: " + tx.getAmount() + "\\n";
        }
        
        // Regex compilation in loop
        for (Transaction tx : transactions) {
            if (Pattern.compile("[0-9]+").matcher(tx.getId()).matches()) {
                report += "Valid ID\\n";
            }
        }
        
        // Autoboxing overhead
        List<Integer> amounts = new ArrayList<>();
        for (int i = 0; i < transactions.size(); i++) {
            amounts.add(transactions.get(i).getAmount());
        }
        
        return report;
    }
}
'''
    
    analyzer = JavaUnifiedAnalyzer()
    findings = analyzer.analyze('ReportGenerator.java', code)
    
    print("Analyzing report generation code for performance issues...\n")
    print_findings(findings)


def demo_4_code_quality():
    """Demo 4: Code Quality Issues"""
    print_banner("DEMO 4: Code Quality Issues")
    
    code = '''
public class DataProcessor {
    public List<String> processData(String filePath) throws Exception {
        List<String> results = new ArrayList<>();
        
        try {
            BufferedReader reader = new BufferedReader(new FileReader(filePath));
            String line;
            while ((line = reader.readLine()) != null) {
                results.add(line);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        return results;
    }
    
    @Override
    public boolean equals(Object obj) {
        if (obj instanceof DataProcessor) {
            return true;
        }
        return false;
    }
    
    public Date getCurrentDate() {
        return new Date();
    }
    
    public void processLargeFile() {
        // TODO: Implement this
        System.out.println("Processing...");
    }
}
'''
    
    analyzer = JavaUnifiedAnalyzer()
    findings = analyzer.analyze('DataProcessor.java', code)
    
    print("Analyzing data processing code for quality issues...\n")
    print_findings(findings)


def demo_5_comprehensive_analysis():
    """Demo 5: Comprehensive Analysis with Summary"""
    print_banner("DEMO 5: Comprehensive Analysis with Summary")
    
    code = '''
public class OrderService {
    private static int orderCount = 0;
    private static final String DB_PASSWORD = "MySecretPassword123";
    
    public Order createOrder(String userId, String productId) throws Exception {
        // SQL injection
        String query = "INSERT INTO orders (user_id, product_id) VALUES ('" + 
                       userId + "', '" + productId + "')";
        Statement stmt = connection.createStatement();
        stmt.executeUpdate(query);
        
        // Thread safety issue
        orderCount++;
        
        // Performance issue
        String log = "";
        for (int i = 0; i < 1000; i++) {
            log += "Processing order " + i + "\\n";
        }
        
        // Quality issue
        try {
            sendEmail(userId);
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        return new Order(userId, productId);
    }
    
    @Override
    public boolean equals(Object obj) {
        return obj instanceof OrderService;
    }
}
'''
    
    analyzer = JavaUnifiedAnalyzer()
    result = analyzer.analyze_with_summary('OrderService.java', code)
    
    print("Analyzing order service with comprehensive analysis...\n")
    
    print(f"📊 SUMMARY")
    print(f"{'─'*80}")
    print(f"Total Findings: {result['summary']['total_findings']}")
    print(f"Risk Level: {result['summary']['risk_level'].upper()}")
    print(f"Risk Score: {result['summary']['risk_score']}")
    print()
    
    print(f"By Severity:")
    for severity, count in result['summary']['by_severity'].items():
        emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}
        print(f"  {emoji.get(severity, '•')} {severity.capitalize()}: {count}")
    print()
    
    print(f"By Category:")
    for category, count in result['summary']['by_category'].items():
        print(f"  • {category.capitalize()}: {count}")
    print()
    
    print(f"Analyzers Run:")
    for analyzer_name in result['summary']['analyzers_run']:
        print(f"  ✓ {analyzer_name}")
    print()
    
    # Show metrics
    metrics = analyzer.get_metrics(code)
    print(f"📈 CODE METRICS")
    print(f"{'─'*80}")
    print(f"Lines of Code: {metrics['code_lines']}")
    print(f"Methods: {metrics['methods']}")
    print(f"Classes: {metrics['classes']}")
    print(f"Avg Method Length: {metrics['avg_method_length']} lines")
    print(f"Estimated Complexity: {metrics['estimated_complexity']}")
    print()
    
    print(f"🔍 DETAILED FINDINGS")
    print(f"{'─'*80}\n")
    print_findings(result['findings'], show_code=False)


def demo_6_custom_configuration():
    """Demo 6: Custom Configuration"""
    print_banner("DEMO 6: Custom Configuration")
    
    code = '''
public class ConfigExample {
    private String password = "secret123";
    
    public void process() {
        String result = "";
        for (int i = 0; i < 100; i++) {
            result += i + ", ";
        }
        System.out.println(result);
    }
}
'''
    
    print("Analysis with default configuration:")
    print("─" * 80)
    analyzer = JavaUnifiedAnalyzer()
    findings = analyzer.analyze('ConfigExample.java', code)
    print(f"Found {len(findings)} issues\n")
    
    print("Analysis with security-only configuration:")
    print("─" * 80)
    config = JavaAnalyzerConfig(
        enable_security=True,
        enable_concurrency=False,
        enable_performance=False,
        enable_quality=False
    )
    analyzer = JavaUnifiedAnalyzer(config)
    findings = analyzer.analyze('ConfigExample.java', code)
    print(f"Found {len(findings)} issues (security only)\n")
    
    print("Analysis with high severity filter:")
    print("─" * 80)
    config = JavaAnalyzerConfig(min_severity='high')
    analyzer = JavaUnifiedAnalyzer(config)
    findings = analyzer.analyze('ConfigExample.java', code)
    print(f"Found {len(findings)} issues (high+ severity only)\n")


def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("  JAVA DEEP CODE ANALYSIS - INTERACTIVE DEMO")
    print("  Powered by reviewr")
    print("="*80)
    
    demos = [
        ("Security Vulnerabilities", demo_1_security_vulnerabilities),
        ("Concurrency Issues", demo_2_concurrency_issues),
        ("Performance Issues", demo_3_performance_issues),
        ("Code Quality", demo_4_code_quality),
        ("Comprehensive Analysis", demo_5_comprehensive_analysis),
        ("Custom Configuration", demo_6_custom_configuration),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run all demos")
    print("  0. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (0-{}): ".format(len(demos) + 1))
            choice = int(choice)
            
            if choice == 0:
                print("\nThank you for trying the Java analyzer demo!")
                break
            elif choice == len(demos) + 1:
                for _, demo_func in demos:
                    demo_func()
                print_banner("ALL DEMOS COMPLETE!")
                print("Java deep code analysis is production-ready! 🚀\n")
                break
            elif 1 <= choice <= len(demos):
                demos[choice - 1][1]()
            else:
                print("Invalid choice. Please try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting demo...")
            break


if __name__ == '__main__':
    main()

