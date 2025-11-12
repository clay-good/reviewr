"""
End-to-end integration tests for diff-based incremental analysis.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
import asyncio
from reviewr.analysis.diff_analyzer import DiffAnalyzer
from reviewr.review.orchestrator import ReviewOrchestrator
from reviewr.config.defaults import get_default_config
from reviewr.providers import ReviewType


@pytest.fixture
def temp_git_repo_with_code():
    """Create a temporary git repository with Python code for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
        
        # Create initial Python file with some issues
        test_file = repo_path / "app.py"
        test_file.write_text("""
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

def main():
    numbers = [1, 2, 3, 4, 5]
    print(calculate_sum(numbers))
""")
        
        # Commit initial file
        subprocess.run(["git", "add", "app.py"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
        
        yield repo_path


def test_diff_analyzer_with_orchestrator(temp_git_repo_with_code):
    """Test diff analyzer integration with orchestrator."""
    repo_path = temp_git_repo_with_code
    
    # Modify the file to add a security issue
    test_file = repo_path / "app.py"
    test_file.write_text("""
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

def execute_command(cmd):
    # SECURITY ISSUE: Command injection vulnerability
    import os
    os.system(cmd)

def main():
    numbers = [1, 2, 3, 4, 5]
    print(calculate_sum(numbers))
""")
    
    # Create diff analyzer
    diff_analyzer = DiffAnalyzer(context_lines=3)
    
    # Verify that changes are detected
    changed_files = diff_analyzer.get_changed_files(repo_path=repo_path)
    assert "app.py" in changed_files
    
    # Get changed content
    changed_content = diff_analyzer.get_changed_content("app.py", repo_path=repo_path)
    assert changed_content is not None
    assert "execute_command" in changed_content
    assert "os.system" in changed_content


def test_orchestrator_diff_mode_filters_files(temp_git_repo_with_code):
    """Test that orchestrator only reviews changed files in diff mode."""
    repo_path = temp_git_repo_with_code
    
    # Create another file that won't be changed
    unchanged_file = repo_path / "utils.py"
    unchanged_file.write_text("""
def helper():
    return "unchanged"
""")
    subprocess.run(["git", "add", "utils.py"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add utils"], cwd=repo_path, check=True, capture_output=True)
    
    # Modify only app.py
    test_file = repo_path / "app.py"
    test_file.write_text("""
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

def new_function():
    # This is a new function
    return "new"

def main():
    numbers = [1, 2, 3, 4, 5]
    print(calculate_sum(numbers))
""")
    
    # Create diff analyzer
    diff_analyzer = DiffAnalyzer(context_lines=3)
    
    # Load config
    config = get_default_config()
    
    # Create orchestrator with diff mode
    orchestrator = ReviewOrchestrator(
        provider=None,  # Local-only mode
        config=config,
        verbose=1,
        use_cache=False,
        use_local_analysis=True,
        diff_analyzer=diff_analyzer,
        diff_base="HEAD",
        diff_target=None
    )
    
    # Run review
    async def run_review():
        return await orchestrator.review_path(
            path=str(repo_path),
            review_types=[ReviewType.SECURITY],
            language="python"
        )
    
    result = asyncio.run(run_review())
    
    # Should only review app.py, not utils.py
    # In diff mode, only changed files are reviewed
    assert result.files_reviewed <= 1  # Only app.py should be reviewed


def test_diff_mode_with_no_changes(temp_git_repo_with_code):
    """Test diff mode when there are no changes."""
    repo_path = temp_git_repo_with_code
    
    # Don't modify anything
    
    # Create diff analyzer
    diff_analyzer = DiffAnalyzer(context_lines=3)
    
    # Load config
    config = get_default_config()
    
    # Create orchestrator with diff mode
    orchestrator = ReviewOrchestrator(
        provider=None,  # Local-only mode
        config=config,
        verbose=0,
        use_cache=False,
        use_local_analysis=True,
        diff_analyzer=diff_analyzer,
        diff_base="HEAD",
        diff_target=None
    )
    
    # Run review
    async def run_review():
        return await orchestrator.review_path(
            path=str(repo_path),
            review_types=[ReviewType.SECURITY],
            language="python"
        )
    
    result = asyncio.run(run_review())
    
    # Should review 0 files since nothing changed
    assert result.files_reviewed == 0
    assert len(result.findings) == 0


def test_diff_mode_with_multiple_files(temp_git_repo_with_code):
    """Test diff mode with multiple changed files."""
    repo_path = temp_git_repo_with_code
    
    # Modify app.py
    test_file = repo_path / "app.py"
    test_file.write_text("""
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

def new_function():
    return "modified"
""")
    
    # Create and modify another file
    new_file = repo_path / "new_module.py"
    new_file.write_text("""
def another_function():
    return "new file"
""")
    subprocess.run(["git", "add", "new_module.py"], cwd=repo_path, check=True, capture_output=True)
    
    # Create diff analyzer
    diff_analyzer = DiffAnalyzer(context_lines=3)
    
    # Get changed files
    changed_files = diff_analyzer.get_changed_files(repo_path=repo_path)
    
    # Should detect both files
    assert "app.py" in changed_files
    assert "new_module.py" in changed_files


def test_diff_context_lines():
    """Test different context line configurations."""
    # Small context
    analyzer_small = DiffAnalyzer(context_lines=1)
    assert analyzer_small.context_lines == 1
    
    # Large context
    analyzer_large = DiffAnalyzer(context_lines=10)
    assert analyzer_large.context_lines == 10
    
    # Default context
    analyzer_default = DiffAnalyzer()
    assert analyzer_default.context_lines == 5


def test_diff_mode_performance_benefit(temp_git_repo_with_code):
    """Test that diff mode reduces the amount of code to review."""
    repo_path = temp_git_repo_with_code
    
    # Add a large file
    large_file = repo_path / "large.py"
    large_content = "\n".join([f"def function_{i}():\n    return {i}" for i in range(100)])
    large_file.write_text(large_content)
    subprocess.run(["git", "add", "large.py"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Add large file"], cwd=repo_path, check=True, capture_output=True)
    
    # Make a small change to the large file
    large_content_modified = large_content + "\n\ndef new_function():\n    return 'new'"
    large_file.write_text(large_content_modified)
    
    # Create diff analyzer
    diff_analyzer = DiffAnalyzer(context_lines=3)
    
    # Get changed content
    changed_content = diff_analyzer.get_changed_content("large.py", repo_path=repo_path)
    
    # Changed content should be much smaller than full file
    assert changed_content is not None
    assert len(changed_content) < len(large_content_modified) / 2  # At least 50% reduction
    assert "new_function" in changed_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

