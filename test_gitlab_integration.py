#!/usr/bin/env python3
"""
Unit tests for GitLab integration.

Run with: python3 -m pytest test_gitlab_integration.py -v
Or: python3 test_gitlab_integration.py
"""

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import the GitLab integration classes
try:
    from reviewr.integrations.gitlab import (
        GitLabIntegration,
        GitLabComment,
        GitLabReviewStatus
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: Could not import GitLab integration. Some tests will be skipped.")


@dataclass
class MockReviewFinding:
    """Mock review finding for testing."""
    file_path: str
    line_start: int
    line_end: int
    severity: str
    message: str
    suggestion: str
    confidence: float = 0.95
    type: str = "security"


class TestGitLabIntegration(unittest.TestCase):
    """Test cases for GitLab integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("GitLab integration not available")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'GITLAB_TOKEN': 'test_token_123',
            'CI_PROJECT_ID': '12345',
            'CI_MERGE_REQUEST_IID': '42',
            'CI_API_V4_URL': 'https://gitlab.example.com/api/v4'
        })
        self.env_patcher.start()
        
        # Mock requests
        self.requests_patcher = patch('reviewr.integrations.gitlab.requests')
        self.mock_requests = self.requests_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'env_patcher'):
            self.env_patcher.stop()
        if hasattr(self, 'requests_patcher'):
            self.requests_patcher.stop()
    
    def test_initialization_with_env_vars(self):
        """Test GitLab integration initializes with environment variables."""
        gitlab = GitLabIntegration()
        
        self.assertEqual(gitlab.token, 'test_token_123')
        self.assertEqual(gitlab.project_id, '12345')
        self.assertEqual(gitlab.api_url, 'https://gitlab.example.com/api/v4')
    
    def test_initialization_with_params(self):
        """Test GitLab integration initializes with parameters."""
        gitlab = GitLabIntegration(
            token='custom_token',
            project_id='67890',
            api_url='https://custom.gitlab.com/api/v4'
        )
        
        self.assertEqual(gitlab.token, 'custom_token')
        self.assertEqual(gitlab.project_id, '67890')
        self.assertEqual(gitlab.api_url, 'https://custom.gitlab.com/api/v4')
    
    def test_get_mr_number_from_env(self):
        """Test MR number detection from environment."""
        gitlab = GitLabIntegration()
        mr_iid = gitlab.get_mr_number()
        
        self.assertEqual(mr_iid, 42)
    
    def test_format_findings_as_comments(self):
        """Test formatting review findings as GitLab comments."""
        gitlab = GitLabIntegration()
        
        findings = [
            MockReviewFinding(
                file_path="src/test.py",
                line_start=10,
                line_end=10,
                severity="high",
                message="Security issue detected",
                suggestion="Fix the security issue",
                confidence=0.95
            ),
            MockReviewFinding(
                file_path="src/other.py",
                line_start=20,
                line_end=20,
                severity="medium",
                message="Performance issue",
                suggestion="Optimize the code",
                confidence=0.85
            )
        ]
        
        comments = gitlab.format_findings_as_comments(findings)
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].path, "src/test.py")
        self.assertEqual(comments[0].line, 10)
        self.assertIn("Security issue detected", comments[0].body)
        self.assertIn("Fix the security issue", comments[0].body)
    
    def test_format_findings_with_file_filter(self):
        """Test filtering findings by changed files."""
        gitlab = GitLabIntegration()
        
        findings = [
            MockReviewFinding(
                file_path="src/changed.py",
                line_start=10,
                line_end=10,
                severity="high",
                message="Issue in changed file",
                suggestion="Fix it"
            ),
            MockReviewFinding(
                file_path="src/unchanged.py",
                line_start=20,
                line_end=20,
                severity="medium",
                message="Issue in unchanged file",
                suggestion="Fix it"
            )
        ]
        
        changed_files = ["src/changed.py"]
        comments = gitlab.format_findings_as_comments(findings, changed_files)
        
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].path, "src/changed.py")
    
    def test_severity_emoji_mapping(self):
        """Test severity emoji mapping."""
        gitlab = GitLabIntegration()
        
        self.assertEqual(gitlab._get_severity_emoji('critical'), '🔴')
        self.assertEqual(gitlab._get_severity_emoji('high'), '🟠')
        self.assertEqual(gitlab._get_severity_emoji('medium'), '🟡')
        self.assertEqual(gitlab._get_severity_emoji('low'), '🔵')
        self.assertEqual(gitlab._get_severity_emoji('info'), 'ℹ️')
        self.assertEqual(gitlab._get_severity_emoji('unknown'), '⚪')
    
    def test_format_summary(self):
        """Test formatting review summary."""
        gitlab = GitLabIntegration()
        
        # Create mock result
        mock_result = Mock()
        mock_result.files_reviewed = 5
        mock_result.findings = [
            MockReviewFinding("file1.py", 1, 1, "critical", "msg1", "sug1"),
            MockReviewFinding("file2.py", 2, 2, "high", "msg2", "sug2"),
            MockReviewFinding("file3.py", 3, 3, "medium", "msg3", "sug3"),
        ]
        mock_result.has_critical_issues = Mock(return_value=True)
        mock_result.get_findings_by_severity = Mock(return_value={
            'critical': [mock_result.findings[0]],
            'high': [mock_result.findings[1]],
            'medium': [mock_result.findings[2]],
            'low': [],
            'info': []
        })
        mock_result.get_findings_by_type = Mock(return_value={
            'security': mock_result.findings[:2],
            'performance': [mock_result.findings[2]]
        })
        
        summary = gitlab.format_summary(mock_result)
        
        self.assertIn("reviewr Code Review Summary", summary)
        self.assertIn("Files reviewed**: 5", summary)
        self.assertIn("Total findings**: 3", summary)
        self.assertIn("🔴 1 critical", summary)
        self.assertIn("🟠 1 high", summary)
        self.assertIn("🟡 1 medium", summary)
        self.assertIn("security: 2", summary)
        self.assertIn("performance: 1", summary)
        self.assertIn("critical or high severity issues", summary)
    
    def test_get_mr_files(self):
        """Test getting MR files."""
        gitlab = GitLabIntegration()
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'changes': [
                {'new_path': 'file1.py', 'old_path': 'file1.py'},
                {'new_path': 'file2.py', 'old_path': 'file2.py'}
            ]
        }
        mock_response.raise_for_status = Mock()
        self.mock_requests.get.return_value = mock_response
        
        files = gitlab.get_mr_files(42)
        
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]['new_path'], 'file1.py')
        self.assertEqual(files[1]['new_path'], 'file2.py')
    
    def test_create_mr_note(self):
        """Test creating MR note."""
        gitlab = GitLabIntegration()
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'id': 123, 'body': 'Test note'}
        mock_response.raise_for_status = Mock()
        self.mock_requests.post.return_value = mock_response
        
        result = gitlab.create_mr_note(42, "Test note body")
        
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['body'], 'Test note')
        
        # Verify API call
        self.mock_requests.post.assert_called_once()
        call_args = self.mock_requests.post.call_args
        self.assertIn('/merge_requests/42/notes', call_args[0][0])
    
    def test_approve_mr(self):
        """Test approving MR."""
        gitlab = GitLabIntegration()
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'approved': True}
        mock_response.raise_for_status = Mock()
        self.mock_requests.post.return_value = mock_response
        
        result = gitlab.approve_mr(42)
        
        self.assertTrue(result['approved'])
        
        # Verify API call
        self.mock_requests.post.assert_called_once()
        call_args = self.mock_requests.post.call_args
        self.assertIn('/merge_requests/42/approve', call_args[0][0])
    
    def test_get_commit_sha(self):
        """Test getting commit SHA."""
        gitlab = GitLabIntegration()
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'sha': 'abc123def456'}
        mock_response.raise_for_status = Mock()
        self.mock_requests.get.return_value = mock_response
        
        sha = gitlab.get_commit_sha(42)
        
        self.assertEqual(sha, 'abc123def456')


class TestGitLabComment(unittest.TestCase):
    """Test cases for GitLabComment dataclass."""
    
    def test_comment_creation(self):
        """Test creating a GitLab comment."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("GitLab integration not available")
        
        comment = GitLabComment(
            path="src/test.py",
            line=42,
            body="Test comment body"
        )
        
        self.assertEqual(comment.path, "src/test.py")
        self.assertEqual(comment.line, 42)
        self.assertEqual(comment.body, "Test comment body")
        self.assertEqual(comment.line_type, "new")
    
    def test_comment_with_custom_line_type(self):
        """Test creating a comment with custom line type."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("GitLab integration not available")
        
        comment = GitLabComment(
            path="src/test.py",
            line=42,
            body="Test comment",
            line_type="old"
        )
        
        self.assertEqual(comment.line_type, "old")


class TestGitLabReviewStatus(unittest.TestCase):
    """Test cases for GitLabReviewStatus enum."""
    
    def test_review_status_values(self):
        """Test review status enum values."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("GitLab integration not available")
        
        self.assertEqual(GitLabReviewStatus.APPROVE.value, "approve")
        self.assertEqual(GitLabReviewStatus.UNAPPROVE.value, "unapprove")


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()

