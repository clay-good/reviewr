"""
Rust Ownership Analyzer

Detects ownership, borrowing, and lifetime issues in Rust code.
This analyzer focuses on Rust's unique ownership system.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class RustOwnershipAnalyzer(LocalAnalyzer):
    """Analyzes Rust code for ownership and borrowing issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'rust'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Rust code for ownership issues.
        
        Args:
            file_path: Path to the Rust file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_move_after_move(content, file_path, lines))
        findings.extend(self._detect_borrow_after_move(content, file_path, lines))
        findings.extend(self._detect_multiple_mutable_borrows(content, file_path, lines))
        findings.extend(self._detect_mutable_and_immutable_borrow(content, file_path, lines))
        findings.extend(self._detect_dangling_references(content, file_path, lines))
        findings.extend(self._detect_lifetime_issues(content, file_path, lines))
        findings.extend(self._detect_clone_on_copy(content, file_path, lines))
        findings.extend(self._detect_unnecessary_clone(content, file_path, lines))
        findings.extend(self._detect_rc_refcell_patterns(content, file_path, lines))
        
        return findings
    
    def _detect_move_after_move(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential use after move."""
        findings = []
        
        # Pattern: variable used after being moved
        # This is a heuristic - actual borrow checker is more sophisticated
        move_patterns = [
            (r'let\s+\w+\s*=\s*(\w+);.*\n.*\1\.', 'Variable potentially used after move'),
            (r'(\w+)\.into\(\).*\n.*\1\.', 'Variable used after .into() (move)'),
            (r'consume\((\w+)\).*\n.*\1\.', 'Variable used after being consumed'),
        ]
        
        for pattern, message in move_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='ownership',
                    message=f'Potential move violation: {message}',
                    suggestion='Use borrowing (&) or clone the value if needed',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_borrow_after_move(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect borrowing after move."""
        findings = []
        
        # Pattern: trying to borrow after move
        patterns = [
            r'let\s+\w+\s*=\s*(\w+);\s*\n\s*let\s+\w+\s*=\s*&\1',
            r'(\w+)\.into\(\);\s*\n\s*&\1',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num + 1,
                    severity='critical',
                    category='ownership',
                    message='Attempting to borrow after move',
                    suggestion='Borrow before moving, or use Rc/Arc for shared ownership',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_multiple_mutable_borrows(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect multiple mutable borrows."""
        findings = []
        
        # Pattern: multiple &mut borrows in same scope
        pattern = r'let\s+\w+\s*=\s*&mut\s+(\w+);\s*\n\s*let\s+\w+\s*=\s*&mut\s+\1'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num + 1,
                severity='critical',
                category='ownership',
                message='Multiple mutable borrows of the same variable',
                suggestion='Only one mutable borrow is allowed at a time. Use scopes to limit borrow lifetime',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_mutable_and_immutable_borrow(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect simultaneous mutable and immutable borrows."""
        findings = []
        
        # Pattern: immutable and mutable borrow in same scope
        pattern = r'let\s+\w+\s*=\s*&(\w+);\s*\n\s*let\s+\w+\s*=\s*&mut\s+\1'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num + 1,
                severity='critical',
                category='ownership',
                message='Mutable borrow while immutable borrow exists',
                suggestion='Cannot have mutable and immutable borrows simultaneously. Use scopes or refactor',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_dangling_references(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential dangling references."""
        findings = []
        
        # Pattern: returning reference to local variable
        patterns = [
            (r'fn\s+\w+.*->\s*&.*\{[^}]*let\s+(\w+)\s*=.*\n[^}]*&\1', 'Returning reference to local variable'),
            (r'&\w+\s*\{[^}]*let\s+(\w+)\s*=.*\n[^}]*\1', 'Reference to temporary value'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='ownership',
                    message=f'Potential dangling reference: {message}',
                    suggestion='Return owned value (String, Vec, etc.) or use lifetime parameters',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_lifetime_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect lifetime annotation issues."""
        findings = []
        
        # Pattern: functions with references but no lifetime annotations
        pattern = r"fn\s+\w+\s*\([^)]*&[^')]*\)\s*->\s*&[^'{\n]*\{"
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Check if lifetime is missing
            if "'" not in line_content or '<' not in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='ownership',
                    message='Function with references may need explicit lifetime annotations',
                    suggestion="Add lifetime parameters: fn foo<'a>(x: &'a str) -> &'a str",
                    code_snippet=line_content
                ))
        
        return findings
    
    def _detect_clone_on_copy(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unnecessary .clone() on Copy types."""
        findings = []
        
        # Pattern: .clone() on primitive types
        copy_types = ['i8', 'i16', 'i32', 'i64', 'i128', 'isize',
                      'u8', 'u16', 'u32', 'u64', 'u128', 'usize',
                      'f32', 'f64', 'bool', 'char']
        
        for copy_type in copy_types:
            pattern = rf':\s*{copy_type}\s*=.*\.clone\(\)'
            
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='ownership',
                    message=f'Unnecessary .clone() on Copy type {copy_type}',
                    suggestion=f'{copy_type} implements Copy, use simple assignment instead',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_unnecessary_clone(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potentially unnecessary clones."""
        findings = []
        
        # Pattern: clone() when value is only used once
        pattern = r'let\s+(\w+)\s*=\s*(\w+)\.clone\(\);\s*\n[^}]*\1\s*[;\)]'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='ownership',
                message='Potentially unnecessary clone: value used only once',
                suggestion='Consider borrowing (&) or moving the original value',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_rc_refcell_patterns(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect Rc/RefCell usage patterns."""
        findings = []
        
        # Pattern: Rc<RefCell<T>> - common but can indicate design issues
        pattern = r'Rc<RefCell<'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='ownership',
                message='Rc<RefCell<T>> pattern detected',
                suggestion='Consider if design can be simplified. This pattern has runtime overhead',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Pattern: Arc<Mutex<T>> in single-threaded context
        pattern = r'Arc<Mutex<'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Check if in async context
            if 'async' not in line_content and 'thread' not in content[max(0, match.start() - 500):match.start()]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='low',
                    category='ownership',
                    message='Arc<Mutex<T>> in potentially single-threaded context',
                    suggestion='Use Rc<RefCell<T>> for single-threaded or consider redesign',
                    code_snippet=line_content
                ))
        
        return findings

