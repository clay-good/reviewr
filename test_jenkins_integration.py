"""
Tests for Jenkins integration.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from reviewr.integrations.jenkins import (
    JenkinsIntegration,
    JenkinsConfig,
    JenkinsBuildStatus,
    review_build
)


class TestJenkinsConfig:
    """Test JenkinsConfig."""
    
    def test_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv('JENKINS_URL', 'https://jenkins.example.com')
        monkeypatch.setenv('JENKINS_USERNAME', 'admin')
        monkeypatch.setenv('JENKINS_API_TOKEN', 'token123')
        monkeypatch.setenv('JOB_NAME', 'my-job')
        monkeypatch.setenv('BUILD_NUMBER', '42')
        
        config = JenkinsConfig.from_env()
        
        assert config.url == 'https://jenkins.example.com'
        assert config.username == 'admin'
        assert config.api_token == 'token123'
        assert config.job_name == 'my-job'
        assert config.build_number == 42
    
    def test_from_env_defaults(self, monkeypatch):
        """Test creating config with defaults."""
        # Clear environment
        for key in ['JENKINS_URL', 'JENKINS_USERNAME', 'JENKINS_API_TOKEN', 'JOB_NAME', 'BUILD_NUMBER']:
            monkeypatch.delenv(key, raising=False)
        
        config = JenkinsConfig.from_env()
        
        assert config.url == ''
        assert config.username is None
        assert config.api_token is None
        assert config.job_name is None
        assert config.build_number is None


class TestJenkinsIntegration:
    """Test JenkinsIntegration."""
    
    def test_init_no_url(self):
        """Test initialization without URL."""
        with pytest.raises(ValueError, match="Jenkins URL not provided"):
            JenkinsIntegration()
    
    def test_init_with_url(self):
        """Test initialization with URL."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        assert integration.url == 'https://jenkins.example.com'
        assert integration.username is None
        assert integration.api_token is None
    
    def test_init_with_credentials(self):
        """Test initialization with credentials."""
        integration = JenkinsIntegration(
            url='https://jenkins.example.com',
            username='admin',
            api_token='token123'
        )
        
        assert integration.url == 'https://jenkins.example.com'
        assert integration.username == 'admin'
        assert integration.api_token == 'token123'
        assert 'Authorization' in integration.headers
    
    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment."""
        monkeypatch.setenv('JENKINS_URL', 'https://jenkins.example.com')
        monkeypatch.setenv('JENKINS_USERNAME', 'admin')
        monkeypatch.setenv('JENKINS_API_TOKEN', 'token123')
        monkeypatch.setenv('JOB_NAME', 'my-job')
        monkeypatch.setenv('BUILD_NUMBER', '42')
        
        integration = JenkinsIntegration()
        
        assert integration.url == 'https://jenkins.example.com'
        assert integration.username == 'admin'
        assert integration.api_token == 'token123'
        assert integration.job_name == 'my-job'
        assert integration.build_number == 42
    
    def test_url_trailing_slash(self):
        """Test URL trailing slash is removed."""
        integration = JenkinsIntegration(url='https://jenkins.example.com/')
        
        assert integration.url == 'https://jenkins.example.com'
    
    @patch('reviewr.integrations.jenkins.requests.get')
    def test_get_build_info(self, mock_get):
        """Test getting build info."""
        mock_get.return_value.json.return_value = {
            'number': 42,
            'result': 'SUCCESS',
            'duration': 12345
        }
        mock_get.return_value.raise_for_status = Mock()
        
        integration = JenkinsIntegration(
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        info = integration.get_build_info()
        
        assert info['number'] == 42
        assert info['result'] == 'SUCCESS'
        mock_get.assert_called_once()
        assert 'my-job/42/api/json' in mock_get.call_args[0][0]
    
    @patch('reviewr.integrations.jenkins.requests.post')
    def test_set_build_description(self, mock_post):
        """Test setting build description."""
        mock_post.return_value.raise_for_status = Mock()
        
        integration = JenkinsIntegration(
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        integration.set_build_description("Test description")
        
        mock_post.assert_called_once()
        assert 'my-job/42/submitDescription' in mock_post.call_args[0][0]
        assert mock_post.call_args[1]['data']['description'] == "Test description"
    
    def test_publish_artifact(self, tmp_path):
        """Test publishing artifact."""
        # Create a test file
        test_file = tmp_path / "report.json"
        test_file.write_text('{"test": "data"}')
        
        integration = JenkinsIntegration(
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        artifact = integration.publish_artifact(str(test_file))
        
        assert artifact['name'] == 'report.json'
        assert artifact['path'] == str(test_file)
        assert 'my-job/42/artifact/report.json' in artifact['url']
        assert artifact['size'] > 0
    
    @patch('reviewr.integrations.jenkins.requests.get')
    @patch('reviewr.integrations.jenkins.requests.post')
    def test_add_badge(self, mock_post, mock_get):
        """Test adding badge."""
        mock_get.return_value.json.return_value = {'description': 'Old description'}
        mock_get.return_value.raise_for_status = Mock()
        mock_post.return_value.raise_for_status = Mock()
        
        integration = JenkinsIntegration(
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        integration.add_badge("Test Badge", "green")
        
        # Should get current description and set new one
        mock_get.assert_called_once()
        mock_post.assert_called_once()
    
    def test_format_review_summary_no_findings(self):
        """Test formatting review summary with no findings."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        summary = integration.format_review_summary([])
        
        assert '✅' in summary
        assert 'No issues found' in summary
        assert '<div' in summary  # HTML formatting
    
    def test_format_review_summary_with_findings(self):
        """Test formatting review summary with findings."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        findings = [
            {'severity': 'critical', 'title': 'SQL Injection'},
            {'severity': 'high', 'title': 'XSS'},
            {'severity': 'medium', 'title': 'Unused variable'}
        ]
        
        summary = integration.format_review_summary(findings)
        
        assert '🔴' in summary
        assert 'Critical' in summary
        assert 'High' in summary
        assert 'Medium' in summary
        assert '<div' in summary  # HTML formatting
    
    def test_format_review_summary_critical_status(self):
        """Test formatting with critical issues."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        findings = [{'severity': 'critical', 'title': 'SQL Injection'}]
        
        summary = integration.format_review_summary(findings)
        
        assert 'Critical Issues Found' in summary
        assert '#f8d7da' in summary  # Red background color
    
    def test_format_review_summary_high_status(self):
        """Test formatting with high issues."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        findings = [{'severity': 'high', 'title': 'XSS'}]
        
        summary = integration.format_review_summary(findings)
        
        assert 'High Priority Issues Found' in summary
        assert '#fff3cd' in summary  # Yellow background color
    
    def test_format_review_summary_low_status(self):
        """Test formatting with only low issues."""
        integration = JenkinsIntegration(url='https://jenkins.example.com')
        
        findings = [{'severity': 'low', 'title': 'Minor issue'}]
        
        summary = integration.format_review_summary(findings)
        
        assert 'Only Minor Issues Found' in summary
        assert '#d1ecf1' in summary  # Blue background color


class TestReviewBuild:
    """Test review_build function."""
    
    @patch('reviewr.integrations.jenkins.JenkinsIntegration')
    @patch('builtins.open', new_callable=mock_open)
    def test_review_build_basic(self, mock_file, mock_integration_class):
        """Test basic build review."""
        mock_integration = Mock()
        mock_integration.format_review_summary.return_value = "Test summary"
        mock_integration.set_build_description = Mock()
        mock_integration.add_badge = Mock()
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'medium', 'title': 'Test', 'file': 'test.py', 'line': 10}
        ]
        
        result = review_build(
            findings=findings,
            output_file='report.json',
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        assert result['total_findings'] == 1
        assert result['description_set'] is True
        assert result['badge_added'] is True
        assert result['output_file'] == 'report.json'
        mock_integration.set_build_description.assert_called_once()
        mock_integration.add_badge.assert_called_once()
    
    @patch('reviewr.integrations.jenkins.JenkinsIntegration')
    def test_review_build_no_description(self, mock_integration_class):
        """Test build review without setting description."""
        mock_integration = Mock()
        mock_integration_class.return_value = mock_integration
        
        findings = []
        
        result = review_build(
            findings=findings,
            set_description=False,
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        assert result['description_set'] is False
        mock_integration.set_build_description.assert_not_called()
    
    @patch('reviewr.integrations.jenkins.JenkinsIntegration')
    def test_review_build_critical_badge(self, mock_integration_class):
        """Test build review with critical issues."""
        mock_integration = Mock()
        mock_integration.format_review_summary.return_value = "Test summary"
        mock_integration.set_build_description = Mock()
        mock_integration.add_badge = Mock()
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'critical', 'title': 'SQL Injection'}
        ]
        
        result = review_build(
            findings=findings,
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        # Should add red badge for critical issues
        mock_integration.add_badge.assert_called_once()
        call_args = mock_integration.add_badge.call_args
        assert 'Issues Found' in call_args[0][0]
        assert call_args[0][1] == 'red'
    
    @patch('reviewr.integrations.jenkins.JenkinsIntegration')
    def test_review_build_passed_badge(self, mock_integration_class):
        """Test build review with no issues."""
        mock_integration = Mock()
        mock_integration.format_review_summary.return_value = "Test summary"
        mock_integration.set_build_description = Mock()
        mock_integration.add_badge = Mock()
        mock_integration_class.return_value = mock_integration
        
        findings = []
        
        result = review_build(
            findings=findings,
            url='https://jenkins.example.com',
            job_name='my-job',
            build_number=42
        )
        
        # Should add green badge for passed review
        mock_integration.add_badge.assert_called_once()
        call_args = mock_integration.add_badge.call_args
        assert 'Passed' in call_args[0][0]
        assert call_args[0][1] == 'green'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

