"""
Tests for reviewer optimization features.
"""

import pytest
from reviewr.utils.finding_optimizer import FindingOptimizer, FindingPriority
from reviewr.providers.base import ReviewFinding, ReviewType
from reviewr.review.orchestrator import ReviewResult


@pytest.fixture
def sample_findings():
    """Create sample findings for testing."""
    return [
        ReviewFinding(
            type=ReviewType.SECURITY,
            severity='critical',
            file_path='app.py',
            line_start=10,
            line_end=12,
            message='SQL injection vulnerability detected',
            suggestion='Use parameterized queries',
            confidence=0.95,
            category='security'
        ),
        ReviewFinding(
            type=ReviewType.SECURITY,
            severity='critical',
            file_path='app.py',
            line_start=11,
            line_end=13,
            message='SQL injection vulnerability detected',
            suggestion='Use parameterized queries',
            confidence=0.90,
            category='security'
        ),
        ReviewFinding(
            type=ReviewType.PERFORMANCE,
            severity='medium',
            file_path='utils.py',
            line_start=50,
            line_end=55,
            message='Inefficient loop detected',
            suggestion='Use list comprehension',
            confidence=0.75,
            category='performance'
        ),
        ReviewFinding(
            type=ReviewType.CORRECTNESS,
            severity='high',
            file_path='app.py',
            line_start=100,
            line_end=102,
            message='Potential null pointer exception',
            suggestion='Add null check',
            confidence=0.85,
            category='correctness'
        ),
        ReviewFinding(
            type=ReviewType.MAINTAINABILITY,
            severity='low',
            file_path='utils.py',
            line_start=200,
            line_end=205,
            message='Function too long',
            confidence=0.70,
            category='quality'
        ),
    ]


class TestFindingOptimizer:
    """Test the FindingOptimizer class."""
    
    def test_deduplication(self, sample_findings):
        """Test that duplicate findings are removed."""
        optimizer = FindingOptimizer()
        
        # Should remove the duplicate SQL injection finding
        deduplicated = optimizer.deduplicate_findings(sample_findings)
        
        assert len(deduplicated) < len(sample_findings)
        assert len(deduplicated) == 4  # One duplicate removed
        
        # Should keep the one with higher confidence
        sql_findings = [f for f in deduplicated if 'SQL injection' in f.message]
        assert len(sql_findings) == 1
        assert sql_findings[0].confidence == 0.95
    
    def test_prioritization(self, sample_findings):
        """Test that findings are prioritized correctly."""
        optimizer = FindingOptimizer()
        
        prioritized = optimizer.prioritize_findings(sample_findings)
        
        # Should return FindingPriority objects
        assert all(isinstance(fp, FindingPriority) for fp in prioritized)
        
        # Should be sorted by priority (highest first)
        scores = [fp.priority_score for fp in prioritized]
        assert scores == sorted(scores, reverse=True)
        
        # Critical security finding should be first
        assert prioritized[0].finding.severity == 'critical'
        assert prioritized[0].finding.type == ReviewType.SECURITY
        
        # Should have reasons
        assert len(prioritized[0].reasons) > 0
    
    def test_group_by_file(self, sample_findings):
        """Test grouping findings by file."""
        optimizer = FindingOptimizer()
        
        by_file = optimizer.group_by_file(sample_findings)
        
        assert 'app.py' in by_file
        assert 'utils.py' in by_file
        assert len(by_file['app.py']) == 3  # 2 SQL + 1 null pointer
        assert len(by_file['utils.py']) == 2  # 1 loop + 1 long function
        
        # Should be sorted by line number
        app_findings = by_file['app.py']
        line_numbers = [f.line_start for f in app_findings]
        assert line_numbers == sorted(line_numbers)
    
    def test_group_by_category(self, sample_findings):
        """Test grouping findings by category."""
        optimizer = FindingOptimizer()
        
        by_category = optimizer.group_by_category(sample_findings)
        
        assert 'security' in by_category
        assert 'performance' in by_category
        assert 'correctness' in by_category
        assert len(by_category['security']) == 2
    
    def test_filter_by_severity(self, sample_findings):
        """Test filtering by severity."""
        optimizer = FindingOptimizer()
        
        # Filter for critical and high only
        filtered = optimizer.filter_findings(
            sample_findings,
            min_severity='high'
        )
        
        assert len(filtered) == 3  # 2 critical + 1 high
        assert all(f.severity in ['critical', 'high'] for f in filtered)
    
    def test_filter_by_confidence(self, sample_findings):
        """Test filtering by confidence."""
        optimizer = FindingOptimizer()
        
        # Filter for high confidence only
        filtered = optimizer.filter_findings(
            sample_findings,
            min_confidence=0.85
        )
        
        assert len(filtered) == 3  # 0.95, 0.90, 0.85
        assert all(f.confidence >= 0.85 for f in filtered)
    
    def test_filter_by_category(self, sample_findings):
        """Test filtering by category."""
        optimizer = FindingOptimizer()
        
        # Filter for security only
        filtered = optimizer.filter_findings(
            sample_findings,
            categories=['security']
        )
        
        assert len(filtered) == 2
        assert all(f.category == 'security' for f in filtered)
    
    def test_filter_by_file_pattern(self, sample_findings):
        """Test filtering by file pattern."""
        optimizer = FindingOptimizer()
        
        # Filter for app.py only
        filtered = optimizer.filter_findings(
            sample_findings,
            file_patterns=['app.py']
        )
        
        assert len(filtered) == 3
        assert all(f.file_path == 'app.py' for f in filtered)
        
        # Filter for Python files
        filtered = optimizer.filter_findings(
            sample_findings,
            file_patterns=['*.py']
        )
        
        assert len(filtered) == 5  # All are Python files
    
    def test_combined_filters(self, sample_findings):
        """Test combining multiple filters."""
        optimizer = FindingOptimizer()
        
        # Critical security issues with high confidence
        filtered = optimizer.filter_findings(
            sample_findings,
            min_severity='critical',
            categories=['security'],
            min_confidence=0.90
        )
        
        assert len(filtered) == 2
        assert all(f.severity == 'critical' for f in filtered)
        assert all(f.category == 'security' for f in filtered)
        assert all(f.confidence >= 0.90 for f in filtered)
    
    def test_quick_summary(self, sample_findings):
        """Test quick summary generation."""
        optimizer = FindingOptimizer()

        summary = optimizer.get_quick_summary(sample_findings)

        assert summary['total_findings'] == 5
        assert summary['files_affected'] == 2
        # high_confidence_critical counts critical AND high severity with confidence >= 0.8
        # 2 SQL injections (critical, 0.95 and 0.90) + 1 null pointer (high, 0.85) = 3
        assert summary['high_confidence_critical'] == 3
        # Actionable findings have suggestions: 2 SQL + 1 loop + 1 null pointer = 4
        assert summary['actionable_findings'] == 4
        assert summary['needs_immediate_attention'] is True
        
        # Check severity breakdown
        assert summary['by_severity']['critical'] == 2
        assert summary['by_severity']['high'] == 1
        assert summary['by_severity']['medium'] == 1
        assert summary['by_severity']['low'] == 1
        
        # Check top files
        assert len(summary['top_files']) == 2
        assert summary['top_files'][0][0] == 'app.py'  # Most issues
        assert summary['top_files'][0][1] == 3


class TestReviewResultEnhancements:
    """Test enhancements to ReviewResult class."""
    
    def test_get_quick_summary(self, sample_findings):
        """Test ReviewResult.get_quick_summary()."""
        result = ReviewResult(
            findings=sample_findings,
            files_reviewed=2,
            total_chunks=5
        )
        
        summary = result.get_quick_summary()
        
        assert summary['total_findings'] == 5
        assert summary['files_affected'] == 2
        assert summary['needs_immediate_attention'] is True
    
    def test_get_prioritized_findings(self, sample_findings):
        """Test ReviewResult.get_prioritized_findings()."""
        result = ReviewResult(
            findings=sample_findings,
            files_reviewed=2,
            total_chunks=5
        )
        
        prioritized = result.get_prioritized_findings()
        
        assert len(prioritized) == 5
        assert all(isinstance(fp, FindingPriority) for fp in prioritized)
        
        # Should be sorted by priority
        scores = [fp.priority_score for fp in prioritized]
        assert scores == sorted(scores, reverse=True)
    
    def test_get_findings_by_file(self, sample_findings):
        """Test ReviewResult.get_findings_by_file()."""
        result = ReviewResult(
            findings=sample_findings,
            files_reviewed=2,
            total_chunks=5
        )
        
        by_file = result.get_findings_by_file()
        
        assert 'app.py' in by_file
        assert 'utils.py' in by_file
        assert len(by_file['app.py']) == 3
    
    def test_get_findings_by_category(self, sample_findings):
        """Test ReviewResult.get_findings_by_category()."""
        result = ReviewResult(
            findings=sample_findings,
            files_reviewed=2,
            total_chunks=5
        )
        
        by_category = result.get_findings_by_category()
        
        assert 'security' in by_category
        assert len(by_category['security']) == 2
    
    def test_deduplicate_findings(self, sample_findings):
        """Test ReviewResult.deduplicate_findings()."""
        result = ReviewResult(
            findings=sample_findings,
            files_reviewed=2,
            total_chunks=5
        )
        
        deduplicated_result = result.deduplicate_findings()
        
        assert len(deduplicated_result.findings) == 4  # One duplicate removed
        assert deduplicated_result.files_reviewed == 2  # Preserved
        assert deduplicated_result.total_chunks == 5  # Preserved


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

