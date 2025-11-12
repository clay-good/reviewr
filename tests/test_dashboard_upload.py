"""
Tests for reviewr dashboard upload functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path

from reviewr.dashboard.database import (
    DatabaseManager,
    Project,
    Review,
    Finding
)


@pytest.fixture
def db_manager():
    """Create a temporary database for testing."""
    db_manager = DatabaseManager('sqlite:///:memory:')
    db_manager.create_tables()
    yield db_manager


@pytest.fixture
def sample_results_file(tmp_path):
    """Create a sample results JSON file for testing."""
    results = {
        "metadata": {
            "total_files": 10,
            "total_lines": 1000,
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "total_tokens": 5000,
            "total_cost": 0.05,
            "duration_seconds": 12.5
        },
        "findings": [
            {
                "type": "security",
                "severity": "critical",
                "category": "sql-injection",
                "file": "app.py",
                "line": 42,
                "line_end": 42,
                "message": "Potential SQL injection vulnerability",
                "suggestion": "Use parameterized queries",
                "confidence": 0.95
            },
            {
                "type": "performance",
                "severity": "high",
                "category": "inefficient-loop",
                "file": "utils.py",
                "line": 100,
                "line_end": 105,
                "message": "Inefficient nested loop",
                "suggestion": "Consider using a hash map",
                "confidence": 0.85
            },
            {
                "type": "style",
                "severity": "low",
                "category": "naming",
                "file": "models.py",
                "line": 20,
                "line_end": 20,
                "message": "Variable name should be snake_case",
                "suggestion": "Rename to snake_case",
                "confidence": 1.0
            }
        ]
    }
    
    results_file = tmp_path / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    return str(results_file)


def test_upload_results_basic(db_manager, sample_results_file):
    """Test basic upload of review results to the dashboard."""
    session = db_manager.get_session()
    
    try:
        # Load results file
        with open(sample_results_file, 'r') as f:
            results = json.load(f)
        
        # Create project
        project = Project(name='test-upload-project')
        session.add(project)
        session.flush()
        
        # Create review
        review = Review(
            project_id=project.id,
            commit_sha='test123',
            branch='main',
            author='test-user',
            status='completed'
        )
        
        # Extract metadata
        if 'metadata' in results:
            metadata = results['metadata']
            review.files_reviewed = metadata.get('total_files', 0)
            review.lines_reviewed = metadata.get('total_lines', 0)
            review.provider = metadata.get('provider')
            review.model = metadata.get('model')
            review.total_tokens = metadata.get('total_tokens')
            review.total_cost = metadata.get('total_cost')
            review.duration_seconds = metadata.get('duration_seconds')
        
        session.add(review)
        session.flush()
        
        # Add findings
        findings = results.get('findings', [])
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        for finding_data in findings:
            finding = Finding(
                review_id=review.id,
                type=finding_data.get('type', 'unknown'),
                severity=finding_data.get('severity', 'info'),
                category=finding_data.get('category'),
                file_path=finding_data.get('file', ''),
                line_start=finding_data.get('line', 0),
                line_end=finding_data.get('line_end', finding_data.get('line', 0)),
                message=finding_data.get('message', ''),
                suggestion=finding_data.get('suggestion'),
                code_snippet=finding_data.get('code_snippet'),
                confidence=finding_data.get('confidence'),
                status='open'
            )
            session.add(finding)
            
            severity = finding_data.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Update review statistics
        review.total_findings = len(findings)
        review.critical_findings = severity_counts['critical']
        review.high_findings = severity_counts['high']
        review.medium_findings = severity_counts['medium']
        review.low_findings = severity_counts['low']
        review.info_findings = severity_counts['info']
        
        session.commit()
        
        # Verify the upload
        queried_review = session.query(Review).filter_by(id=review.id).first()
        assert queried_review is not None
        assert queried_review.total_findings == 3
        assert queried_review.critical_findings == 1
        assert queried_review.high_findings == 1
        assert queried_review.low_findings == 1
        assert queried_review.provider == 'anthropic'
        assert queried_review.model == 'claude-3-5-sonnet-20241022'
        
        # Verify findings were created
        queried_findings = session.query(Finding).filter_by(review_id=review.id).all()
        assert len(queried_findings) == 3
        
        # Verify finding details
        critical_finding = session.query(Finding).filter_by(
            review_id=review.id,
            severity='critical'
        ).first()
        assert critical_finding is not None
        assert critical_finding.type == 'security'
        assert critical_finding.category == 'sql-injection'
        assert critical_finding.file_path == 'app.py'
        assert critical_finding.line_start == 42
        
    finally:
        session.close()


def test_upload_results_no_metadata(db_manager, tmp_path):
    """Test upload of results without metadata."""
    session = db_manager.get_session()
    
    # Create results file without metadata
    results = {
        "findings": [
            {
                "type": "security",
                "severity": "high",
                "file": "test.py",
                "line": 10,
                "message": "Test finding"
            }
        ]
    }
    
    results_file = tmp_path / "results_no_metadata.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Create project and review
        project = Project(name='test-no-metadata')
        session.add(project)
        session.flush()
        
        review = Review(
            project_id=project.id,
            status='completed'
        )
        session.add(review)
        session.flush()
        
        # Add findings
        findings = results.get('findings', [])
        for finding_data in findings:
            finding = Finding(
                review_id=review.id,
                type=finding_data.get('type', 'unknown'),
                severity=finding_data.get('severity', 'info'),
                file_path=finding_data.get('file', ''),
                line_start=finding_data.get('line', 0),
                line_end=finding_data.get('line_end', finding_data.get('line', 0)),
                message=finding_data.get('message', ''),
                status='open'
            )
            session.add(finding)
        
        review.total_findings = len(findings)
        review.high_findings = 1
        
        session.commit()
        
        # Verify
        queried_review = session.query(Review).filter_by(id=review.id).first()
        assert queried_review is not None
        assert queried_review.total_findings == 1
        assert queried_review.high_findings == 1
        
    finally:
        session.close()


def test_upload_results_empty_findings(db_manager, tmp_path):
    """Test upload of results with no findings."""
    session = db_manager.get_session()
    
    # Create results file with no findings
    results = {
        "metadata": {
            "total_files": 5,
            "total_lines": 500
        },
        "findings": []
    }
    
    results_file = tmp_path / "results_empty.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Create project and review
        project = Project(name='test-empty-findings')
        session.add(project)
        session.flush()
        
        review = Review(
            project_id=project.id,
            status='completed',
            files_reviewed=results['metadata']['total_files'],
            lines_reviewed=results['metadata']['total_lines']
        )
        session.add(review)
        session.flush()
        
        # No findings to add
        review.total_findings = 0
        
        session.commit()
        
        # Verify
        queried_review = session.query(Review).filter_by(id=review.id).first()
        assert queried_review is not None
        assert queried_review.total_findings == 0
        assert queried_review.files_reviewed == 5
        assert queried_review.lines_reviewed == 500
        
    finally:
        session.close()

