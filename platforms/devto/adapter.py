import json
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class DevtoAdapter(PlatformAdapter):
    """Dev.to platform adapter optimized for developer audience"""
    
    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)
        
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate dev.to article optimized for developer community"""
        prompt = self._build_devto_prompt(content_dna)
        
        result = self._make_llm_call(prompt)
        
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

        # Intelligent DNA transformation for DEV.to - emphasize learning journey and code
        tech_stack = content_dna.technical_details if content_dna.technical_details else []
        main_tech = tech_stack[0] if tech_stack else 'general'
        problem_context = content_dna.problem_solved
        unique_approach = content_dna.unique_aspects[0] if content_dna.unique_aspects else ''

        return f"""You are writing for DEV.to (dev.to), a welcoming developer community that celebrates learning, sharing, and building. The culture is supportive, beginner-friendly, and values practical knowledge over gatekeeping.

=== DEV.TO CULTURE ===
What resonates:
- "I built this and learned X" narratives
- Step-by-step breakdowns with code
- Admitting what you didn't know and how you learned
- Helping others avoid your mistakes
- Open source appreciation
- Celebrating small wins
- Inclusive language ("Let's build..." not "You should know...")

What falls flat:
- Gatekeeping or elitism
- Dense theory without practical application
- No code examples in technical posts
- Corporate/marketing voice
- Assuming too much prior knowledge without linking resources

=== DEV.TO ALGORITHM & FEATURES ===
Engagement drivers:
- Cover images dramatically increase visibility (1000x420 recommended)
- Tags determine feed placement - choose strategically
- First paragraph appears in feed preview
- Series group related posts and build followers
- Reactions: ❤️ 🦄 🔖 (unicorn = "this blew my mind")

High-reach tags:
- #beginners (huge audience, welcoming)
- #tutorial (people actively seeking to learn)
- #webdev, #javascript, #python (large communities)
- #opensource, #productivity (engaged readers)
- #showdev (for project showcases - like Show HN)

=== CONTENT TO TRANSFORM ===
What you built: {content_dna.value_proposition}
Problem context: {problem_context}
Tech stack: {', '.join(tech_stack)}
Key differentiator: {unique_approach}
Who it helps: {content_dna.target_audience}

=== ARTICLE STRUCTURE ===

**Title:**
- Clear and specific: what will reader learn or see?
- Patterns that work: "Building [X] with [Y]", "How I [solved problem]", "[Tool]: [What it does]"
- Include main technology if relevant
- Max 100 chars

**Introduction (2-3 paragraphs):**
- Hook: What are we building/exploring?
- Context: Why does this matter?
- Preview: What will the reader walk away with?

**Prerequisites (if needed):**
- Quick bulleted list
- Link to resources for each prerequisite
- Keep it short - don't scare beginners

**Main Content (bulk of article):**
- Break into clear sections with ## headers
- Code blocks with syntax highlighting (```python, ```javascript, etc.)
- Explain the "why" not just the "how"
- Use comments in code to explain non-obvious parts
- Keep code snippets focused - don't dump entire files

**Challenges/Gotchas (1-2 paragraphs):**
- What tripped you up?
- What would you do differently?
- This builds trust and helps others

**Conclusion:**
- What did we accomplish?
- Possible next steps or extensions
- Links to repo/demo if applicable
- Invite questions and discussion

**Call to Engage:**
- End with a genuine question
- "What's your approach to X?"
- "Have you tried something similar?"

=== FORMATTING RULES ===
- Use ```language for code blocks (specify language!)
- ## for main sections, ### for subsections
- Bold for key terms on first use
- Bullet lists for scannable content
- Short paragraphs (2-4 sentences)
- Include at least 2-3 code snippets for technical posts

=== TAGS ===
Choose exactly 4 tags (DEV.to limit):
- 1 broad reach (#webdev, #programming)
- 1-2 technology-specific (#python, #react, #node)
- 1 content-type (#tutorial, #showdev, #beginners)

Return JSON:
{{
  "title": "[Clear, descriptive title, max 100 chars]",
  "description": "[SEO description, max 160 chars - appears in search]",
  "body": "[Full markdown article with code blocks and ## headers]",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "cover_image_prompt": "[Description for generating/finding cover image]",
  "series": "[Series name if this could be part 1 of a series, else null]"
}}"""
    
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