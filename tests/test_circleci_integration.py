"""
Tests for CircleCI integration.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from reviewr.integrations.circleci import (
    CircleCIIntegration,
    CircleCIConfig,
    CircleCIStatus,
    review_workflow
)


class TestCircleCIConfig:
    """Test CircleCIConfig."""
    
    def test_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv('CIRCLE_TOKEN', 'token123')
        monkeypatch.setenv('CIRCLE_PROJECT_USERNAME', 'myorg')
        monkeypatch.setenv('CIRCLE_PROJECT_REPONAME', 'myrepo')
        monkeypatch.setenv('CIRCLE_REPOSITORY_URL', 'https://github.com/myorg/myrepo')
        monkeypatch.setenv('CIRCLE_WORKFLOW_ID', 'workflow123')
        monkeypatch.setenv('CIRCLE_BUILD_NUM', '42')
        
        config = CircleCIConfig.from_env()
        
        assert config.api_token == 'token123'
        assert config.project_slug == 'gh/myorg/myrepo'
        assert config.workflow_id == 'workflow123'
        assert config.job_number == '42'
    
    def test_from_env_defaults(self, monkeypatch):
        """Test creating config with defaults."""
        # Clear environment
        for key in ['CIRCLE_TOKEN', 'CIRCLE_PROJECT_USERNAME', 'CIRCLE_PROJECT_REPONAME', 
                    'CIRCLE_WORKFLOW_ID', 'CIRCLE_BUILD_NUM']:
            monkeypatch.delenv(key, raising=False)
        
        config = CircleCIConfig.from_env()
        
        assert config.api_token is None
        assert config.project_slug is None
        assert config.workflow_id is None
        assert config.job_number is None


class TestCircleCIIntegration:
    """Test CircleCIIntegration."""
    
    def test_init_no_token(self):
        """Test initialization without API token."""
        with pytest.raises(ValueError, match="CircleCI API token not provided"):
            CircleCIIntegration()
    
    def test_init_with_token(self):
        """Test initialization with API token."""
        integration = CircleCIIntegration(api_token='token123')
        
        assert integration.api_token == 'token123'
        assert integration.project_slug is None
        assert integration.workflow_id is None
    
    def test_init_with_full_config(self):
        """Test initialization with full configuration."""
        integration = CircleCIIntegration(
            api_token='token123',
            project_slug='gh/myorg/myrepo',
            workflow_id='workflow123',
            job_number='42'
        )
        
        assert integration.api_token == 'token123'
        assert integration.project_slug == 'gh/myorg/myrepo'
        assert integration.workflow_id == 'workflow123'
        assert integration.job_number == '42'
    
    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment."""
        monkeypatch.setenv('CIRCLE_TOKEN', 'token123')
        monkeypatch.setenv('CIRCLE_PROJECT_USERNAME', 'myorg')
        monkeypatch.setenv('CIRCLE_PROJECT_REPONAME', 'myrepo')
        monkeypatch.setenv('CIRCLE_REPOSITORY_URL', 'https://github.com/myorg/myrepo')
        monkeypatch.setenv('CIRCLE_WORKFLOW_ID', 'workflow123')
        monkeypatch.setenv('CIRCLE_BUILD_NUM', '42')
        
        integration = CircleCIIntegration()
        
        assert integration.api_token == 'token123'
        assert integration.project_slug == 'gh/myorg/myrepo'
        assert integration.workflow_id == 'workflow123'
        assert integration.job_number == '42'
    
    def test_get_project_slug_github(self, monkeypatch):
        """Test getting project slug for GitHub."""
        monkeypatch.setenv('CIRCLE_PROJECT_USERNAME', 'myorg')
        monkeypatch.setenv('CIRCLE_PROJECT_REPONAME', 'myrepo')
        monkeypatch.setenv('CIRCLE_REPOSITORY_URL', 'https://github.com/myorg/myrepo')
        
        integration = CircleCIIntegration(api_token='token123')
        
        assert integration.project_slug == 'gh/myorg/myrepo'
    
    def test_get_project_slug_bitbucket(self, monkeypatch):
        """Test getting project slug for Bitbucket."""
        monkeypatch.setenv('CIRCLE_PROJECT_USERNAME', 'myorg')
        monkeypatch.setenv('CIRCLE_PROJECT_REPONAME', 'myrepo')
        monkeypatch.setenv('CIRCLE_REPOSITORY_URL', 'https://bitbucket.org/myorg/myrepo')
        
        integration = CircleCIIntegration(api_token='token123')
        
        assert integration.project_slug == 'bb/myorg/myrepo'
    
    @patch('reviewr.integrations.circleci.requests.get')
    def test_get_workflow_info(self, mock_get):
        """Test getting workflow info."""
        mock_get.return_value.json.return_value = {
            'id': 'workflow123',
            'name': 'test-workflow',
            'status': 'running'
        }
        mock_get.return_value.raise_for_status = Mock()
        
        integration = CircleCIIntegration(
            api_token='token123',
            workflow_id='workflow123'
        )
        
        info = integration.get_workflow_info()
        
        assert info['id'] == 'workflow123'
        assert info['name'] == 'test-workflow'
        assert info['status'] == 'running'
        mock_get.assert_called_once()
        assert 'workflow/workflow123' in mock_get.call_args[0][0]
    
    @patch('reviewr.integrations.circleci.requests.get')
    def test_get_workflow_jobs(self, mock_get):
        """Test getting workflow jobs."""
        mock_get.return_value.json.return_value = {
            'items': [
                {'name': 'job1', 'status': 'success'},
                {'name': 'job2', 'status': 'running'}
            ]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        integration = CircleCIIntegration(
            api_token='token123',
            workflow_id='workflow123'
        )
        
        jobs = integration.get_workflow_jobs()
        
        assert len(jobs) == 2
        assert jobs[0]['name'] == 'job1'
        assert jobs[1]['name'] == 'job2'
        mock_get.assert_called_once()
        assert 'workflow/workflow123/job' in mock_get.call_args[0][0]
    
    @patch('reviewr.integrations.circleci.requests.get')
    def test_get_job_artifacts(self, mock_get):
        """Test getting job artifacts."""
        mock_get.return_value.json.return_value = {
            'items': [
                {'path': 'report.json', 'url': 'https://example.com/report.json'}
            ]
        }
        mock_get.return_value.raise_for_status = Mock()
        
        integration = CircleCIIntegration(
            api_token='token123',
            project_slug='gh/myorg/myrepo',
            job_number='42'
        )
        
        artifacts = integration.get_job_artifacts()
        
        assert len(artifacts) == 1
        assert artifacts[0]['path'] == 'report.json'
        mock_get.assert_called_once()
        assert 'project/gh/myorg/myrepo/42/artifacts' in mock_get.call_args[0][0]
    
    def test_store_artifact(self, tmp_path):
        """Test storing artifact."""
        # Create a test file
        test_file = tmp_path / "report.json"
        test_file.write_text('{"test": "data"}')
        
        integration = CircleCIIntegration(api_token='token123')
        
        artifact = integration.store_artifact(str(test_file))
        
        assert artifact['name'] == 'report.json'
        assert artifact['path'] == str(test_file)
        assert artifact['destination'] == 'artifacts/report.json'
        assert artifact['size'] > 0
    
    def test_store_artifact_not_found(self):
        """Test storing non-existent artifact."""
        integration = CircleCIIntegration(api_token='token123')
        
        with pytest.raises(FileNotFoundError):
            integration.store_artifact('nonexistent.json')
    
    def test_store_test_results(self, tmp_path):
        """Test storing test results."""
        # Create a test directory
        test_dir = tmp_path / "test-results"
        test_dir.mkdir()
        
        integration = CircleCIIntegration(api_token='token123')
        
        results = integration.store_test_results(str(test_dir))
        
        assert results['path'] == str(test_dir)
        assert results['destination'] == 'test-results'
    
    def test_format_review_summary_no_findings(self):
        """Test formatting review summary with no findings."""
        integration = CircleCIIntegration(api_token='token123')
        
        summary = integration.format_review_summary([])
        
        assert '✅' in summary
        assert 'no issues found' in summary.lower()
    
    def test_format_review_summary_with_findings(self):
        """Test formatting review summary with findings."""
        integration = CircleCIIntegration(api_token='token123')
        
        findings = [
            {'severity': 'critical', 'title': 'SQL Injection'},
            {'severity': 'high', 'title': 'XSS'},
            {'severity': 'medium', 'title': 'Unused variable'}
        ]
        
        summary = integration.format_review_summary(findings)
        
        assert 'Total Issues: 3' in summary
        assert 'Critical: 1' in summary
        assert 'High: 1' in summary
        assert 'Medium: 1' in summary
    
    def test_format_review_summary_critical_status(self):
        """Test formatting with critical issues."""
        integration = CircleCIIntegration(api_token='token123')
        
        findings = [{'severity': 'critical', 'title': 'SQL Injection'}]
        
        summary = integration.format_review_summary(findings)
        
        assert '🔴' in summary
        assert 'CRITICAL' in summary
    
    def test_format_review_summary_high_status(self):
        """Test formatting with high issues."""
        integration = CircleCIIntegration(api_token='token123')
        
        findings = [{'severity': 'high', 'title': 'XSS'}]
        
        summary = integration.format_review_summary(findings)
        
        assert '🟡' in summary
        assert 'HIGH PRIORITY' in summary


class TestReviewWorkflow:
    """Test review_workflow function."""
    
    @patch('reviewr.integrations.circleci.CircleCIIntegration')
    @patch('builtins.open', new_callable=mock_open)
    def test_review_workflow_basic(self, mock_file, mock_integration_class):
        """Test basic workflow review."""
        mock_integration = Mock()
        mock_integration.format_review_summary.return_value = "Test summary"
        mock_integration.workflow_id = 'workflow123'
        mock_integration.store_artifact.return_value = {
            'name': 'report.json',
            'path': 'report.json',
            'destination': 'artifacts/report.json',
            'size': 100
        }
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'medium', 'title': 'Test', 'file': 'test.py', 'line': 10}
        ]
        
        result = review_workflow(
            findings=findings,
            output_file='report.json',
            api_token='token123',
            workflow_id='workflow123'
        )
        
        assert result['total_findings'] == 1
        assert result['artifact_stored'] is True
        assert result['output_file'] == 'report.json'
        assert result['workflow_id'] == 'workflow123'
    
    @patch('reviewr.integrations.circleci.CircleCIIntegration')
    def test_review_workflow_no_output(self, mock_integration_class):
        """Test workflow review without output file."""
        mock_integration = Mock()
        mock_integration.format_review_summary.return_value = "Test summary"
        mock_integration.workflow_id = 'workflow123'
        mock_integration_class.return_value = mock_integration
        
        findings = []
        
        result = review_workflow(
            findings=findings,
            api_token='token123',
            workflow_id='workflow123'
        )
        
        assert result['artifact_stored'] is False
        assert result['output_file'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

