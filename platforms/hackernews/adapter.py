from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult
from .validator import HackerNewsValidator


class HackernewsAdapter(PlatformAdapter):
    """Hacker News platform adapter with cultural awareness"""
    
    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)
        self.validator = HackerNewsValidator(self.profile)
    
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate HN-specific content following community guidelines"""
        prompt = self._build_hn_prompt(content_dna)
        
        result = self._make_llm_call(prompt)
        
        return PlatformContent(
            platform="hackernews",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata=result.get("metadata", {}),
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_hn_prompt(self, content_dna: ContentDNA) -> str:
        """Build HN-specific prompt with deep cultural context"""

        # Intelligent DNA transformation for HN - emphasize technical depth
        tech_emphasis = ', '.join(content_dna.technical_details) if content_dna.technical_details else 'Not specified'
        limitations_text = ', '.join(content_dna.limitations) if content_dna.limitations else 'None mentioned'
        metrics_text = ', '.join(content_dna.key_metrics) if content_dna.key_metrics else ''
        unique_text = ', '.join(content_dna.unique_aspects) if content_dna.unique_aspects else ''

        return f"""You are writing a Show HN post. HN is a community of engineers, founders, and intellectually curious people who despise marketing and respect technical honesty.

=== HACKER NEWS CULTURE ===
What HN values:
- Technical depth and implementation details
- Honest discussion of trade-offs and limitations
- Novel approaches to real problems
- Sharing what you learned, not what you're selling
- Engaging with criticism gracefully

What HN despises (instant downvotes):
- Marketing language ("revolutionary", "game-changing", "disrupt", "10x", "AI-powered")
- Superlatives ("best", "amazing", "incredible", "ultimate", "perfect")
- Clickbait or sensationalism
- Hiding limitations or overselling
- Emoji, excessive punctuation, or ALL CAPS
- Generic startup pitch language

=== TITLE RULES ===
- Format: "Show HN: [Name] – [what it does in plain technical terms]"
- Maximum 60 characters
- Use en-dash (–) not hyphen (-) between name and description
- Be specific: "SQLite-based job queue" not "fast job queue"
- Include a technical differentiator if possible

=== CONTENT TO TRANSFORM ===
Core value: {content_dna.value_proposition}
Problem solved: {content_dna.problem_solved}
Technical stack/approach: {tech_emphasis}
What makes it different: {unique_text}
Known limitations: {limitations_text}
Metrics (if any): {metrics_text}
Target users: {content_dna.target_audience}

=== BODY STRUCTURE ===
Write 4-6 paragraphs:

1. **Opening**: State what you built and the core technical problem it solves. No fluff. First sentence should be immediately clear.

2. **Background/Motivation**: Why did you build this? What existing solutions did you try? Why weren't they sufficient? Be specific about technical shortcomings.

3. **Technical Approach**: How does it work? What key architectural decisions did you make? Include specific technologies, algorithms, or techniques. This is where you earn HN's respect.

4. **Challenges & Trade-offs**: What was hard? What trade-offs did you accept? What doesn't it do well? HN respects honesty here more than anywhere else.

5. **Current State & Limitations**: Be upfront about what's missing, what's experimental, what might break.

6. **Closing**: Invite technical discussion. Ask a genuine question you're curious about. Don't ask for upvotes or shares.

=== TONE ===
- Write like you're explaining to a smart colleague, not pitching to investors
- Use "I" not "we" (unless actually a team)
- Be humble but confident in your technical choices
- Show curiosity, not certainty

=== REALITY CHECK (Include as comment in metadata) ===
Before posting, the user should honestly assess:
- Have they commented on other HN posts recently? New accounts with no history get buried.
- Is their account >30 days old with some karma? First-time posters have it harder.
- Is this genuinely interesting to HN, or just interesting to them?
- Timing matters: Tuesday-Thursday, 9-11am EST is peak HN activity.

If they're new to HN, they should consider:
1. Spending 2 weeks commenting helpfully on others' posts first
2. Their first Show HN should be genuinely novel, not just "I made a thing"
3. Even great content from unknown accounts often gets 5-10 points and fades

Return JSON:
{{
  "title": "Show HN: [Name] – [technical description]",
  "body": "[Full post body with paragraphs separated by double newlines]",
  "metadata": {{
    "category": "Show HN",
    "discussion_hook": "[The genuine technical question you're asking the community]",
    "best_posting_time": "Tuesday-Thursday, 9-11am EST",
    "reality_check": "Before posting: (1) Do you have HN karma from commenting? (2) Is your account >30 days old? (3) Is this genuinely novel? If not, build reputation first."
  }}
}}"""
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate content using HN-specific rules"""
        return self.validator.validate(content)
