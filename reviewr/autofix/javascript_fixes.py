"""JavaScript/TypeScript-specific auto-fix generators."""

import re
from typing import Optional, Any

from .base import FixGenerator, Fix, FixCategory


class JavaScriptFixGenerator(FixGenerator):
    """Generate fixes for JavaScript/TypeScript code issues."""
    
    def __init__(self):
        """Initialize JavaScript fix generator."""
        super().__init__("javascript")
        
        self.fix_patterns = {
            'var_to_const': self._fix_var_to_const,
            'var_to_let': self._fix_var_to_let,
            'arrow_function': self._fix_arrow_function,
            'template_literal': self._fix_template_literal,
            'strict_equality': self._fix_strict_equality,
            'optional_chaining': self._fix_optional_chaining,
            'nullish_coalescing': self._fix_nullish_coalescing,
        }
    
    def can_fix(self, finding: Any) -> bool:
        """Check if we can fix this finding."""
        message = finding.message.lower()
        
        fixable_keywords = [
            'use const',
            'use let',
            'var declaration',
            'arrow function',
            'template literal',
            'use ===',
            'strict equality',
            'optional chaining',
            'nullish coalescing',
            'use async/await',
        ]
        
        return any(keyword in message for keyword in fixable_keywords)
    
    def generate_fix(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Generate a fix for the finding."""
        message = finding.message.lower()
        
        # Try each fix pattern
        if 'const' in message or 'var' in message:
            return self._fix_var_to_const(finding, file_content)
        elif 'let' in message:
            return self._fix_var_to_let(finding, file_content)
        elif 'arrow function' in message:
            return self._fix_arrow_function(finding, file_content)
        elif 'template literal' in message or 'template string' in message:
            return self._fix_template_literal(finding, file_content)
        elif '===' in message or 'strict equality' in message:
            return self._fix_strict_equality(finding, file_content)
        elif 'optional chaining' in message:
            return self._fix_optional_chaining(finding, file_content)
        elif 'nullish coalescing' in message:
            return self._fix_nullish_coalescing(finding, file_content)
        
        return None
    
    def _fix_var_to_const(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert var to const."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        if 'var ' in old_code:
            new_code = old_code.replace('var ', 'const ')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Replace var with const",
                old_code=old_code,
                new_code=new_code,
                confidence=0.90,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="Use const for variables that are never reassigned. It prevents accidental reassignment."
            )
        
        return None
    
    def _fix_var_to_let(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert var to let."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        if 'var ' in old_code:
            new_code = old_code.replace('var ', 'let ')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Replace var with let",
                old_code=old_code,
                new_code=new_code,
                confidence=0.95,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="Use let instead of var for block-scoped variables."
            )
        
        return None
    
    def _fix_arrow_function(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert function expression to arrow function."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Pattern: function(args) { body } -> (args) => { body }
        pattern = r'function\s*\(([^)]*)\)\s*\{([^}]*)\}'
        match = re.search(pattern, old_code)
        
        if match:
            args = match.group(1)
            body = match.group(2).strip()
            
            # Simple single-expression body
            if '\n' not in body and 'return' in body:
                body = body.replace('return', '').strip().rstrip(';')
                new_code = old_code.replace(match.group(0), f'({args}) => {body}')
            else:
                new_code = old_code.replace(match.group(0), f'({args}) => {{{match.group(2)}}}')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Convert to arrow function",
                old_code=old_code,
                new_code=new_code,
                confidence=0.80,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="Arrow functions are more concise and have lexical 'this' binding."
            )
        
        return None
    
    def _fix_template_literal(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert string concatenation to template literals."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Pattern: "text" + var + "more" -> `text${var}more`
        # Simple case: single concatenation
        pattern = r'"([^"]*)"[\s]*\+[\s]*(\w+)[\s]*\+[\s]*"([^"]*)"'
        match = re.search(pattern, old_code)
        
        if match:
            before = match.group(1)
            var = match.group(2)
            after = match.group(3)
            
            new_code = old_code.replace(match.group(0), f'`{before}${{{var}}}{after}`')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Convert to template literal",
                old_code=old_code,
                new_code=new_code,
                confidence=0.85,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="Template literals are more readable than string concatenation."
            )
        
        return None
    
    def _fix_strict_equality(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert == to ===."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        new_code = old_code
        
        # Replace == with === (but not ===)
        if ' == ' in old_code and ' === ' not in old_code:
            new_code = old_code.replace(' == ', ' === ')
        
        # Replace != with !==
        if ' != ' in old_code and ' !== ' not in old_code:
            new_code = new_code.replace(' != ', ' !== ')
        
        if new_code != old_code:
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.CORRECTNESS,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Use strict equality (===)",
                old_code=old_code,
                new_code=new_code,
                confidence=0.95,
                safe=True,
                requires_validation=False,
                finding_message=finding.message,
                explanation="Use === and !== to avoid type coercion bugs."
            )
        
        return None
    
    def _fix_optional_chaining(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert null checks to optional chaining."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Pattern: obj && obj.prop -> obj?.prop
        pattern = r'(\w+)\s*&&\s*\1\.(\w+)'
        match = re.search(pattern, old_code)
        
        if match:
            obj = match.group(1)
            prop = match.group(2)
            
            new_code = old_code.replace(match.group(0), f'{obj}?.{prop}')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.STYLE,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Use optional chaining (?.)",
                old_code=old_code,
                new_code=new_code,
                confidence=0.90,
                safe=True,
                requires_validation=True,
                finding_message=finding.message,
                explanation="Optional chaining (?.) is more concise and readable than && checks."
            )
        
        return None
    
    def _fix_nullish_coalescing(self, finding: Any, file_content: str) -> Optional[Fix]:
        """Convert || to ?? for default values."""
        old_code = self._extract_code_lines(
            file_content,
            finding.line_start,
            finding.line_end
        )
        
        # Pattern: value || default -> value ?? default
        # Only when it's clear we want null/undefined check, not falsy check
        if ' || ' in old_code and ('null' in old_code.lower() or 'undefined' in old_code.lower()):
            new_code = old_code.replace(' || ', ' ?? ')
            
            return Fix(
                fix_id=self._generate_fix_id(finding),
                category=FixCategory.CORRECTNESS,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                description="Use nullish coalescing (??)",
                old_code=old_code,
                new_code=new_code,
                confidence=0.75,
                safe=False,  # Behavior differs from ||
                requires_validation=True,
                finding_message=finding.message,
                explanation="Use ?? for null/undefined checks. Unlike ||, it doesn't treat 0, '', false as falsy."
            )
        
        return None

