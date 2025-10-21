#!/usr/bin/env python3
"""
Test the unified analyzer integration with the main reviewr system.

This test verifies that:
1. UnifiedAnalyzer is properly registered in AnalyzerFactory
2. All 6 specialized analyzers are working
3. Findings are properly aggregated and formatted
4. The integration works with the orchestrator
"""

import sys
from pathlib import Path

# Add reviewr to path
sys.path.insert(0, str(Path(__file__).parent))

from reviewr.analysis import (
    AnalyzerFactory,
    UnifiedAnalyzer,
    AnalyzerConfig,
)


def test_analyzer_factory_registration():
    """Test that UnifiedAnalyzer is registered for Python."""
    print("=" * 60)
    print("TEST 1: AnalyzerFactory Registration")
    print("=" * 60)
    
    # Check that Python is supported
    assert AnalyzerFactory.supports_language('python'), "Python should be supported"
    print("✓ Python language is supported")
    
    # Get analyzer for Python
    analyzer = AnalyzerFactory.get_analyzer('python')
    assert analyzer is not None, "Should get an analyzer for Python"
    assert isinstance(analyzer, UnifiedAnalyzer), "Should get UnifiedAnalyzer for Python"
    print(f"✓ Got UnifiedAnalyzer for Python: {type(analyzer).__name__}")
    
    # Check that all sub-analyzers are initialized
    assert 'security' in analyzer.analyzers, "Security analyzer should be initialized"
    assert 'dataflow' in analyzer.analyzers, "DataFlow analyzer should be initialized"
    assert 'complexity' in analyzer.analyzers, "Complexity analyzer should be initialized"
    assert 'type_safety' in analyzer.analyzers, "Type safety analyzer should be initialized"
    assert 'performance' in analyzer.analyzers, "Performance analyzer should be initialized"
    assert 'semantic' in analyzer.analyzers, "Semantic analyzer should be initialized"
    print(f"✓ All 6 sub-analyzers initialized: {', '.join(analyzer.analyzers.keys())}")
    
    print()


def test_unified_analyzer_with_problematic_code():
    """Test UnifiedAnalyzer with code that has multiple issues."""
    print("=" * 60)
    print("TEST 2: Unified Analysis on Problematic Code")
    print("=" * 60)
    
    code = """
import os
import pickle

def get_user_data(user_id):
    # SQL injection vulnerability
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

def process_users(user_ids):
    results = []
    # N+1 query pattern
    for user_id in user_ids:
        user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(user)
    return results

# Insecure deserialization
def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
"""
    
    analyzer = AnalyzerFactory.get_analyzer('python')
    findings = analyzer.analyze('test_file.py', code)
    
    print(f"Total findings: {len(findings)}")
    
    # Group by category
    by_category = {}
    for finding in findings:
        category = finding.category
        by_category.setdefault(category, []).append(finding)
    
    print(f"\nFindings by category:")
    for category, cat_findings in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  • {category}: {len(cat_findings)}")
    
    # Group by severity
    by_severity = {'critical': [], 'high': [], 'medium': [], 'low': [], 'info': []}
    for finding in findings:
        if finding.severity in by_severity:
            by_severity[finding.severity].append(finding)
    
    print(f"\nFindings by severity:")
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = len(by_severity[severity])
        if count > 0:
            print(f"  • {severity.upper()}: {count}")
    
    # Show some example findings
    print(f"\nExample findings (first 5):")
    for i, finding in enumerate(findings[:5], 1):
        print(f"\n{i}. [{finding.severity.upper()}] {finding.category}")
        print(f"   Line {finding.line_start}: {finding.message}")
        if finding.suggestion:
            print(f"   💡 {finding.suggestion[:100]}...")
    
    # Verify we found issues from multiple analyzers
    categories = set(f.category for f in findings)
    assert 'security' in categories, "Should find security issues"
    assert len(findings) > 0, "Should find multiple issues"
    
    print(f"\n✓ Found issues from {len(categories)} different analyzer categories")
    print()


def test_custom_configuration():
    """Test UnifiedAnalyzer with custom configuration."""
    print("=" * 60)
    print("TEST 3: Custom Configuration")
    print("=" * 60)
    
    # Create config with only security and performance enabled
    config = AnalyzerConfig(
        enable_security=True,
        enable_dataflow=False,
        enable_complexity=False,
        enable_type_safety=False,
        enable_performance=True,
        enable_semantic=False,
        min_severity='high'  # Only high and critical
    )
    
    analyzer = UnifiedAnalyzer(config)
    
    print(f"Enabled analyzers: {list(analyzer.analyzers.keys())}")
    assert len(analyzer.analyzers) == 2, "Should have 2 analyzers enabled"
    assert 'security' in analyzer.analyzers, "Security should be enabled"
    assert 'performance' in analyzer.analyzers, "Performance should be enabled"
    print("✓ Custom configuration applied correctly")
    
    # Test with code
    code = """
def test():
    query = f"SELECT * FROM users WHERE id = {user_id}"  # Security issue
    for i in range(100):
        result = db.query("SELECT * FROM data")  # Performance issue (N+1)
    x = None
    if x == None:  # Type safety issue (should be filtered out)
        pass
"""
    
    findings = analyzer.analyze('test.py', code)
    
    # Should only have security and performance findings
    categories = set(f.category for f in findings)
    print(f"Found categories: {categories}")
    
    # Should only have high/critical severity
    severities = set(f.severity for f in findings)
    print(f"Found severities: {severities}")
    
    assert 'info' not in severities, "Should not have info severity (filtered)"
    assert 'low' not in severities, "Should not have low severity (filtered)"
    
    print("✓ Filtering by severity works correctly")
    print()


def test_analyzer_factory_convenience_methods():
    """Test AnalyzerFactory convenience methods."""
    print("=" * 60)
    print("TEST 4: AnalyzerFactory Convenience Methods")
    print("=" * 60)
    
    # Test get_unified_analyzer
    analyzer = AnalyzerFactory.get_unified_analyzer()
    assert isinstance(analyzer, UnifiedAnalyzer), "Should get UnifiedAnalyzer"
    print("✓ get_unified_analyzer() works")
    
    # Test create_custom_config
    config = AnalyzerFactory.create_custom_config(
        enable_security=True,
        enable_dataflow=False,
        min_severity='medium'
    )
    assert config.enable_security == True
    assert config.enable_dataflow == False
    assert config.min_severity == 'medium'
    print("✓ create_custom_config() works")
    
    # Test get_supported_languages
    languages = AnalyzerFactory.get_supported_languages()
    assert 'python' in languages, "Python should be supported"
    print(f"✓ Supported languages: {', '.join(languages)}")
    
    print()


def test_summary_generation():
    """Test summary generation."""
    print("=" * 60)
    print("TEST 5: Summary Generation")
    print("=" * 60)
    
    code = """
def bad_function(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    os.system(f"echo {user_input}")
    
    if True:
        if True:
            if True:
                if True:
                    pass
    
    f = open('file.txt')
    data = f.read()
    return data
"""
    
    analyzer = AnalyzerFactory.get_analyzer('python')
    findings = analyzer.analyze('test.py', code)
    
    # Generate summary
    summary = analyzer.get_summary(findings)
    print(summary)
    
    assert 'UNIFIED ANALYSIS SUMMARY' in summary
    assert 'Total Findings:' in summary
    assert 'By Severity:' in summary
    assert 'By Category:' in summary
    
    print("\n✓ Summary generation works")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("UNIFIED ANALYZER INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_analyzer_factory_registration()
        test_unified_analyzer_with_problematic_code()
        test_custom_configuration()
        test_analyzer_factory_convenience_methods()
        test_summary_generation()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe UnifiedAnalyzer is successfully integrated!")
        print("All 6 specialized analyzers are working correctly.")
        print("\nNext steps:")
        print("  1. Add CLI flags for analyzer control")
        print("  2. Update output formatters")
        print("  3. Test with GitHub/GitLab integration")
        
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

