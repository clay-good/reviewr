"""
Bitbucket integration for automated pull request reviews.

Supports:
- Bitbucket Cloud (bitbucket.org)
- Bitbucket Server/Data Center (self-hosted)
- Inline PR comments
- Summary comments
- Auto-approval
- Build status reporting
"""

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


class BitbucketReviewStatus(Enum):
    """Bitbucket review status."""
    APPROVED = "APPROVED"
    NEEDS_WORK = "NEEDS_WORK"
    UNAPPROVED = "UNAPPROVED"


@dataclass
class BitbucketComment:
    """A comment on a Bitbucket PR."""
    path: str
    line: int
    body: str
    severity: str = "NORMAL"  # BLOCKER, CRITICAL, MAJOR, NORMAL, MINOR


class BitbucketIntegration:
    """Integration with Bitbucket for PR reviews."""
    
    def __init__(
        self,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        workspace: Optional[str] = None,
        repo_slug: Optional[str] = None,
        is_server: bool = False,
        server_url: Optional[str] = None
    ):
        """
        Initialize Bitbucket integration.
        
        Args:
            username: Bitbucket username (defaults to BITBUCKET_USERNAME env var)
            app_password: Bitbucket app password (defaults to BITBUCKET_APP_PASSWORD env var)
            workspace: Workspace/project key (auto-detected from git if not provided)
            repo_slug: Repository slug (auto-detected from git if not provided)
            is_server: True for Bitbucket Server/Data Center, False for Cloud
            server_url: Bitbucket Server URL (required if is_server=True)
        """
        if requests is None:
            raise ImportError(
                "requests library is required for Bitbucket integration. "
                "Install with: pip install requests"
            )
        
        self.username = username or os.getenv('BITBUCKET_USERNAME')
        self.app_password = app_password or os.getenv('BITBUCKET_APP_PASSWORD')
        
        if not self.username or not self.app_password:
            raise ValueError(
                "Bitbucket credentials not provided. Set BITBUCKET_USERNAME and "
                "BITBUCKET_APP_PASSWORD environment variables or pass parameters."
            )
        
        self.is_server = is_server
        self.server_url = server_url
        
        if self.is_server and not self.server_url:
            self.server_url = os.getenv('BITBUCKET_SERVER_URL')
            if not self.server_url:
                raise ValueError(
                    "Bitbucket Server URL not provided. Set BITBUCKET_SERVER_URL "
                    "environment variable or pass server_url parameter."
                )
        
        # Auto-detect workspace and repo
        detected = self._detect_repo()
        self.workspace = workspace or detected.get('workspace')
        self.repo_slug = repo_slug or detected.get('repo_slug')
        
        if not self.workspace or not self.repo_slug:
            raise ValueError(
                "Could not detect Bitbucket repository. Provide workspace and "
                "repo_slug parameters."
            )
        
        # Set API base URL
        if self.is_server:
            self.api_base = f"{self.server_url}/rest/api/1.0"
        else:
            self.api_base = "https://api.bitbucket.org/2.0"
        
        self.auth = (self.username, self.app_password)
    
    def _detect_repo(self) -> Dict[str, Optional[str]]:
        """Detect Bitbucket repository from git remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse Bitbucket URL
            # Cloud: https://bitbucket.org/workspace/repo.git or git@bitbucket.org:workspace/repo.git
            # Server: https://bitbucket.company.com/scm/project/repo.git
            
            if 'bitbucket.org' in remote_url:
                # Bitbucket Cloud
                if remote_url.startswith('https://'):
                    parts = remote_url.replace('https://bitbucket.org/', '').replace('.git', '').split('/')
                elif remote_url.startswith('git@'):
                    parts = remote_url.replace('git@bitbucket.org:', '').replace('.git', '').split('/')
                else:
                    return {'workspace': None, 'repo_slug': None}
                
                if len(parts) >= 2:
                    return {'workspace': parts[0], 'repo_slug': parts[1]}
            
            elif '/scm/' in remote_url:
                # Bitbucket Server
                if remote_url.startswith('https://'):
                    # Extract project and repo from /scm/PROJECT/repo.git
                    parts = remote_url.split('/scm/')
                    if len(parts) == 2:
                        project_repo = parts[1].replace('.git', '').split('/')
                        if len(project_repo) >= 2:
                            return {'workspace': project_repo[0], 'repo_slug': project_repo[1]}
            
            return {'workspace': None, 'repo_slug': None}
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {'workspace': None, 'repo_slug': None}
    
    def get_pr_number(self) -> Optional[int]:
        """Get PR number from environment (Bitbucket Pipelines)."""
        # Bitbucket Pipelines environment variables
        pr_id = os.getenv('BITBUCKET_PR_ID')
        if pr_id:
            return int(pr_id)
        
        return None
    
    def get_pr_files(self, pr_number: int) -> List[str]:
        """Get list of files changed in a PR."""
        if self.is_server:
            url = f"{self.api_base}/projects/{self.workspace}/repos/{self.repo_slug}/pull-requests/{pr_number}/changes"
        else:
            url = f"{self.api_base}/repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_number}/diffstat"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            
            if self.is_server:
                # Server format
                return [change['path']['toString'] for change in data.get('values', [])]
            else:
                # Cloud format
                return [item['new']['path'] if item.get('new') else item['old']['path'] 
                       for item in data.get('values', [])]
        except requests.RequestException as e:
            print(f"Error fetching PR files: {e}")
            return []
    
    def get_commit_sha(self) -> Optional[str]:
        """Get current commit SHA."""
        commit = os.getenv('BITBUCKET_COMMIT')
        if commit:
            return commit
        
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def post_review(
        self,
        pr_number: int,
        findings: List[Any],
        status: BitbucketReviewStatus = BitbucketReviewStatus.UNAPPROVED,
        auto_approve: bool = False
    ) -> bool:
        """
        Post a review to a Bitbucket PR.
        
        Args:
            pr_number: Pull request number
            findings: List of review findings
            status: Review status
            auto_approve: Auto-approve if no critical issues
            
        Returns:
            True if successful
        """
        # Post inline comments
        comments = self.format_findings_as_comments(findings)
        for comment in comments:
            self.post_comment(pr_number, comment)
        
        # Post summary comment
        summary = self.format_summary(findings)
        self.post_summary_comment(pr_number, summary)
        
        # Approve if requested and no critical issues
        if auto_approve and not self._has_critical_issues(findings):
            self.approve_pr(pr_number)
        
        return True
    
    def post_comment(self, pr_number: int, comment: BitbucketComment) -> bool:
        """Post an inline comment on a PR."""
        if self.is_server:
            url = f"{self.api_base}/projects/{self.workspace}/repos/{self.repo_slug}/pull-requests/{pr_number}/comments"
            payload = {
                "text": comment.body,
                "anchor": {
                    "path": comment.path,
                    "line": comment.line,
                    "lineType": "ADDED"
                },
                "severity": comment.severity
            }
        else:
            url = f"{self.api_base}/repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_number}/comments"
            payload = {
                "content": {
                    "raw": comment.body
                },
                "inline": {
                    "path": comment.path,
                    "to": comment.line
                }
            }
        
        try:
            response = requests.post(url, json=payload, auth=self.auth)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error posting comment: {e}")
            return False
    
    def post_summary_comment(self, pr_number: int, summary: str) -> bool:
        """Post a summary comment on a PR."""
        if self.is_server:
            url = f"{self.api_base}/projects/{self.workspace}/repos/{self.repo_slug}/pull-requests/{pr_number}/comments"
            payload = {"text": summary}
        else:
            url = f"{self.api_base}/repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_number}/comments"
            payload = {"content": {"raw": summary}}
        
        try:
            response = requests.post(url, json=payload, auth=self.auth)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error posting summary: {e}")
            return False

    def approve_pr(self, pr_number: int) -> bool:
        """Approve a pull request."""
        if self.is_server:
            url = f"{self.api_base}/projects/{self.workspace}/repos/{self.repo_slug}/pull-requests/{pr_number}/approve"
        else:
            url = f"{self.api_base}/repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_number}/approve"

        try:
            response = requests.post(url, auth=self.auth)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error approving PR: {e}")
            return False

    def format_findings_as_comments(
        self,
        findings: List[Any],
        file_filter: Optional[List[str]] = None
    ) -> List[BitbucketComment]:
        """Format review findings as Bitbucket comments."""
        comments = []

        for finding in findings:
            # Skip if file filter is provided and file not in filter
            if file_filter and finding.file not in file_filter:
                continue

            # Map severity to Bitbucket severity
            severity_map = {
                'critical': 'BLOCKER',
                'high': 'CRITICAL',
                'medium': 'MAJOR',
                'low': 'NORMAL',
                'info': 'MINOR'
            }
            severity = severity_map.get(finding.severity, 'NORMAL')

            # Format comment body
            emoji = self._get_severity_emoji(finding.severity)
            body = f"{emoji} **{finding.severity.upper()}**: {finding.message}\n\n"

            if hasattr(finding, 'suggestion') and finding.suggestion:
                body += f"**Suggestion**: {finding.suggestion}\n\n"

            if hasattr(finding, 'category') and finding.category:
                body += f"*Category: {finding.category}*\n"

            body += f"*Type: {finding.type.value}*"

            comments.append(BitbucketComment(
                path=finding.file,
                line=finding.line,
                body=body,
                severity=severity
            ))

        return comments

    def format_summary(self, findings: List[Any]) -> str:
        """Format review findings as a summary comment."""
        if not findings:
            return "✅ **Code Review Complete** - No issues found!"

        # Count by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }

        for finding in findings:
            if finding.severity in severity_counts:
                severity_counts[finding.severity] += 1

        # Build summary
        summary = "## 🔍 Code Review Summary\n\n"
        summary += f"**Total findings**: {len(findings)}\n\n"

        if severity_counts['critical'] > 0:
            summary += f"🔴 **Critical**: {severity_counts['critical']}\n"
        if severity_counts['high'] > 0:
            summary += f"🟠 **High**: {severity_counts['high']}\n"
        if severity_counts['medium'] > 0:
            summary += f"🟡 **Medium**: {severity_counts['medium']}\n"
        if severity_counts['low'] > 0:
            summary += f"🔵 **Low**: {severity_counts['low']}\n"
        if severity_counts['info'] > 0:
            summary += f"ℹ️ **Info**: {severity_counts['info']}\n"

        summary += "\n---\n"
        summary += "*Automated review by [reviewr](https://github.com/yourusername/reviewr)*"

        return summary

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return emoji_map.get(severity, 'ℹ️')

    def _has_critical_issues(self, findings: List[Any]) -> bool:
        """Check if there are any critical or high severity issues."""
        return any(f.severity in ('critical', 'high') for f in findings)

    def create_build_status(
        self,
        commit_sha: str,
        state: str,
        key: str = "reviewr",
        name: str = "Code Review",
        url: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Create a build status for a commit.

        Args:
            commit_sha: Commit SHA
            state: Build state (SUCCESSFUL, FAILED, INPROGRESS, STOPPED)
            key: Unique key for this build
            name: Display name
            url: URL to build details
            description: Description of the build

        Returns:
            True if successful
        """
        if self.is_server:
            url_endpoint = f"{self.api_base}/projects/{self.workspace}/repos/{self.repo_slug}/commits/{commit_sha}/builds"
            payload = {
                "state": state,
                "key": key,
                "name": name,
                "url": url or "",
                "description": description or ""
            }
        else:
            url_endpoint = f"{self.api_base}/repositories/{self.workspace}/{self.repo_slug}/commit/{commit_sha}/statuses/build"
            payload = {
                "state": state,
                "key": key,
                "name": name,
                "url": url or "",
                "description": description or ""
            }

        try:
            response = requests.post(url_endpoint, json=payload, auth=self.auth)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error creating build status: {e}")
            return False

