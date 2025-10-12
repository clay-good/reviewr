import json
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import LLMProvider, CodeChunk, ReviewType, ReviewFinding


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro",
                 max_tokens: int = 4096, temperature: float = 0.0, timeout: int = 60):
        """Initialize Gemini provider."""
        super().__init__(api_key, model, max_tokens, temperature, timeout)
        genai.configure(api_key=api_key)
        
        # Configure safety settings to be less restrictive for code review
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
        
        self.model_instance = genai.GenerativeModel(
            model_name=model,
            safety_settings=self.safety_settings,
        )
        
        # Model context sizes
        self._context_sizes = {
            "gemini-pro": 32760,
            "gemini-1.5-pro": 1000000,
            "gemini-1.5-flash": 1000000,
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
        """Review code using Gemini."""
        prompt = self._build_review_prompt(chunk, review_types)
        
        try:
            # Gemini doesn't have native async support, so we'll use sync
            response = self.model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )
            
            # Track usage (Gemini doesn't provide detailed token counts easily)
            input_tokens = self.estimate_tokens(prompt)
            output_tokens = self.estimate_tokens(response.text)
            self._track_usage(input_tokens, output_tokens)
            
            # Parse response
            content = response.text
            findings = self._parse_response(content, chunk)
            
            return findings
            
        except Exception as e:
            print(f"Error reviewing code with Gemini: {e}")
            raise
    
    def _parse_response(self, content: str, chunk: CodeChunk) -> List[ReviewFinding]:
        """Parse Gemini's response into ReviewFinding objects."""
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
            findings_data = json.loads(content)
            
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
        return self._context_sizes.get(self.model, 32760)

