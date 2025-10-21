"""
Jenkins integration for automated code review in CI/CD pipelines.

Supports:
- Jenkins REST API integration
- Build status updates
- Artifact publishing
- Pipeline integration
- Credentials management
"""

import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import base64

try:
    import requests
except ImportError:
    requests = None


class JenkinsBuildStatus(Enum):
    """Jenkins build status values."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNSTABLE = "UNSTABLE"
    ABORTED = "ABORTED"
    NOT_BUILT = "NOT_BUILT"


@dataclass
class JenkinsConfig:
    """Jenkins configuration."""
    url: str
    username: Optional[str] = None
    api_token: Optional[str] = None
    job_name: Optional[str] = None
    build_number: Optional[int] = None
    
    @classmethod
    def from_env(cls) -> 'JenkinsConfig':
        """Create config from environment variables."""
        return cls(
            url=os.getenv('JENKINS_URL', ''),
            username=os.getenv('JENKINS_USERNAME'),
            api_token=os.getenv('JENKINS_API_TOKEN'),
            job_name=os.getenv('JOB_NAME'),
            build_number=int(os.getenv('BUILD_NUMBER', '0')) if os.getenv('BUILD_NUMBER') else None
        )


class JenkinsIntegration:
    """Integration with Jenkins for CI/CD automation."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        job_name: Optional[str] = None,
        build_number: Optional[int] = None
    ):
        """
        Initialize Jenkins integration.
        
        Args:
            url: Jenkins URL (defaults to JENKINS_URL env var)
            username: Jenkins username (defaults to JENKINS_USERNAME env var)
            api_token: Jenkins API token (defaults to JENKINS_API_TOKEN env var)
            job_name: Job name (defaults to JOB_NAME env var)
            build_number: Build number (defaults to BUILD_NUMBER env var)
        """
        if requests is None:
            raise ImportError(
                "requests library is required for Jenkins integration. "
                "Install with: pip install requests"
            )
        
        self.url = (url or os.getenv('JENKINS_URL', '')).rstrip('/')
        self.username = username or os.getenv('JENKINS_USERNAME')
        self.api_token = api_token or os.getenv('JENKINS_API_TOKEN')
        self.job_name = job_name or os.getenv('JOB_NAME')
        self.build_number = build_number or (
            int(os.getenv('BUILD_NUMBER', '0')) if os.getenv('BUILD_NUMBER') else None
        )
        
        if not self.url:
            raise ValueError(
                "Jenkins URL not provided. Set JENKINS_URL environment variable "
                "or pass url parameter."
            )
        
        # Set up authentication headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.username and self.api_token:
            auth_string = f"{self.username}:{self.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self.headers["Authorization"] = f"Basic {auth_b64}"
    
    def get_build_info(self, job_name: Optional[str] = None, build_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Get build information.
        
        Args:
            job_name: Job name (defaults to instance job_name)
            build_number: Build number (defaults to instance build_number)
        
        Returns:
            Build information
        """
        job = job_name or self.job_name
        build = build_number or self.build_number
        
        if not job or not build:
            raise ValueError("Job name and build number are required")
        
        url = f"{self.url}/job/{job}/{build}/api/json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def set_build_description(
        self,
        description: str,
        job_name: Optional[str] = None,
        build_number: Optional[int] = None
    ) -> None:
        """
        Set build description.
        
        Args:
            description: Build description (HTML supported)
            job_name: Job name (defaults to instance job_name)
            build_number: Build number (defaults to instance build_number)
        """
        job = job_name or self.job_name
        build = build_number or self.build_number
        
        if not job or not build:
            raise ValueError("Job name and build number are required")
        
        url = f"{self.url}/job/{job}/{build}/submitDescription"
        data = {"description": description}
        
        # Jenkins expects form data for this endpoint
        response = requests.post(
            url,
            data=data,
            headers={k: v for k, v in self.headers.items() if k != "Content-Type"}
        )
        response.raise_for_status()
    
    def publish_artifact(
        self,
        file_path: str,
        artifact_name: Optional[str] = None,
        job_name: Optional[str] = None,
        build_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Publish an artifact to Jenkins.
        
        Note: This requires the artifact to be in the workspace.
        Use this method to document artifact locations.
        
        Args:
            file_path: Path to artifact file
            artifact_name: Artifact name (defaults to filename)
            job_name: Job name (defaults to instance job_name)
            build_number: Build number (defaults to instance build_number)
        
        Returns:
            Artifact information
        """
        job = job_name or self.job_name
        build = build_number or self.build_number
        
        if not job or not build:
            raise ValueError("Job name and build number are required")
        
        path = Path(file_path)
        name = artifact_name or path.name
        
        # Return artifact URL
        artifact_url = f"{self.url}/job/{job}/{build}/artifact/{name}"
        
        return {
            "name": name,
            "path": str(path),
            "url": artifact_url,
            "size": path.stat().st_size if path.exists() else 0
        }
    
    def add_badge(
        self,
        text: str,
        color: str = "blue",
        job_name: Optional[str] = None,
        build_number: Optional[int] = None
    ) -> None:
        """
        Add a badge to the build (requires Groovy Postbuild or Badge plugin).
        
        Args:
            text: Badge text
            color: Badge color (blue, green, yellow, red)
            job_name: Job name (defaults to instance job_name)
            build_number: Build number (defaults to instance build_number)
        """
        job = job_name or self.job_name
        build = build_number or self.build_number
        
        if not job or not build:
            raise ValueError("Job name and build number are required")
        
        # This requires the Badge plugin or Groovy Postbuild plugin
        # We'll set the description with badge HTML
        badge_html = f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:3px;">{text}</span>'
        
        try:
            current_desc = self.get_build_info(job, build).get('description', '')
            new_desc = f"{current_desc}<br>{badge_html}" if current_desc else badge_html
            self.set_build_description(new_desc, job, build)
        except Exception as e:
            print(f"Warning: Failed to add badge: {e}")
    
    def format_review_summary(self, findings: List[Dict[str, Any]]) -> str:
        """
        Format review findings as HTML for Jenkins.
        
        Args:
            findings: List of review findings
        
        Returns:
            HTML formatted string
        """
        if not findings:
            return """
            <div style="background-color:#d4edda;border:1px solid #c3e6cb;padding:12px;border-radius:4px;">
                <strong style="color:#155724;">✅ Code Review Complete</strong><br>
                No issues found! Great work! 🎉
            </div>
            """
        
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
            status_color = '#f8d7da'
            border_color = '#f5c6cb'
            text_color = '#721c24'
            status_text = '🔴 Critical Issues Found'
        elif severity_counts['high'] > 0:
            status_color = '#fff3cd'
            border_color = '#ffeaa7'
            text_color = '#856404'
            status_text = '🟠 High Priority Issues Found'
        elif severity_counts['medium'] > 0:
            status_color = '#fff3cd'
            border_color = '#ffeaa7'
            text_color = '#856404'
            status_text = '🟡 Medium Priority Issues Found'
        else:
            status_color = '#d1ecf1'
            border_color = '#bee5eb'
            text_color = '#0c5460'
            status_text = '🟢 Only Minor Issues Found'
        
        # Build HTML
        html = f"""
        <div style="background-color:{status_color};border:1px solid {border_color};padding:12px;border-radius:4px;margin:10px 0;">
            <strong style="color:{text_color};">📋 Code Review Summary</strong><br>
            <strong style="color:{text_color};">Status: {status_text}</strong>
        </div>
        <div style="background-color:#f8f9fa;border:1px solid #dee2e6;padding:12px;border-radius:4px;margin:10px 0;">
            <strong>Findings by Severity:</strong><br>
        """
        
        if severity_counts['critical'] > 0:
            html += f"🔴 <strong>Critical:</strong> {severity_counts['critical']}<br>"
        if severity_counts['high'] > 0:
            html += f"🟠 <strong>High:</strong> {severity_counts['high']}<br>"
        if severity_counts['medium'] > 0:
            html += f"🟡 <strong>Medium:</strong> {severity_counts['medium']}<br>"
        if severity_counts['low'] > 0:
            html += f"🔵 <strong>Low:</strong> {severity_counts['low']}<br>"
        if severity_counts['info'] > 0:
            html += f"ℹ️ <strong>Info:</strong> {severity_counts['info']}<br>"
        
        html += """
        </div>
        <div style="font-size:12px;color:#6c757d;margin:10px 0;">
            <em>Generated by reviewr - AI-powered code review</em>
        </div>
        """
        
        return html


def review_build(
    findings: List[Dict[str, Any]],
    output_file: Optional[str] = None,
    set_description: bool = True,
    add_badge: bool = True,
    url: Optional[str] = None,
    username: Optional[str] = None,
    api_token: Optional[str] = None,
    job_name: Optional[str] = None,
    build_number: Optional[int] = None
) -> Dict[str, Any]:
    """
    Review a Jenkins build with findings.
    
    Args:
        findings: List of review findings
        output_file: Path to save review report
        set_description: Set build description with summary
        add_badge: Add badge to build
        url: Jenkins URL
        username: Jenkins username
        api_token: Jenkins API token
        job_name: Job name
        build_number: Build number
    
    Returns:
        Summary of actions taken
    """
    integration = JenkinsIntegration(
        url=url,
        username=username,
        api_token=api_token,
        job_name=job_name,
        build_number=build_number
    )
    
    # Save report if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(findings, f, indent=2)
    
    # Set build description
    description_set = False
    if set_description:
        try:
            summary = integration.format_review_summary(findings)
            integration.set_build_description(summary)
            description_set = True
        except Exception as e:
            print(f"Warning: Failed to set build description: {e}")
    
    # Add badge
    badge_added = False
    if add_badge:
        try:
            has_critical = any(f.get('severity', '').lower() in ['critical', 'high'] for f in findings)
            if has_critical:
                integration.add_badge("Review: Issues Found", "red")
            elif findings:
                integration.add_badge("Review: Minor Issues", "yellow")
            else:
                integration.add_badge("Review: Passed", "green")
            badge_added = True
        except Exception as e:
            print(f"Warning: Failed to add badge: {e}")
    
    return {
        'total_findings': len(findings),
        'description_set': description_set,
        'badge_added': badge_added,
        'output_file': output_file
    }

