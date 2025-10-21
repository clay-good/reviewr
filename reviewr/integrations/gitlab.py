"""GitLab integration for reviewr."""

import os
import json
import subprocess
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    import requests
except ImportError:
    requests = None


class GitLabReviewStatus(Enum):
    """GitLab MR review status."""
    APPROVE = "approve"
    UNAPPROVE = "unapprove"


@dataclass
class GitLabComment:
    """Represents a GitLab MR comment."""
    path: str
    line: int
    body: str
    line_type: str = "new"  # "new" or "old"


class GitLabIntegration:
    """Integration with GitLab for posting MR reviews."""
    
    def __init__(self, token: Optional[str] = None, project_id: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize GitLab integration.
        
        Args:
            token: GitLab token (defaults to GITLAB_TOKEN or CI_JOB_TOKEN env var)
            project_id: Project ID or path (auto-detected from git if not provided)
            api_url: GitLab API URL (defaults to https://gitlab.com/api/v4)
        """
        if requests is None:
            raise ImportError("requests library is required for GitLab integration. Install with: pip install requests")
        
        # Try multiple token sources
        self.token = token or os.getenv('GITLAB_TOKEN') or os.getenv('CI_JOB_TOKEN')
        if not self.token:
            raise ValueError("GitLab token not provided. Set GITLAB_TOKEN or CI_JOB_TOKEN environment variable or pass token parameter.")
        
        self.api_url = api_url or os.getenv('CI_API_V4_URL', 'https://gitlab.com/api/v4')
        self.project_id = project_id or self._detect_project_id()
        if not self.project_id:
            raise ValueError("Could not detect GitLab project. Provide project_id parameter.")
        
        self.headers = {
            'PRIVATE-TOKEN': self.token,
            'Content-Type': 'application/json'
        }
    
    def _detect_project_id(self) -> Optional[str]:
        """Detect GitLab project ID from environment or git remote."""
        # Try CI environment variable first
        project_id = os.getenv('CI_PROJECT_ID')
        if project_id:
            return project_id
        
        # Try to parse from git remote
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse GitLab URL
            # Supports: https://gitlab.com/owner/repo.git or git@gitlab.com:owner/repo.git
            if 'gitlab' in remote_url:
                if remote_url.startswith('https://'):
                    # https://gitlab.com/owner/repo.git
                    parts = remote_url.split('/')
                    if len(parts) >= 2:
                        # Extract owner/repo and URL encode it
                        path = '/'.join(parts[-2:]).replace('.git', '')
                        return path.replace('/', '%2F')
                elif remote_url.startswith('git@'):
                    # git@gitlab.com:owner/repo.git
                    parts = remote_url.split(':')
                    if len(parts) >= 2:
                        path = parts[1].replace('.git', '')
                        return path.replace('/', '%2F')
            
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_mr_number(self) -> Optional[int]:
        """Get MR number from environment (GitLab CI)."""
        # Try GitLab CI environment variables
        mr_iid = os.getenv('CI_MERGE_REQUEST_IID')
        if mr_iid:
            return int(mr_iid)
        
        return None
    
    def get_mr_files(self, mr_iid: int) -> List[Dict[str, Any]]:
        """
        Get list of files changed in an MR.
        
        Args:
            mr_iid: Merge request IID
            
        Returns:
            List of file information dicts
        """
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}/changes"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('changes', [])
    
    def create_mr_note(
        self,
        mr_iid: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Create a note (comment) on an MR.
        
        Args:
            mr_iid: Merge request IID
            body: Comment body
            
        Returns:
            API response
        """
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}/notes"
        
        payload = {
            "body": body
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_discussion(
        self,
        mr_iid: int,
        comments: List[GitLabComment]
    ) -> List[Dict[str, Any]]:
        """
        Create discussions (inline comments) on an MR.
        
        Args:
            mr_iid: Merge request IID
            comments: List of inline comments
            
        Returns:
            List of API responses
        """
        responses = []
        
        # Get the latest commit SHA for the MR
        commit_sha = self.get_commit_sha(mr_iid)
        
        for comment in comments:
            url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}/discussions"
            
            payload = {
                "body": comment.body,
                "position": {
                    "base_sha": commit_sha,
                    "start_sha": commit_sha,
                    "head_sha": commit_sha,
                    "position_type": "text",
                    "new_path": comment.path,
                    "new_line": comment.line,
                    "line_range": {
                        "start": {
                            "line_code": f"{comment.path}_{comment.line}",
                            "type": comment.line_type
                        },
                        "end": {
                            "line_code": f"{comment.path}_{comment.line}",
                            "type": comment.line_type
                        }
                    }
                }
            }
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                responses.append(response.json())
            except requests.exceptions.HTTPError as e:
                # Log error but continue with other comments
                print(f"Warning: Failed to post comment on {comment.path}:{comment.line}: {e}")
                continue
        
        return responses
    
    def approve_mr(self, mr_iid: int) -> Dict[str, Any]:
        """
        Approve an MR.
        
        Args:
            mr_iid: Merge request IID
            
        Returns:
            API response
        """
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}/approve"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def unapprove_mr(self, mr_iid: int) -> Dict[str, Any]:
        """
        Unapprove an MR.
        
        Args:
            mr_iid: Merge request IID
            
        Returns:
            API response
        """
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}/unapprove"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_commit_sha(self, mr_iid: int) -> str:
        """
        Get the latest commit SHA for an MR.
        
        Args:
            mr_iid: Merge request IID
            
        Returns:
            Commit SHA
        """
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_iid}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        mr_data = response.json()
        return mr_data['sha']
    
    def format_findings_as_comments(
        self,
        findings: List,
        changed_files: Optional[List[str]] = None
    ) -> List[GitLabComment]:
        """
        Convert review findings to GitLab comments.
        
        Args:
            findings: List of ReviewFinding objects
            changed_files: Optional list of changed file paths to filter by
            
        Returns:
            List of GitLab comments
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
            
            comment = GitLabComment(
                path=finding.file_path,
                line=finding.line_start,
                body="\n".join(body_parts)
            )
            comments.append(comment)

        return comments

    def format_summary(self, result) -> str:
        """
        Format a review summary for MR comment.

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
            lines.append("**Findings by severity**: " + ", ".join(severity_counts))
        else:
            lines.append("**No issues found!** ✨")

        # Findings by type
        by_type = result.get_findings_by_type()
        if by_type:
            lines.append("\n**Findings by type**:")
            for type_name, type_findings in by_type.items():
                lines.append(f"- {type_name}: {len(type_findings)}")

        lines.append("")

        # Critical/High issues warning
        if result.has_critical_issues():
            lines.append("⚠️ **This MR has critical or high severity issues that should be addressed.**")
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

