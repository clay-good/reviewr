"""Python-specific auto-fix generators."""

import re
import ast
from typing import Optional, Any

from .base import FixGenerator, Fix, FixCategory


class PythonFixGenerator(FixGenerator):
    """Generate fixes for Python code issues."""
    
    def __init__(self):
        """Initialize Python fix generator."""
        super().__init__("python")
        
        # Patterns for different fix types
        self.fix_patterns = {
            'unused_import': self._fix_unused_import,
            'f_string_conversion': self._fix_f_string_conversion,
            'is_comparison': self._fix_is_comparison,
            'exception_bare': self._fix_bare_except,
            'mutable_default': self._fix_mutable_default,
            'string_concatenation': self._fix_string_concatenation,
        }
    
    def can_fix(self, finding: Any) -> bool:
        """Check if we can fix this finding."""
        message = finding.message.lower()
        
        # Check for fixable patterns
        fixable_keywords = [
            'unused import',
            'missing type hint',
            'use f-string',
            'use is/is not',
            'bare except',
            'mutable default',
            'string concatenation in loop',
            'use pathlib',
            'use with statement',
        ]
        
        return any(keyword in message for keyword in fixable_keywords)
    
    def generate_fix(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Generate a fix for the finding."""
        message = finding.message.lower()

        # Try each fix pattern
        for pattern_name, fix_func in self.fix_patterns.items():
            if pattern_name.replace('_', ' ') in message:
                return fix_func(finding, file_content)

        # Try generic fixes based on message content
        if 'unused import' in message:
            return self._fix_unused_import(finding, file_content)
        elif 'f-string' in message or 'format string' in message:
            return self._fix_f_string_conversion(finding, file_content)
        elif 'is' in message and ('none' in message or 'comparison' in message or 'true' in message or 'false' in message):
            return self._fix_is_comparison(finding, file_content)
        elif 'bare except' in message:
            return self._fix_bare_except(finding, file_content)
        elif 'mutable default' in message:
            return self._fix_mutable_default(finding, file_content)
        elif 'string concatenation' in message:
            return self._fix_string_concatenation(finding, file_content)

        return None
    
    def _fix_unused_import(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Fix unused import by removing it."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Simply remove the import line
        new_code = ""
        
        return Fix(
            fix_id=self._generate_fix_id(finding),
            category=FixCategory.IMPORTS,
            file_path=finding.file_path,
            line_start=finding.line_start,
            line_end=finding.line_end,
            description="Remove unused import",
            old_code=old_code,
            new_code=new_code,
            confidence=0.95,
            safe=True,
            requires_validation=True,
            finding_message=finding.message,
            explanation="Removing unused imports improves code clarity and reduces namespace pollution."
        )
    
    def _fix_f_string_conversion(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert string formatting to f-strings."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Try to convert .format() to f-string
        # Pattern: "text {}".format(var) -> f"text {var}"
        format_pattern = r'"([^"]*)"\.format\((.*?)\)'
        match = re.search(format_pattern, old_code)
        
        if match:
            template = match.group(1)
            args = match.group(2)
            
            # Simple conversion for single argument
            if ',' not in args:
                new_code = old_code.replace(
                    match.group(0),
                    f'f"{template.replace("{}", "{" + args.strip() + "}")}"'
                )
                
                return Fix(
                    fix_id=self._generate_fix_id(finding),
                    category=FixCategory.STYLE,
                    file_path=finding.file_path,
                    line_start=finding.line_start,
                    line_end=finding.line_end,
                    description="Convert to f-string",
                    old_code=old_code,
                    new_code=new_code,
                    confidence=0.85,
                    safe=True,
                    requires_validation=True,
                    finding_message=finding.message,
                    explanation="F-strings are more readable and performant than .format()."
                )
        
        # Try to convert % formatting
        # Pattern: "text %s" % var -> f"text {var}"
        percent_pattern = r'"([^"]*%[sd])".*?%\s*(\w+)'
        match = re.search(percent_pattern, old_code)
        
        if match:
            template = match.group(1)
            var = match.group(2)
            
            new_template = template.replace('%s', f'{{{var}}}').replace('%d', f'{{{var}}}')
            new_code = old_code.replace(match.group(0), f'f"{new_template}"')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Convert % formatting to f-string",
                old_code=old_code,
                new_code=new_code,
                confidence=0.80,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="F-strings are more readable and performant than % formatting."
            )
        
        return None
    
    def _fix_is_comparison(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Fix == None to is None comparisons."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        new_code = old_code
        
        # Replace == None with is None
        if '== None' in old_code:
            new_code = old_code.replace('== None', 'is None')
        
        # Replace != None with is not None
        if '!= None' in old_code:
            new_code = old_code.replace('!= None', 'is not None')
        
        # Replace == True/False with is True/False
        if '== True' in old_code:
            new_code = old_code.replace('== True', 'is True')
        if '== False' in old_code:
            new_code = old_code.replace('== False', 'is False')
        
        if new_code != old_code:
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.CORRECTNESS,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Use 'is' for None/True/False comparisons",
                old_code=old_code,
                new_code=new_code,
                confidence=0.95,
                safe=True,
                requires_validation=False,
                finding_message=finding.message,
                explanation="Use 'is' for singleton comparisons (None, True, False) instead of '=='."
            )
        
        return None
    
    def _fix_bare_except(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Fix bare except clauses."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Replace 'except:' with 'except Exception:'
        if 'except:' in old_code:
            new_code = old_code.replace('except:', 'except Exception:')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.CORRECTNESS,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Replace bare except with except Exception",
                old_code=old_code,
                new_code=new_code,
                confidence=0.90,
                safe=True,
                requires_validation=False,
                finding_message=finding.message,
                explanation="Bare except catches SystemExit and KeyboardInterrupt, which is usually not intended."
            )
        
        return None
    
    def _fix_mutable_default(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Fix mutable default arguments."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Pattern: def func(arg=[]) -> def func(arg=None)
        # This is complex, so we'll provide a lower confidence fix
        
        if '=[]' in old_code or '={}' in old_code:
            # Replace with None and add initialization in function body
            new_code = old_code.replace('=[]', '=None').replace('={}', '=None')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.CORRECTNESS,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Replace mutable default argument with None",
                old_code=old_code,
                new_code=new_code,
                confidence=0.70,
                safe=False,  # Requires manual verification
                requires_validation=True,
                finding_message=finding.message,
                explanation="Mutable default arguments are shared between calls. Use None and initialize inside the function."
            )
        
        return None
    
    def _fix_string_concatenation(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Fix string concatenation in loops."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # This is a complex fix that requires understanding the loop context
        # We'll provide a suggestion rather than an automatic fix
        
        # Look for pattern: result += something
        if '+=' in old_code and 'str' in old_code.lower():
            # Suggest using join instead
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.PERFORMANCE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Use list and join() instead of string concatenation",
                old_code=old_code,
                new_code=old_code + "  # TODO: Use list.append() and ''.join(list)",
                confidence=0.60,
                safe=False,
                requires_validation=True,
                finding_message=finding.message,
                explanation="String concatenation in loops is O(n²). Use list.append() and ''.join() for O(n)."
            )
        
        return None

