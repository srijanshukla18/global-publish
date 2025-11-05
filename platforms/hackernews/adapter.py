from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult
from .validator import HackerNewsValidator


class HackernewsAdapter(PlatformAdapter):
    """Hacker News platform adapter with cultural awareness"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        super().__init__(model, api_key)
        self.validator = HackerNewsValidator()

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate HN-specific content following community guidelines"""
        prompt = self._build_hn_prompt(content_dna)

        result_text = self.adapt_content(prompt)
        import json
        result = json.loads(result_text)
        
        return PlatformContent(
            platform="hackernews",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata=result.get("metadata", {}),
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_hn_prompt(self, content_dna: ContentDNA) -> str:
        """Build HN-specific prompt with cultural context"""
        forbidden_words = [
            'revolutionary', 'game-changing', 'innovative', 'disruptive',
            'cutting-edge', 'next-generation', 'breakthrough', 'amazing',
            'incredible', 'ultimate', 'best', 'perfect', 'unique'
        ]
        return f"""
You are writing for Hacker News, a technical community that values:
- Technical depth over marketing fluff
- Honest discussion of limitations
- Substance over style
- Intellectual curiosity

STRICT RULES:
- Title MUST start with "Show HN:" for tools
- Title MUST be ≤60 characters
- NO marketing words: {', '.join(forbidden_words)}
- NO emoji, excessive punctuation, or superlatives
- Format: "Show HN: [Tool name] - [what it does technically]"

Content DNA:
- Value: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Type: {content_dna.content_type}
- Limitations: {', '.join(content_dna.limitations)}

Body should include:
1. Technical problem you solved
2. Your approach/implementation
3. Key technical details or challenges
4. Honest limitations or areas for improvement
5. Invite technical discussion

Write in a humble, technical tone. Focus on the engineering, not the marketing.

Return JSON:
{{
  "title": "Show HN: [exact title]",
  "body": "Technical explanation...",
  "metadata": {{"category": "Show HN", "target_engagement": "technical_discussion"}}
}}
"""
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content using HN-specific rules"""
        return self.validator.validate(content)
