"""
Rust Safety Analyzer

Detects safety issues in Rust code including unsafe blocks, panic patterns,
unwrap abuse, and memory safety concerns.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class RustSafetyAnalyzer(LocalAnalyzer):
    """Analyzes Rust code for safety issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'rust'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Rust code for safety issues.
        
        Args:
            file_path: Path to the Rust file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_unsafe_blocks(content, file_path, lines))
        findings.extend(self._detect_unwrap_abuse(content, file_path, lines))
        findings.extend(self._detect_expect_usage(content, file_path, lines))
        findings.extend(self._detect_panic_patterns(content, file_path, lines))
        findings.extend(self._detect_ffi_issues(content, file_path, lines))
        findings.extend(self._detect_transmute_usage(content, file_path, lines))
        findings.extend(self._detect_raw_pointer_deref(content, file_path, lines))
        findings.extend(self._detect_uninitialized_memory(content, file_path, lines))
        findings.extend(self._detect_index_without_bounds_check(content, file_path, lines))
        findings.extend(self._detect_todo_unimplemented(content, file_path, lines))
        
        return findings
    
    def _detect_unsafe_blocks(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect unsafe blocks and functions."""
        findings = []
        
        # Unsafe blocks
        for match in re.finditer(r'unsafe\s*\{', content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if there's a comment explaining why
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start()]
            has_safety_comment = 'SAFETY:' in context or 'Safety:' in context
            
            severity = 'medium' if has_safety_comment else 'high'
            message = 'Unsafe block detected'
            if not has_safety_comment:
                message += ' without SAFETY comment'
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=severity,
                category='safety',
                message=message,
                suggestion='Add // SAFETY: comment explaining why unsafe is needed and invariants maintained',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Unsafe functions
        for match in re.finditer(r'unsafe\s+fn\s+\w+', content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='safety',
                message='Unsafe function detected',
                suggestion='Document safety requirements in function documentation',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_unwrap_abuse(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect excessive use of .unwrap()."""
        findings = []
        
        # .unwrap() usage
        for match in re.finditer(r'\.unwrap\(\)', content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Lower severity in tests
            severity = 'low' if '#[test]' in content or 'mod tests' in content else 'medium'
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=severity,
                category='safety',
                message='Use of .unwrap() can cause panic',
                suggestion='Use pattern matching, if let, or ? operator for proper error handling',
                code_snippet=line_content
            ))
        
        # .unwrap_or_default() is better but still worth noting
        for match in re.finditer(r'\.unwrap_or_default\(\)', content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='info',
                category='safety',
                message='Use of .unwrap_or_default() - consider explicit default',
                suggestion='Consider using .unwrap_or(value) with explicit default for clarity',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_expect_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect .expect() usage."""
        findings = []
        
        for match in re.finditer(r'\.expect\([^)]+\)', content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # .expect() is better than .unwrap() but still can panic
            severity = 'low' if '#[test]' in content else 'medium'
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity=severity,
                category='safety',
                message='Use of .expect() can cause panic',
                suggestion='Use pattern matching or ? operator for recoverable errors',
                code_snippet=line_content
            ))
        
        return findings
    
    def _detect_panic_patterns(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect explicit panic calls."""
        findings = []
        
        panic_patterns = [
            (r'panic!\(', 'Explicit panic! macro'),
            (r'unreachable!\(', 'unreachable! macro (panics if reached)'),
            (r'assert!\(', 'assert! macro (panics on failure)'),
            (r'assert_eq!\(', 'assert_eq! macro (panics on failure)'),
            (r'assert_ne!\(', 'assert_ne! macro (panics on failure)'),
        ]
        
        for pattern, message in panic_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                
                # Lower severity in tests and debug builds
                in_test = '#[test]' in content or 'mod tests' in content
                in_debug = 'debug_assert' in line_content
                
                if in_test or in_debug:
                    severity = 'info'
                elif 'panic!' in pattern:
                    severity = 'high'
                else:
                    severity = 'medium'
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity=severity,
                    category='safety',
                    message=message,
                    suggestion='Consider returning Result<T, E> for recoverable errors',
                    code_snippet=line_content
                ))
        
        return findings
    
    def _detect_ffi_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect FFI (Foreign Function Interface) issues."""
        findings = []
        
        # extern "C" functions
        for match in re.finditer(r'extern\s+"C"\s+fn', content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='safety',
                message='FFI function detected - requires careful safety review',
                suggestion='Ensure proper error handling, null checks, and memory management',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # CString usage (common FFI pattern)
        for match in re.finditer(r'CString::', content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            if '.unwrap()' in line_content:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='safety',
                    message='CString::new().unwrap() can panic on null bytes',
                    suggestion='Handle NulError properly or use CString::new().expect() with clear message',
                    code_snippet=line_content
                ))
        
        return findings
    
    def _detect_transmute_usage(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect std::mem::transmute usage."""
        findings = []
        
        for match in re.finditer(r'transmute[:<]', content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='critical',
                category='safety',
                message='std::mem::transmute is extremely unsafe',
                suggestion='Use safer alternatives like From/Into traits, or document safety invariants',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_raw_pointer_deref(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect raw pointer dereferences."""
        findings = []
        
        # Pattern: *raw_ptr
        pattern = r'\*\s*\w+\s*as\s*\*(?:const|mut)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='safety',
                message='Raw pointer dereference detected',
                suggestion='Ensure pointer is valid, aligned, and properly initialized',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_uninitialized_memory(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect uninitialized memory usage."""
        findings = []
        
        patterns = [
            (r'MaybeUninit::uninit\(\)', 'Uninitialized memory - must be initialized before use'),
            (r'mem::uninitialized\(\)', 'Deprecated uninitialized() - use MaybeUninit instead'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='critical',
                    category='safety',
                    message=message,
                    suggestion='Ensure memory is properly initialized before reading',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_index_without_bounds_check(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect array/slice indexing without bounds checking."""
        findings = []
        
        # Pattern: array[index] without .get()
        pattern = r'\w+\[[\w\s+\-*/]+\]'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1] if line_num <= len(lines) else ''
            
            # Skip if it's in a test or has obvious bounds check nearby
            if '#[test]' in content or 'if' in line_content or 'assert' in line_content:
                continue
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='safety',
                message='Direct indexing can panic on out-of-bounds',
                suggestion='Use .get() for safe access or ensure bounds are checked',
                code_snippet=line_content
            ))
        
        return findings
    
    def _detect_todo_unimplemented(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect todo!() and unimplemented!() macros."""
        findings = []
        
        patterns = [
            (r'todo!\(', 'todo! macro - code not yet implemented (panics)'),
            (r'unimplemented!\(', 'unimplemented! macro - panics when called'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='safety',
                    message=message,
                    suggestion='Implement the functionality or return an error',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings

