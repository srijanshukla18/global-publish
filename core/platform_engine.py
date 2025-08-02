
import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import openai

from .models import ContentDNA, PlatformContent, ValidationResult

class PlatformAdapter(ABC):
    """Base class for all platform-specific adapters"""
    
    def __init__(self, config_dir: Path, model: str = None):
        self.config_dir = config_dir
        self.model = model or "gpt-4o"
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        """Load platform profile from yaml config (optional)"""
        profile_path = self.config_dir / "profile.yaml"
        if not profile_path.exists():
            return {}
        with open(profile_path, 'r') as f:
            return yaml.safe_load(f) or {}
            
    @abstractmethod
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate platform-specific content from DNA"""
        pass
        
    @abstractmethod
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate generated content against platform rules"""
        pass
        
    def _make_llm_call(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Execute LLM call with error handling and JSON parsing via LiteLLM"""
        from litellm import completion
        import re

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = completion(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=8000  # Ensure we get full long-form responses
            )

            content = response.choices[0].message.content
            return self._parse_json_response(content)

        except Exception as e:
            print(f"Error in LLM call: {e}")
            return {}

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with robust error handling"""
        import re

        # Try to extract JSON from markdown code blocks
        # Use greedy match to handle nested code blocks in body content
        json_match = re.search(r'^```(?:json)?\s*\n([\s\S]*)\n```\s*$', content.strip())
        if json_match:
            content = json_match.group(1).strip()
        else:
            # Try finding JSON object directly (starts with { ends with })
            brace_match = re.search(r'(\{[\s\S]*\})\s*$', content)
            if brace_match:
                content = brace_match.group(1)

        # Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Fix common JSON issues: unescaped newlines in string values
        # Replace actual newlines inside strings with \n
        def fix_string_newlines(s: str) -> str:
            result = []
            in_string = False
            escape_next = False
            for char in s:
                if escape_next:
                    result.append(char)
                    escape_next = False
                elif char == '\\':
                    result.append(char)
                    escape_next = True
                elif char == '"':
                    result.append(char)
                    in_string = not in_string
                elif char == '\n' and in_string:
                    result.append('\\n')
                elif char == '\r' and in_string:
                    result.append('\\r')
                elif char == '\t' and in_string:
                    result.append('\\t')
                else:
                    result.append(char)
            return ''.join(result)

        try:
            fixed = fix_string_newlines(content)
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            print(f"Error in LLM call: {e}")
            return {}

class Validator(ABC):
    """Base class for content validators"""
    
    @abstractmethod
    def validate(self, content: PlatformContent) -> ValidationResult:
        pass