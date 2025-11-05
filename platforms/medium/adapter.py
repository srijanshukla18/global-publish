import json
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class MediumAdapter(PlatformAdapter):
    """Medium platform adapter with SEO optimization"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        super().__init__(model, api_key)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Medium article optimized for SEO and engagement"""
        prompt = self._build_medium_prompt(content_dna)

        result_text = self.adapt_content(prompt)
        result = json.loads(result_text)
        
        return PlatformContent(
            platform="medium",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "tags": result.get("tags", []),
                "subtitle": result.get("subtitle", ""),
                "seo_optimized": True,
                "canonical_url": None  # Will be set during posting
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_medium_prompt(self, content_dna: ContentDNA) -> str:
        """Build Medium-specific prompt for article generation"""
        return f"""
You are writing for Medium, a platform that values:
- In-depth, thoughtful content
- Personal storytelling and insights
- Clear structure with headings
- Engaging introductions and conclusions
- SEO-optimized titles

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a Medium article that:
1. Has an SEO-optimized title (≤100 chars)
2. Includes a compelling subtitle
3. Uses personal narrative and insights
4. Has clear section headers
5. Includes actionable takeaways
6. Optimized for Medium's algorithm

Structure:
- Hook: Personal angle or surprising insight
- Problem: Why this matters to readers
- Solution: Your approach with details
- Results: Outcomes and benefits
- Lessons: What readers can apply
- Conclusion: Call to action or reflection

Return JSON:
{{
  "title": "SEO-optimized title under 100 chars",
  "subtitle": "Compelling subtitle that hooks readers",
  "body": "Full markdown article with headers and sections",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
"""
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Medium article content"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate title
        title = content.title
        if not title:
            errors.append("Title is required")
        elif len(title) > 100:
            errors.append(f"Title too long: {len(title)}/100 characters")
        elif len(title) < 10:
            warnings.append("Title might be too short for SEO")
        
        # Validate body
        body = content.body
        if not body:
            errors.append("Body content is required")
        elif len(body) < 500:
            warnings.append("Article might be too short for Medium (recommend >1000 words)")
        
        # Check for headers
        if not any(line.startswith('#') for line in body.split('\n')):
            suggestions.append("Consider adding section headers for better readability")
        
        # Validate tags
        tags = content.metadata.get("tags", [])
        if len(tags) > 5:
            warnings.append(f"Medium only uses first 5 tags, you have {len(tags)}")
        elif len(tags) == 0:
            warnings.append("Consider adding tags for better discoverability")
        
        # Check for personal elements
        personal_indicators = ['i ', 'my ', 'we ', 'our ', 'when i', 'i\'ve', 'i\'m']
        if not any(indicator in body.lower() for indicator in personal_indicators):
            suggestions.append("Consider adding personal insights or experiences")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )