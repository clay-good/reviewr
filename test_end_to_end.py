"""End-to-end integration tests for reviewr."""

import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys


class TestEndToEnd:
    """End-to-end tests for the complete reviewr workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_python_file(self, temp_dir):
        """Create a sample Python file with issues."""
        file_path = temp_dir / "sample.py"
        file_path.write_text("""
import os
import sys
import json  # unused

PASSWORD = "admin123"

def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query

def inefficient_loop():
    result = ""
    for i in range(1000):
        result = result + str(i)
    return result

def bare_except():
    try:
        risky_operation()
    except:
        pass

def risky_operation():
    return 1 / 0
""")
        return file_path
    
    def test_preset_list_command(self):
        """Test that preset list command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "preset", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "security" in result.stdout
        assert "performance" in result.stdout
        assert "quick" in result.stdout
    
    def test_preset_show_command(self):
        """Test that preset show command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "preset", "show", "security"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Security-focused" in result.stdout or "security-focused" in result.stdout
        assert "review types" in result.stdout.lower()
    
    def test_learning_init_command(self, temp_dir):
        """Test that learning init command works."""
        db_path = temp_dir / "feedback.db"
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "learn", "init", "--db-path", str(db_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert db_path.exists()
    
    def test_fix_help_command(self):
        """Test that fix help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "fix", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "apply" in result.stdout
        assert "rollback" in result.stdout
    
    def test_dashboard_help_command(self):
        """Test that dashboard help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "dashboard", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "start" in result.stdout
        assert "init-db" in result.stdout
    
    def test_main_help_command(self):
        """Test that main help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "security" in result.stdout
        assert "performance" in result.stdout
        assert "preset" in result.stdout
    
    def test_preset_compare_command(self):
        """Test that preset compare command works."""
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "preset", "compare", "security", "performance"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "security" in result.stdout.lower()
        assert "performance" in result.stdout.lower()
    
    def test_learning_stats_command(self, temp_dir):
        """Test that learning stats command works with empty database."""
        db_path = temp_dir / "feedback.db"
        # Initialize database first
        subprocess.run(
            [sys.executable, "-m", "reviewr", "learn", "init", "--db-path", str(db_path)],
            capture_output=True,
            text=True
        )
        
        # Get stats
        result = subprocess.run(
            [sys.executable, "-m", "reviewr", "learn", "stats", "--db-path", str(db_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Should show empty stats
        assert "0" in result.stdout or "No feedback" in result.stdout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

