from pathlib import Path
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class SubstackAdapter(PlatformAdapter):
    """Substack platform adapter for newsletter format"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Substack newsletter post"""
        prompt = self._build_substack_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="substack",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "subtitle": result.get("subtitle", ""),
                "preview_text": result.get("preview_text", ""),
                "section": result.get("section", ""),
                "is_free": result.get("is_free", True)
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_substack_prompt(self, content_dna: ContentDNA) -> str:
        """Build Substack-specific prompt for newsletter format"""

        # Intelligent DNA transformation for Substack - emphasize insight and personal voice
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []
        lessons = content_dna.limitations  # Reframe as insights
        tech = content_dna.technical_details if content_dna.technical_details else []

        return f"""You are writing a Substack newsletter post. Substack is for writers with distinctive voices sharing deep insights with their audience. Think email-first: subscribers chose to receive this.

=== SUBSTACK CULTURE ===
What works:
- Strong personal voice and perspective
- Deep dives on topics you genuinely care about
- Opinions and takes, not just information
- Writing that rewards careful reading
- Personal anecdotes woven with insights
- Treating subscribers as a community, not an audience
- Authenticity over polish

What doesn't work:
- Generic content available everywhere
- Pure news aggregation without perspective
- Clickbait titles that don't deliver
- Corporate or impersonal tone
- Writing for SEO instead of readers
- Excessive self-promotion

=== SUBSTACK DYNAMICS ===
- Email open rates matter more than views
- Subject line = title (must work in inbox)
- Preview text appears in email clients
- Free vs paid content strategy
- Comments are for engaged subscribers
- Subscribers expect consistency and voice

=== CONTENT TO TRANSFORM ===
Core insight: {value}
Problem/context: {problem}
Unique perspective: {', '.join(unique) if unique else 'N/A'}
Lessons/reflections: {', '.join(lessons) if lessons else 'Still processing'}
Technical details: {', '.join(tech) if tech else 'N/A'}

=== NEWSLETTER STRUCTURE ===

**Title (also email subject):**
- Must work in email inbox preview
- Intrigue without clickbait
- Hint at the insight, don't give it all away
- 50-60 chars ideal for mobile email clients

**Subtitle:**
- Expands on title
- Often a question or setup
- Shows in email after subject line

**Preview Text:**
- First 100 chars of email preview
- Hook the reader to open

**Opening (first 2-3 paragraphs):**
- Start with something specific: a moment, observation, or question
- NOT: "In this week's newsletter..."
- Draw reader into your thinking
- Establish the question or tension you'll explore

**The Meat (main content):**
- Go deep on one idea, not shallow on many
- Mix personal experience with broader insights
- Include unexpected connections
- Show your thinking process
- It's okay to not have all answers

**The Insight:**
- What's your actual take?
- What did you realize or learn?
- Why does this matter to your readers?

**Closing:**
- Circle back to opening
- Leave reader with something to think about
- Natural transition to engagement (reply, share, discuss)
- NOT: hard CTA to subscribe/upgrade

=== FORMATTING ===
- Substack supports full markdown
- Use headers sparingly (this isn't a blog post)
- Pull quotes for key lines
- Images/charts where they add value
- Shorter paragraphs for email readability
- Links work but don't overdo it

=== TONE ===
- Conversational but thoughtful
- Like writing to a smart friend
- Have opinions, defend them
- Okay to be uncertain and explore
- Personal but not diary-like

Return JSON:
{{
  "title": "[Email subject line / post title, 50-60 chars]",
  "subtitle": "[Expands on title, adds context]",
  "preview_text": "[First ~100 chars that appear in email preview]",
  "body": "[Full newsletter post, 800-2000 words]",
  "section": "[Newsletter section if applicable: null, or 'Tools I'm Using', 'What I'm Building', etc.]",
  "is_free": true,
  "engagement_prompt": "[Natural way to invite reader response]"
}}"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Substack newsletter content"""
        errors = []
        warnings = []
        suggestions = []

        title = content.title
        body = content.body
        meta = content.metadata

        if not title:
            errors.append("Title is required")
        elif len(title) > 80:
            warnings.append(f"Title may be too long for email subject ({len(title)} chars)")

        if not body:
            errors.append("Body is required")
        elif len(body) < 500:
            warnings.append("Newsletter post seems short - Substack readers expect depth")
        elif len(body) > 5000:
            warnings.append("Very long post - consider if this should be a series")

        # Check preview text
        preview = meta.get('preview_text', '')
        if not preview:
            suggestions.append("Add preview text for email client display")
        elif len(preview) > 150:
            warnings.append("Preview text may be truncated in email clients")

        # Check for personal voice
        personal_indicators = [' I ', "I'm", "I've", ' my ', ' me ']
        has_personal_voice = any(indicator in body for indicator in personal_indicators)
        if not has_personal_voice:
            suggestions.append("Consider adding more personal voice - Substack readers value author perspective")

        # Check for opening hook
        first_paragraph = body.split('\n\n')[0] if body else ''
        weak_openers = ['in this', 'today we', 'this week', 'welcome to']
        if any(opener in first_paragraph.lower() for opener in weak_openers):
            suggestions.append("Consider a stronger opening - avoid generic newsletter intros")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
