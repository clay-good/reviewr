import json
import asyncio
from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import LLMProvider, CodeChunk, ReviewType, ReviewFinding

try:
    from ..security import get_security_prompt_context
    SECURITY_CONTEXT_AVAILABLE = True
except ImportError:
    SECURITY_CONTEXT_AVAILABLE = False


class ClaudeProvider(LLMProvider):
    """Claude/Anthropic LLM provider."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514",
                 max_tokens: int = 8192, temperature: float = 0.0, timeout: int = 60):
        """Initialize Claude provider."""
        super().__init__(api_key, model, max_tokens, temperature, timeout)
        # Use x-api-key header as per Anthropic API
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)

        # Model context sizes
        self._context_sizes = {
            "claude-sonnet-4-20250514": 200000,
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def review_code(
        self,
        chunk: CodeChunk,
        review_types: List[ReviewType],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[ReviewFinding]:
        """Review code using Claude."""
        prompt = self._build_claude_prompt(chunk, review_types)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="You are an expert code reviewer. Analyze code carefully and provide specific, actionable feedback. Return your findings as a JSON array."
            )
            
            # Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self._track_usage(input_tokens, output_tokens)
            
            # Parse response
            content = response.content[0].text
            findings = self._parse_response(content, chunk)
            
            return findings
            
        except Exception as e:
            print(f"Error reviewing code with Claude: {e}")
            raise
    
    def _build_claude_prompt(self, chunk: CodeChunk, review_types: List[ReviewType]) -> str:
        """Build Claude-specific prompt with XML tags."""
        # Check if this is an explain-only request
        if len(review_types) == 1 and review_types[0] == ReviewType.EXPLAIN:
            return self._build_claude_explain_prompt(chunk)

        # Use comprehensive security context if security review is requested
        if ReviewType.SECURITY in review_types and SECURITY_CONTEXT_AVAILABLE:
            return self._build_claude_security_prompt(chunk, review_types)

        review_types_str = ', '.join(rt.value for rt in review_types)

        prompt = f"""<task>
Review the following {chunk.language} code for {review_types_str} issues.
</task>

<code_context>
File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}
Language: {chunk.language}
</code_context>

<code>
{chunk.content}
</code>
"""

        if chunk.context:
            prompt += f"\n<surrounding_context>\n{chunk.context}\n</surrounding_context>\n"

        prompt += f"""
<instructions>
1. Identify CRITICAL and HIGH severity issues in the code related to: {review_types_str}
2. For SECURITY issues, provide comprehensive analysis:
   - Vulnerability type with CWE/CVE reference if applicable
   - Exploitation scenario showing how an attacker could abuse this
   - Real-world impact (data breach, RCE, privilege escalation, etc.)
   - MULTIPLE fix options (2-3 different approaches) with:
     * Option 1 - Quick Fix: Immediate mitigation with code snippet (pros/cons)
     * Option 2 - Secure Fix: More comprehensive solution with code snippet (pros/cons)
     * Option 3 - Best Practice: Industry-standard approach with code snippet (pros/cons)
   - Recommended option with clear justification
   - Confidence score (0.9-1.0 for critical security issues)

3. For NON-SECURITY issues provide:
   - Type: one of [{', '.join(rt.value for rt in review_types)}]
   - Severity: critical, high, medium, low, or info
   - Line numbers where the issue occurs (relative to lines {chunk.start_line}-{chunk.end_line})
   - Clear explanation of the problem
   - 2-3 different fix approaches with code snippets and tradeoffs
   - Recommended approach
   - Confidence score (0.0-1.0)

4. Format response as JSON array of findings
5. ONLY report critical/high severity issues - ignore minor style or low-impact items
6. Consider the context and {chunk.language}-specific best practices
7. Be specific and actionable with concrete code examples
</instructions>

<response_format>
Return ONLY a valid JSON array (no markdown, no explanation):
[
  {{
    "type": "security|performance|correctness|maintainability|architecture|standards",
    "severity": "critical|high|medium|low|info",
    "line_start": number,
    "line_end": number,
    "message": "Clear description of the issue",
    "suggestion": "How to fix it",
    "confidence": 0.0-1.0
  }}
]

If no issues are found, return: []
</response_format>
"""
        return prompt

    def _build_claude_explain_prompt(self, chunk: CodeChunk) -> str:
        """Build Claude-specific explanation prompt."""
        prompt = f"""<task>
Provide a comprehensive explanation of the following {chunk.language} code to help a developer understand it quickly.
</task>

<code_context>
File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}
Language: {chunk.language}
</code_context>

<code>
{chunk.content}
</code>
"""

        if chunk.context:
            prompt += f"\n<surrounding_context>\n{chunk.context}\n</surrounding_context>\n"

        prompt += f"""
<instructions>
Provide a comprehensive explanation as a single finding that covers:

