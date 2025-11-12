"""
Tests for diff-based incremental analysis.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from reviewr.analysis.diff_analyzer import DiffAnalyzer, DiffHunk, FileDiff


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
        
        # Create initial file
        test_file = repo_path / "test.py"
        test_file.write_text("""def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x + y
""")
        
        # Commit initial file
        subprocess.run(["git", "add", "test.py"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
        
        yield repo_path


def test_diff_analyzer_initialization():
    """Test DiffAnalyzer initialization."""
    analyzer = DiffAnalyzer(context_lines=3)
    assert analyzer.context_lines == 3
    
    analyzer = DiffAnalyzer()
    assert analyzer.context_lines == 5  # Default


def test_get_changed_files_no_changes(temp_git_repo):
    """Test getting changed files when there are no changes."""
    analyzer = DiffAnalyzer()
    changed_files = analyzer.get_changed_files(repo_path=temp_git_repo)
    assert changed_files == []


def test_get_changed_files_with_changes(temp_git_repo):
    """Test getting changed files when there are changes."""
    # Modify file
    test_file = temp_git_repo / "test.py"
    test_file.write_text("""def hello():
    print("Hello, Universe!")

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x + y
""")
    
    analyzer = DiffAnalyzer()
    changed_files = analyzer.get_changed_files(repo_path=temp_git_repo)
    assert "test.py" in changed_files


def test_get_changed_files_new_file(temp_git_repo):
    """Test getting changed files with a new file."""
    # Create new file
    new_file = temp_git_repo / "new.py"
    new_file.write_text("print('New file')")
    
    # Stage the file
    subprocess.run(["git", "add", "new.py"], cwd=temp_git_repo, check=True, capture_output=True)
    
    analyzer = DiffAnalyzer()
    changed_files = analyzer.get_changed_files(repo_path=temp_git_repo)
    assert "new.py" in changed_files


def test_get_file_diff_no_changes(temp_git_repo):
    """Test getting diff for unchanged file."""
    analyzer = DiffAnalyzer()
    file_diff = analyzer.get_file_diff("test.py", repo_path=temp_git_repo)
    assert file_diff is None


def test_get_file_diff_with_changes(temp_git_repo):
    """Test getting diff for changed file."""
    # Modify file
    test_file = temp_git_repo / "test.py"
    test_file.write_text("""def hello():
    print("Hello, Universe!")

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x * y  # Changed from + to *
""")
    
    analyzer = DiffAnalyzer()
    file_diff = analyzer.get_file_diff("test.py", repo_path=temp_git_repo)
    
    assert file_diff is not None
    assert file_diff.file_path == "test.py"
    assert file_diff.has_changes
    assert not file_diff.is_new
    assert not file_diff.is_deleted
    assert len(file_diff.hunks) > 0


def test_diff_hunk_properties():
    """Test DiffHunk properties."""
    hunk = DiffHunk(
        file_path="test.py",
        old_start=10,
        old_count=3,
        new_start=10,
        new_count=5,
        lines=["line1", "line2", "line3", "line4", "line5"],
        context_before=["context1", "context2"],
        context_after=["context3"]
    )
    
    assert hunk.changed_line_numbers == [10, 11, 12, 13, 14]
    assert "line1" in hunk.full_content
    assert "context1" in hunk.full_content
    assert "context3" in hunk.full_content


def test_file_diff_properties():
    """Test FileDiff properties."""
    hunk1 = DiffHunk(
        file_path="test.py",
        old_start=5,
        old_count=2,
        new_start=5,
        new_count=2,
        lines=["line1", "line2"],
        context_before=[],
        context_after=[]
    )
    
    hunk2 = DiffHunk(
        file_path="test.py",
        old_start=15,
        old_count=1,
        new_start=15,
        new_count=1,
        lines=["line3"],
        context_before=[],
        context_after=[]
    )
    
    file_diff = FileDiff(
        file_path="test.py",
        old_path=None,
        is_new=False,
        is_deleted=False,
        is_renamed=False,
        hunks=[hunk1, hunk2]
    )
    
    assert file_diff.has_changes
    assert file_diff.all_changed_lines == [5, 6, 15]


def test_get_changed_content(temp_git_repo):
    """Test getting changed content with context."""
    # Modify file
    test_file = temp_git_repo / "test.py"
    test_file.write_text("""def hello():
    print("Hello, Universe!")  # Changed

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x * y  # Changed from + to *
""")
    
    analyzer = DiffAnalyzer(context_lines=2)
    changed_content = analyzer.get_changed_content("test.py", repo_path=temp_git_repo)
    
    assert changed_content is not None
    assert "Hello, Universe!" in changed_content
    assert "x * y" in changed_content


def test_should_review_line_changed(temp_git_repo):
    """Test should_review_line for changed lines."""
    # Modify file
    test_file = temp_git_repo / "test.py"
    test_file.write_text("""def hello():
    print("Hello, Universe!")  # Line 2 changed

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x + y
""")
    
    analyzer = DiffAnalyzer(context_lines=2)
    file_diff = analyzer.get_file_diff("test.py", repo_path=temp_git_repo)
    
    # Line 2 is changed
    assert analyzer.should_review_line("test.py", 2, file_diff)
    
    # Lines near the change should also be reviewed (within context)
    assert analyzer.should_review_line("test.py", 1, file_diff)
    assert analyzer.should_review_line("test.py", 3, file_diff)
    assert analyzer.should_review_line("test.py", 4, file_diff)
    
    # Lines far from changes should not be reviewed
    assert not analyzer.should_review_line("test.py", 8, file_diff)


def test_should_review_line_no_diff():
    """Test should_review_line when no diff info available."""
    analyzer = DiffAnalyzer()
    
    # Without diff info, should review all lines
    assert analyzer.should_review_line("test.py", 1, None)
    assert analyzer.should_review_line("test.py", 100, None)


def test_new_file_detection(temp_git_repo):
    """Test detection of new files."""
    # Create and stage new file
    new_file = temp_git_repo / "new.py"
    new_file.write_text("print('New file')")
    subprocess.run(["git", "add", "new.py"], cwd=temp_git_repo, check=True, capture_output=True)
    
    analyzer = DiffAnalyzer()
    file_diff = analyzer.get_file_diff("new.py", repo_path=temp_git_repo)
    
    assert file_diff is not None
    assert file_diff.is_new
    assert not file_diff.is_deleted


def test_deleted_file_detection(temp_git_repo):
    """Test detection of deleted files."""
    # Delete file
    test_file = temp_git_repo / "test.py"
    test_file.unlink()
    subprocess.run(["git", "add", "test.py"], cwd=temp_git_repo, check=True, capture_output=True)
    
    analyzer = DiffAnalyzer()
    file_diff = analyzer.get_file_diff("test.py", repo_path=temp_git_repo)
    
    assert file_diff is not None
    assert file_diff.is_deleted
    assert not file_diff.is_new


def test_multiple_hunks(temp_git_repo):
    """Test file with multiple changed sections."""
    # Modify file in multiple places
    test_file = temp_git_repo / "test.py"
    test_file.write_text("""def hello():
    print("Hello, Universe!")  # Changed

def goodbye():
    print("Goodbye!")

def calculate(x, y):
    return x * y  # Changed

def new_function():
    return "new"  # Added
""")
    
    analyzer = DiffAnalyzer()
    file_diff = analyzer.get_file_diff("test.py", repo_path=temp_git_repo)
    
    assert file_diff is not None
    assert len(file_diff.hunks) >= 1  # At least one hunk
    assert file_diff.has_changes


def test_context_lines_configuration():
    """Test different context line configurations."""
    analyzer_small = DiffAnalyzer(context_lines=1)
    assert analyzer_small.context_lines == 1
    
    analyzer_large = DiffAnalyzer(context_lines=10)
    assert analyzer_large.context_lines == 10


def test_empty_repository_error():
    """Test error handling for non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = DiffAnalyzer()
        
        with pytest.raises(RuntimeError):
            analyzer.get_changed_files(repo_path=Path(tmpdir))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

