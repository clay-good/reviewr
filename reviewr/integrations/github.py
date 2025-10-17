import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess

try:
    import requests
except ImportError:
    requests = None


class GitHubReviewStatus(Enum):
    """GitHub review status."""
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class GitHubComment:
    """A comment on a GitHub PR."""
    path: str
    line: int
    body: str
    side: str = "RIGHT"  # RIGHT for new code, LEFT for old code


class GitHubIntegration:
    """Integration with GitHub for PR reviews."""
    
    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub integration.
        
        Args:
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            repo: Repository in format "owner/repo" (auto-detected from git if not provided)
        """
        if requests is None:
            raise ImportError("requests library is required for GitHub integration. Install with: pip install requests")
        
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not provided. Set GITHUB_TOKEN environment variable or pass token parameter.")
        
        self.repo = repo or self._detect_repo()
        if not self.repo:
            raise ValueError("Could not detect GitHub repository. Provide repo parameter in format 'owner/repo'.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _detect_repo(self) -> Optional[str]:
        """Detect GitHub repository from git remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse GitHub URL
            # Supports: https://github.com/owner/repo.git or git@github.com:owner/repo.git
            if 'github.com' in remote_url:
                if remote_url.startswith('https://'):
                    # https://github.com/owner/repo.git
                    parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
                elif remote_url.startswith('git@'):
                    # git@github.com:owner/repo.git
                    parts = remote_url.replace('git@github.com:', '').replace('.git', '').split('/')
                else:
                    return None
                
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
            
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_pr_number(self) -> Optional[int]:
        """Get PR number from environment (GitHub Actions)."""
        # Try GitHub Actions environment variables
        pr_number = os.getenv('GITHUB_PR_NUMBER')
        if pr_number:
            return int(pr_number)
        
        # Try to extract from GITHUB_REF (e.g., refs/pull/123/merge)
        github_ref = os.getenv('GITHUB_REF', '')
        if github_ref.startswith('refs/pull/'):
            parts = github_ref.split('/')
            if len(parts) >= 3:
                try:
                    return int(parts[2])
                except ValueError:
                    pass
        
        # Try GITHUB_EVENT_PATH
        event_path = os.getenv('GITHUB_EVENT_PATH')
        if event_path and os.path.exists(event_path):
            try:
                with open(event_path, 'r') as f:
                    event_data = json.load(f)
                    if 'pull_request' in event_data:
                        return event_data['pull_request']['number']
                    elif 'number' in event_data:
                        return event_data['number']
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None
    
    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get list of files changed in a PR.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            List of file information dicts
        """
        url = f"{self.api_base}/repos/{self.repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_review_comment(
        self,
        pr_number: int,
        commit_id: str,
        comments: List[GitHubComment],
        body: Optional[str] = None,
        event: GitHubReviewStatus = GitHubReviewStatus.COMMENT
    ) -> Dict[str, Any]:
        """
        Create a review with comments on a PR.
        
        Args:
            pr_number: Pull request number
            commit_id: Commit SHA to review
            comments: List of inline comments
            body: Overall review body
            event: Review event type (APPROVE, REQUEST_CHANGES, COMMENT)
            
        Returns:
            API response
        """
        url = f"{self.api_base}/repos/{self.repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "commit_id": commit_id,
            "event": event.value,
            "comments": [
                {
                    "path": comment.path,
                    "line": comment.line,
                    "body": comment.body,
                    "side": comment.side
                }
                for comment in comments
            ]
        }
        
        if body:
            payload["body"] = body
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_issue_comment(self, pr_number: int, body: str) -> Dict[str, Any]:
        """
        Create a general comment on a PR (not inline).
        
        Args:
            pr_number: Pull request number
            body: Comment body
            
        Returns:
            API response
        """
        url = f"{self.api_base}/repos/{self.repo}/issues/{pr_number}/comments"
        
        payload = {"body": body}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_commit_sha(self, pr_number: int) -> str:
        """
        Get the latest commit SHA for a PR.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Commit SHA
        """
        url = f"{self.api_base}/repos/{self.repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        pr_data = response.json()
        return pr_data['head']['sha']
    
    def format_findings_as_comments(
        self,
        findings: List,
        changed_files: Optional[List[str]] = None
    ) -> List[GitHubComment]:
        """
        Convert review findings to GitHub comments.
        
        Args:
            findings: List of ReviewFinding objects
            changed_files: Optional list of changed file paths to filter by
            
        Returns:
            List of GitHub comments
        """
        comments = []
        
        for finding in findings:
            # Filter to only changed files if provided
            if changed_files and finding.file_path not in changed_files:
                continue
            
            # Format comment body
            severity_emoji = self._get_severity_emoji(finding.severity)
            body_parts = [
                f"{severity_emoji} **{finding.severity.upper()}**: {finding.message}"
            ]
            
            if finding.suggestion:
                body_parts.append(f"\n**Suggestion**: {finding.suggestion}")
            
            if hasattr(finding, 'confidence') and finding.confidence < 1.0:
                body_parts.append(f"\n*Confidence: {finding.confidence:.0%}*")
            
            comment = GitHubComment(
                path=finding.file_path,
                line=finding.line_start,
                body="\n".join(body_parts)
            )
            comments.append(comment)
        
        return comments
    
    def format_summary(self, result) -> str:
        """
        Format a review summary for PR comment.
        
        Args:
            result: ReviewResult object
            
        Returns:
            Formatted markdown summary
        """
        lines = ["## 🤖 reviewr Code Review Summary\n"]
        
        # Statistics
        lines.append(f"**Files reviewed**: {result.files_reviewed}")
        lines.append(f"**Total findings**: {len(result.findings)}\n")
        
        # Findings by severity
        by_severity = result.get_findings_by_severity()
        
        severity_counts = []
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(by_severity[severity])
            if count > 0:
                emoji = self._get_severity_emoji(severity)
                severity_counts.append(f"{emoji} {count} {severity}")
        
        if severity_counts:
            lines.append("**Findings by severity**:")
            lines.append(", ".join(severity_counts))
            lines.append("")
        
        # Local analysis stats
        local_stats = result.provider_stats.get('local_analysis_stats')
        if local_stats and local_stats.get('findings', 0) > 0:
            lines.append(f"**Local analysis**: {local_stats['findings']} issues found (no API calls)")
        
        # Cache stats
        cache_stats = result.provider_stats.get('cache_stats')
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate', 0)
            if hit_rate > 0:
                lines.append(f"**Cache hit rate**: {hit_rate:.1%}")
        
        lines.append("")
        
        # Critical/High issues warning
        if result.has_critical_issues():
            lines.append("⚠️ **This PR has critical or high severity issues that should be addressed.**")
        else:
            lines.append("✅ **No critical or high severity issues found.**")
        
        lines.append("\n---")
        lines.append("*Powered by [reviewr](https://github.com/clay-good/reviewr)*")
        
        return "\n".join(lines)
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return emoji_map.get(severity.lower(), '⚪')

