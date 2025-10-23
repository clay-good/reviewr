#!/usr/bin/env python3
"""
Comprehensive test runner for reviewr.
Runs all tests and generates a detailed report.
"""

import subprocess
import sys
import time
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text):
 """Print a formatted header."""
 print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
 print(f"{BLUE}{BOLD}{text:^80}{RESET}")
 print(f"{BLUE}{BOLD}{'=' * 80}{RESET}\n")

def print_success(text):
 """Print success message."""
 print(f"{GREEN} {text}{RESET}")

def print_error(text):
 """Print error message."""
 print(f"{RED} {text}{RESET}")

def print_warning(text):
 """Print warning message."""
 print(f"{YELLOW} {text}{RESET}")

def run_test_suite(name, test_files):
 """Run a test suite and return results."""
 print_header(f"Running {name}")
 
 cmd = ['python3', '-m', 'pytest'] + test_files + ['-v', '--tb=short', '-q']
 
 start_time = time.time()
 result = subprocess.run(cmd, capture_output=True, text=True)
 duration = time.time() - start_time
 
 # Parse output
 passed = failed = 0
 for line in result.stdout.split('\n'):
 if 'passed' in line:
 parts = line.split()
 for i, part in enumerate(parts):
 if 'passed' in part and i > 0:
 try:
 passed = int(parts[i-1])
 except:
 pass
 if 'failed' in line:
 parts = line.split()
 for i, part in enumerate(parts):
 if 'failed' in part and i > 0:
 try:
 failed = int(parts[i-1])
 except:
 pass
 
 # Print results
 if result.returncode == 0:
 print_success(f"{name}: {passed} tests passed in {duration:.2f}s")
 return True, passed, 0
 else:
 print_error(f"{name}: {failed} tests failed, {passed} tests passed in {duration:.2f}s")
 if failed > 0:
 print("\nFailed test output:")
 print(result.stdout[-1000:]) # Last 1000 chars
 return False, passed, failed

def main():
 """Run all test suites."""
 print_header("reviewr Comprehensive Test Suite")
 
 test_suites = [
 ("Auto-Fix Tests", ["test_autofix.py"]),
 ("Dashboard Tests", ["test_dashboard.py"]),
 ("CI/CD Integration Tests", ["test_ci_integration.py"]),
 ("API Efficiency Tests", ["test_api_efficiency.py"]),
 ("CLI Integration Tests", ["test_cli_integration.py"]),
 ("JavaScript/TypeScript Analyzer Tests", ["test_javascript_unified.py"]),
 ("Go Analyzer Tests", ["test_go_unified.py"]),
 ("Rust Analyzer Tests", ["test_rust_unified.py"]),
 ("Java Analyzer Tests", ["test_java_unified.py"]),
 ("Unified Integration Tests", ["test_unified_integration.py"]),
 ("Simple Integration Tests", ["test_integration_simple.py"]),
 ("Enhanced Formatters Tests", ["test_enhanced_formatters.py"]),
 ("GitLab Integration Tests", ["test_gitlab_integration.py"]),
 ]
 
 results = []
 total_passed = 0
 total_failed = 0
 
 for name, files in test_suites:
 # Check if test files exist
 missing = [f for f in files if not Path(f).exists()]
 if missing:
 print_warning(f"{name}: Skipped (files not found: {', '.join(missing)})")
 continue
 
 success, passed, failed = run_test_suite(name, files)
 results.append((name, success, passed, failed))
 total_passed += passed
 total_failed += failed
 
 # Print summary
 print_header("Test Summary")
 
 for name, success, passed, failed in results:
 status = f"{GREEN} PASSED{RESET}" if success else f"{RED} FAILED{RESET}"
 print(f"{status} {name}: {passed} passed, {failed} failed")
 
 print(f"\n{BOLD}Total: {total_passed} passed, {total_failed} failed{RESET}")
 
 if total_failed == 0:
 print(f"\n{GREEN}{BOLD} ALL TESTS PASSED! {RESET}\n")
 return 0
 else:
 print(f"\n{RED}{BOLD} SOME TESTS FAILED{RESET}\n")
 return 1

if __name__ == '__main__':
 sys.exit(main())
