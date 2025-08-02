from pathlib import Path
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class IndiehackersAdapter(PlatformAdapter):
    """Indie Hackers platform adapter for builder community"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Indie Hackers post for builder community"""
        prompt = self._build_indiehackers_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="indiehackers",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "post_type": result.get("post_type", "milestone"),
                "group": result.get("group", ""),
                "key_takeaways": result.get("key_takeaways", [])
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_indiehackers_prompt(self, content_dna: ContentDNA) -> str:
        """Build Indie Hackers-specific prompt"""

        # Intelligent DNA transformation for IH - emphasize journey, metrics, lessons
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        metrics = content_dna.key_metrics if content_dna.key_metrics else []
        lessons = content_dna.limitations  # Reframe as honest learnings
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []
        tech = content_dna.technical_details if content_dna.technical_details else []

        return f"""You are writing for Indie Hackers, the community for solo founders, bootstrappers, and indie makers. This is where builders share their journeys openly.

=== INDIE HACKERS CULTURE ===
What resonates deeply:
- Transparency about revenue, metrics, struggles
- "Building in public" narratives
- Honest failure stories with lessons
- Milestone posts: "$X MRR", "First customer", "Just launched"
- Detailed breakdowns of what worked and didn't
- Practical, actionable advice from experience
- Celebrating small wins authentically

What falls flat:
- Pure promotion without value
- Vague posts without specifics
- Pretending everything is going perfectly
- Generic startup advice not from experience
- Corporate tone or press release style
- Not engaging with comments

=== IH COMMUNITY ===
- Solo founders, indie hackers, bootstrappers
- Side project builders
- People building without VC funding
- Value profitability over growth-at-all-costs
- Skeptical of "startup theater"
- Appreciate scrappiness and resourcefulness

=== CONTENT TO TRANSFORM ===
What you built: {value}
Why you built it: {problem}
Metrics (be specific): {', '.join(metrics) if metrics else 'Early stage / pre-launch'}
Lessons/challenges: {', '.join(lessons) if lessons else 'Still learning'}
What makes it different: {', '.join(unique) if unique else 'N/A'}
Tech stack: {', '.join(tech) if tech else 'N/A'}

=== POST STRUCTURE ===

**Title:**
- Be specific: include numbers if you have them
- Patterns: "How I built [X]", "Launched [X] — here's what I learned", "[Metric] reached — my journey"
- Honest: "Failed at [X], pivoted to [Y]" works great
- Avoid: "Check out my new app" (too promotional)

**Body Structure (Long-form welcome):**

1. **The Hook / Context**
   - Where are you in your journey?
   - What milestone are you sharing?
   - Set the stage briefly

2. **The Story**
   - Why did you start this?
   - What problem hit you personally?
   - The moment of realization

3. **The Build**
   - What did you create?
   - Key decisions you made
   - Tech stack if relevant
   - Timeline: how long did it take?

4. **The Numbers** (IH loves specifics)
   - Users, signups, revenue if applicable
   - Time invested
   - Costs incurred
   - Even "$0 revenue but 50 signups" is valuable

5. **What Worked / What Didn't**
   - Be brutally honest
   - Specific tactics and results
   - What you'd do differently

6. **Key Takeaways**
   - 3-5 bullet points
   - Actionable for other builders
   - Your genuine advice

7. **Ask**
   - What feedback do you want?
   - What decisions are you facing?
   - Invite the community in

=== GROUPS ===
IH has groups for different topics. Suggest the best fit:
- "Products and Launches" - for launch announcements
- "Growth and Marketing" - for growth tactics
- "Revenue and Finances" - for revenue milestones
- "Technology and Product" - for technical discussions
- "Motivation and Mindset" - for struggles and wins

=== FORMATTING ===
- Long-form is welcome (1000+ words common)
- Use headers to break up sections
- Bullet points for key takeaways
- Bold for emphasis on important points
- Include a TL;DR at top for longer posts

Return JSON:
{{
  "title": "[Specific, honest title with numbers if applicable]",
  "body": "[Full post with sections, headers, bullet points]",
  "post_type": "launch|milestone|growth_update|lessons_learned|ask_ih",
  "group": "[Suggested IH group]",
  "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
  "tldr": "[2-3 sentence summary for top of post]"
}}"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Indie Hackers post content"""
        errors = []
        warnings = []
        suggestions = []

        title = content.title
        body = content.body

        if not title:
            errors.append("Title is required")
        elif len(title) > 200:
            warnings.append(f"Title is long ({len(title)} chars) - consider shortening")

        if not body:
            errors.append("Body is required")
        elif len(body) < 300:
            warnings.append("Post may be too short for IH - community appreciates detail")

        # Check for specifics
        has_numbers = any(char.isdigit() for char in body)
        if not has_numbers:
            suggestions.append("Consider adding specific numbers (users, time spent, costs)")

        # Check for headers/structure
        if '##' not in body and '**' not in body:
            suggestions.append("Consider adding headers or bold text for structure")

        # Check for takeaways
        takeaways = content.metadata.get('key_takeaways', [])
        if not takeaways or len(takeaways) < 2:
            suggestions.append("Add 3-5 key takeaways for readers")

        # Check for question/engagement
        if '?' not in body:
            suggestions.append("Consider ending with a question to drive discussion")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
