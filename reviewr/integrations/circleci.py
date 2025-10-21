"""
CircleCI integration for reviewr.

This module provides integration with CircleCI for automated code reviews
in CI/CD pipelines.
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CircleCIStatus(Enum):
    """CircleCI job status values."""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    NOT_RUN = "not_run"
    CANCELED = "canceled"


@dataclass
class CircleCIConfig:
    """CircleCI configuration."""
    api_token: Optional[str] = None
    project_slug: Optional[str] = None  # Format: vcs-slug/org-name/repo-name
    workflow_id: Optional[str] = None
    job_number: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'CircleCIConfig':
        """Create config from environment variables."""
        # CircleCI sets these environment variables automatically
        # https://circleci.com/docs/variables/#built-in-environment-variables
        
        # Build project slug from environment variables
        vcs_type = os.getenv('CIRCLE_PROJECT_REPONAME')  # git
        org_name = os.getenv('CIRCLE_PROJECT_USERNAME')
        repo_name = os.getenv('CIRCLE_PROJECT_REPONAME')
        
        project_slug = None
        if vcs_type and org_name and repo_name:
            # CircleCI uses format: gh/org/repo or bb/org/repo
            vcs_slug = 'gh' if 'github' in os.getenv('CIRCLE_REPOSITORY_URL', '').lower() else 'bb'
            project_slug = f"{vcs_slug}/{org_name}/{repo_name}"
        
        return cls(
            api_token=os.getenv('CIRCLE_TOKEN'),
            project_slug=project_slug,
            workflow_id=os.getenv('CIRCLE_WORKFLOW_ID'),
            job_number=os.getenv('CIRCLE_BUILD_NUM')
        )


class CircleCIIntegration:
    """Integration with CircleCI for CI/CD automation."""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        project_slug: Optional[str] = None,
        workflow_id: Optional[str] = None,
        job_number: Optional[str] = None
    ):
        """
        Initialize CircleCI integration.
        
        Args:
            api_token: CircleCI API token
            project_slug: Project slug (format: vcs-slug/org-name/repo-name)
            workflow_id: Workflow ID
            job_number: Job number
        """
        self.api_token = api_token or os.getenv('CIRCLE_TOKEN')
        self.project_slug = project_slug or self._get_project_slug_from_env()
        self.workflow_id = workflow_id or os.getenv('CIRCLE_WORKFLOW_ID')
        self.job_number = job_number or os.getenv('CIRCLE_BUILD_NUM')
        
        self.base_url = "https://circleci.com/api/v2"
        self.headers = {
            "Circle-Token": self.api_token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if not self.api_token:
            raise ValueError("CircleCI API token not provided. Set CIRCLE_TOKEN environment variable.")
    
    def _get_project_slug_from_env(self) -> Optional[str]:
        """Get project slug from environment variables."""
        org_name = os.getenv('CIRCLE_PROJECT_USERNAME')
        repo_name = os.getenv('CIRCLE_PROJECT_REPONAME')
        
        if org_name and repo_name:
            # Determine VCS type from repository URL
            repo_url = os.getenv('CIRCLE_REPOSITORY_URL', '').lower()
            vcs_slug = 'gh' if 'github' in repo_url else 'bb'
            return f"{vcs_slug}/{org_name}/{repo_name}"
        
        return None
    
    def get_workflow_info(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get workflow information.
        
        Args:
            workflow_id: Workflow ID (defaults to current workflow)
        
        Returns:
            Workflow information
        """
        workflow_id = workflow_id or self.workflow_id
        if not workflow_id:
            raise ValueError("Workflow ID not provided")
        
        url = f"{self.base_url}/workflow/{workflow_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_workflow_jobs(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get jobs in a workflow.
        
        Args:
            workflow_id: Workflow ID (defaults to current workflow)
        
        Returns:
            List of jobs
        """
        workflow_id = workflow_id or self.workflow_id
        if not workflow_id:
            raise ValueError("Workflow ID not provided")
        
        url = f"{self.base_url}/workflow/{workflow_id}/job"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('items', [])
    
    def get_job_artifacts(self, job_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get artifacts for a job.
        
        Args:
            job_number: Job number (defaults to current job)
        
        Returns:
            List of artifacts
        """
        job_number = job_number or self.job_number
        if not job_number or not self.project_slug:
            raise ValueError("Job number and project slug are required")
        
        url = f"{self.base_url}/project/{self.project_slug}/{job_number}/artifacts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('items', [])
    
    def store_artifact(self, file_path: str) -> Dict[str, Any]:
        """
        Store an artifact (note: actual upload happens via CircleCI CLI).
        
        This method documents the artifact and returns metadata.
        CircleCI artifacts are uploaded using the `store_artifacts` step in config.yml.
        
        Args:
            file_path: Path to the artifact file
        
        Returns:
            Artifact metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")
        
        # Return metadata for the artifact
        # Actual upload happens via CircleCI's store_artifacts step
        return {
            'path': str(path),
            'name': path.name,
            'size': path.stat().st_size,
            'destination': f"artifacts/{path.name}"
        }
    
    def store_test_results(self, results_dir: str) -> Dict[str, Any]:
        """
        Store test results (note: actual upload happens via CircleCI CLI).
        
        This method documents the test results directory.
        CircleCI test results are uploaded using the `store_test_results` step.
        
        Args:
            results_dir: Path to test results directory
        
        Returns:
            Test results metadata
        """
        path = Path(results_dir)
        if not path.exists():
            raise FileNotFoundError(f"Test results directory not found: {results_dir}")
        
        return {
            'path': str(path),
            'destination': 'test-results'
        }
    
    def format_review_summary(self, findings: List[Dict[str, Any]]) -> str:
        """
        Format review findings as a summary.
        
        Args:
            findings: List of review findings
        
        Returns:
            Formatted summary string
        """
        if not findings:
            return "✅ Code review passed - no issues found!"
        
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
        
        # Determine overall status
        if severity_counts['critical'] > 0:
            status = "🔴 CRITICAL ISSUES FOUND"
        elif severity_counts['high'] > 0:
            status = "🟡 HIGH PRIORITY ISSUES FOUND"
        elif severity_counts['medium'] > 0:
            status = "🟡 ISSUES FOUND"
        else:
            status = "🔵 ONLY MINOR ISSUES FOUND"
        
        # Build summary
        summary_lines = [
            status,
            "",
            f"Total Issues: {len(findings)}",
            ""
        ]
        
        if severity_counts['critical'] > 0:
            summary_lines.append(f"🔴 Critical: {severity_counts['critical']}")
        if severity_counts['high'] > 0:
            summary_lines.append(f"🟠 High: {severity_counts['high']}")
        if severity_counts['medium'] > 0:
            summary_lines.append(f"🟡 Medium: {severity_counts['medium']}")
        if severity_counts['low'] > 0:
            summary_lines.append(f"🔵 Low: {severity_counts['low']}")
        if severity_counts['info'] > 0:
            summary_lines.append(f"ℹ️  Info: {severity_counts['info']}")
        
        return "\n".join(summary_lines)


def review_workflow(
    findings: List[Dict[str, Any]],
    output_file: Optional[str] = None,
    api_token: Optional[str] = None,
    project_slug: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review a CircleCI workflow with findings.
    
    Args:
        findings: List of review findings
        output_file: Optional output file for review report
        api_token: CircleCI API token
        project_slug: Project slug
        workflow_id: Workflow ID
    
    Returns:
        Summary of actions taken
    """
    integration = CircleCIIntegration(
        api_token=api_token,
        project_slug=project_slug,
        workflow_id=workflow_id
    )
    
    # Format summary
    summary = integration.format_review_summary(findings)
    
    # Save report if output file specified
    artifact_stored = False
    if output_file:
        report = {
            'summary': summary,
            'findings': findings,
            'total_findings': len(findings),
            'workflow_id': integration.workflow_id
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Document artifact (actual upload via store_artifacts step)
        artifact_info = integration.store_artifact(output_file)
        artifact_stored = True
    
    return {
        'summary': summary,
        'total_findings': len(findings),
        'artifact_stored': artifact_stored,
        'output_file': output_file,
        'workflow_id': integration.workflow_id
    }

