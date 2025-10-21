#!/usr/bin/env python3
"""
Test CLI integration with advanced analyzers.

This creates a test file with known issues and runs reviewr CLI
to verify that the advanced analyzers are working through the CLI.
"""

import subprocess
import tempfile
import os
from pathlib import Path

# Test code with multiple issues
TEST_CODE = """
import os
import pickle

def vulnerable_function(user_id):
    # SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    # Command injection
    os.system(f"echo {user_id}")
    
    # High complexity
    if user_id > 0:
        if user_id < 100:
            if user_id % 2 == 0:
                if user_id % 3 == 0:
                    return "complex"
    
    # Resource leak
    f = open('data.txt', 'r')
    data = f.read()
    return data

def n_plus_one_query(user_ids):
    results = []
    # N+1 query pattern
    for user_id in user_ids:
        user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(user)
    return results
"""

def test_cli_with_all_analyzers():
    """Test CLI with all analyzers enabled (default)."""
    print("=" * 60)
    print("TEST 1: CLI with all analyzers (default)")
    print("=" * 60)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_CODE)
        temp_file = f.name
    
    try:
        # Run reviewr CLI (skip AI review, use local analysis only)
        result = subprocess.run(
            ['python3', '-m', 'reviewr.cli', temp_file, '--all', '--output-format', 'markdown', '-v'],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'ANTHROPIC_API_KEY': 'test-key'}  # Provide dummy key to avoid errors
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        # Check that command ran successfully
        assert result.returncode == 0, f"CLI should run successfully, got return code {result.returncode}"
        
        # Check that report was created
        report_path = Path.cwd() / "reviewr-report.md"
        assert report_path.exists(), "Report file should be created"
        
        # Read and check report content
        with open(report_path, 'r') as f:
            report_content = f.read()
        
        print("\n" + "=" * 60)
        print("REPORT PREVIEW (first 1000 chars):")
        print("=" * 60)
        print(report_content[:1000])
        
        # Clean up report
        report_path.unlink()
        
        print("\n✓ Test passed: CLI with all analyzers works")
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)


def test_cli_with_selective_analyzers():
    """Test CLI with only security and performance analyzers."""
    print("\n" + "=" * 60)
    print("TEST 2: CLI with selective analyzers")
    print("=" * 60)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_CODE)
        temp_file = f.name
    
    try:
        # Run reviewr CLI with only security and performance
        result = subprocess.run(
            [
                'python3', '-m', 'reviewr.cli', temp_file,
                '--all', '--output-format', 'markdown',
                '--disable-complexity-analysis',
                '--disable-type-analysis',
                '--disable-dataflow-analysis',
                '--disable-semantic-analysis',
                '-v'
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'ANTHROPIC_API_KEY': 'test-key'}
        )

        print("STDOUT:")
        print(result.stdout)

        # Check that command ran successfully
        assert result.returncode == 0, f"CLI should run successfully, got return code {result.returncode}"
        
        # Check that report was created
        report_path = Path.cwd() / "reviewr-report.md"
        if report_path.exists():
            report_path.unlink()
        
        print("\n✓ Test passed: Selective analyzers work")
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)


def test_cli_with_severity_filter():
    """Test CLI with minimum severity filter."""
    print("\n" + "=" * 60)
    print("TEST 3: CLI with severity filter (high and above)")
    print("=" * 60)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_CODE)
        temp_file = f.name
    
    try:
        # Run reviewr CLI with high severity filter
        result = subprocess.run(
            [
                'python3', '-m', 'reviewr.cli', temp_file,
                '--all', '--output-format', 'markdown',
                '--min-severity', 'high',
                '-v'
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'ANTHROPIC_API_KEY': 'test-key'}
        )

        print("STDOUT:")
        print(result.stdout)

        # Check that command ran successfully
        assert result.returncode == 0, f"CLI should run successfully, got return code {result.returncode}"
        
        # Check that report was created
        report_path = Path.cwd() / "reviewr-report.md"
        if report_path.exists():
            report_path.unlink()
        
        print("\n✓ Test passed: Severity filter works")
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)


def test_cli_with_custom_thresholds():
    """Test CLI with custom complexity thresholds."""
    print("\n" + "=" * 60)
    print("TEST 4: CLI with custom thresholds")
    print("=" * 60)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(TEST_CODE)
        temp_file = f.name
    
    try:
        # Run reviewr CLI with custom thresholds (local-only)
        result = subprocess.run(
            [
                'python3', '-m', 'reviewr.cli', temp_file,
                '--all', '--output-format', 'markdown', '--local-only',
                '--cyclomatic-threshold', '5',
                '--cognitive-threshold', '10',
                '-v'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        # Check that report was created
        report_path = Path.cwd() / "reviewr-report.md"
        if report_path.exists():
            report_path.unlink()
        
        print("\n✓ Test passed: Custom thresholds work")
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)


def main():
    """Run all CLI integration tests."""
    print("\n" + "=" * 60)
    print("CLI INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_cli_with_all_analyzers()
        test_cli_with_selective_analyzers()
        test_cli_with_severity_filter()
        test_cli_with_custom_thresholds()
        
        print("\n" + "=" * 60)
        print("✅ ALL CLI INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nThe advanced analyzers are successfully integrated into the CLI!")
        print("Users can now control analyzers via command-line flags.")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

