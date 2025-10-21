"""
Status check integration for CI/CD platforms.

This module provides utilities for posting commit status checks
to GitHub and GitLab.
"""

import os
import requests
from typing import Optional, Dict, Any
from enum import Enum


class CheckStatus(Enum):
    """Status check states."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class GitHubStatusCheck:
    """Post commit status checks to GitHub."""
    
    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub status check.
        
        Args:
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            repo: Repository in format "owner/repo" (defaults to GITHUB_REPOSITORY env var)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN', '')
        self.repo = repo or os.environ.get('GITHUB_REPOSITORY', '')
        self.api_base = 'https://api.github.com'
        
        if not self.token:
            raise ValueError("GitHub token is required")
        if not self.repo:
            raise ValueError("Repository is required")
    
    def post_status(
        self,
        commit_sha: str,
        state: CheckStatus,
        context: str = "reviewr",
        description: str = "",
        target_url: Optional[str] = None
    ) -> bool:
        """
        Post a commit status check.
        
        Args:
            commit_sha: Git commit SHA
            state: Status state (pending, success, failure, error)
            context: Status check context/name
            description: Short description of the status
            target_url: URL to link to for more details
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{self.repo}/statuses/{commit_sha}"
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'state': state.value,
            'context': context,
            'description': description[:140]  # GitHub limit
        }
        
        if target_url:
            payload['target_url'] = target_url
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting GitHub status: {e}")
            return False
    
    def post_check_run(
        self,
        commit_sha: str,
        name: str = "reviewr",
        status: str = "completed",
        conclusion: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        text: Optional[str] = None
    ) -> bool:
        """
        Post a GitHub Check Run (more detailed than status).
        
        Args:
            commit_sha: Git commit SHA
            name: Check run name
            status: Status (queued, in_progress, completed)
            conclusion: Conclusion if completed (success, failure, neutral, cancelled, skipped, timed_out, action_required)
            title: Title of the check run
            summary: Summary markdown text
            text: Detailed markdown text
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{self.repo}/check-runs"
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'name': name,
            'head_sha': commit_sha,
            'status': status
        }
        
        if conclusion:
            payload['conclusion'] = conclusion
        
        if title or summary or text:
            payload['output'] = {}
            if title:
                payload['output']['title'] = title
            if summary:
                payload['output']['summary'] = summary
            if text:
                payload['output']['text'] = text
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting GitHub check run: {e}")
            return False


class GitLabStatusCheck:
    """Post commit status checks to GitLab."""
    
    def __init__(self, token: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize GitLab status check.
        
        Args:
            token: GitLab token (defaults to GITLAB_TOKEN or CI_JOB_TOKEN env var)
            project_id: Project ID (defaults to CI_PROJECT_ID env var)
        """
        self.token = token or os.environ.get('GITLAB_TOKEN') or os.environ.get('CI_JOB_TOKEN', '')
        self.project_id = project_id or os.environ.get('CI_PROJECT_ID', '')
        self.api_base = os.environ.get('CI_API_V4_URL', 'https://gitlab.com/api/v4')
        
        if not self.token:
            raise ValueError("GitLab token is required")
        if not self.project_id:
            raise ValueError("Project ID is required")
    
    def post_status(
        self,
        commit_sha: str,
        state: str,
        name: str = "reviewr",
        description: str = "",
        target_url: Optional[str] = None
    ) -> bool:
        """
        Post a commit status.
        
        Args:
            commit_sha: Git commit SHA
            state: Status state (pending, running, success, failed, canceled)
            name: Status name
            description: Short description
            target_url: URL to link to for more details
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/projects/{self.project_id}/statuses/{commit_sha}"
        
        headers = {
            'PRIVATE-TOKEN': self.token,
            'Content-Type': 'application/json'
        }
        
        # Map CheckStatus to GitLab states
        gitlab_state_map = {
            'pending': 'pending',
            'success': 'success',
            'failure': 'failed',
            'error': 'failed'
        }
        
        payload = {
            'state': gitlab_state_map.get(state, state),
            'name': name,
            'description': description
        }
        
        if target_url:
            payload['target_url'] = target_url
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting GitLab status: {e}")
            return False


def post_status_from_results(
    result: Any,
    platform: str = "github",
    commit_sha: Optional[str] = None,
    fail_on_critical: bool = True,
    high_threshold: int = 5
) -> bool:
    """
    Post status check based on review results.
    
    Args:
        result: ReviewResult object
        platform: Platform (github or gitlab)
        commit_sha: Commit SHA (auto-detected if not provided)
        fail_on_critical: Fail on critical issues
        high_threshold: Fail if high severity issues exceed this
        
    Returns:
        True if successful, False otherwise
    """
    # Auto-detect commit SHA
    if not commit_sha:
        commit_sha = os.environ.get('GITHUB_SHA') or os.environ.get('CI_COMMIT_SHA', '')
    
    if not commit_sha:
        print("Warning: No commit SHA found, skipping status check")
        return False
    
    # Count issues by severity
    by_severity = result.get_findings_by_severity()
    critical_count = len(by_severity['critical'])
    high_count = len(by_severity['high'])
    total_count = len(result.findings)
    
    # Determine status
    if fail_on_critical and critical_count > 0:
        state = CheckStatus.FAILURE
        description = f"❌ {critical_count} critical issue(s) found"
    elif high_threshold > 0 and high_count > high_threshold:
        state = CheckStatus.FAILURE
        description = f"❌ {high_count} high severity issue(s) exceed threshold"
    elif total_count > 0:
        state = CheckStatus.SUCCESS
        description = f"✅ {total_count} issue(s) found, none critical"
    else:
        state = CheckStatus.SUCCESS
        description = "✅ No issues found"
    
    # Post status
    try:
        if platform.lower() == "github":
            checker = GitHubStatusCheck()
            return checker.post_status(
                commit_sha=commit_sha,
                state=state,
                context="reviewr/code-review",
                description=description
            )
        elif platform.lower() == "gitlab":
            checker = GitLabStatusCheck()
            return checker.post_status(
                commit_sha=commit_sha,
                state=state.value,
                name="reviewr/code-review",
                description=description
            )
        else:
            print(f"Unknown platform: {platform}")
            return False
    except Exception as e:
        print(f"Error posting status check: {e}")
        return False


def create_summary_markdown(result: Any) -> str:
    """
    Create a summary markdown for check runs.
    
    Args:
        result: ReviewResult object
        
    Returns:
        Markdown summary string
    """
    by_severity = result.get_findings_by_severity()
    critical_count = len(by_severity['critical'])
    high_count = len(by_severity['high'])
    medium_count = len(by_severity['medium'])
    low_count = len(by_severity['low'])
    total_count = len(result.findings)
    
    summary = f"""## reviewr Code Review Summary

**Files Reviewed:** {result.files_reviewed}
**Total Issues:** {total_count}

### Issues by Severity

| Severity | Count |
|----------|-------|
| 🔴 Critical | {critical_count} |
| 🟠 High | {high_count} |
| 🟡 Medium | {medium_count} |
| 🔵 Low | {low_count} |
"""
    
    return summary

