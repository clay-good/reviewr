import json
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import LLMProvider, CodeChunk, ReviewType, ReviewFinding


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 4096, temperature: float = 0.0, timeout: int = 60):
        """Initialize OpenAI provider."""
        super().__init__(api_key, model, max_tokens, temperature, timeout)
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        
        # Model context sizes
        self._context_sizes = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
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
        """Review code using OpenAI."""
        prompt = self._build_review_prompt(chunk, review_types)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer. Analyze code carefully and provide specific, actionable feedback. Return your findings as a JSON array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"} if "turbo" in self.model else None,
            )
            
            # Track usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self._track_usage(input_tokens, output_tokens)
            
            # Parse response
            content = response.choices[0].message.content
            findings = self._parse_response(content, chunk)
            
            return findings
            
        except Exception as e:
            print(f"Error reviewing code with OpenAI: {e}")
            raise
    
    def _parse_response(self, content: str, chunk: CodeChunk) -> List[ReviewFinding]:
        """Parse OpenAI's response into ReviewFinding objects."""
        content = content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            data = json.loads(content)
            
            # Handle both direct array and object with findings key
            if isinstance(data, dict):
                findings_data = data.get("findings", data.get("results", []))
            else:
                findings_data = data
            
            if not isinstance(findings_data, list):
                print(f"Warning: Expected list, got {type(findings_data)}")
                return []
            
            findings = []
            for item in findings_data:
                try:
                    review_type = ReviewType(item["type"])
                    
                    finding = ReviewFinding(
                        type=review_type,
                        severity=item["severity"],
                        file_path=chunk.file_path,
                        line_start=item["line_start"],
                        line_end=item["line_end"],
                        message=item["message"],
                        suggestion=item.get("suggestion"),
                        code_snippet=None,
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
        """Estimate tokens using rough approximation (4 chars per token)."""
        return len(text) // 4
    
    def get_max_context_size(self) -> int:
        """Get maximum context size for the current model."""
        return self._context_sizes.get(self.model, 8192)

