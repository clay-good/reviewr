import json
import asyncio
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from .base import LLMProvider, CodeChunk, ReviewType, ReviewFinding

try:
    from ..security import get_security_prompt_context
    SECURITY_CONTEXT_AVAILABLE = True
except ImportError:
    SECURITY_CONTEXT_AVAILABLE = False


class AugmentCodeProvider(LLMProvider):
    """Augment Code LLM provider."""

    def __init__(self, api_key: str, model: str = "augment-code-1",
                 max_tokens: int = 8192, temperature: float = 0.0, timeout: int = 60):
        """Initialize Augment Code provider."""
        super().__init__(api_key, model, max_tokens, temperature, timeout)
        self.base_url = "https://api.augmentcode.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )

        # Model context sizes
        self._context_sizes = {
            "augment-code-1": 200000,
            "augment-code-2": 200000,
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
        """Review code using Augment Code."""
        prompt = self._build_augmentcode_prompt(chunk, review_types)

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert code security reviewer specializing in identifying critical security vulnerabilities. Provide specific, actionable feedback with multiple solution options and clear tradeoffs."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )

            response.raise_for_status()
            data = response.json()

            # Track usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            self._track_usage(input_tokens, output_tokens)

            # Parse response
            content = data["choices"][0]["message"]["content"]
            findings = self._parse_response(content, chunk)

            return findings

        except Exception as e:
            print(f"Error reviewing code with Augment Code: {e}")
            raise

    def _build_augmentcode_prompt(self, chunk: CodeChunk, review_types: List[ReviewType]) -> str:
        """Build Augment Code-specific prompt focused on critical security issues."""
        # Check if this is an explain-only request
        if len(review_types) == 1 and review_types[0] == ReviewType.EXPLAIN:
            return self._build_augmentcode_explain_prompt(chunk)

        # Use comprehensive security context if security review is requested
        if ReviewType.SECURITY in review_types and SECURITY_CONTEXT_AVAILABLE:
            security_context = get_security_prompt_context()
            return self._build_augmentcode_security_prompt(chunk, review_types, security_context)

        review_types_str = ', '.join(rt.value for rt in review_types)

        prompt = f"""CRITICAL SECURITY CODE REVIEW

File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}
Language: {chunk.language}
Review Types: {review_types_str}

CODE TO REVIEW:
```{chunk.language}
{chunk.content}
```
"""

        if chunk.context:
            prompt += f"\nSURROUNDING CONTEXT:\n```{chunk.language}\n{chunk.context}\n```\n"

        prompt += f"""
INSTRUCTIONS:
Focus ONLY on critical and high-severity security issues that could lead to:
- Data breaches or unauthorized access
- Code injection vulnerabilities (SQL, XSS, Command, etc.)
- Authentication/authorization bypasses
- Sensitive data exposure
- Remote code execution
- Cryptographic failures

For each critical issue found:
1. Identify the specific vulnerability type and CWE/CVE if applicable
2. Explain the exploitation scenario and potential impact
3. Provide AT LEAST 2-3 different fix approaches with TRADEOFFS:
   - Quick fix: Immediate solution (pros/cons)
   - Secure fix: More comprehensive approach (pros/cons)
   - Best practice: Industry-standard solution (pros/cons)
4. Include concrete code snippets for EACH solution
5. Rate confidence (0.9-1.0 for critical security issues)

RESPONSE FORMAT (JSON array):
[
  {{
    "type": "security|performance|correctness|maintainability|architecture|standards",
    "severity": "critical|high",
    "line_start": number,
    "line_end": number,
    "message": "Clear vulnerability description with exploitation scenario and impact",
    "suggestion": "Multiple fix options with tradeoffs:\n\nOPTION 1 - Quick Fix:\nCode: [snippet]\nPros: [benefits]\nCons: [drawbacks]\n\nOPTION 2 - Secure Fix:\nCode: [snippet]\nPros: [benefits]\nCons: [drawbacks]\n\nOPTION 3 - Best Practice:\nCode: [snippet]\nPros: [benefits]\nCons: [drawbacks]\n\nRECOMMENDATION: [which option and why]",
    "confidence": 0.9-1.0
  }}
]

IMPORTANT: Only report critical/high severity issues. Ignore minor style or low-impact items.
If no critical/high issues found, return: []
"""
        return prompt

    def _build_augmentcode_explain_prompt(self, chunk: CodeChunk) -> str:
        """Build Augment Code-specific explanation prompt."""
        prompt = f"""COMPREHENSIVE CODE EXPLANATION

File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}
Language: {chunk.language}

CODE TO EXPLAIN:
```{chunk.language}
{chunk.content}
```
"""

        if chunk.context:
            prompt += f"\nSURROUNDING CONTEXT:\n```{chunk.language}\n{chunk.context}\n```\n"

        prompt += f"""
Provide a detailed technical explanation covering:

1. **Purpose & Functionality**: What does this code accomplish?
2. **Key Components**: Main classes, functions, variables, and their relationships
3. **Execution Flow**: Step-by-step logic flow and decision points
4. **Design Patterns**: Any patterns or architectural approaches used
5. **Dependencies**: External libraries, APIs, or modules required
6. **Security Considerations**: Any security-relevant aspects or concerns
7. **Performance Characteristics**: Notable performance implications
8. **Potential Issues**: Edge cases, limitations, or improvement opportunities

RESPONSE FORMAT (JSON array with single finding):
[
  {{
    "type": "explain",
    "severity": "info",
    "line_start": {chunk.start_line},
    "line_end": {chunk.end_line},
    "message": "Comprehensive explanation covering all 8 points above in clear, structured format",
    "suggestion": "Recommendations for improvements, security hardening, or performance optimization with specific code examples",
    "confidence": 1.0
  }}
]
"""
        return prompt

    def _parse_response(self, content: str, chunk: CodeChunk) -> List[ReviewFinding]:
        """Parse Augment Code's response into ReviewFinding objects."""
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
        """Estimate tokens using standard approximation (roughly 4 chars per token)."""
        return len(text) // 4

    def get_max_context_size(self) -> int:
        """Get maximum context size for the current model."""
        return self._context_sizes.get(self.model, 200000)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self.client.aclose()

    def _build_augmentcode_security_prompt(self, chunk: CodeChunk, review_types: List[ReviewType], security_context: str) -> str:
        """Build Augment Code-specific security-focused prompt with comprehensive vulnerability database."""

        prompt = f"""{security_context}

═══════════════════════════════════════════════════════════════════════════════
CODE UNDER REVIEW
═══════════════════════════════════════════════════════════════════════════════

FILE: {chunk.file_path}
LINES: {chunk.start_line}-{chunk.end_line}
LANGUAGE: {chunk.language}

```{chunk.language}
{chunk.content}
```
"""

        if chunk.context:
            prompt += f"""
SURROUNDING CODE CONTEXT:
```{chunk.language}
{chunk.context}
```
"""

        prompt += """
═══════════════════════════════════════════════════════════════════════════════
YOUR CRITICAL SECURITY AUDIT TASK
═══════════════════════════════════════════════════════════════════════════════

As an EXPERT SECURITY RESEARCHER, systematically analyze this code for ALL exploitable vulnerabilities.

For EACH critical/high severity vulnerability, provide:

1. CWE ID and vulnerability name
2. Exact line numbers
3. Detailed exploitation scenario
4. Real-world impact assessment
5. THREE fix options with complete code examples:

   OPTION 1 - Quick Fix (immediate mitigation):
   ```language
   [exact code]
   ```
   ✅ PROS: [specific benefits]
   ❌ CONS: [specific limitations]
   ⏱️  Implementation time: [realistic estimate]
   🛡️  Risk reduction: [percentage]

   OPTION 2 - Secure Fix (comprehensive):
   ```language
   [exact code]
   ```
   ✅ PROS: [specific benefits]
   ❌ CONS: [specific limitations]
   ⏱️  Implementation time: [realistic estimate]
   🛡️  Risk reduction: [percentage]

   OPTION 3 - Best Practice (industry standard):
   ```language
   [exact code]
   ```
   ✅ PROS: [specific benefits]
   ❌ CONS: [specific limitations]
   ⏱️  Implementation time: [realistic estimate]
   🛡️  Risk reduction: [percentage]

6. RECOMMENDATION with clear justification

RESPONSE FORMAT (JSON array):
[
  {
    "type": "security",
    "severity": "critical|high",
    "line_start": <number>,
    "line_end": <number>,
    "message": "CWE-XXX: [Name]\\n\\nDETAILS:\\n[description]\\n\\nEXPLOITATION:\\n[scenario]\\n\\nIMPACT:\\n[consequences]",
    "suggestion": "[Format as shown above with 3 options]",
    "confidence": <0.9-1.0>
  }
]

CRITICAL RULES:
✓ ONLY critical/high severity
✓ CONCRETE code examples
✓ SPECIFIC exploitation details
✓ CWE references mandatory
✓ Confidence ≥0.9

Return [] if no critical/high issues found.
"""
        return prompt
