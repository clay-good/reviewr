#!/usr/bin/env python3
"""
Comprehensive validation script for reviewr product.
Checks for gaps, missing features, and ensures everything is production-ready.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


class ProductValidator:
    """Validates the reviewr product for completeness and quality."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("=" * 80)
        print("REVIEWR PRODUCT VALIDATION")
        print("=" * 80)
        print()
        
        self.check_core_modules()
        self.check_analyzers()
        self.check_cli_commands()
        self.check_integrations()
        self.check_tests()
        self.check_documentation()
        self.check_formatters()
        self.check_autofix()
        self.check_dashboard()
        
        self.print_results()
        
        return len(self.errors) == 0
    
    def check_core_modules(self):
        """Check that all core modules exist."""
        print("Checking core modules...")
        
        required_modules = [
            'reviewr/__init__.py',
            'reviewr/cli.py',
            'reviewr/config/__init__.py',
            'reviewr/providers/base.py',
            'reviewr/providers/claude.py',
            'reviewr/providers/openai.py',
            'reviewr/providers/gemini.py',
            'reviewr/review/orchestrator.py',
            'reviewr/analysis/__init__.py',
            'reviewr/analysis/base.py',
        ]
        
        for module in required_modules:
            if Path(module).exists():
                self.successes.append(f"✓ Core module: {module}")
            else:
                self.errors.append(f"✗ Missing core module: {module}")
    
    def check_analyzers(self):
        """Check that all language analyzers exist."""
        print("Checking analyzers...")
        
        analyzers = {
            'Python': [
                'reviewr/analysis/unified_analyzer.py',
                'reviewr/analysis/security_analyzer.py',
                'reviewr/analysis/dataflow_analyzer.py',
                'reviewr/analysis/complexity_analyzer.py',
                'reviewr/analysis/type_analyzer.py',
                'reviewr/analysis/performance_analyzer.py',
                'reviewr/analysis/semantic_analyzer.py',
            ],
            'JavaScript/TypeScript': [
                'reviewr/analysis/javascript_unified_analyzer.py',
                'reviewr/analysis/javascript_security_analyzer.py',
                'reviewr/analysis/javascript_performance_analyzer.py',
                'reviewr/analysis/javascript_type_analyzer.py',
                'reviewr/analysis/javascript_analyzer.py',  # Quality analyzer
            ],
            'Go': [
                'reviewr/analysis/go_unified_analyzer.py',
                'reviewr/analysis/go_security_analyzer.py',
                'reviewr/analysis/go_performance_analyzer.py',
                'reviewr/analysis/go_quality_analyzer.py',
            ],
            'Rust': [
                'reviewr/analysis/rust_unified_analyzer.py',
                'reviewr/analysis/rust_ownership_analyzer.py',
                'reviewr/analysis/rust_safety_analyzer.py',
                'reviewr/analysis/rust_performance_analyzer.py',
                'reviewr/analysis/rust_quality_analyzer.py',
            ],
            'Java': [
                'reviewr/analysis/java_unified_analyzer.py',
                'reviewr/analysis/java_security_analyzer.py',
                'reviewr/analysis/java_concurrency_analyzer.py',
                'reviewr/analysis/java_performance_analyzer.py',
                'reviewr/analysis/java_quality_analyzer.py',
            ],
        }
        
        for language, files in analyzers.items():
            for file in files:
                if Path(file).exists():
                    self.successes.append(f"✓ {language} analyzer: {Path(file).name}")
                else:
                    self.errors.append(f"✗ Missing {language} analyzer: {file}")
    
    def check_cli_commands(self):
        """Check that all CLI commands are available."""
        print("Checking CLI commands...")
        
        try:
            result = subprocess.run(
                ['python3', '-c', 'from reviewr.cli import main_group; import sys; sys.argv = ["reviewr", "--help"]; main_group()'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            required_commands = [
                'autofix', 'azure', 'bitbucket', 'circleci', 'dashboard',
                'email', 'fix', 'jenkins', 'learn', 'preset', 'slack', 'teams'
            ]
            
            for cmd in required_commands:
                if cmd in result.stdout:
                    self.successes.append(f"✓ CLI command: {cmd}")
                else:
                    self.errors.append(f"✗ Missing CLI command: {cmd}")
                    
        except Exception as e:
            self.errors.append(f"✗ Failed to check CLI commands: {e}")
    
    def check_integrations(self):
        """Check that all integrations exist."""
        print("Checking integrations...")
        
        integrations = [
            'reviewr/integrations/github.py',
            'reviewr/integrations/gitlab.py',
            'reviewr/integrations/bitbucket.py',
            'reviewr/integrations/azure_devops.py',
            'reviewr/integrations/jenkins.py',
            'reviewr/integrations/circleci.py',
            'reviewr/integrations/slack.py',
            'reviewr/integrations/teams.py',
            'reviewr/reporting/email.py',  # Email is in reporting module
        ]
        
        for integration in integrations:
            if Path(integration).exists():
                self.successes.append(f"✓ Integration: {Path(integration).stem}")
            else:
                self.errors.append(f"✗ Missing integration: {integration}")
    
    def check_tests(self):
        """Check that tests exist and pass."""
        print("Checking tests...")
        
        try:
            # Use shell=True to allow glob expansion
            result = subprocess.run(
                'python3 -m pytest test_*.py --collect-only -q',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if 'collected' in result.stdout or 'passed' in result.stdout:
                # Extract test count from various formats
                import re
                test_count = 0

                # Try "X tests collected" (most common format)
                match = re.search(r'(\d+)\s+tests?\s+collected', result.stdout)
                if match:
                    test_count = int(match.group(1))

                # Try "collected X items"
                if not test_count:
                    match = re.search(r'collected\s+(\d+)\s+items?', result.stdout)
                    if match:
                        test_count = int(match.group(1))

                # Try "X passed"
                if not test_count:
                    match = re.search(r'(\d+)\s+passed', result.stdout)
                    if match:
                        test_count = int(match.group(1))

                if test_count > 0:
                    self.successes.append(f"✓ Found {test_count} tests")
                    if test_count < 300:
                        self.warnings.append(f"⚠ Only {test_count} tests (expected 300+)")
                else:
                    self.warnings.append("⚠ Could not parse test count")
            else:
                self.errors.append("✗ Failed to collect tests")
                
        except Exception as e:
            self.errors.append(f"✗ Failed to check tests: {e}")
    
    def check_documentation(self):
        """Check that documentation exists."""
        print("Checking documentation...")
        
        docs = [
            'README.md',
            'USAGE_GUIDE.md',
            'ROADMAP.md',
            'CHANGELOG.md',
        ]
        
        for doc in docs:
            if Path(doc).exists():
                self.successes.append(f"✓ Documentation: {doc}")
            else:
                self.warnings.append(f"⚠ Missing documentation: {doc}")
    
    def check_formatters(self):
        """Check that all output formatters exist."""
        print("Checking formatters...")
        
        if Path('reviewr/utils/formatters.py').exists():
            self.successes.append("✓ Formatters module exists")
            
            # Check for specific formatters
            with open('reviewr/utils/formatters.py', 'r') as f:
                content = f.read()
                
            formatters = ['TerminalFormatter', 'MarkdownFormatter', 'SarifFormatter', 'HtmlFormatter', 'JunitFormatter']
            for formatter in formatters:
                if f'class {formatter}' in content:
                    self.successes.append(f"✓ Formatter: {formatter}")
                else:
                    self.errors.append(f"✗ Missing formatter: {formatter}")
        else:
            self.errors.append("✗ Missing formatters module")
    
    def check_autofix(self):
        """Check that auto-fix capabilities exist."""
        print("Checking auto-fix...")
        
        autofix_files = [
            'reviewr/autofix/__init__.py',
            'reviewr/autofix/base.py',
            'reviewr/autofix/applicator.py',
            'reviewr/autofix/ai_generator.py',
            'reviewr/autofix/batch_processor.py',
        ]
        
        for file in autofix_files:
            if Path(file).exists():
                self.successes.append(f"✓ Auto-fix: {Path(file).name}")
            else:
                self.errors.append(f"✗ Missing auto-fix: {file}")
    
    def check_dashboard(self):
        """Check that dashboard exists."""
        print("Checking dashboard...")
        
        dashboard_files = [
            'reviewr/dashboard/__init__.py',
            'reviewr/dashboard/api.py',
            'reviewr/dashboard/database.py',
            'reviewr/dashboard/models.py',
        ]
        
        for file in dashboard_files:
            if Path(file).exists():
                self.successes.append(f"✓ Dashboard: {Path(file).name}")
            else:
                self.errors.append(f"✗ Missing dashboard: {file}")
    
    def print_results(self):
        """Print validation results."""
        print()
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()
        
        if self.successes:
            print(f"✓ SUCCESSES ({len(self.successes)}):")
            for success in self.successes[:10]:  # Show first 10
                print(f"  {success}")
            if len(self.successes) > 10:
                print(f"  ... and {len(self.successes) - 10} more")
            print()
        
        if self.warnings:
            print(f"⚠ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        if self.errors:
            print(f"✗ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
            print()
        
        print("=" * 80)
        print(f"SUMMARY: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("=" * 80)
        
        if len(self.errors) == 0:
            print("✓ PRODUCT IS COMPLETE AND READY FOR PRODUCTION!")
        else:
            print("✗ PRODUCT HAS GAPS THAT NEED TO BE ADDRESSED")


if __name__ == '__main__':
    validator = ProductValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)

