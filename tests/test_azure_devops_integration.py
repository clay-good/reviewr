"""
Tests for Azure DevOps integration.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from reviewr.integrations.azure_devops import (
    AzureDevOpsIntegration,
    AzureDevOpsComment,
    AzureDevOpsVote,
    review_pull_request
)


class TestAzureDevOpsIntegration:
    """Test AzureDevOpsIntegration."""
    
    def test_init_no_pat(self):
        """Test initialization without PAT."""
        with pytest.raises(ValueError, match="Azure DevOps PAT not provided"):
            AzureDevOpsIntegration()
    
    def test_init_with_pat(self, monkeypatch):
        """Test initialization with PAT."""
        monkeypatch.setenv('AZURE_DEVOPS_PAT', 'test-pat')
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'test-org')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'test-project')
        monkeypatch.setenv('AZURE_DEVOPS_REPO', 'test-repo')
        
        integration = AzureDevOpsIntegration()
        
        assert integration.pat == 'test-pat'
        assert integration.organization == 'test-org'
        assert integration.project == 'test-project'
        assert integration.repository == 'test-repo'
    
    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert integration.pat == 'test-pat'
        assert integration.organization == 'test-org'
        assert integration.project == 'test-project'
        assert integration.repository == 'test-repo'
    
    def test_api_base_url_cloud(self):
        """Test API base URL for Azure DevOps Services."""
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert integration.api_base == 'https://dev.azure.com/test-org'
    
    def test_api_base_url_server(self):
        """Test API base URL for Azure DevOps Server."""
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo',
            server_url='https://azuredevops.company.com'
        )
        
        assert integration.api_base == 'https://azuredevops.company.com/test-org'
    
    def test_get_pr_id_from_env(self, monkeypatch):
        """Test getting PR ID from environment."""
        monkeypatch.setenv('SYSTEM_PULLREQUEST_PULLREQUESTID', '123')
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert integration.get_pr_id() == 123
    
    def test_get_pr_id_from_branch(self, monkeypatch):
        """Test getting PR ID from branch name."""
        monkeypatch.setenv('BUILD_SOURCEBRANCH', 'refs/pull/456/merge')
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert integration.get_pr_id() == 456
    
    @patch('reviewr.integrations.azure_devops.requests.post')
    def test_post_comment(self, mock_post):
        """Test posting a comment."""
        mock_post.return_value.json.return_value = {'id': 1}
        mock_post.return_value.raise_for_status = Mock()
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        result = integration.post_comment(123, "Test comment")
        
        assert result['id'] == 1
        mock_post.assert_called_once()
        
        # Check URL
        call_args = mock_post.call_args
        assert 'pullRequests/123/threads' in call_args[0][0]
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['comments'][0]['content'] == "Test comment"
    
    @patch('reviewr.integrations.azure_devops.requests.post')
    def test_post_inline_comments(self, mock_post):
        """Test posting inline comments."""
        mock_post.return_value.json.return_value = {'id': 1}
        mock_post.return_value.raise_for_status = Mock()
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        comments = [
            AzureDevOpsComment(path='test.py', line=10, body='Issue 1'),
            AzureDevOpsComment(path='test.py', line=20, body='Issue 2')
        ]
        
        results = integration.post_inline_comments(123, comments)
        
        assert len(results) == 2
        assert mock_post.call_count == 2
    
    @patch('reviewr.integrations.azure_devops.requests.get')
    @patch('reviewr.integrations.azure_devops.requests.put')
    def test_set_vote(self, mock_put, mock_get):
        """Test setting vote on PR."""
        mock_get.return_value.json.return_value = {
            'authenticatedUser': {'id': 'user-123'}
        }
        mock_get.return_value.raise_for_status = Mock()
        mock_put.return_value.json.return_value = {'vote': 10}
        mock_put.return_value.raise_for_status = Mock()
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        result = integration.set_vote(123, AzureDevOpsVote.APPROVED)
        
        assert result['vote'] == 10
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        
        # Check vote value
        call_args = mock_put.call_args
        assert call_args[1]['json']['vote'] == 10
    
    @patch('reviewr.integrations.azure_devops.requests.post')
    def test_update_build_status(self, mock_post):
        """Test updating build status."""
        mock_post.return_value.json.return_value = {'id': 1}
        mock_post.return_value.raise_for_status = Mock()
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        result = integration.update_build_status(
            'abc123',
            'succeeded',
            'Review passed'
        )
        
        assert result['id'] == 1
        mock_post.assert_called_once()
        
        # Check payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['state'] == 'succeeded'
        assert payload['description'] == 'Review passed'
    
    @patch('reviewr.integrations.azure_devops.requests.put')
    def test_link_work_item(self, mock_put):
        """Test linking work item to PR."""
        mock_put.return_value.json.return_value = {'id': 456}
        mock_put.return_value.raise_for_status = Mock()
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        result = integration.link_work_item(123, 456)
        
        assert result['id'] == 456
        mock_put.assert_called_once()
        
        # Check URL
        call_args = mock_put.call_args
        assert 'pullRequests/123/workitems/456' in call_args[0][0]
    
    @patch('reviewr.integrations.azure_devops.requests.get')
    def test_get_pr_files(self, mock_get):
        """Test getting PR files."""
        # Mock PR details
        pr_response = Mock()
        pr_response.json.return_value = {
            'lastMergeSourceCommit': {'commitId': 'source123'},
            'lastMergeTargetCommit': {'commitId': 'target123'}
        }
        pr_response.raise_for_status = Mock()
        
        # Mock diff response
        diff_response = Mock()
        diff_response.json.return_value = {
            'changes': [
                {'item': {'path': '/src/test.py'}},
                {'item': {'path': '/src/utils.py'}}
            ]
        }
        diff_response.raise_for_status = Mock()
        
        mock_get.side_effect = [pr_response, diff_response]
        
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        files = integration.get_pr_files(123)
        
        assert len(files) == 2
        assert 'src/test.py' in files
        assert 'src/utils.py' in files
    
    def test_format_review_comment_no_findings(self):
        """Test formatting review comment with no findings."""
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        comment = integration.format_review_comment([])
        
        assert '✅' in comment
        assert 'No issues found' in comment
    
    def test_format_review_comment_with_findings(self):
        """Test formatting review comment with findings."""
        integration = AzureDevOpsIntegration(
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        findings = [
            {'severity': 'critical', 'title': 'SQL Injection'},
            {'severity': 'high', 'title': 'XSS'},
            {'severity': 'medium', 'title': 'Unused variable'}
        ]
        
        comment = integration.format_review_comment(findings)
        
        assert '🔴' in comment
        assert 'Critical' in comment
        assert 'High' in comment
        assert 'Medium' in comment


class TestReviewPullRequest:
    """Test review_pull_request function."""
    
    @patch('reviewr.integrations.azure_devops.AzureDevOpsIntegration')
    def test_review_pull_request_basic(self, mock_integration_class):
        """Test basic PR review."""
        mock_integration = Mock()
        mock_integration.format_review_comment.return_value = "Test comment"
        mock_integration.post_comment.return_value = {'id': 1}
        mock_integration.post_inline_comments.return_value = []
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'medium', 'title': 'Test', 'file': 'test.py', 'line': 10}
        ]
        
        result = review_pull_request(
            pr_id=123,
            findings=findings,
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert result['pr_id'] == 123
        assert result['summary_posted'] is True
        assert result['total_findings'] == 1
        mock_integration.post_comment.assert_called_once()
    
    @patch('reviewr.integrations.azure_devops.AzureDevOpsIntegration')
    def test_review_pull_request_with_auto_approve(self, mock_integration_class):
        """Test PR review with auto-approval."""
        mock_integration = Mock()
        mock_integration.format_review_comment.return_value = "Test comment"
        mock_integration.post_comment.return_value = {'id': 1}
        mock_integration.post_inline_comments.return_value = []
        mock_integration.set_vote.return_value = {'vote': 10}
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'low', 'title': 'Test', 'file': 'test.py', 'line': 10}
        ]
        
        result = review_pull_request(
            pr_id=123,
            findings=findings,
            auto_approve=True,
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert result['vote_set'] is True
        mock_integration.set_vote.assert_called_once()
    
    @patch('reviewr.integrations.azure_devops.AzureDevOpsIntegration')
    def test_review_pull_request_no_auto_approve_with_critical(self, mock_integration_class):
        """Test PR review doesn't auto-approve with critical issues."""
        mock_integration = Mock()
        mock_integration.format_review_comment.return_value = "Test comment"
        mock_integration.post_comment.return_value = {'id': 1}
        mock_integration.post_inline_comments.return_value = []
        mock_integration_class.return_value = mock_integration
        
        findings = [
            {'severity': 'critical', 'title': 'SQL Injection', 'file': 'test.py', 'line': 10}
        ]
        
        result = review_pull_request(
            pr_id=123,
            findings=findings,
            auto_approve=True,
            pat='test-pat',
            organization='test-org',
            project='test-project',
            repository='test-repo'
        )
        
        assert result['vote_set'] is False
        mock_integration.set_vote.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

