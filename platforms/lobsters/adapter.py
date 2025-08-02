from pathlib import Path
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class LobstersAdapter(PlatformAdapter):
    """Lobsters platform adapter - stricter technical community"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Lobsters submission"""
        prompt = self._build_lobsters_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="lobsters",
            title=result.get("title", ""),
            body=result.get("description", ""),
            metadata={
                "tags": result.get("tags", []),
                "submission_type": result.get("submission_type", "link"),
                "author_note": result.get("author_note", "")
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_lobsters_prompt(self, content_dna: ContentDNA) -> str:
        """Build Lobsters-specific prompt - stricter than HN"""

        # Intelligent DNA transformation for Lobsters - maximum technical focus
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        tech = content_dna.technical_details if content_dna.technical_details else []
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []
        limitations = content_dna.limitations if content_dna.limitations else []

        return f"""You are submitting to Lobsters (lobste.rs), a computing-focused link aggregation site. Lobsters is STRICTER than Hacker News - it's invite-only, heavily moderated, and deeply technical.

=== LOBSTERS CULTURE (CRITICAL) ===
What defines Lobsters:
- Invite-only creates quality-focused community
- Tags are curated and enforced
- Must disclose if you're the author ("via" tag)
- Heavily moderated - off-topic = removed
- Programming, systems, technical content only
- NO startup culture, business, marketing
- Quality over novelty

What gets submissions removed:
- Self-promotion without disclosure
- Non-technical content
- Blogspam or low-effort content
- Sensationalist titles
- Off-topic (business, politics, culture)
- Duplicate submissions

Comparison to HN:
- More technical, less startup/business
- Smaller, tighter community
- Better signal-to-noise ratio
- Harsher on low-quality content
- Requires author disclosure

=== TAG SYSTEM ===
Lobsters has curated tags. Common ones:
- programming, plt (programming language theory)
- web, rust, go, python, javascript
- devops, linux, unix, networking
- databases, distributed, security
- show (for your own projects - requires disclosure)
- release, announce (for version releases)
- practices, testing, debugging
- performance, scaling

=== CONTENT TO TRANSFORM ===
What you built: {value}
Problem solved: {problem}
Technical details: {', '.join(tech) if tech else 'N/A'}
What's unique: {', '.join(unique) if unique else 'N/A'}
Limitations: {', '.join(limitations) if limitations else 'N/A'}

=== SUBMISSION FORMAT ===

**Title:**
- Descriptive, not clickbait
- Technical and specific
- For your own projects: just describe what it is
- NO: "I built...", "Check out...", "Introducing..."
- YES: "[Tool name]: [what it does technically]"
- Include language/tech if relevant: "pgx: Pure Go PostgreSQL driver"
- Maximum ~80 characters

**Description (optional):**
- Brief technical summary if needed
- Only if the linked content needs context
- Keep it factual, not promotional
- Usually omit for straightforward links

**Author Disclosure:**
- If you wrote the content or built the tool: MUST use "authored by me" or similar
- Lobsters shows "via [username]" for author submissions
- This is a rule, not optional

**Tags:**
- Select 1-3 appropriate tags
- Be honest about categorization
- "show" tag for personal projects
- Primary technology tag (rust, python, etc.)
- Domain tag (web, databases, devops)

=== WHAT MAKES GOOD LOBSTERS CONTENT ===
- Technical depth and novelty
- Open source projects with clear utility
- Interesting technical approaches
- Performance/optimization stories
- Language/tool comparisons
- Systems programming content
- Research papers and technical writing

Return JSON:
{{
  "title": "[Descriptive technical title, max 80 chars]",
  "description": "[Optional 1-2 sentence technical context, or empty string]",
  "tags": ["show", "python", "web"],
  "submission_type": "link|text",
  "author_note": "[Disclosure note if you're the author]",
  "url": "[Link to content/repo]"
}}"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Lobsters submission content"""
        errors = []
        warnings = []
        suggestions = []

        title = content.title
        meta = content.metadata

        if not title:
            errors.append("Title is required")
        elif len(title) > 100:
            errors.append(f"Title too long ({len(title)} chars) - Lobsters prefers concise titles")

        # Check for promotional language
        promo_phrases = ['check out', 'introducing', 'announcing', 'excited', 'i built', 'i made', 'my new']
        for phrase in promo_phrases:
            if phrase in title.lower():
                warnings.append(f"Promotional language detected ('{phrase}') - Lobsters prefers factual titles")
                break

        # Check tags
        tags = meta.get('tags', [])
        if not tags:
            errors.append("Tags are required for Lobsters")
        elif len(tags) > 4:
            warnings.append("Too many tags - 1-3 is typical for Lobsters")

        # Check for author disclosure
        author_note = meta.get('author_note', '')
        if 'show' in [t.lower() for t in tags] and not author_note:
            errors.append("Author disclosure required for 'show' submissions")

        # Check for technical specificity
        generic_words = ['tool', 'app', 'utility', 'software', 'project']
        is_generic = all(word not in title.lower() for word in meta.get('tags', []))
        if title and not any(char.isdigit() for char in title):
            # No version numbers or specific technical terms might indicate generic title
            if len(title.split()) < 4:
                suggestions.append("Consider a more specific/technical title")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
