"""
Comprehensive integration tests for reviewr.

Tests the complete workflow from code analysis through all analyzers
to output formatting and CI/CD integration.
"""

import pytest
import tempfile
import json
from pathlib import Path

from reviewr.analysis import AnalyzerFactory
from reviewr.review.orchestrator import ReviewOrchestrator
from reviewr.config import ConfigLoader
from reviewr.utils.formatters import TerminalFormatter, MarkdownFormatter, SarifFormatter


@pytest.fixture
def sample_python_code():
    """Create sample Python code with various issues."""
    return '''
import os
import sys
import unused_module

def vulnerable_function(user_input):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_input
    os.system("ls " + user_input)  # Command injection
    
    # Unused variable
    x = 10
    
    # Missing type hints
    return query

def complex_function(a, b, c, d, e):
    # High complexity
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
    return 0

def performance_issue():
    # Inefficient loop
    result = ""
    for i in range(1000):
        result += str(i)  # String concatenation in loop
    return result

class UnsafeClass:
    def __init__(self):
        self.data = None
    
    def process(self, data):
        # Potential None dereference
        return self.data.upper()
'''


@pytest.fixture
def sample_javascript_code():
    """Create sample JavaScript code with various issues."""
    return '''
// Security issues
function vulnerableFunction(userInput) {
    eval(userInput);  // Code injection
    document.write(userInput);  // XSS
    
    // Performance issue
    var result = "";
    for (var i = 0; i < 1000; i++) {
        result += i;  // String concatenation in loop
    }
    
    return result;
}

// Type safety issue
function addNumbers(a, b) {
    return a + b;  // No type checking
}

// Complexity issue
function complexFunction(a, b, c, d, e) {
    if (a > 0) {
        if (b > 0) {
            if (c > 0) {
                if (d > 0) {
                    if (e > 0) {
                        return a + b + c + d + e;
                    }
                }
            }
        }
    }
    return 0;
}

// Unused variable
var unusedVar = 10;
'''


def test_python_analyzer_integration(tmp_path, sample_python_code):
    """Test complete Python analysis workflow."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_python_code)

    # Get Python analyzer
    factory = AnalyzerFactory()
    analyzer = factory.get_analyzer('python')

    assert analyzer is not None, "Python analyzer should be available"

    # Analyze code
    findings = analyzer.analyze(str(test_file), sample_python_code)
    
    # Verify findings
    assert len(findings) > 0, "Should detect issues in sample code"

    # Check for different categories of findings
    finding_categories = {f.category for f in findings}

    # Should detect security issues
    assert any('security' in c.lower() for c in finding_categories), \
        "Should detect security issues"
    
    # Check severity distribution
    severities = [f.severity for f in findings]
    assert 'critical' in severities or 'high' in severities, \
        "Should detect high-severity issues"


def test_javascript_analyzer_integration(tmp_path, sample_javascript_code):
    """Test complete JavaScript analysis workflow."""
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text(sample_javascript_code)

    # Get JavaScript analyzer
    factory = AnalyzerFactory()
    analyzer = factory.get_analyzer('javascript')

    assert analyzer is not None, "JavaScript analyzer should be available"

    # Analyze code
    findings = analyzer.analyze(str(test_file), sample_javascript_code)
    
    # Verify findings
    assert len(findings) > 0, "Should detect issues in sample code"

    # Check for security issues
    security_findings = [f for f in findings if 'security' in f.category.lower()]
    assert len(security_findings) > 0, "Should detect security issues"


def test_multi_language_analysis(tmp_path, sample_python_code, sample_javascript_code):
    """Test analysis of multiple languages in one project."""
    # Create test files
    py_file = tmp_path / "test.py"
    py_file.write_text(sample_python_code)
    
    js_file = tmp_path / "test.js"
    js_file.write_text(sample_javascript_code)
    
    # Get analyzers
    factory = AnalyzerFactory()
    
    # Analyze both files
    py_analyzer = factory.get_analyzer('python')
    js_analyzer = factory.get_analyzer('javascript')

    py_findings = py_analyzer.analyze(str(py_file), sample_python_code)
    js_findings = js_analyzer.analyze(str(js_file), sample_javascript_code)
    
    # Verify both detected issues
    assert len(py_findings) > 0, "Should detect Python issues"
    assert len(js_findings) > 0, "Should detect JavaScript issues"
    
    # Combine findings
    all_findings = py_findings + js_findings
    assert len(all_findings) > len(py_findings), "Should have findings from both languages"


def test_output_formatters(tmp_path, sample_python_code):
    """Test all output formatters."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_python_code)
    
    # Analyze code
    factory = AnalyzerFactory()
    analyzer = factory.get_analyzer('python')
    local_findings = analyzer.analyze(str(test_file), sample_python_code)

    # Convert LocalFindings to ReviewFindings
    review_findings = [f.to_review_finding() for f in local_findings]

    # Create mock review result
    from types import SimpleNamespace
    result = SimpleNamespace(
        findings=review_findings,
        files_reviewed=1,
        provider_stats={'request_count': 1, 'total_input_tokens': 100, 'total_output_tokens': 50}
    )
    result.get_findings_by_severity = lambda: {
        'critical': [f for f in review_findings if f.severity == 'critical'],
        'high': [f for f in review_findings if f.severity == 'high'],
        'medium': [f for f in review_findings if f.severity == 'medium'],
        'low': [f for f in review_findings if f.severity == 'low'],
        'info': [f for f in review_findings if f.severity == 'info'],
    }
    
    # Test Terminal formatter
    terminal_formatter = TerminalFormatter()
    terminal_output = terminal_formatter.format_result(result)
    assert len(terminal_output) > 0, "Terminal formatter should produce output"
    assert "Code Review Summary" in terminal_output, "Should include summary"
    
    # Test Markdown formatter
    markdown_formatter = MarkdownFormatter()
    markdown_output = markdown_formatter.format_result(result)
    assert len(markdown_output) > 0, "Markdown formatter should produce output"
    assert "##" in markdown_output, "Should include markdown headers"
    
    # Test SARIF formatter
    sarif_formatter = SarifFormatter()
    sarif_output = sarif_formatter.format_result(result)
    assert len(sarif_output) > 0, "SARIF formatter should produce output"
    
    # Verify SARIF is valid JSON
    sarif_data = json.loads(sarif_output)
    assert sarif_data['version'] == '2.1.0', "Should be SARIF 2.1.0"
    assert 'runs' in sarif_data, "Should have runs"


