from pathlib import Path
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class HashnodeAdapter(PlatformAdapter):
    """Hashnode platform adapter for developer blogging"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Hashnode blog post"""
        prompt = self._build_hashnode_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="hashnode",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "subtitle": result.get("subtitle", ""),
                "tags": result.get("tags", []),
                "series": result.get("series", None),
                "canonical_url": result.get("canonical_url", None),
                "cover_image_prompt": result.get("cover_image_prompt", "")
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_hashnode_prompt(self, content_dna: ContentDNA) -> str:
        """Build Hashnode-specific prompt for developer blogging"""

        # Intelligent DNA transformation for Hashnode - emphasize technical depth with teaching
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        tech = content_dna.technical_details if content_dna.technical_details else []
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []
        limitations = content_dna.limitations if content_dna.limitations else []

        return f"""You are writing for Hashnode, a blogging platform popular with developers. It's like DEV.to's more SEO-focused sibling - great for building a personal tech blog with custom domain support.

=== HASHNODE CULTURE ===
What works:
- Technical tutorials with code examples
- Deep dives on specific technologies
- "How I built X" narratives
- Learning journeys and discoveries
- Open source project announcements
- SEO-optimized titles (Hashnode blogs rank well)
- Series for multi-part content

What doesn't work:
- Surface-level content without depth
- No code in technical posts
- Pure opinions without backing
- Clickbait without substance

=== HASHNODE FEATURES ===
- Custom domains (your-blog.com)
- Built-in newsletter functionality
- Series for connected posts
- Canonical URL support (for cross-posting)
- Good SEO out of the box
- Code blocks with syntax highlighting
- Backup/export as markdown

=== CONTENT TO TRANSFORM ===
What you built/explored: {value}
Problem context: {problem}
Technologies used: {', '.join(tech) if tech else 'N/A'}
What's unique: {', '.join(unique) if unique else 'N/A'}
Challenges/limitations: {', '.join(limitations) if limitations else 'N/A'}

=== ARTICLE STRUCTURE ===

**Title:**
- SEO-optimized but not clickbaity
- Include primary keyword naturally
- Patterns: "Building [X] with [Y]", "Understanding [Concept]", "[Technology]: A Deep Dive"
- 50-70 chars ideal for SEO

**Subtitle:**
- Expands on title
- Can include secondary keywords
- Sets reader expectations

**Introduction:**
- Hook with the problem or question
- What will the reader learn?
- Brief preview of what's coming
- Keep to 2-3 paragraphs

**Main Content:**
- Break into logical sections with ## headers
- Each section: concept → explanation → code → results
- Code blocks with language tags (```python, ```javascript, etc.)
- Explain the "why" not just the "what"
- Include output/results where relevant

**Code Guidelines:**
- Use syntax highlighting (specify language)
- Keep snippets focused (not entire files)
- Add comments for non-obvious parts
- Show input and output where applicable

**Gotchas/Learnings:**
- What surprised you?
- What would you do differently?
- Common mistakes to avoid

**Conclusion:**
- Summarize key points
- Suggest next steps or further reading
- Link to repo/demo if applicable
- Invite comments/questions

=== TAGS ===
Hashnode uses tags for discoverability:
- Pick 3-5 relevant tags
- Mix broad (javascript, webdev) with specific (nextjs, prisma)
- Check popular Hashnode tags in your niche

=== FORMATTING ===
- Hashnode markdown: ## for headers, ``` for code
- Use > for blockquotes/callouts
- Tables supported
- Image alt text for accessibility
- Embed support for CodeSandbox, CodePen, etc.

Return JSON:
{{
  "title": "[SEO-optimized title, 50-70 chars]",
  "subtitle": "[Expands on title, adds context]",
  "body": "[Full markdown article with code blocks and headers]",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "series": "[Series name if part of series, else null]",
  "cover_image_prompt": "[Description for cover image]",
  "canonical_url": null,
  "seo_description": "[155 chars meta description for SEO]"
}}"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Hashnode blog post content"""
        errors = []
        warnings = []
        suggestions = []

        title = content.title
        body = content.body
        meta = content.metadata

        if not title:
            errors.append("Title is required")
        elif len(title) > 100:
            warnings.append(f"Title may be too long for SEO ({len(title)} chars)")

        if not body:
            errors.append("Body is required")
        elif len(body) < 500:
            warnings.append("Article seems short for Hashnode - consider adding more depth")

        # Check for code blocks in technical posts
        if '```' not in body:
            suggestions.append("Consider adding code examples for technical content")

        # Check for headers
        if '##' not in body:
            suggestions.append("Add section headers (##) for better structure")

        # Check tags
        tags = meta.get('tags', [])
        if not tags:
            warnings.append("No tags specified - important for Hashnode discoverability")
        elif len(tags) > 5:
            warnings.append("Too many tags - recommend 3-5")

        # Check for images/visuals suggestion
        cover = meta.get('cover_image_prompt', '')
        if not cover:
            suggestions.append("Consider adding a cover image for better engagement")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
