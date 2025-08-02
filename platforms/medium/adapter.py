import json
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class MediumAdapter(PlatformAdapter):
    """Medium platform adapter with SEO optimization"""
    
    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)
        
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Medium article optimized for SEO and engagement"""
        prompt = self._build_medium_prompt(content_dna)
        
        result = self._make_llm_call(prompt)
        
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

        # Intelligent DNA transformation for Medium - emphasize personal narrative and lessons
        personal_angle = content_dna.problem_solved  # What drove you to build this
        lessons = content_dna.limitations  # Honest lessons learned
        outcomes = content_dna.key_metrics if content_dna.key_metrics else ['Early stage']
        tech_context = ', '.join(content_dna.technical_details[:2]) if content_dna.technical_details else ''

        return f"""You are writing a Medium article. Medium rewards personal narratives with genuine insights. The algorithm heavily weights read time and claps-per-read, so engagement throughout the article matters.

=== MEDIUM ALGORITHM INSIGHTS ===
What the algorithm rewards:
- 7-minute read time is optimal (1,600-2,000 words)
- First 100 words are critical - they appear in previews and determine click-through
- Personal stories outperform how-to listicles (oversaturated)
- "I" voice with vulnerable moments gets more claps
- Section headers every 300 words improves completion rate
- Ending with reflection > ending with hard CTA

What kills articles:
- Generic titles that don't promise a specific insight
- Listicles without narrative thread
- No personal stake or vulnerability
- Walls of text without headers
- Starting with "In this article, I will..."
- Ending with "Follow me for more"

=== CONTENT TO TRANSFORM ===
Your journey (make this personal): {personal_angle}
What you built: {content_dna.value_proposition}
Technical context (weave in naturally): {tech_context}
Honest lessons/limitations: {', '.join(lessons) if lessons else 'Not specified'}
Outcomes/results: {', '.join(outcomes)}
Who benefits: {content_dna.target_audience}

=== TITLE FORMULA ===
Winning patterns:
- "I [did unexpected thing] and [surprising result]"
- "Why [common practice] is [counterintuitive take]"
- "What I Learned [Building/Doing X]"
- "[Specific insight] Changed How I [Do Y]"

Avoid:
- "How to..." (oversaturated)
- "The Ultimate Guide to..." (clickbait fatigue)
- Questions as titles (low CTR on Medium)

Title: Max 60 chars for mobile preview
Subtitle: Expand on the promise, add intrigue

=== ARTICLE STRUCTURE ===

**Opening (first 100 words - CRITICAL):**
Start with a hook: a moment, a failure, a realization. Not context-setting.
Bad: "As developers, we often face challenges with..."
Good: "The third time my script crashed at 3 AM, I realized I'd been solving the wrong problem."

**The Struggle (2-3 paragraphs):**
- What problem were you facing?
- What did you try that didn't work?
- What was the turning point?

**The Insight (2-3 paragraphs):**
- What did you realize or build?
- Why is this different from obvious solutions?
- Include just enough technical detail to be credible, not overwhelming

**The Implementation (2-3 paragraphs):**
- How does it work (high-level)?
- What were the key decisions?
- What surprised you?

**The Lessons (2-3 paragraphs):**
- What would you do differently?
- What did this teach you beyond the technical?
- Connect to reader's potential experience

**Closing (1-2 paragraphs):**
- Reflection, not CTA
- Leave reader with a thought to sit with
- Optional: genuine question that invites comments

=== FORMATTING ===
- Use ## for major sections (Medium renders these well)
- Pull quotes for key insights (use > blockquote)
- Bold key phrases sparingly
- Short paragraphs (3-4 sentences max)
- One code block maximum (if essential)

=== TAGS ===
Choose 5 tags strategically:
- 1-2 broad reach tags (Programming, Technology, Startup)
- 2-3 specific niche tags (match your audience)
- Consider publication tags if submitting to publications

Return JSON:
{{
  "title": "[Compelling title, max 60 chars]",
  "subtitle": "[Expands on promise, adds intrigue, max 140 chars]",
  "body": "[Full markdown article, ~1600-2000 words, with ## headers]",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4", "Tag5"],
  "meta": {{
    "estimated_read_time": "[X] min",
    "target_publications": ["[Relevant Medium publications to submit to]"]
  }}
}}"""
    
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