1. **Overview**: What does this code do? What is its main purpose?
2. **Key Components**: What are the main classes, functions, variables, or data structures?
3. **Logic Flow**: How does the code work? What are the main execution paths?
4. **Patterns & Conventions**: What design patterns, idioms, or conventions are used?
5. **Dependencies**: What external libraries, modules, or APIs does it use?
6. **Entry Points**: What are the main functions/methods that would be called by other code?
7. **Notable Details**: Any important edge cases, optimizations, or gotchas?

Be thorough but concise. Write in clear, accessible language. Focus on helping someone understand the code quickly.
</instructions>

<response_format>
Return ONLY a valid JSON array with a single finding (no markdown, no explanation):
[
  {{
    "type": "explain",
    "severity": "info",
    "line_start": {chunk.start_line},
    "line_end": {chunk.end_line},
    "message": "Your comprehensive explanation here, covering all the points above in a well-structured narrative",
    "suggestion": "Additional context, recommendations for further reading, or tips for working with this code",
    "confidence": 1.0
  }}
]
</response_format>
"""
        return prompt
    
    def _parse_response(self, content: str, chunk: CodeChunk) -> List[ReviewFinding]:
        """Parse Claude's response into ReviewFinding objects."""
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            findings_data = json.loads(content)
            
            if not isinstance(findings_data, list):
                print(f"Warning: Expected list, got {type(findings_data)}")
                return []
            
            findings = []
            for item in findings_data:
                try:
                    # Map type string to ReviewType enum
                    review_type = ReviewType(item["type"])
                    
                    finding = ReviewFinding(
                        type=review_type,
                        severity=item["severity"],
                        file_path=chunk.file_path,
                        line_start=item["line_start"],
                        line_end=item["line_end"],
                        message=item["message"],
                        suggestion=item.get("suggestion"),
                        code_snippet=None,  # Will be filled by orchestrator
                        confidence=item.get("confidence", 1.0),
                    )
                    findings.append(finding)
                except (KeyError, ValueError) as e:
                    print(f"Warning: Skipping invalid finding: {e}")
                    continue
            
            return findings
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response content: {content[:500]}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using Claude's approximation (roughly 4 chars per token)."""
        return len(text) // 4
    
    def get_max_context_size(self) -> int:
        """Get maximum context size for the current model."""
        return self._context_sizes.get(self.model, 200000)

    def _build_claude_security_prompt(self, chunk: CodeChunk, review_types: List[ReviewType]) -> str:
        """Build Claude-specific security-focused prompt with comprehensive vulnerability detection."""
        security_context = get_security_prompt_context()

        prompt = f"""<security_audit_protocol>
{security_context}
</security_audit_protocol>

<code_under_review>
<file_path>{chunk.file_path}</file_path>
<line_range>{chunk.start_line}-{chunk.end_line}</line_range>
<language>{chunk.language}</language>

<code>
{chunk.content}
</code>
"""

        if chunk.context:
            prompt += f"""
<surrounding_context>
{chunk.context}
</surrounding_context>
"""

        prompt += """
</code_under_review>

<task>
You are a CRITICAL SECURITY AUDITOR analyzing code for exploitable vulnerabilities.

SYSTEMATICALLY CHECK FOR:
1. Injection flaws (SQL, Command, XSS, LDAP, XXE)
2. Authentication & access control issues
3. Cryptographic failures
4. Code execution risks
5. Path traversal vulnerabilities
6. SSRF vulnerabilities
7. Race conditions

For EACH critical/high severity vulnerability found:
- Identify CWE/CVE
- Explain exploitation scenario
- Assess real-world impact
- Provide 2-3 fix options with code examples
- Include pros/cons for each option
- Recommend best approach
</task>

<response_format>
Return ONLY valid JSON array (no markdown wrapping):
[
  {
    "type": "security",
    "severity": "critical|high",
    "line_start": <number>,
    "line_end": <number>,
    "message": "CWE-XXX: [Name]\\n\\nDETAILS:\\n[description]\\n\\nEXPLOITATION:\\n[how to exploit]\\n\\nIMPACT:\\n[consequences]",
    "suggestion": "OPTION 1 - Quick Fix:\\n```\\n[code]\\n```\\n✅ PROS: [list]\\n❌ CONS: [list]\\n⏱️ Time: [estimate]\\n\\nOPTION 2 - Secure Fix:\\n```\\n[code]\\n```\\n✅ PROS: [list]\\n❌ CONS: [list]\\n⏱️ Time: [estimate]\\n\\nOPTION 3 - Best Practice:\\n```\\n[code]\\n```\\n✅ PROS: [list]\\n❌ CONS: [list]\\n⏱️ Time: [estimate]\\n\\nRECOMMENDATION: [which and why]",
    "confidence": <0.9-1.0>
  }
]

Return [] if no critical/high issues found.
</response_format>
"""
        return prompt

