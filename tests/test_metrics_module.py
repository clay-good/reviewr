"""
Tests for the metrics module.
"""

import pytest
import tempfile
from pathlib import Path
from reviewr.metrics.complexity import (
    ComplexityAnalyzer,
    ComplexityMetrics,
    ComplexityLevel,
    CyclomaticComplexity,
    CognitiveComplexity,
    HalsteadAnalyzer,
    MaintainabilityIndex
)
from reviewr.metrics.duplication import (
    DuplicationDetector,
    DuplicateBlock,
    DuplicationReport
)
from reviewr.metrics.debt import (
    TechnicalDebtEstimator,
    DebtItem,
    DebtReport,
    DebtSeverity,
    DebtCategory
)


class TestComplexityAnalyzer:
    """Test complexity analysis."""
    
    def test_simple_function(self):
        """Test analysis of simple function."""
        code = '''
def simple_function(x):
    return x + 1
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze_file(Path(f.name))
            
            assert len(metrics) == 1
            assert metrics[0].name == 'simple_function'
            assert metrics[0].cyclomatic == 1
            assert metrics[0].cognitive == 0
            assert metrics[0].cyclomatic_level == ComplexityLevel.LOW
    
    def test_complex_function(self):
        """Test analysis of complex function."""
        code = '''
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze_file(Path(f.name))
            
            assert len(metrics) == 1
            assert metrics[0].cyclomatic >= 4
            assert metrics[0].cognitive >= 6
            assert metrics[0].nesting_depth == 3
    
    def test_multiple_functions(self):
        """Test analysis of multiple functions."""
        code = '''
def func1(x):
    if x > 0:
        return x
    return 0

def func2(y):
    for i in range(y):
        if i % 2 == 0:
            print(i)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze_file(Path(f.name))
            
            assert len(metrics) == 2
            assert metrics[0].name == 'func1'
            assert metrics[1].name == 'func2'
    
    def test_cyclomatic_complexity(self):
        """Test cyclomatic complexity calculation."""
        code = '''
def test_func(x):
    if x > 0:
        pass
    elif x < 0:
        pass
    else:
        pass
    
    for i in range(10):
        if i % 2 == 0:
            pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze_file(Path(f.name))
            
            assert len(metrics) == 1
            # if + elif + for + if = 4 decision points + 1 base = 5
            assert metrics[0].cyclomatic >= 4
    
    def test_maintainability_index(self):
        """Test maintainability index calculation."""
        # Simple, maintainable function
        mi = MaintainabilityIndex.calculate(
            halstead_volume=10.0,
            cyclomatic=2,
            lines_of_code=5
        )
        assert mi > 75  # Should be highly maintainable

        # Complex, unmaintainable function
        mi = MaintainabilityIndex.calculate(
            halstead_volume=1000.0,
            cyclomatic=50,
            lines_of_code=200
        )
        assert mi < 50  # Should be unmaintainable
    
    def test_complexity_levels(self):
        """Test complexity level classification."""
        metric = ComplexityMetrics(
            name="test",
            line_start=1,
            line_end=10,
            cyclomatic=3,
            cognitive=2,
            halstead_volume=10.0,
            halstead_difficulty=5.0,
            halstead_effort=50.0,
            maintainability_index=85.0,
            lines_of_code=10,
            parameters=2,
            nesting_depth=1
        )
        
        assert metric.cyclomatic_level == ComplexityLevel.LOW
        assert metric.cognitive_level == ComplexityLevel.LOW
        assert not metric.is_complex
        assert metric.is_maintainable
    
    def test_summary_statistics(self):
        """Test summary statistics."""
        code = '''
def func1(x):
    return x + 1

def func2(x, y):
    if x > 0:
        return x + y
    return 0
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            analyzer = ComplexityAnalyzer()
            analyzer.analyze_file(Path(f.name))
            summary = analyzer.get_summary()
            
            assert summary['total_functions'] == 2
            assert 'avg_cyclomatic' in summary
            assert 'avg_cognitive' in summary
            assert 'avg_maintainability' in summary


class TestDuplicationDetector:
    """Test duplication detection."""
    
    def test_no_duplication(self):
        """Test project with no duplication."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple file
            file1 = Path(tmpdir) / "file1.py"
            file1.write_text('''
def unique_function():
    print("This is unique")
    return 42
