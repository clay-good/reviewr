"""
Java Concurrency Analyzer

Detects concurrency issues in Java code including race conditions, deadlocks,
thread safety violations, and improper synchronization.
"""

import re
from typing import List
from .base import LocalAnalyzer, LocalFinding


class JavaConcurrencyAnalyzer(LocalAnalyzer):
    """Analyzes Java code for concurrency issues."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports the given language."""
        return language.lower() == 'java'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Analyze Java code for concurrency issues.
        
        Args:
            file_path: Path to the Java file
            content: File content
            
        Returns:
            List of findings
        """
        findings = []
        lines = content.split('\n')
        
        findings.extend(self._detect_race_conditions(content, file_path, lines))
        findings.extend(self._detect_double_checked_locking(content, file_path, lines))
        findings.extend(self._detect_synchronized_issues(content, file_path, lines))
        findings.extend(self._detect_volatile_misuse(content, file_path, lines))
        findings.extend(self._detect_thread_safety_issues(content, file_path, lines))
        findings.extend(self._detect_deadlock_potential(content, file_path, lines))
        findings.extend(self._detect_concurrent_collection_issues(content, file_path, lines))
        findings.extend(self._detect_executor_issues(content, file_path, lines))
        findings.extend(self._detect_atomic_issues(content, file_path, lines))
        
        return findings
    
    def _detect_race_conditions(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential race conditions."""
        findings = []
        
        # Unsynchronized access to shared mutable state
        # Pattern: field access without synchronization
        pattern = r'(private|protected|public)\s+(static\s+)?(?!final)[^;]*\s+(\w+)\s*;'
        
        for match in re.finditer(pattern, content):
            field_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if field is accessed in multiple methods without synchronization
            # Look for the field being used
            field_usage_pattern = rf'\b{field_name}\b\s*[=+\-*/]'
            usages = list(re.finditer(field_usage_pattern, content))
            
            if len(usages) > 1:
                # Check if any usage is in a method without synchronized
                context_start = max(0, match.start() - 500)
                context_end = min(len(content), match.end() + 1000)
                context = content[context_start:context_end]
                
                has_sync = 'synchronized' in context or 'volatile' in match.group(0)
                
                if not has_sync and 'static' in match.group(0):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='high',
                        category='concurrency',
                        message=f'Potential race condition: Shared mutable field "{field_name}" without synchronization',
                        suggestion='Use synchronized, volatile, or concurrent collections',
                        code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_double_checked_locking(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect broken double-checked locking pattern."""
        findings = []
        
        # Double-checked locking without volatile
        pattern = r'if\s*\([^)]*==\s*null\)\s*\{[^}]*synchronized[^}]*\{[^}]*if\s*\([^)]*==\s*null\)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if the field is volatile
            context_start = max(0, match.start() - 1000)
            context = content[context_start:match.start()]
            
            # Extract variable name
            var_match = re.search(r'if\s*\((\w+)\s*==\s*null\)', match.group())
            if var_match:
                var_name = var_match.group(1)
                
                # Check if variable is declared as volatile
                volatile_pattern = rf'volatile\s+[^;]*\b{var_name}\b'
                if not re.search(volatile_pattern, context):
                    findings.append(LocalFinding(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        severity='high',
                        category='concurrency',
                        message='Broken double-checked locking: Field must be volatile',
                        suggestion=f'Declare {var_name} as volatile or use initialization-on-demand holder idiom',
                        code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                    ))
        
        return findings
    
    def _detect_synchronized_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect synchronization issues."""
        findings = []
        
        # Synchronizing on String literal
        pattern = r'synchronized\s*\(\s*"[^"]*"\s*\)'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='concurrency',
                message='Synchronizing on String literal - can cause deadlock',
                suggestion='Synchronize on a private final Object lock instead',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Synchronizing on boxed primitive
        pattern = r'synchronized\s*\(\s*(Integer|Long|Boolean|Double|Float|Short|Byte|Character)\.'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='concurrency',
                message='Synchronizing on boxed primitive - can cause deadlock',
                suggestion='Use a dedicated lock object',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Empty synchronized block
        pattern = r'synchronized\s*\([^)]+\)\s*\{\s*\}'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='concurrency',
                message='Empty synchronized block - unnecessary overhead',
                suggestion='Remove empty synchronized block',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_volatile_misuse(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect volatile keyword misuse."""
        findings = []
        
        # volatile on non-atomic operations
        pattern = r'volatile\s+(?!boolean|int|long|float|double|char|byte|short)[^\s]+\s+(\w+)'
        
        for match in re.finditer(pattern, content):
            var_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for compound operations on this variable
            compound_pattern = rf'{var_name}\s*(\+\+|--|[\+\-\*/]=)'
            
            if re.search(compound_pattern, content):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='high',
                    category='concurrency',
                    message=f'Volatile variable "{var_name}" used in non-atomic operation',
                    suggestion='Use AtomicInteger/AtomicLong or synchronization for compound operations',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        # volatile array (only reference is volatile, not elements)
        pattern = r'volatile\s+\w+\[\]'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='concurrency',
                message='Volatile array: Only reference is volatile, not array elements',
                suggestion='Use AtomicReferenceArray or synchronization for array elements',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_thread_safety_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect thread safety issues."""
        findings = []
        
        # SimpleDateFormat in instance variable (not thread-safe)
        pattern = r'(private|protected|public)\s+(static\s+)?SimpleDateFormat'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='concurrency',
                message='SimpleDateFormat is not thread-safe',
                suggestion='Use ThreadLocal<SimpleDateFormat> or DateTimeFormatter (Java 8+)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # Calendar in instance variable (not thread-safe)
        pattern = r'(private|protected|public)\s+(static\s+)?Calendar'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='concurrency',
                message='Calendar is not thread-safe',
                suggestion='Use ThreadLocal<Calendar> or java.time API (Java 8+)',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings
    
    def _detect_deadlock_potential(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect potential deadlock situations."""
        findings = []
        
        # Nested synchronized blocks
        pattern = r'synchronized\s*\([^)]+\)\s*\{[^}]*synchronized\s*\([^)]+\)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='medium',
                category='concurrency',
                message='Nested synchronized blocks - potential deadlock',
                suggestion='Ensure consistent lock ordering or use java.util.concurrent locks',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        # wait() without loop
        pattern = r'\bwait\s*\('

        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            # Check if wait is in a loop
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start()]

            if 'while' not in context[-100:]:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='concurrency',
                    message='wait() should be called in a loop',
                    suggestion='Use while loop to check condition after waking up',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_concurrent_collection_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect issues with concurrent collections."""
        findings = []
        
        # Using non-concurrent collections in concurrent context
        pattern = r'(HashMap|ArrayList|HashSet|TreeMap|TreeSet|LinkedList)\s*<'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            collection_type = match.group(1)
            
            # Check if in a class with threading indicators
            context_start = max(0, match.start() - 2000)
            context = content[context_start:match.start()]
            
            threading_indicators = ['Thread', 'Runnable', 'ExecutorService', 'synchronized', 'volatile']
            
            if any(indicator in context for indicator in threading_indicators):
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='concurrency',
                    message=f'{collection_type} is not thread-safe',
                    suggestion=f'Use Concurrent{collection_type} or Collections.synchronized{collection_type}()',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_executor_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect ExecutorService issues."""
        findings = []
        
        # ExecutorService without shutdown
        pattern = r'ExecutorService\s+\w+\s*=\s*Executors\.'
        
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if shutdown is called
            context_end = min(len(content), match.end() + 2000)
            context = content[match.start():context_end]
            
            if 'shutdown()' not in context and 'shutdownNow()' not in context:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=line_num,
                    line_end=line_num,
                    severity='medium',
                    category='concurrency',
                    message='ExecutorService created without shutdown - resource leak',
                    suggestion='Call shutdown() or shutdownNow() when done, preferably in finally block',
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
                ))
        
        return findings
    
    def _detect_atomic_issues(self, content: str, file_path: str, lines: List[str]) -> List[LocalFinding]:
        """Detect issues with atomic operations."""
        findings = []
        
        # Check-then-act on AtomicInteger
        pattern = r'if\s*\(\s*(\w+)\.get\(\)[^)]*\)\s*\{[^}]*\1\.(set|incrementAndGet|decrementAndGet)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)
            
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                severity='high',
                category='concurrency',
                message=f'Check-then-act race condition on Atomic variable "{var_name}"',
                suggestion='Use compareAndSet() or other atomic methods',
                code_snippet=lines[line_num - 1] if line_num <= len(lines) else ''
            ))
        
        return findings

