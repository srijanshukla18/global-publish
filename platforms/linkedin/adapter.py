from pathlib import Path
from typing import Dict, Any

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class LinkedinAdapter(PlatformAdapter):
    """LinkedIn platform adapter optimized for professional reach"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate LinkedIn post optimized for algorithm and engagement"""
        prompt = self._build_linkedin_prompt(content_dna)
        result = self._make_llm_call(prompt)

        return PlatformContent(
            platform="linkedin",
            title=result.get("hook", "LinkedIn Post"),
            body=result.get("body", ""),
            metadata={
                "hashtags": result.get("hashtags", []),
                "comment_with_link": result.get("comment_with_link", ""),
                "engagement_hook": result.get("engagement_hook", "")
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def _build_linkedin_prompt(self, content_dna: ContentDNA) -> str:
        """Build LinkedIn-specific prompt with algorithm awareness"""

        # Intelligent DNA transformation for LinkedIn - emphasize problem/solution and professional insight
        problem = content_dna.problem_solved
        solution = content_dna.value_proposition
        metrics = content_dna.key_metrics if content_dna.key_metrics else []
        lessons = content_dna.limitations  # Reframe as lessons
        tech = content_dna.technical_details[:2] if content_dna.technical_details else []

        return f"""You are writing a LinkedIn post. LinkedIn rewards authentic professional narratives. The algorithm heavily penalizes external links in the main post body.

=== LINKEDIN ALGORITHM (CRITICAL) ===
What the algorithm rewards:
- First 2 lines visible before "...see more" - MUST hook the reader
- Dwell time: longer reads = more reach
- Comments > reactions (ask questions that invite responses)
- Native content: NO external links in post body (kills reach by 50%+)
- Text-only posts often outperform image posts
- Line breaks for mobile readability

What kills reach:
- External links in post body (put in FIRST COMMENT instead)
- Hashtags in the middle of text (put at bottom)
- Tagging too many people (looks spammy)
- "I'm excited to announce" (overused, algorithm deprioritizes)
- Corporate/formal tone (feels inauthentic)
- Asking for likes/shares directly

=== LINKEDIN CULTURE ===
What resonates:
- Personal stories with professional lessons
- "Here's what I learned" narratives
- Contrarian takes on industry topics
- Celebrating others (humblebrags work when you lift others)
- Vulnerability: what went wrong, what you learned
- Concrete numbers and results
- Building in public updates

What falls flat:
- Pure self-promotion
- Corporate press release tone
- No personal stake or story
- Generic advice without personal experience
- Walls of text without line breaks

=== CONTENT TO TRANSFORM ===
Problem you solved: {problem}
What you built: {solution}
Results/metrics: {', '.join(metrics) if metrics else 'Early stage'}
Lessons learned: {', '.join(lessons) if lessons else 'Not specified'}
Technical context: {', '.join(tech) if tech else 'N/A'}

=== POST STRUCTURE ===

**Hook (First 2 lines - CRITICAL):**
- This is what shows before "see more"
- Pattern interrupt, surprising insight, or relatable pain
- NOT "I'm excited to announce..."
- Good: "I used to think AI pair programmers were magic—until I asked one a simple question."
- Good: "The third time my script crashed at 3 AM, I knew something had to change."

**The Story (3-5 short paragraphs):**
- One idea per paragraph
- Short sentences
- Line break between EVERY paragraph (mobile readability)
- Personal narrative: what happened, what you tried, what worked
- Include a turning point or realization

**The Insight (1-2 paragraphs):**
- What did you learn?
- What would you tell others facing this?
- Make it actionable

**The Close:**
- Question that invites comments (NOT "thoughts?" - too generic)
- Specific question: "Have you faced [specific problem]? What worked for you?"
- Or: "What's one thing you wish you knew about [topic]?"

**Formatting:**
- Hashtags at the VERY END (3-5 max)
- One blank line between paragraphs
- NO external links in post body
- Keep under 1,300 characters if possible (shows full post without "see more" on some clients)
- Up to 3,000 characters if story needs it

=== FIRST COMMENT STRATEGY ===
Since links kill reach, put your link in the first comment:
"Link to [what it is]: [URL]"

Prepare this text but don't include it in the main post.

Return JSON:
{{
  "hook": "[First 2 lines that appear before 'see more']",
  "body": "[Full post with line breaks between paragraphs, hashtags at end]",
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "comment_with_link": "[Text for first comment with the link]",
  "engagement_hook": "[The specific question you're asking at the end]"
}}"""

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate LinkedIn post content"""
        errors = []
        warnings = []
        suggestions = []

        body = content.body

        if not body:
            errors.append("Post body is required")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings, suggestions=suggestions)

        # Check length
        if len(body) > 3000:
            errors.append(f"Post too long: {len(body)}/3000 characters")
        elif len(body) > 1300:
            warnings.append(f"Post length ({len(body)} chars) will be truncated with 'see more'")

        # Check for external links (algorithm killer)
        if 'http://' in body or 'https://' in body:
            errors.append("External link in post body kills reach - move to first comment")

        # Check for overused phrases
        overused = ['excited to announce', 'thrilled to share', 'proud to announce', 'delighted to']
        for phrase in overused:
            if phrase.lower() in body.lower():
                warnings.append(f"Overused phrase detected: '{phrase}' - algorithm may deprioritize")
                break

        # Check for line breaks (mobile readability)
        paragraphs = body.split('\n\n')
        if len(paragraphs) < 3:
            suggestions.append("Add more line breaks between paragraphs for mobile readability")

        # Check for engagement hook
        if '?' not in body:
            suggestions.append("Consider ending with a question to drive comments")

        # Check hashtag placement
        lines = body.strip().split('\n')
        if lines and '#' in lines[0]:
            warnings.append("Hashtags should be at the end, not the beginning")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
