"""Comprehensive tests for auto-fix functionality."""

import os
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass

# Mock ReviewFinding for testing
@dataclass
class MockFinding:
    """Mock finding for testing."""
    file_path: str
    line_start: int
    line_end: int
    severity: str
    message: str
    suggestion: str = ""
    confidence: float = 0.95


def test_python_fix_generator():
    """Test Python fix generator."""
    print("\n" + "="*80)
    print("TEST 1: Python Fix Generator")
    print("="*80)
    
    from reviewr.autofix import PythonFixGenerator, FixCategory
    
    generator = PythonFixGenerator()
    
    # Test 1: Unused import
    finding1 = MockFinding(
        file_path="test.py",
        line_start=1,
        line_end=1,
        severity="low",
        message="Unused import: os"
    )
    
    file_content = "import os\nimport sys\n\nprint('hello')\n"
    
    fix = generator.generate_fix(finding1, file_content)
    
    assert fix is not None, "Should generate fix for unused import"
    assert fix.category == FixCategory.IMPORTS
    assert fix.old_code == "import os"
    assert fix.new_code == ""
    print("✓ Unused import fix generated correctly")
    
    # Test 2: is comparison
    finding2 = MockFinding(
        file_path="test.py",
        line_start=1,
        line_end=1,
        severity="medium",
        message="Use 'is' for None comparison"
    )
    
    file_content2 = "if x == None:\n    pass\n"
    
    fix2 = generator.generate_fix(finding2, file_content2)
    
    assert fix2 is not None, "Should generate fix for is comparison"
    assert fix2.category == FixCategory.CORRECTNESS
    assert "is None" in fix2.new_code
    print("✓ is comparison fix generated correctly")
    
    # Test 3: Bare except
    finding3 = MockFinding(
        file_path="test.py",
        line_start=3,
        line_end=3,
        severity="high",
        message="Bare except clause"
    )

    file_content3 = "try:\n    pass\nexcept:\n    pass\n"

    fix3 = generator.generate_fix(finding3, file_content3)

    assert fix3 is not None, "Should generate fix for bare except"
    assert "except Exception:" in fix3.new_code
    print("✓ Bare except fix generated correctly")
    
    print("\n✅ Python fix generator tests passed!")
    return True


def test_javascript_fix_generator():
    """Test JavaScript fix generator."""
    print("\n" + "="*80)
    print("TEST 2: JavaScript Fix Generator")
    print("="*80)
    
    from reviewr.autofix import JavaScriptFixGenerator, FixCategory
    
    generator = JavaScriptFixGenerator()
    
    # Test 1: var to const
    finding1 = MockFinding(
        file_path="test.js",
        line_start=1,
        line_end=1,
        severity="low",
        message="Use const instead of var"
    )
    
    file_content = "var x = 5;\n"
    
    fix = generator.generate_fix(finding1, file_content)
    
    assert fix is not None, "Should generate fix for var to const"
    assert fix.category == FixCategory.STYLE
    assert "const x = 5;" in fix.new_code
    print("✓ var to const fix generated correctly")
    
    # Test 2: Strict equality
    finding2 = MockFinding(
        file_path="test.js",
        line_start=1,
        line_end=1,
        severity="medium",
        message="Use strict equality (===)"
    )
    
    file_content2 = "if (x == 5) {\n"
    
    fix2 = generator.generate_fix(finding2, file_content2)
    
    assert fix2 is not None, "Should generate fix for strict equality"
    assert "===" in fix2.new_code
    print("✓ Strict equality fix generated correctly")
    
    print("\n✅ JavaScript fix generator tests passed!")
    return True


def test_fix_applicator():
    """Test fix applicator with real files."""
    print("\n" + "="*80)
    print("TEST 3: Fix Applicator")
    print("="*80)
    
    from reviewr.autofix import FixApplicator, Fix, FixCategory, FixStatus
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file
        test_file = tmpdir / "test.py"
        original_content = "import os\nimport sys\n\nif x == None:\n    pass\n"
        test_file.write_text(original_content)
        
        # Create fix
        fix = Fix(
            fix_id="test123",
            category=FixCategory.CORRECTNESS,
            file_path=str(test_file),
            line_start=4,
            line_end=4,
            description="Use 'is None'",
            old_code="if x == None:",
            new_code="if x is None:",
            confidence=0.95,
            safe=True,
            requires_validation=False
        )
        
        # Apply fix
        applicator = FixApplicator(
            backup_dir=str(tmpdir / "backups"),
            dry_run=False,
            validate_syntax=False,
            verbose=False
        )
        
        result = applicator.apply_fix(fix)
        
        assert result.status == FixStatus.SUCCESS, f"Fix should succeed: {result.message}"
        print("✓ Fix applied successfully")
        
        # Verify file was modified
        new_content = test_file.read_text()
        assert "is None" in new_content, "File should contain 'is None'"
        assert "== None" not in new_content, "File should not contain '== None'"
        print("✓ File modified correctly")
        
        # Verify backup was created
        backup_dir = tmpdir / "backups"
        assert backup_dir.exists(), "Backup directory should exist"
        backups = list(backup_dir.glob("*.backup"))
        assert len(backups) > 0, "Backup file should exist"
        print("✓ Backup created")
        
        # Test rollback
        count = applicator.rollback_all()
        assert count > 0, "Should rollback at least one file"
        
        rolled_back_content = test_file.read_text()
        assert rolled_back_content == original_content, "Content should be restored"
        print("✓ Rollback successful")
    
    print("\n✅ Fix applicator tests passed!")
    return True


def test_dry_run_mode():
    """Test dry run mode."""
    print("\n" + "="*80)
    print("TEST 4: Dry Run Mode")
    print("="*80)
    
    from reviewr.autofix import FixApplicator, Fix, FixCategory, FixStatus
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        test_file = tmpdir / "test.py"
        original_content = "if x == None:\n    pass\n"
        test_file.write_text(original_content)
        
        fix = Fix(
            fix_id="test456",
            category=FixCategory.CORRECTNESS,
            file_path=str(test_file),
            line_start=1,
            line_end=1,
            description="Use 'is None'",
            old_code="if x == None:",
            new_code="if x is None:",
            confidence=0.95,
            safe=True
        )
        
        # Apply in dry run mode
        applicator = FixApplicator(dry_run=True)
        result = applicator.apply_fix(fix)
        
        assert result.status == FixStatus.SUCCESS, "Dry run should succeed"
        print("✓ Dry run succeeded")
        
        # Verify file was NOT modified
        content = test_file.read_text()
        assert content == original_content, "File should not be modified in dry run"
        print("✓ File not modified in dry run")
        
        # Verify diff was generated
        assert result.diff is not None, "Diff should be generated"
        assert "is None" in result.diff, "Diff should show the change"
        print("✓ Diff generated correctly")
    
    print("\n✅ Dry run mode tests passed!")
    return True


def test_composite_generator():
    """Test composite fix generator."""
    print("\n" + "="*80)
    print("TEST 5: Composite Fix Generator")
    print("="*80)
    
    from reviewr.autofix import CompositeFixGenerator, PythonFixGenerator, JavaScriptFixGenerator
    
    composite = CompositeFixGenerator()
    composite.add_generator(PythonFixGenerator())
    composite.add_generator(JavaScriptFixGenerator())
    
    # Create mixed findings
    findings = [
        MockFinding(
            file_path="test.py",
            line_start=1,
            line_end=1,
            severity="low",
            message="Unused import: os"
        ),
        MockFinding(
            file_path="test.js",
            line_start=1,
            line_end=1,
            severity="low",
            message="Use const instead of var"
        ),
    ]
    
    file_contents = {
        "test.py": "import os\n",
        "test.js": "var x = 5;\n"
    }
    
    fixes = composite.generate_fixes(findings, file_contents)
    
    assert len(fixes) == 2, "Should generate 2 fixes"
    print(f"✓ Generated {len(fixes)} fixes from composite generator")
    
    # Verify Python fix
    python_fixes = [f for f in fixes if f.file_path == "test.py"]
    assert len(python_fixes) == 1, "Should have 1 Python fix"
    print("✓ Python fix generated")
    
    # Verify JavaScript fix
    js_fixes = [f for f in fixes if f.file_path == "test.js"]
    assert len(js_fixes) == 1, "Should have 1 JavaScript fix"
    print("✓ JavaScript fix generated")
    
    print("\n✅ Composite generator tests passed!")
    return True


def test_fix_filtering():
    """Test fix filtering by confidence and safety."""
    print("\n" + "="*80)
    print("TEST 6: Fix Filtering")
    print("="*80)
    
    from reviewr.autofix import Fix, FixCategory
    
    fixes = [
        Fix(
            fix_id="fix1",
            category=FixCategory.IMPORTS,
            file_path="test.py",
            line_start=1,
            line_end=1,
            description="Remove unused import",
            old_code="import os",
            new_code="",
            confidence=0.95,
            safe=True
        ),
        Fix(
            fix_id="fix2",
            category=FixCategory.SECURITY,
            file_path="test.py",
            line_start=5,
            line_end=5,
            description="Fix SQL injection",
            old_code="query = f'SELECT * FROM users WHERE id={user_id}'",
            new_code="query = 'SELECT * FROM users WHERE id=?'",
            confidence=0.70,
            safe=False
        ),
        Fix(
            fix_id="fix3",
            category=FixCategory.STYLE,
            file_path="test.py",
            line_start=10,
            line_end=10,
            description="Use f-string",
            old_code='"Hello %s" % name',
            new_code='f"Hello {name}"',
            confidence=0.85,
            safe=True
        ),
    ]
    
    # Filter by safety
    safe_fixes = [f for f in fixes if f.safe]
    assert len(safe_fixes) == 2, "Should have 2 safe fixes"
    print(f"✓ Filtered to {len(safe_fixes)} safe fixes")
    
    # Filter by confidence
    high_conf_fixes = [f for f in fixes if f.confidence >= 0.85]
    assert len(high_conf_fixes) == 2, "Should have 2 high-confidence fixes"
    print(f"✓ Filtered to {len(high_conf_fixes)} high-confidence fixes")
    
    # Filter by category
    import_fixes = [f for f in fixes if f.category == FixCategory.IMPORTS]
    assert len(import_fixes) == 1, "Should have 1 import fix"
    print(f"✓ Filtered to {len(import_fixes)} import fixes")
    
    print("\n✅ Fix filtering tests passed!")
    return True


def run_all_tests():
    """Run all auto-fix tests."""
    print("\n" + "="*80)
    print("🧪 RUNNING AUTO-FIX TESTS")
    print("="*80)
    
    tests = [
        ("Python Fix Generator", test_python_fix_generator),
        ("JavaScript Fix Generator", test_javascript_fix_generator),
        ("Fix Applicator", test_fix_applicator),
        ("Dry Run Mode", test_dry_run_mode),
        ("Composite Generator", test_composite_generator),
        ("Fix Filtering", test_fix_filtering),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for name, _ in tests:
        status = "✅ PASSED" if name in [t[0] for t in tests[:passed]] else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("="*80)
    print(f"TOTAL: {passed}/{len(tests)} tests passed ({passed/len(tests)*100:.1f}%)")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Auto-fix functionality is ready!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

