"""AI-powered fix generator using LLMs."""

import asyncio
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

from .base import Fix, FixGenerator, FixCategory
from ..providers import ProviderFactory, ReviewType
from ..config import ReviewrConfig


class AIFixGenerator(FixGenerator):
    """Generate fixes using AI/LLM providers."""
    
    def __init__(
        self,
        language: str,
        provider_factory: ProviderFactory,
        config: ReviewrConfig,
        max_context_lines: int = 50
    ):
        """
        Initialize AI fix generator.

        Args:
            language: Programming language
            provider_factory: Factory for creating LLM providers
            config: Configuration object
            max_context_lines: Maximum lines of context to include
        """
        super().__init__(language)
        self.provider_factory = provider_factory
        self.config = config
        self.max_context_lines = max_context_lines
    
    def can_fix(self, finding: Any) -> bool:
        """
        Check if this generator can create a fix for the given finding.
        
        AI generator can attempt to fix any finding, but we filter by:
        - Confidence level
        - Severity (focus on high-impact issues)
        - Category (some categories are better suited for AI fixes)
        
        Args:
            finding: ReviewFinding or LocalFinding to check
            
        Returns:
            True if this generator should attempt to create a fix
        """
        # Check if finding has required attributes
        if not hasattr(finding, 'file_path') or not hasattr(finding, 'message'):
            return False
        
        # Check if finding has a suggestion (AI can enhance it)
        # or if it's a high-severity issue worth fixing
        severity = getattr(finding, 'severity', 'info').lower()
        
        # Prioritize critical, high, and medium severity issues
        if severity in ['critical', 'high', 'medium']:
            return True
        
        # Also fix if there's already a suggestion (we can improve it)
        if hasattr(finding, 'suggestion') and finding.suggestion:
            return True
        
        return False
    
    def generate_fix(self, finding: Any, file_content: str) -> Optional[Fix]:
        """
        Generate a fix for the given finding using AI.
        
        Args:
            finding: ReviewFinding or LocalFinding to fix
            file_content: Full content of the file
            
        Returns:
            Fix object if a fix can be generated, None otherwise
        """
        # Run async fix generation in sync context
        return asyncio.run(self._generate_fix_async(finding, file_content))
    
    async def _generate_fix_async(self, finding: Any, file_content: str) -> Optional[Fix]:
        """
        Async implementation of fix generation.
        
        Args:
            finding: ReviewFinding or LocalFinding to fix
            file_content: Full content of the file
            
        Returns:
            Fix object if a fix can be generated, None otherwise
        """
        try:
            # Extract context around the issue
            context = self._extract_context(
                file_content,
                finding.line_start,
                getattr(finding, 'line_end', finding.line_start)
            )
            
            # Build prompt for AI
            prompt = self._build_fix_prompt(finding, context, file_content)
            
            # Get AI provider
            provider_name = self.config.default_provider
            provider_config = self.config.providers.get(provider_name)
            if not provider_config:
                return None

            provider = self.provider_factory.create_provider(
                provider_name,
                provider_config.api_key,
                provider_config.model
            )
            
            # Request fix from AI
            response = await provider.review_code(
                code=prompt,
                file_path=finding.file_path,
                review_type=ReviewType.CORRECTNESS,
                context={"task": "generate_fix"}
            )
            
            # Parse AI response to extract fix
            fix = self._parse_fix_response(response, finding, file_content)
            
            return fix
            
        except Exception as e:
            # Log error but don't fail - just return None
            # Note: verbose mode would be passed separately if needed
            return None
    
    def _extract_context(self, content: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        Extract context around the issue location.
        
        Args:
            content: Full file content
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based)
            
        Returns:
            Dictionary with context information
        """
        lines = content.splitlines()
        
        # Calculate context window
        context_before = max(0, start_line - 1 - self.max_context_lines // 2)
        context_after = min(len(lines), end_line + self.max_context_lines // 2)
        
        # Extract lines
        before_lines = lines[context_before:start_line - 1]
        issue_lines = lines[start_line - 1:end_line]
        after_lines = lines[end_line:context_after]
        
        return {
            "before": "\n".join(before_lines),
            "issue": "\n".join(issue_lines),
            "after": "\n".join(after_lines),
            "start_line": start_line,
            "end_line": end_line,
            "context_start": context_before + 1,
            "context_end": context_after,
        }
    
    def _build_fix_prompt(self, finding: Any, context: Dict[str, Any], full_content: str) -> str:
        """
        Build a prompt for the AI to generate a fix.
        
        Args:
            finding: Finding to fix
            context: Context information
            full_content: Full file content
            
        Returns:
            Prompt string
        """
        # Get finding details
        severity = getattr(finding, 'severity', 'medium')
        category = getattr(finding, 'category', 'unknown')
        message = finding.message
        suggestion = getattr(finding, 'suggestion', '')
        
        prompt = f"""You are an expert code reviewer and fixer. Your task is to generate a precise code fix.