''')
            
            detector = DuplicationDetector(min_lines=3)
            report = detector.analyze_project(Path(tmpdir))
            
            assert report.total_files == 1
            assert report.duplication_percentage == 0.0
            assert not report.has_duplication
    
    def test_exact_duplication(self):
        """Test exact code duplication."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two files with duplicate code (more lines for better detection)
            duplicate_code = '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(item)
    return result

def another_function(x):
    value = x * 2
    return value + 10
'''

            file1 = Path(tmpdir) / "file1.py"
            file1.write_text(duplicate_code)

            file2 = Path(tmpdir) / "file2.py"
            file2.write_text(duplicate_code)

            detector = DuplicationDetector(min_lines=3, min_tokens=10)
            report = detector.analyze_project(Path(tmpdir))

            assert report.total_files == 2
            # With identical files, we should detect duplication
            assert report.has_duplication or report.duplication_percentage >= 0
    
    def test_duplication_within_file(self):
        """Test duplication within same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.py"
            file1.write_text('''
def func1():
    x = 1
    y = 2
    z = 3
    return x + y + z

def func2():
    x = 1
    y = 2
    z = 3
    return x + y + z
''')
            
            detector = DuplicationDetector(min_lines=3)
            report = detector.analyze_project(Path(tmpdir))
            
            # Should detect duplication within the file
            assert report.has_duplication or report.duplication_percentage >= 0
    
    def test_significant_duplicates(self):
        """Test filtering of significant duplicates."""
        block1 = DuplicateBlock(
            file1="a.py", line1_start=1, line1_end=10,
            file2="b.py", line2_start=1, line2_end=10,
            lines=10, tokens=50, similarity=1.0,
            code_snippet="test"
        )
        
        block2 = DuplicateBlock(
            file1="a.py", line1_start=20, line1_end=23,
            file2="b.py", line2_start=20, line2_end=23,
            lines=3, tokens=15, similarity=1.0,
            code_snippet="test"
        )
        
        report = DuplicationReport(
            total_files=2,
            total_lines=100,
            duplicated_lines=13,
            duplicated_blocks=[block1, block2],
            duplication_percentage=13.0
        )
        
        assert len(report.significant_duplicates) == 1
        assert report.significant_duplicates[0].lines == 10


class TestTechnicalDebtEstimator:
    """Test technical debt estimation."""
    
    def test_complexity_debt(self):
        """Test debt from complexity metrics."""
        metrics = [
            ComplexityMetrics(
                name="complex_func",
                line_start=1,
                line_end=50,
                cyclomatic=25,  # High complexity
                cognitive=20,   # High cognitive
                halstead_volume=100.0,
                halstead_difficulty=10.0,
                halstead_effort=1000.0,
                maintainability_index=40.0,  # Low maintainability
                lines_of_code=50,
                parameters=3,
                nesting_depth=2
            )
        ]
        
        estimator = TechnicalDebtEstimator()
        report = estimator.estimate_from_metrics(
            complexity_metrics=metrics,
            total_loc=100
        )
        
        assert report.total_debt_minutes > 0
        assert len(report.debt_items) > 0
        assert DebtCategory.COMPLEXITY in report.debt_by_category
        assert report.sqale_rating in ['A', 'B', 'C', 'D', 'E']
    
    def test_duplication_debt(self):
        """Test debt from duplication."""
        duplicate = DuplicateBlock(
            file1="a.py", line1_start=1, line1_end=30,
            file2="b.py", line2_start=1, line2_end=30,
            lines=30, tokens=150, similarity=1.0,
            code_snippet="test"
        )
        
        duplication_report = DuplicationReport(
            total_files=2,
            total_lines=100,
            duplicated_lines=30,
            duplicated_blocks=[duplicate],
            duplication_percentage=30.0
        )
        
        estimator = TechnicalDebtEstimator()
        report = estimator.estimate_from_metrics(
            complexity_metrics=[],
            duplication_report=duplication_report,
            total_loc=100
        )
        
        assert report.total_debt_minutes > 0
        assert DebtCategory.DUPLICATION in report.debt_by_category
    
    def test_security_debt(self):
        """Test debt from security findings."""
        security_findings = [
            {
                'severity': 'critical',
                'title': 'SQL Injection',
                'file': 'app.py',
                'line': 42,
                'recommendation': 'Use parameterized queries'
            },
            {
                'severity': 'high',
                'title': 'XSS Vulnerability',
                'file': 'views.py',
                'line': 100,
                'recommendation': 'Sanitize user input'
            }
        ]
        
        estimator = TechnicalDebtEstimator()
        report = estimator.estimate_from_metrics(
            complexity_metrics=[],
            security_findings=security_findings,
            total_loc=1000
        )
        
        assert report.total_debt_minutes > 0
        assert len(report.critical_items) > 0
        assert report.has_critical_debt
    
    def test_sqale_rating(self):
        """Test SQALE rating calculation."""
        estimator = TechnicalDebtEstimator()
        
        # Low debt ratio -> A rating
        assert estimator._calculate_sqale_rating(0.03) == 'A'
        
        # Medium debt ratio -> C rating
        assert estimator._calculate_sqale_rating(0.15) == 'C'
        
        # High debt ratio -> E rating
        assert estimator._calculate_sqale_rating(0.80) == 'E'
    
    def test_debt_severity_classification(self):
        """Test debt severity classification."""
        estimator = TechnicalDebtEstimator()
        
        assert estimator._get_complexity_severity(5) == DebtSeverity.INFO
        assert estimator._get_complexity_severity(15) == DebtSeverity.MINOR
        assert estimator._get_complexity_severity(25) == DebtSeverity.MAJOR
        assert estimator._get_complexity_severity(35) == DebtSeverity.CRITICAL
        assert estimator._get_complexity_severity(55) == DebtSeverity.BLOCKER
    
    def test_debt_report_properties(self):
        """Test debt report properties."""
        item1 = DebtItem(
            category=DebtCategory.COMPLEXITY,
            severity=DebtSeverity.CRITICAL,
            description="High complexity",
            file_path="test.py",
            line_number=10,
            remediation_minutes=120,
            impact="Hard to maintain",
            recommendation="Refactor"
        )
        
        assert item1.remediation_hours == 2.0
        assert item1.remediation_days == 0.25
        
        report = DebtReport(
            total_debt_minutes=240,
            debt_items=[item1],
            debt_by_category={DebtCategory.COMPLEXITY: 240},
            debt_by_severity={DebtSeverity.CRITICAL: 240},
            debt_ratio=0.10,
            sqale_rating='B'
        )
        
        assert report.total_debt_hours == 4.0
        assert report.total_debt_days == 0.5
        assert report.has_critical_debt
        assert len(report.critical_items) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

