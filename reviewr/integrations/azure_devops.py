"""
Azure DevOps integration for automated pull request reviews.

Supports:
- Azure DevOps Services (dev.azure.com)
- Azure DevOps Server (on-premises)
- Pull request comments (threads)
- Inline comments
- Summary comments
- Auto-approval/voting
- Build status reporting
- Work item linking
"""

import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess
import base64

try:
    import requests
except ImportError:
    requests = None


class AzureDevOpsVote(Enum):
    """Azure DevOps PR vote values."""
    APPROVED = 10
    APPROVED_WITH_SUGGESTIONS = 5
    NO_VOTE = 0
    WAITING_FOR_AUTHOR = -5
    REJECTED = -10


@dataclass
class AzureDevOpsComment:
    """A comment on an Azure DevOps PR."""
    path: str
    line: int
    body: str
    comment_type: str = "text"  # text, system, unknown


class AzureDevOpsIntegration:
    """Integration with Azure DevOps for PR reviews."""
    
    def __init__(
        self,
        pat: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        repository: Optional[str] = None,
        server_url: Optional[str] = None
    ):
        """
        Initialize Azure DevOps integration.
        
        Args:
            pat: Personal Access Token (defaults to AZURE_DEVOPS_PAT env var)
            organization: Organization name (auto-detected from git if not provided)
            project: Project name (auto-detected from git if not provided)
            repository: Repository name (auto-detected from git if not provided)
            server_url: Azure DevOps Server URL (for on-premises, defaults to dev.azure.com)
        """
        if requests is None:
            raise ImportError(
                "requests library is required for Azure DevOps integration. "
                "Install with: pip install requests"
            )
        
        self.pat = pat or os.getenv('AZURE_DEVOPS_PAT')
        if not self.pat:
            raise ValueError(
                "Azure DevOps PAT not provided. Set AZURE_DEVOPS_PAT environment "
                "variable or pass pat parameter."
            )
        
        # Auto-detect from git remote or environment
        detected = self._detect_repo()
        self.organization = organization or detected.get('organization') or os.getenv('AZURE_DEVOPS_ORG')
        self.project = project or detected.get('project') or os.getenv('AZURE_DEVOPS_PROJECT')
        self.repository = repository or detected.get('repository') or os.getenv('AZURE_DEVOPS_REPO')
        
        if not self.organization or not self.project or not self.repository:
            raise ValueError(
                "Could not detect Azure DevOps repository. Provide organization, "
                "project, and repository parameters or set environment variables."
            )
        
        # Set up API base URL
        self.server_url = server_url or os.getenv('AZURE_DEVOPS_SERVER_URL', 'https://dev.azure.com')
        if self.server_url == 'https://dev.azure.com':
            self.api_base = f"{self.server_url}/{self.organization}"
        else:
            # On-premises server
            self.api_base = f"{self.server_url}/{self.organization}"
        
        # Set up authentication headers
        auth_string = f":{self.pat}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _detect_repo(self) -> Dict[str, Optional[str]]:
        """Detect Azure DevOps repository from git remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse Azure DevOps URL
            # Supports:
            # - https://dev.azure.com/{org}/{project}/_git/{repo}
            # - https://{org}@dev.azure.com/{org}/{project}/_git/{repo}
            # - https://{server}/{org}/{project}/_git/{repo}
            
            if 'dev.azure.com' in remote_url or '_git' in remote_url:
                # Remove credentials if present
                if '@' in remote_url:
                    remote_url = 'https://' + remote_url.split('@', 1)[1]
                
                # Extract components
                parts = remote_url.replace('https://', '').split('/')
                
                if 'dev.azure.com' in remote_url:
                    # https://dev.azure.com/{org}/{project}/_git/{repo}
                    if len(parts) >= 5 and parts[2] == '_git':
                        return {
                            'organization': parts[1],
                            'project': parts[2],
                            'repository': parts[4]
                        }
                    elif len(parts) >= 4 and '_git' in parts:
                        git_index = parts.index('_git')
                        return {
                            'organization': parts[1],
                            'project': parts[git_index - 1],
                            'repository': parts[git_index + 1] if git_index + 1 < len(parts) else None
                        }
                else:
                    # On-premises server
                    if '_git' in parts:
                        git_index = parts.index('_git')
                        return {
                            'organization': parts[1] if len(parts) > 1 else None,
                            'project': parts[git_index - 1] if git_index > 0 else None,
                            'repository': parts[git_index + 1] if git_index + 1 < len(parts) else None
                        }
            
            return {'organization': None, 'project': None, 'repository': None}
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {'organization': None, 'project': None, 'repository': None}
    
    def get_pr_id(self) -> Optional[int]:
        """Get PR ID from environment (Azure Pipelines)."""
        # Try Azure Pipelines environment variables
        pr_id = os.getenv('SYSTEM_PULLREQUEST_PULLREQUESTID')
        if pr_id:
            return int(pr_id)
        
        # Try BUILD_SOURCEBRANCH (e.g., refs/pull/123/merge)
        source_branch = os.getenv('BUILD_SOURCEBRANCH', '')
        if source_branch.startswith('refs/pull/'):
            parts = source_branch.split('/')
            if len(parts) >= 3:
                try:
                    return int(parts[2])
                except ValueError:
                    pass
        
        return None
    
    def post_comment(self, pr_id: int, body: str) -> Dict[str, Any]:
        """
        Post a summary comment on a pull request.
        
        Args:
            pr_id: Pull request ID
            body: Comment body (markdown supported)
        
        Returns:
            API response
        """
        url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"pullRequests/{pr_id}/threads?api-version=7.0"
        )
        
        payload = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": body,
                    "commentType": 1  # 1 = text
                }
            ],
            "status": 1  # 1 = active
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def post_inline_comments(
        self,
        pr_id: int,
        comments: List[AzureDevOpsComment]
    ) -> List[Dict[str, Any]]:
        """
        Post inline comments on specific lines of a pull request.
        
        Args:
            pr_id: Pull request ID
            comments: List of comments to post
        
        Returns:
            List of API responses
        """
        responses = []
        
        for comment in comments:
            url = (
                f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
                f"pullRequests/{pr_id}/threads?api-version=7.0"
            )
            
            payload = {
                "comments": [
                    {
                        "parentCommentId": 0,
                        "content": comment.body,
                        "commentType": 1  # 1 = text
                    }
                ],
                "status": 1,  # 1 = active
                "threadContext": {
                    "filePath": f"/{comment.path}",
                    "rightFileStart": {
                        "line": comment.line,
                        "offset": 1
                    },
                    "rightFileEnd": {
                        "line": comment.line,
                        "offset": 1
                    }
                }
            }
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                responses.append(response.json())
            except requests.exceptions.RequestException as e:
                print(f"Warning: Failed to post comment on {comment.path}:{comment.line}: {e}")
                continue
        
        return responses
    
    def set_vote(self, pr_id: int, vote: AzureDevOpsVote) -> Dict[str, Any]:
        """
        Set vote on a pull request.
        
        Args:
            pr_id: Pull request ID
            vote: Vote value (APPROVED, REJECTED, etc.)
        
        Returns:
            API response
        """
        # Get current user ID
        user_url = f"{self.api_base}/_apis/connectionData?api-version=7.0"
        user_response = requests.get(user_url, headers=self.headers)
        user_response.raise_for_status()
        user_id = user_response.json()['authenticatedUser']['id']
        
        # Set vote
        url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"pullRequests/{pr_id}/reviewers/{user_id}?api-version=7.0"
        )
        
        payload = {
            "vote": vote.value
        }
        
        response = requests.put(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def update_build_status(
        self,
        commit_id: str,
        state: str,
        description: str,
        context: str = "reviewr"
    ) -> Dict[str, Any]:
        """
        Update build status for a commit.

        Args:
            commit_id: Commit SHA
            state: Status state (succeeded, failed, pending, error)
            description: Status description
            context: Status context/name

        Returns:
            API response
        """
        url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"commits/{commit_id}/statuses?api-version=7.0"
        )

        # Map state to Azure DevOps status
        state_map = {
            'succeeded': 'succeeded',
            'failed': 'failed',
            'pending': 'pending',
            'error': 'error',
            'success': 'succeeded'
        }

        payload = {
            "state": state_map.get(state, state),
            "description": description,
            "context": {
                "name": context,
                "genre": "continuous-integration"
            }
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def link_work_item(self, pr_id: int, work_item_id: int) -> Dict[str, Any]:
        """
        Link a work item to a pull request.

        Args:
            pr_id: Pull request ID
            work_item_id: Work item ID

        Returns:
            API response
        """
        url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"pullRequests/{pr_id}/workitems/{work_item_id}?api-version=7.0"
        )

        response = requests.put(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_pr_files(self, pr_id: int) -> List[str]:
        """
        Get list of files changed in a pull request.

        Args:
            pr_id: Pull request ID

        Returns:
            List of file paths
        """
        # Get PR details
        pr_url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"pullRequests/{pr_id}?api-version=7.0"
        )

        pr_response = requests.get(pr_url, headers=self.headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        source_commit = pr_data['lastMergeSourceCommit']['commitId']
        target_commit = pr_data['lastMergeTargetCommit']['commitId']

        # Get diff between commits
        diff_url = (
            f"{self.api_base}/{self.project}/_apis/git/repositories/{self.repository}/"
            f"diffs/commits?baseVersion={target_commit}&targetVersion={source_commit}&api-version=7.0"
        )

        diff_response = requests.get(diff_url, headers=self.headers)
        diff_response.raise_for_status()
        diff_data = diff_response.json()

        files = []
        for change in diff_data.get('changes', []):
            if 'item' in change and 'path' in change['item']:
                files.append(change['item']['path'].lstrip('/'))

        return files

    def format_review_comment(self, findings: List[Dict[str, Any]]) -> str:
        """
        Format review findings as a markdown comment.

        Args:
            findings: List of review findings

        Returns:
            Formatted markdown string
        """
        if not findings:
            return "## ✅ Code Review Complete\n\nNo issues found! Great work! 🎉"

        # Count by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }

        for finding in findings:
            severity = finding.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Build comment
        lines = ["## 📋 Code Review Summary\n"]

        # Overall status
        if severity_counts['critical'] > 0:
            lines.append("**Status**: 🔴 Critical issues found\n")
        elif severity_counts['high'] > 0:
            lines.append("**Status**: 🟠 High priority issues found\n")
        elif severity_counts['medium'] > 0:
            lines.append("**Status**: 🟡 Medium priority issues found\n")
        else:
            lines.append("**Status**: 🟢 Only minor issues found\n")

        # Severity breakdown
        lines.append("### Findings by Severity\n")
        if severity_counts['critical'] > 0:
            lines.append(f"- 🔴 **Critical**: {severity_counts['critical']}")
        if severity_counts['high'] > 0:
            lines.append(f"- 🟠 **High**: {severity_counts['high']}")
        if severity_counts['medium'] > 0:
            lines.append(f"- 🟡 **Medium**: {severity_counts['medium']}")
        if severity_counts['low'] > 0:
            lines.append(f"- 🔵 **Low**: {severity_counts['low']}")
        if severity_counts['info'] > 0:
            lines.append(f"- ℹ️ **Info**: {severity_counts['info']}")

        lines.append("\n### Details\n")
        lines.append("See inline comments for specific issues and recommendations.\n")

        lines.append("\n---")
        lines.append("*Generated by [reviewr](https://github.com/yourusername/reviewr) - AI-powered code review*")

        return "\n".join(lines)


def review_pull_request(
    pr_id: int,
    findings: List[Dict[str, Any]],
    auto_approve: bool = False,
    post_inline: bool = True,
    pat: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    repository: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review a pull request with findings.

    Args:
        pr_id: Pull request ID
        findings: List of review findings
        auto_approve: Automatically approve if no critical/high issues
        post_inline: Post inline comments for each finding
        pat: Personal Access Token
        organization: Organization name
        project: Project name
        repository: Repository name

    Returns:
        Summary of actions taken
    """
    integration = AzureDevOpsIntegration(
        pat=pat,
        organization=organization,
        project=project,
        repository=repository
    )

    # Post summary comment
    summary = integration.format_review_comment(findings)
    integration.post_comment(pr_id, summary)

    # Post inline comments
    inline_count = 0
    if post_inline and findings:
        comments = []
        for finding in findings:
            if 'file' in finding and 'line' in finding:
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵',
                    'info': 'ℹ️'
                }.get(finding.get('severity', 'info').lower(), 'ℹ️')

                body = f"{severity_emoji} **{finding.get('title', 'Issue')}**\n\n"
                body += finding.get('description', '')

                if 'recommendation' in finding:
                    body += f"\n\n**Recommendation**: {finding['recommendation']}"

                comments.append(AzureDevOpsComment(
                    path=finding['file'],
                    line=finding['line'],
                    body=body
                ))

        if comments:
            integration.post_inline_comments(pr_id, comments)
            inline_count = len(comments)

    # Auto-approve if requested and no critical/high issues
    vote_set = False
    if auto_approve:
        has_critical = any(f.get('severity', '').lower() in ['critical', 'high'] for f in findings)
        if not has_critical:
            integration.set_vote(pr_id, AzureDevOpsVote.APPROVED)
            vote_set = True

    return {
        'pr_id': pr_id,
        'summary_posted': True,
        'inline_comments': inline_count,
        'vote_set': vote_set,
        'total_findings': len(findings)
    }

