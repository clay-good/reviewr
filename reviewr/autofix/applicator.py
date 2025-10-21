"""Fix applicator for safely applying code fixes."""

import os
import shutil
import difflib
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Callable
from datetime import datetime

from .base import Fix, FixResult, FixStatus


class FixApplicator:
    """Applies fixes to code files safely with backup and rollback support."""
    
    def __init__(
        self,
        backup_dir: Optional[str] = None,
        dry_run: bool = False,
        validate_syntax: bool = True,
        verbose: bool = False
    ):
        """
        Initialize fix applicator.
        
        Args:
            backup_dir: Directory to store backups (default: .reviewr_backups)
            dry_run: If True, don't actually apply fixes
            validate_syntax: If True, validate syntax after applying fixes
            verbose: If True, print detailed information
        """
        self.backup_dir = Path(backup_dir or ".reviewr_backups")
        self.dry_run = dry_run
        self.validate_syntax = validate_syntax
        self.verbose = verbose
        
        # Create backup directory if it doesn't exist
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_fix(self, fix: Fix) -> FixResult:
        """
        Apply a single fix to a file.
        
        Args:
            fix: Fix to apply
            
        Returns:
            FixResult with status and details
        """
        file_path = Path(fix.file_path)
        
        # Check if file exists
        if not file_path.exists():
            return FixResult(
                fix=fix,
                status=FixStatus.FAILED,
                message=f"File not found: {file_path}"
            )
        
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply the fix
            new_content = self._apply_fix_to_content(
                original_content,
                fix.line_start,
                fix.line_end,
                fix.old_code,
                fix.new_code
            )
            
            if new_content is None:
                return FixResult(
                    fix=fix,
                    status=FixStatus.FAILED,
                    message="Failed to apply fix: old code not found at specified location"
                )
            
            # Generate diff
            diff = self._generate_diff(
                original_content,
                new_content,
                str(file_path)
            )
            
            # Dry run - don't actually write
            if self.dry_run:
                return FixResult(
                    fix=fix,
                    status=FixStatus.SUCCESS,
                    message="Fix would be applied (dry run)",
                    diff=diff
                )
            
            # Create backup
            backup_path = self._create_backup(file_path, original_content)
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Validate syntax if requested
            validation_passed = True
            validation_errors = []
            
            if self.validate_syntax and fix.requires_validation:
                validation_passed, validation_errors = self._validate_syntax(
                    file_path,
                    self._get_language_from_path(file_path)
                )
                
                if not validation_passed:
                    # Rollback on validation failure
                    self._rollback(file_path, backup_path)
                    return FixResult(
                        fix=fix,
                        status=FixStatus.FAILED,
                        message="Fix caused syntax errors (rolled back)",
                        backup_path=str(backup_path),
                        validation_passed=False,
                        validation_errors=validation_errors,
                        diff=diff
                    )
            
            return FixResult(
                fix=fix,
                status=FixStatus.SUCCESS,
                message="Fix applied successfully",
                backup_path=str(backup_path),
                validation_passed=validation_passed,
                diff=diff
            )
            
        except Exception as e:
            return FixResult(
                fix=fix,
                status=FixStatus.FAILED,
                message=f"Error applying fix: {str(e)}"
            )
    
    def apply_fixes(
        self,
        fixes: List[Fix],
        interactive: bool = False,
        confirm_callback: Optional[Callable[[Fix], bool]] = None
    ) -> List[FixResult]:
        """
        Apply multiple fixes.
        
        Args:
            fixes: List of fixes to apply
            interactive: If True, ask for confirmation before each fix
            confirm_callback: Optional callback for confirmation (returns True to apply)
            
        Returns:
            List of FixResult objects
        """
        results = []
        
        # Group fixes by file to avoid conflicts
        fixes_by_file = self._group_fixes_by_file(fixes)
        
        for file_path, file_fixes in fixes_by_file.items():
            # Sort fixes by line number (reverse order to apply from bottom to top)
            file_fixes.sort(key=lambda f: f.line_start, reverse=True)
            
            for fix in file_fixes:
                # Interactive confirmation
                if interactive or confirm_callback:
                    if confirm_callback:
                        should_apply = confirm_callback(fix)
                    else:
                        should_apply = self._interactive_confirm(fix)
                    
                    if not should_apply:
                        results.append(FixResult(
                            fix=fix,
                            status=FixStatus.SKIPPED,
                            message="Skipped by user"
                        ))
                        continue
                
                # Apply the fix
                result = self.apply_fix(fix)
                results.append(result)
                
                if self.verbose:
                    self._print_result(result)
        
        return results
    
    def rollback_all(self, backup_dir: Optional[Path] = None) -> int:
        """
        Rollback all fixes by restoring from backups.

        Args:
            backup_dir: Directory containing backups (default: self.backup_dir)

        Returns:
            Number of files rolled back
        """
        backup_dir = Path(backup_dir) if backup_dir else self.backup_dir

        if not backup_dir.exists():
            return 0

        count = 0
        for backup_file in backup_dir.glob("*.backup"):
            # Read backup content
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_content = f.read()

            # Look for corresponding metadata file
            meta_file = backup_file.with_suffix('.meta')

            if meta_file.exists():
                # Read original path from metadata
                with open(meta_file, 'r', encoding='utf-8') as f:
                    original_path = Path(f.read().strip())

                if original_path.exists():
                    with open(original_path, 'w', encoding='utf-8') as f:
                        f.write(backup_content)
                    count += 1
            else:
                # Fallback: try to find the file
                original_name = backup_file.stem.rsplit('_', 1)[0]

                possible_paths = [
                    Path(original_name),
                    Path.cwd() / original_name,
                    backup_dir.parent / original_name,
                ]

                for original_path in possible_paths:
                    if original_path.exists():
                        with open(original_path, 'w', encoding='utf-8') as f:
                            f.write(backup_content)
                        count += 1
                        break

        return count
    
    def _apply_fix_to_content(
        self,
        content: str,
        line_start: int,
        line_end: int,
        old_code: str,
        new_code: str
    ) -> Optional[str]:
        """Apply fix to file content."""
        lines = content.splitlines(keepends=True)
        
        # Convert to 0-based indexing
        start_idx = line_start - 1
        end_idx = line_end
        
        # Validate indices
        if start_idx < 0 or end_idx > len(lines):
            return None
        
        # Extract the section to replace
        section = ''.join(lines[start_idx:end_idx])
        
        # Verify old code matches (with some flexibility for whitespace)
        if old_code.strip() not in section.strip():
            return None
        
        # Replace the section
        new_lines = lines[:start_idx] + [new_code + '\n'] + lines[end_idx:]
        
        return ''.join(new_lines)
    
    def _create_backup(self, file_path: Path, content: str) -> Path:
        """Create a backup of the file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        # Write backup content
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Write metadata file to track original path
        metadata_path = self.backup_dir / f"{file_path.name}_{timestamp}.meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(str(file_path.absolute()))

        return backup_path
    
    def _rollback(self, file_path: Path, backup_path: Path):
        """Rollback a file from backup."""
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
    
    def _generate_diff(self, old_content: str, new_content: str, filename: str) -> str:
        """Generate unified diff."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def _validate_syntax(self, file_path: Path, language: str) -> tuple[bool, List[str]]:
        """Validate syntax of the file."""
        errors = []
        
        try:
            if language == "python":
                # Use Python's compile to check syntax
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(file_path), 'exec')
            
            elif language in ["javascript", "typescript"]:
                # Use node to check syntax
                result = subprocess.run(
                    ['node', '--check', str(file_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    errors.append(result.stderr)
            
            # Add more language validators as needed
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
        
        return len(errors) == 0, errors
    
    def _get_language_from_path(self, file_path: Path) -> str:
        """Get language from file extension."""
        ext = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
        }
        
        return language_map.get(ext, 'unknown')
    
    def _group_fixes_by_file(self, fixes: List[Fix]) -> Dict[str, List[Fix]]:
        """Group fixes by file path."""
        by_file: Dict[str, List[Fix]] = {}
        
        for fix in fixes:
            if fix.file_path not in by_file:
                by_file[fix.file_path] = []
            by_file[fix.file_path].append(fix)
        
        return by_file
    
    def _interactive_confirm(self, fix: Fix) -> bool:
        """Ask user for confirmation."""
        print(f"\n{'='*80}")
        print(f"Fix: {fix.description}")
        print(f"File: {fix.file_path} (lines {fix.line_start}-{fix.line_end})")
        print(f"Category: {fix.category.value}")
        print(f"Confidence: {fix.confidence:.0%}")
        print(f"\nOld code:\n{fix.old_code}")
        print(f"\nNew code:\n{fix.new_code}")
        
        if fix.explanation:
            print(f"\nExplanation: {fix.explanation}")
        
        response = input("\nApply this fix? [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    
    def _print_result(self, result: FixResult):
        """Print fix result."""
        status_emoji = {
            FixStatus.SUCCESS: "✅",
            FixStatus.FAILED: "❌",
            FixStatus.SKIPPED: "⏭️",
            FixStatus.PARTIAL: "⚠️"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        print(f"{emoji} {result.fix.description}: {result.message}")

