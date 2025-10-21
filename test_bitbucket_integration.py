"""
Tests for Bitbucket integration.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from reviewr.integrations.bitbucket import (
    BitbucketIntegration,
    BitbucketComment,
    BitbucketReviewStatus
)


@dataclass
class MockFinding:
    """Mock finding for testing."""
    file: str
    line: int
    message: str
    severity: str
    type: Mock
    category: str = "test"
    suggestion: str = ""


class TestBitbucketIntegration:
    """Test Bitbucket integration."""
    
    def test_init_cloud(self):
        """Test initialization for Bitbucket Cloud."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(workspace='testworkspace', repo_slug='testrepo')
            
            assert bb.username == 'testuser'
            assert bb.app_password == 'testpass'
            assert bb.workspace == 'testworkspace'
            assert bb.repo_slug == 'testrepo'
            assert not bb.is_server
            assert bb.api_base == 'https://api.bitbucket.org/2.0'
    
    def test_init_server(self):
        """Test initialization for Bitbucket Server."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(
                workspace='PROJECT',
                repo_slug='testrepo',
                is_server=True,
                server_url='https://bitbucket.company.com'
            )
            
            assert bb.is_server
            assert bb.server_url == 'https://bitbucket.company.com'
            assert bb.api_base == 'https://bitbucket.company.com/rest/api/1.0'
    
    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Bitbucket credentials not provided"):
                BitbucketIntegration(workspace='test', repo_slug='test')
    
    def test_init_missing_server_url(self):
        """Test initialization with missing server URL."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            with pytest.raises(ValueError, match="Bitbucket Server URL not provided"):
                BitbucketIntegration(
                    workspace='test',
                    repo_slug='test',
                    is_server=True
                )
    
    def test_detect_repo_cloud_https(self):
        """Test repository detection for Cloud HTTPS URL."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout='https://bitbucket.org/myworkspace/myrepo.git\n',
                    returncode=0
                )
                
                bb = BitbucketIntegration()
                
                assert bb.workspace == 'myworkspace'
                assert bb.repo_slug == 'myrepo'
    
    def test_detect_repo_cloud_ssh(self):
        """Test repository detection for Cloud SSH URL."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout='git@bitbucket.org:myworkspace/myrepo.git\n',
                    returncode=0
                )
                
                bb = BitbucketIntegration()
                
                assert bb.workspace == 'myworkspace'
                assert bb.repo_slug == 'myrepo'
    
    def test_detect_repo_server(self):
        """Test repository detection for Server URL."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass',
            'BITBUCKET_SERVER_URL': 'https://bitbucket.company.com'
        }):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout='https://bitbucket.company.com/scm/PROJECT/myrepo.git\n',
                    returncode=0
                )
                
                bb = BitbucketIntegration(is_server=True)
                
                assert bb.workspace == 'PROJECT'
                assert bb.repo_slug == 'myrepo'
    
    def test_get_pr_number_from_env(self):
        """Test getting PR number from environment."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass',
            'BITBUCKET_PR_ID': '123'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            assert bb.get_pr_number() == 123
    
    def test_get_pr_number_none(self):
        """Test getting PR number when not available."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            assert bb.get_pr_number() is None
    
    @patch('requests.get')
    def test_get_pr_files_cloud(self, mock_get):
        """Test getting PR files for Cloud."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            mock_response = Mock()
            mock_response.json.return_value = {
                'values': [
                    {'new': {'path': 'file1.py'}},
                    {'new': {'path': 'file2.py'}},
                    {'old': {'path': 'file3.py'}}
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            files = bb.get_pr_files(123)
            
            assert files == ['file1.py', 'file2.py', 'file3.py']
            mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_pr_files_server(self, mock_get):
        """Test getting PR files for Server."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            mock_response = Mock()
            mock_response.json.return_value = {
                'values': [
                    {'path': {'toString': 'file1.py'}},
                    {'path': {'toString': 'file2.py'}}
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            bb = BitbucketIntegration(
                workspace='PROJECT',
                repo_slug='test',
                is_server=True,
                server_url='https://bitbucket.company.com'
            )
            files = bb.get_pr_files(123)
            
            assert files == ['file1.py', 'file2.py']
            mock_get.assert_called_once()
    
    def test_get_commit_sha_from_env(self):
        """Test getting commit SHA from environment."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass',
            'BITBUCKET_COMMIT': 'abc123'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            assert bb.get_commit_sha() == 'abc123'
    
    def test_get_commit_sha_from_git(self):
        """Test getting commit SHA from git."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout='abc123def456\n',
                    returncode=0
                )
                
                bb = BitbucketIntegration(workspace='test', repo_slug='test')
                assert bb.get_commit_sha() == 'abc123def456'
    
    def test_format_findings_as_comments(self):
        """Test formatting findings as comments."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            
            mock_type = Mock()
            mock_type.value = 'security'
            
            findings = [
                MockFinding(
                    file='test.py',
                    line=10,
                    message='Security issue',
                    severity='critical',
                    type=mock_type,
                    category='security',
                    suggestion='Fix this'
                ),
                MockFinding(
                    file='test.py',
                    line=20,
                    message='Performance issue',
                    severity='medium',
                    type=mock_type,
                    category='performance'
                )
            ]
            
            comments = bb.format_findings_as_comments(findings)
            
            assert len(comments) == 2
            assert comments[0].path == 'test.py'
            assert comments[0].line == 10
            assert comments[0].severity == 'BLOCKER'
            assert 'Security issue' in comments[0].body
            assert 'Fix this' in comments[0].body
            
            assert comments[1].line == 20
            assert comments[1].severity == 'MAJOR'
    
    def test_format_summary_no_findings(self):
        """Test formatting summary with no findings."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            summary = bb.format_summary([])
            
            assert 'No issues found' in summary
            assert '✅' in summary
    
    def test_format_summary_with_findings(self):
        """Test formatting summary with findings."""
        with patch.dict(os.environ, {
            'BITBUCKET_USERNAME': 'testuser',
            'BITBUCKET_APP_PASSWORD': 'testpass'
        }):
            bb = BitbucketIntegration(workspace='test', repo_slug='test')
            
            mock_type = Mock()
            mock_type.value = 'security'
            
            findings = [
                MockFinding('test.py', 10, 'Issue 1', 'critical', mock_type),
                MockFinding('test.py', 20, 'Issue 2', 'high', mock_type),
                MockFinding('test.py', 30, 'Issue 3', 'medium', mock_type)
            ]
            
            summary = bb.format_summary(findings)
            
            assert 'Total findings' in summary
            assert '3' in summary
            assert 'Critical' in summary
            assert 'High' in summary
            assert 'Medium' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

