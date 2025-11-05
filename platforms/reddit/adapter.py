import json
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class RedditAdapter(PlatformAdapter):
    """Reddit platform adapter - generates Reddit-optimized content"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        super().__init__(model, api_key)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Reddit content optimized for community engagement"""
        prompt = self._build_reddit_prompt(content_dna)

        result_text = self.adapt_content(prompt)
        result = json.loads(result_text)

        return PlatformContent(
            platform="reddit",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "suggested_subreddits": result.get("suggested_subreddits", []),
                "post_type": result.get("post_type", "text")
            },
            validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        )

    def _build_reddit_prompt(self, content_dna: ContentDNA) -> str:
        """Build Reddit-specific prompt"""
        return f"""
You are a Reddit community expert. Generate Reddit post content that follows community guidelines.

Reddit Culture:
- Values authenticity and transparency
- Appreciates detailed explanations
- Dislikes blatant self-promotion
- Prefers storytelling over marketing
- Engages with honest limitations discussion

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a Reddit post that:
1. Has an authentic, non-promotional title (≤300 chars)
2. Tells a story about the problem and solution
3. Includes technical details without jargon overload
4. Mentions limitations honestly
5. Invites community feedback
6. Suggests 2-3 appropriate subreddits for posting

Structure:
- Hook: Why you built this
- Problem: Personal pain point
- Solution: Your approach
- Technical details: Implementation highlights
- Limitations: What's not perfect
- Ask: Specific feedback you're seeking

Return JSON:
{{
  "title": "Authentic title without hype",
  "body": "Full Reddit post with story and details",
  "suggested_subreddits": ["programming", "sideproject", "webdev"],
  "post_type": "text"
}}
"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Reddit content"""
        warnings = []
        errors = []
        suggestions = []

        # Check title length
        if len(content.title) > 300:
            errors.append(f"Title too long: {len(content.title)}/300")

        # Check body length
        if len(content.body) > 40000:
            errors.append(f"Body too long: {len(content.body)}/40000")
        elif len(content.body) < 100:
            warnings.append("Post might be too short for meaningful discussion")

        # Check for spam indicators
        if content.body.count('http') > 3:
            warnings.append("Multiple links may trigger spam filters")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
