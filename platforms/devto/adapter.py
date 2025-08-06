import json
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class DevtoAdapter(PlatformAdapter):
    """Dev.to platform adapter optimized for developer audience"""
    
    def __init__(self, config_dir: Path):
        super().__init__(config_dir)
        
    def generate_content(self, content_dna: ContentDNA, api_key: str) -> PlatformContent:
        """Generate dev.to article optimized for developer community"""
        prompt = self._build_devto_prompt(content_dna)
        
        result = self._make_llm_call(prompt, api_key)
        
        return PlatformContent(
            platform="devto",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "tags": result.get("tags", []),
                "description": result.get("description", ""),
                "cover_image": result.get("cover_image", None),
                "canonical_url": None,  # Will be set during posting
                "series": result.get("series", None)
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_devto_prompt(self, content_dna: ContentDNA) -> str:
        """Build dev.to-specific prompt for article generation"""
        return f"""
You are writing for dev.to, a developer-focused platform that values:
- Practical, actionable tutorials
- Code examples and snippets
- Beginner-friendly explanations
- Community engagement
- Open source and learning culture

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a dev.to article that:
1. Has a clear, descriptive title
2. Includes practical code examples
3. Explains concepts in beginner-friendly terms
4. Has actionable takeaways
5. Encourages community discussion

Structure:
- Introduction: What we're building/solving
- Prerequisites: What readers need to know
- Step-by-step tutorial with code
- Explanations of key concepts
- Conclusion with next steps
- Call for community feedback/questions

Use markdown with:
- Code blocks with language syntax
- Headers for clear sections
- Lists for easy scanning
- Emphasis for key points

Return JSON:
{{
  "title": "Clear, descriptive title",
  "description": "Brief description for SEO (under 160 chars)",
  "body": "Full markdown article with code examples",
  "tags": ["javascript", "tutorial", "beginners", "webdev"],
  "cover_image": "suggested cover image description",
  "series": "optional series name if part of a series"
}}
"""
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate dev.to article content"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate title
        title = content.title
        if not title:
            errors.append("Title is required")
        elif len(title) > 250:
            errors.append(f"Title too long: {len(title)}/250 characters")
        
        # Validate description
        description = content.metadata.get("description", "")
        if description and len(description) > 160:
            warnings.append(f"Description too long for SEO: {len(description)}/160 characters")
        
        # Validate body
        body = content.body
        if not body:
            errors.append("Body content is required")
        elif len(body) < 300:
            warnings.append("Article might be too short for dev.to")
        
        # Check for code blocks
        if '```' not in body:
            suggestions.append("Consider adding code examples for better dev.to engagement")
        
        # Check for headers
        if not any(line.startswith('#') for line in body.split('\n')):
            warnings.append("Article should have clear section headers")
        
        # Validate tags
        tags = content.metadata.get("tags", [])
        if len(tags) > 4:
            warnings.append(f"dev.to recommends max 4 tags, you have {len(tags)}")
        elif len(tags) == 0:
            warnings.append("Tags are important for discoverability on dev.to")
        
        # Check for beginner-friendly elements
        beginner_indicators = ['step', 'first', 'let\'s', 'we\'ll', 'tutorial', 'guide']
        if not any(indicator in body.lower() for indicator in beginner_indicators):
            suggestions.append("Consider making content more beginner-friendly")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )