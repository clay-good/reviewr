#!/usr/bin/env python3
"""
Demo script showcasing the new GitLab integration for reviewr.

This script demonstrates:
1. GitLab MR detection and file retrieval
2. Formatting findings as GitLab comments
3. Creating inline discussions on MRs
4. Posting summary comments
5. Auto-approval based on review results

Note: This is a demonstration script. In production, use the reviewr-gitlab CLI command.
"""

import os
from typing import List
from dataclasses import dataclass

# Mock classes for demonstration (in real usage, these come from reviewr)
@dataclass
class MockReviewFinding:
    """Mock review finding for demonstration."""
    file_path: str
    line_start: int
    line_end: int
    severity: str
    message: str
    suggestion: str
    confidence: float = 0.95


@dataclass
class MockReviewResult:
    """Mock review result for demonstration."""
    findings: List[MockReviewFinding]
    files_reviewed: int
    
    def has_critical_issues(self) -> bool:
        return any(f.severity in ('critical', 'high') for f in self.findings)
    
    def get_findings_by_severity(self):
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': [], 'info': []}
        for finding in self.findings:
            if finding.severity in by_severity:
                by_severity[finding.severity].append(finding)
        return by_severity
    
    def get_findings_by_type(self):
        # Simplified for demo
        return {'security': self.findings[:2], 'performance': self.findings[2:]}


def demo_gitlab_integration():
    """Demonstrate GitLab integration features."""
    
    print("=" * 80)
    print("reviewr GitLab Integration Demo")
    print("=" * 80)
    print()
    
    # 1. Environment Detection
    print("1. Environment Detection")
    print("-" * 80)
    print("GitLab CI automatically provides these environment variables:")
    print(f"  CI_PROJECT_ID: {os.getenv('CI_PROJECT_ID', 'Not set (would be auto-detected)')}")
    print(f"  CI_MERGE_REQUEST_IID: {os.getenv('CI_MERGE_REQUEST_IID', 'Not set (would be auto-detected)')}")
    print(f"  CI_API_V4_URL: {os.getenv('CI_API_V4_URL', 'https://gitlab.com/api/v4 (default)')}")
    print(f"  GITLAB_TOKEN: {'Set ✓' if os.getenv('GITLAB_TOKEN') else 'Not set (required)'}")
    print()
    
    # 2. Mock Review Results
    print("2. Mock Review Results")
    print("-" * 80)
    
    mock_findings = [
        MockReviewFinding(
            file_path="src/auth.py",
            line_start=45,
            line_end=45,
            severity="critical",
            message="SQL injection vulnerability detected",
            suggestion="Use parameterized queries to prevent SQL injection.",
            confidence=0.95
        ),
        MockReviewFinding(
            file_path="src/auth.py",
            line_start=78,
            line_end=78,
            severity="high",
            message="Hardcoded credentials detected",
            suggestion="Move credentials to environment variables or a secrets manager.",
            confidence=0.90
        ),
        MockReviewFinding(
            file_path="src/api.py",
            line_start=123,
            line_end=125,
            severity="medium",
            message="Inefficient database query in loop",
            suggestion="Move the query outside the loop or use batch operations.",
            confidence=0.85
        ),
        MockReviewFinding(
            file_path="src/utils.py",
            line_start=56,
            line_end=56,
            severity="low",
            message="Unused import 'datetime'",
            suggestion="Remove unused import to keep code clean.",
            confidence=0.99
        )
    ]
    
    result = MockReviewResult(
        findings=mock_findings,
        files_reviewed=3
    )
    
    print(f"Files reviewed: {result.files_reviewed}")
    print(f"Total findings: {len(result.findings)}")
    print()
    
    # 3. Format Inline Comments
    print("3. Inline Comments Format")
    print("-" * 80)
    print("reviewr posts inline discussions on specific lines:")
    print()
    
    for finding in mock_findings[:2]:  # Show first 2
        severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}
        emoji = severity_emoji.get(finding.severity, '⚪')
        
        print(f"📍 {finding.file_path}:{finding.line_start}")
        print(f"{emoji} **{finding.severity.upper()}**: {finding.message}")
        print(f"**Suggestion**: {finding.suggestion}")
        print(f"*Confidence: {finding.confidence:.0%}*")
        print()
    
    # 4. Summary Comment
    print("4. Summary Comment Format")
    print("-" * 80)
    
    summary_lines = ["## 🤖 reviewr Code Review Summary\n"]
    summary_lines.append(f"**Files reviewed**: {result.files_reviewed}")
    summary_lines.append(f"**Total findings**: {len(result.findings)}\n")
    
    by_severity = result.get_findings_by_severity()
    severity_counts = []
    emoji_map = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': 'ℹ️'}
    
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = len(by_severity[severity])
        if count > 0:
            emoji = emoji_map[severity]
            severity_counts.append(f"{emoji} {count} {severity}")
    
    summary_lines.append("**Findings by severity**: " + ", ".join(severity_counts))
    
    by_type = result.get_findings_by_type()
    summary_lines.append("\n**Findings by type**:")
    for type_name, type_findings in by_type.items():
        summary_lines.append(f"- {type_name}: {len(type_findings)}")
    
    summary_lines.append("")
    
    if result.has_critical_issues():
        summary_lines.append("⚠️ **This MR has critical or high severity issues that should be addressed.**")
    else:
        summary_lines.append("✅ **No critical or high severity issues found.**")
    
    summary_lines.append("\n---")
    summary_lines.append("*Powered by [reviewr](https://github.com/clay-good/reviewr)*")
    
    summary = "\n".join(summary_lines)
    print(summary)
    print()
    
    # 5. Usage Examples
    print("5. Usage Examples")
    print("-" * 80)
    print("Command line usage:")
    print()
    print("# Review current MR (auto-detected in GitLab CI)")
    print("reviewr-gitlab --all")
    print()
    print("# Review specific MR")
    print("reviewr-gitlab --mr-iid 123 --all")
    print()
    print("# Review with specific types")
    print("reviewr-gitlab --mr-iid 123 --security --performance")
    print()
    print("# Review and approve if no critical issues")
    print("reviewr-gitlab --all --approve-if-clean")
    print()
    print("# Review without posting comments (dry run)")
    print("reviewr-gitlab --all --no-post-comments --no-post-summary")
    print()
    
    # 6. GitLab CI Configuration
    print("6. GitLab CI Configuration")
    print("-" * 80)
    print("Add to .gitlab-ci.yml:")
    print()
    print("""stages:
  - review

reviewr_mr_review:
  stage: review
  image: python:3.11
  before_script:
    - pip install -e ".[gitlab]"
  script:
    - reviewr-gitlab --all --post-comments --post-summary
  only:
    - merge_requests
  variables:
    GITLAB_TOKEN: $GITLAB_TOKEN
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
""")
    print()
    
    # 7. Features Summary
    print("7. Features Summary")
    print("-" * 80)
    print("✅ Automated MR Reviews - Reviews all changed files automatically")
    print("✅ Inline Discussions - Posts findings as inline discussions on specific lines")
    print("✅ Review Status - Can approve MRs if no critical issues found")
    print("✅ Smart Filtering - Only comments on changed files")
    print("✅ Rich Summaries - Posts comprehensive review summaries")
    print("✅ Auto-detection - Automatically detects MR IID and project ID in GitLab CI")
    print("✅ Self-hosted Support - Works with self-hosted GitLab instances")
    print("✅ Token Flexibility - Supports both personal tokens and CI_JOB_TOKEN")
    print()
    
    # 8. Comparison with GitHub Integration
    print("8. Comparison: GitHub vs GitLab Integration")
    print("-" * 80)
    print("Feature                    | GitHub          | GitLab")
    print("-" * 80)
    print("Inline Comments            | ✓               | ✓")
    print("Summary Comments           | ✓               | ✓")
    print("Auto-detection in CI       | ✓               | ✓")
    print("Approval/Request Changes   | ✓               | ✓")
    print("Self-hosted Support        | ✗               | ✓")
    print("CLI Command                | reviewr-github  | reviewr-gitlab")
    print("Token Env Var              | GITHUB_TOKEN    | GITLAB_TOKEN")
    print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("To use in production:")
    print("1. Install: pip install -e '.[gitlab]'")
    print("2. Set GITLAB_TOKEN environment variable")
    print("3. Run: reviewr-gitlab --all")
    print()


if __name__ == "__main__":
    demo_gitlab_integration()

