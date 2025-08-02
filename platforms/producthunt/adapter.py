from pathlib import Path
from typing import Dict, Any, List

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class ProducthuntAdapter(PlatformAdapter):
    """Product Hunt platform adapter for launch preparation"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Product Hunt launch content"""
        prompt = self._build_producthunt_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="producthunt",
            title=result.get("tagline", "Product Hunt Launch"),
            body=self._format_launch_preview(result),
            metadata={
                "name": result.get("name", ""),
                "tagline": result.get("tagline", ""),
                "description": result.get("description", ""),
                "first_comment": result.get("first_comment", ""),
                "topics": result.get("topics", []),
                "media_suggestions": result.get("media_suggestions", [])
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_producthunt_prompt(self, content_dna: ContentDNA) -> str:
        """Build Product Hunt-specific prompt"""

        # Intelligent DNA transformation for PH - emphasize value prop and differentiation
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []
        audience = content_dna.target_audience
        tech = content_dna.technical_details[:2] if content_dna.technical_details else []

        return f"""You are preparing a Product Hunt launch. Product Hunt is where early adopters discover new products. The launch day performance depends heavily on preparation.

=== PRODUCT HUNT DYNAMICS ===
What drives success:
- Tagline is everything: 60 chars to capture attention
- First comment from maker sets the tone
- Responding to EVERY comment (engagement matters)
- Visuals: GIF/video showing the product in action
- Launching Tuesday-Thursday (avoid weekends)
- Having a hunter with followers helps (but not required)
- Being in the right topics/categories

What fails:
- Vague taglines that don't explain value
- No maker engagement in comments
- Static screenshots instead of GIFs/video
- Description that reads like marketing copy
- Launching without preparation (need upvotes in first hour)
- Not having the product ready (PH users will try it immediately)

=== PH COMMUNITY CULTURE ===
- Early adopters, tech-savvy, willing to try new things
- Appreciate transparency about stage (beta, early access)
- Value "why I built this" stories
- Will give harsh feedback if product doesn't work
- Supportive of indie makers and open source
- Skeptical of corporate launches without personality

=== CONTENT TO TRANSFORM ===
What it does: {value}
Problem solved: {problem}
What's unique: {', '.join(unique)}
Who it's for: {audience}
Technical approach: {', '.join(tech) if tech else 'N/A'}

=== LAUNCH CONTENT ===

**Product Name:**
- Keep it short and memorable
- Should give a hint of what it does

**Tagline (60 chars MAX):**
- Single most important text
- Formula: [What it is] for [who/use case]
- Or: [Action] [outcome] [how]
- Examples: "The keyboard for coders who hate leaving the home row"
- Examples: "Turn voice into text in real-time, anywhere on macOS"
- Be specific, not clever

**Description (260 chars):**
- Expand on tagline
- What does it do specifically?
- Who is it for?
- Key differentiator

**First Comment from Maker:**
This is critical - it's where you tell your story.
- Start with "Hey Product Hunt! 👋"
- Why you built this (personal motivation)
- What makes it different from alternatives
- Current status (beta, stable, etc.)
- What you're hoping to learn from the community
- Genuine question for feedback
- Keep it personal, not corporate

**Topics:**
- Select 2-4 relevant PH topics
- Common: Developer Tools, Productivity, Open Source, Design Tools, AI

**Media Suggestions:**
- What screenshots/GIFs/videos would best show the product
- GIF of main workflow is essential
- Before/after comparison if applicable

Return JSON:
{{
  "name": "[Product name]",
  "tagline": "[60 chars max - the hook]",
  "description": "[260 chars - expands on tagline]",
  "first_comment": "[Maker's story and engagement hook, 500-800 chars]",
  "topics": ["Topic1", "Topic2", "Topic3"],
  "media_suggestions": [
    {{
      "type": "gif|screenshot|video",
      "description": "[What to show]",
      "purpose": "[Why this visual matters]"
    }}
  ],
  "launch_tips": "[Specific tips for this product's PH launch]"
}}"""

    def _format_launch_preview(self, result: Dict) -> str:
        """Format launch content for preview"""
        preview = []
        preview.append(f"=== PRODUCT HUNT LAUNCH PREP ===\n")
        preview.append(f"Name: {result.get('name', 'N/A')}")
        preview.append(f"Tagline: {result.get('tagline', 'N/A')}")
        preview.append(f"Topics: {', '.join(result.get('topics', []))}")
        preview.append(f"\n--- Description ---")
        preview.append(result.get('description', 'N/A'))
        preview.append(f"\n--- First Comment (Maker Story) ---")
        preview.append(result.get('first_comment', 'N/A'))
        preview.append(f"\n--- Media Suggestions ---")
        for media in result.get('media_suggestions', []):
            preview.append(f"• [{media.get('type', 'unknown')}] {media.get('description', 'N/A')}")
        preview.append(f"\n--- Launch Tips ---")
        preview.append(result.get('launch_tips', 'N/A'))
        return "\n".join(preview)

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Product Hunt launch content"""
        errors = []
        warnings = []
        suggestions = []

        meta = content.metadata

        # Validate tagline
        tagline = meta.get('tagline', '')
        if not tagline:
            errors.append("Tagline is required")
        elif len(tagline) > 80:
            errors.append(f"Tagline too long: {len(tagline)}/80 chars")
        elif len(tagline) < 20:
            warnings.append("Tagline may be too short to convey value")

        # Validate description
        description = meta.get('description', '')
        if len(description) > 260:
            errors.append(f"Description too long: {len(description)}/260 chars")

        # Validate first comment
        first_comment = meta.get('first_comment', '')
        if not first_comment:
            errors.append("First comment (maker story) is required")
        elif len(first_comment) < 200:
            warnings.append("First comment may be too short - tell your story")
        elif len(first_comment) > 1000:
            warnings.append("First comment is quite long - consider condensing")

        # Check for question in first comment
        if first_comment and '?' not in first_comment:
            suggestions.append("Consider adding a question in first comment to drive engagement")

        # Validate topics
        topics = meta.get('topics', [])
        if not topics:
            warnings.append("No topics selected - this affects discoverability")
        elif len(topics) > 4:
            warnings.append("Too many topics - select 2-4 most relevant")

        # Check media suggestions
        media = meta.get('media_suggestions', [])
        if not media:
            warnings.append("No media suggestions - GIFs/videos are essential for PH success")
        else:
            has_gif = any(m.get('type') == 'gif' for m in media)
            if not has_gif:
                suggestions.append("Consider adding a GIF showing main workflow")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
