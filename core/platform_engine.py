import json
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI
from .models import ContentDNA, PlatformContent, ValidationResult, PublishResult


class PlatformAdapter(ABC):
    """Base class for all platform adapters"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.profile = self._load_profile()
        
    def _load_profile(self) -> Dict[str, Any]:
        """Load platform profile from YAML"""
        profile_path = self.config_dir / "profile.yaml"
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    @abstractmethod
    def generate_content(self, content_dna: ContentDNA, api_key: str) -> PlatformContent:
        """Generate platform-specific content"""
        pass
    
    @abstractmethod
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content against platform rules"""
        pass
    
    @abstractmethod
    def post_content(self, content: PlatformContent) -> PublishResult:
        """Post content to the platform"""
        pass
    
    def _build_platform_prompt(self, content_dna: ContentDNA) -> str:
        """Build platform-specific prompt using profile"""
        base_prompt = f"""
You are an expert copywriter for {self.profile.get('name', 'this platform')}.

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Audience: {content_dna.target_audience}
- Technical: {', '.join(content_dna.technical_details)}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Platform Culture: {json.dumps(self.profile.get('culture', {}), indent=2)}
Content Rules: {json.dumps(self.profile.get('content_rules', {}), indent=2)}

Generate content that respects this platform's culture and rules.
Return JSON with: title, body, metadata
"""
        return base_prompt
    
    def _make_llm_call(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """Make LLM call with error handling"""
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Return only valid JSON. Be concise and platform-appropriate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")


class Validator:
    """Base validator with common validation logic"""
    
    @staticmethod
    def check_length(text: str, max_length: int, field_name: str) -> List[str]:
        """Check text length"""
        if len(text) > max_length:
            return [f"{field_name} exceeds {max_length} characters ({len(text)})"]
        return []
    
    @staticmethod
    def check_forbidden_words(text: str, forbidden: List[str], field_name: str) -> List[str]:
        """Check for forbidden words"""
        text_lower = text.lower()
        found = [word for word in forbidden if word.lower() in text_lower]
        if found:
            return [f"{field_name} contains forbidden words: {', '.join(found)}"]
        return []
    
    @staticmethod
    def check_required_elements(text: str, required: List[str], field_name: str) -> List[str]:
        """Check for required elements"""
        text_lower = text.lower()
        missing = [element for element in required if element.lower() not in text_lower]
        if missing:
            return [f"{field_name} missing required elements: {', '.join(missing)}"]
        return []