**Issue Details:**
- Severity: {severity}
- Category: {category}
- Message: {message}
{f"- Suggestion: {suggestion}" if suggestion else ""}

**Code Context:**
File: {finding.file_path}
Lines {context['start_line']}-{context['end_line']}

```{self.language}
{context['before']}
>>> ISSUE STARTS HERE <<<
{context['issue']}
>>> ISSUE ENDS HERE <<<
{context['after']}
```

**Instructions:**
1. Analyze the issue carefully
2. Generate a fix that:
   - Resolves the issue completely
   - Maintains code style and formatting
   - Preserves functionality
   - Follows best practices for {self.language}
3. Provide ONLY the fixed code for lines {context['start_line']}-{context['end_line']}
4. Do NOT include explanations, just the fixed code
5. Maintain exact indentation

**Response Format:**
Return a JSON object with:
{{
    "fixed_code": "the fixed code here",
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of the fix",
    "safe": true/false (whether this fix is safe to auto-apply)
}}

Generate the fix now:"""
        
        return prompt
    
    def _parse_fix_response(
        self,
        response: Any,
        finding: Any,
        file_content: str
    ) -> Optional[Fix]:
        """
        Parse AI response to extract fix information.
        
        Args:
            response: Response from AI provider
            finding: Original finding
            file_content: Full file content
            
        Returns:
            Fix object if parsing successful, None otherwise
        """
        try:
            # Extract response text
            if hasattr(response, 'findings') and response.findings:
                # Response is a ReviewResult with findings
                response_text = response.findings[0].message
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            # Try to parse as JSON
            # Look for JSON in the response (might be wrapped in markdown)
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                return None
            
            fix_data = json.loads(json_match.group(0))
            
            # Extract fix details
            fixed_code = fix_data.get('fixed_code', '').strip()
            confidence = float(fix_data.get('confidence', 0.7))
            explanation = fix_data.get('explanation', '')
            safe = fix_data.get('safe', False)
            
            if not fixed_code:
                return None
            
            # Extract old code
            old_code = self._extract_code_lines(
                file_content,
                finding.line_start,
                getattr(finding, 'line_end', finding.line_start)
            )
            
            # Determine category
            category = self._determine_category(finding)
            
            # Create Fix object
            fix = Fix(
                fix_id=self._generate_fix_id(finding),
                category=category,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=getattr(finding, 'line_end', finding.line_start),
                description=f"AI-generated fix: {finding.message}",
                old_code=old_code,
                new_code=fixed_code,
                confidence=confidence,
                safe=safe and confidence >= 0.8,  # Only mark as safe if high confidence
                requires_validation=True,  # Always validate AI-generated fixes
                finding_message=finding.message,
                explanation=explanation
            )
            
            return fix
            
        except Exception as e:
            # Log error but don't fail - just return None
            return None
    
    def _determine_category(self, finding: Any) -> FixCategory:
        """
        Determine fix category from finding.
        
        Args:
            finding: Finding to categorize
            
        Returns:
            FixCategory enum value
        """
        # Try to get category from finding
        if hasattr(finding, 'category'):
            category_str = finding.category.lower()
            
            # Map common categories
            category_map = {
                'security': FixCategory.SECURITY,
                'performance': FixCategory.PERFORMANCE,
                'correctness': FixCategory.CORRECTNESS,
                'style': FixCategory.STYLE,
                'formatting': FixCategory.FORMATTING,
                'imports': FixCategory.IMPORTS,
                'type': FixCategory.TYPE_HINTS,
                'documentation': FixCategory.DOCUMENTATION,
            }
            
            for key, value in category_map.items():
                if key in category_str:
                    return value
        
        # Default to correctness
        return FixCategory.CORRECTNESS