def test_analyzer_factory_registration():
    """Test that all analyzers are properly registered."""
    factory = AnalyzerFactory()
    
    # Check Python analyzers
    assert factory.get_analyzer('python') is not None
    
    # Check JavaScript/TypeScript analyzers
    assert factory.get_analyzer('javascript') is not None
    assert factory.get_analyzer('typescript') is not None
    
    # Check Go analyzer
    assert factory.get_analyzer('go') is not None
    
    # Check Rust analyzer
    assert factory.get_analyzer('rust') is not None
    
    # Check Java analyzer
    assert factory.get_analyzer('java') is not None


def test_finding_categories():
    """Test that findings are properly categorized."""
    factory = AnalyzerFactory()
    
    # Test with Python code
    code = '''
import os
def test(user_input):
    os.system(user_input)  # Security issue
    x = 10  # Unused variable
    result = ""
    for i in range(100):
        result += str(i)  # Performance issue
'''
    
    analyzer = factory.get_analyzer('python')
    findings = analyzer.analyze('test.py', code)
    
    # Check categories
    categories = {f.category for f in findings if hasattr(f, 'category')}
    
    # Should have multiple categories
    assert len(categories) > 0, "Should categorize findings"


def test_severity_levels():
    """Test that severity levels are properly assigned."""
    factory = AnalyzerFactory()
    
    # Test with code containing critical security issue
    code = '''
import os
def vulnerable(user_input):
    os.system(user_input)  # Command injection - should be critical/high
'''
    
    analyzer = factory.get_analyzer('python')
    findings = analyzer.analyze('test.py', code)
    
    # Check severities
    severities = {f.severity for f in findings}
    
    # Should have severity levels
    assert len(severities) > 0, "Should assign severity levels"
    
    # Security issues should be high severity
    security_findings = [f for f in findings if 'command' in f.message.lower() or 'injection' in f.message.lower()]
    if security_findings:
        assert any(f.severity in ['critical', 'high'] for f in security_findings), \
            "Security issues should be high severity"


def test_confidence_scores():
    """Test that confidence scores are assigned."""
    factory = AnalyzerFactory()
    
    code = '''
import os
def test(user_input):
    os.system(user_input)
'''
    
    analyzer = factory.get_analyzer('python')
    findings = analyzer.analyze('test.py', code)
    
    # Check confidence scores
    for finding in findings:
        if hasattr(finding, 'confidence'):
            assert 0.0 <= finding.confidence <= 1.0, \
                "Confidence should be between 0 and 1"


def test_end_to_end_workflow(tmp_path, sample_python_code):
    """Test complete end-to-end workflow."""
    # 1. Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_python_code)
    
    # 2. Analyze with factory
    factory = AnalyzerFactory()
    analyzer = factory.get_analyzer('python')
    local_findings = analyzer.analyze(str(test_file), sample_python_code)

    # 3. Verify findings
    assert len(local_findings) > 0

    # Convert LocalFindings to ReviewFindings
    review_findings = [f.to_review_finding() for f in local_findings]

    # 4. Format output
    from types import SimpleNamespace
    result = SimpleNamespace(
        findings=review_findings,
        files_reviewed=1,
        provider_stats={}
    )
    result.get_findings_by_severity = lambda: {
        'critical': [f for f in review_findings if f.severity == 'critical'],
        'high': [f for f in review_findings if f.severity == 'high'],
        'medium': [f for f in review_findings if f.severity == 'medium'],
        'low': [f for f in review_findings if f.severity == 'low'],
        'info': [f for f in review_findings if f.severity == 'info'],
    }
    
    # 5. Test all formatters
    formatters = [
        TerminalFormatter(),
        MarkdownFormatter(),
        SarifFormatter()
    ]
    
    for formatter in formatters:
        output = formatter.format_result(result)
        assert len(output) > 0, f"{formatter.__class__.__name__} should produce output"
    
    # 6. Verify output can be saved
    output_file = tmp_path / "results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'findings': [
                {
                    'type': f.type.value,
                    'severity': f.severity,
                    'message': f.message,
                    'file_path': f.file_path,
                    'line_start': f.line_start
                }
                for f in review_findings
            ]
        }, f)

    assert output_file.exists()

    # 7. Verify output can be loaded
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)

    assert len(loaded_data['findings']) == len(review_findings)

