from pathlib import Path
from typing import Dict, Any, List

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class RedditAdapter(PlatformAdapter):
    """Reddit platform adapter with subreddit-aware content generation"""

    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Reddit content for multiple subreddits"""
        prompt = self._build_reddit_prompt(content_dna)
        result = self._make_llm_call(prompt)

        # Format the output for preview
        posts = result.get("posts", [])
        body = self._format_posts_preview(posts)

        return PlatformContent(
            platform="reddit",
            title=f"Reddit Strategy: {len(posts)} subreddit posts",
            body=body,
            metadata={
                "posts": posts,
                "subreddit_count": len(posts),
                "strategy": result.get("strategy", "")
            },
            validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        )

    def _build_reddit_prompt(self, content_dna: ContentDNA) -> str:
        """Build Reddit-specific prompt with anti-self-promo awareness"""

        # Intelligent DNA transformation for Reddit - emphasize community value
        value = content_dna.value_proposition
        problem = content_dna.problem_solved
        tech = content_dna.technical_details if content_dna.technical_details else []
        audience = content_dna.target_audience
        unique = content_dna.unique_aspects if content_dna.unique_aspects else []

        return f"""You are crafting Reddit posts. Reddit is hostile to self-promotion but loves genuine value-sharing. Each subreddit is its own culture with strict norms.

=== REDDIT CULTURE (CRITICAL) ===
What Redditors hate (instant downvotes/bans):
- Obvious self-promotion ("Check out my tool!")
- New accounts posting links
- Same content crossposted everywhere
- Marketing language of any kind
- Not being part of the community first
- Ignoring subreddit rules

What works:
- Framing as discovery: "I found/came across/stumbled upon..."
- Framing as discussion: "What's your experience with [problem]? I've been using..."
- Framing as help-seeking: "Looking for feedback on my approach to..."
- Genuine value before any self-mention
- Matching the subreddit's exact tone and norms
- Text posts often outperform link posts

=== CONTENT TO ADAPT ===
What it does: {value}
Problem it solves: {problem}
Technical details: {', '.join(tech)}
Who it's for: {audience}
What's unique: {', '.join(unique)}

=== YOUR TASK ===

1. **Select 3 relevant subreddits** based on the content. Consider:
   - r/programming, r/webdev, r/coding (technical tools)
   - r/SideProject, r/indiehackers (for builders)
   - r/selfhosted (self-hostable tools)
   - r/opensource (open source projects)
   - r/productivity, r/software (general tools)
   - Technology-specific: r/python, r/javascript, r/golang, r/rust, etc.
   - Domain-specific: r/devops, r/datascience, r/machinelearning, etc.

2. **For each subreddit**, create a post that:
   - Matches that subreddit's specific culture and rules
   - Uses appropriate framing (discovery, discussion, or help-seeking)
   - Provides value BEFORE any self-mention
   - Feels like it comes from a community member, not a marketer

=== SUBREDDIT-SPECIFIC GUIDANCE ===

**r/programming** - Highly technical, skeptical audience
- Frame: Technical discussion or interesting discovery
- Focus on implementation details, trade-offs
- Be ready for harsh criticism
- Link to source code if available

**r/SideProject** - Builders supporting builders
- Frame: "Shipped this, learned X, happy to share the journey"
- Personal story + what you learned works best
- Metrics and honest struggles appreciated
- Most self-promo friendly, but still value-first

**r/selfhosted** - Privacy/control-focused users
- Frame: "Found this self-hostable alternative to X"
- Emphasize: no cloud dependency, data ownership
- Docker/deployment details are gold
- "I can host this myself" is the hook

**r/webdev** - Mixed skill levels, practical focus
- Frame: "Built this to solve [common problem]"
- Show and tell format works
- Include technical stack
- Live demo links appreciated

**r/opensource** - Community contribution focus
- Frame: Contribution to ecosystem, not personal promo
- Emphasize: MIT/Apache license, accepting PRs
- "Made this, hope others find it useful"
- Repository link expected

=== POST FORMAT ===

Title:
- 100-300 characters
- No clickbait, no ALL CAPS
- Be specific about what it does
- Include technology if relevant to subreddit

Body:
- Text post preferred (better engagement than link posts)
- Open with context/problem (2-3 sentences)
- Explain value (what does this enable?)
- Brief technical details (if technical subreddit)
- Honest limitations or early-stage disclaimer
- End with invitation for feedback/discussion
- Link at the END, not the beginning
- NO emoji (Reddit culture)

Return JSON:
{{
  "posts": [
    {{
      "subreddit": "subredditname (without r/)",
      "title": "[Post title]",
      "body": "[Full post body]",
      "framing": "discovery|discussion|help_seeking|show_and_tell",
      "flair": "[Suggested post flair if subreddit uses them]",
      "why_this_subreddit": "[One sentence: why this subreddit fits]"
    }}
  ],
  "strategy": "[Brief explanation of the cross-posting strategy and timing]"
}}"""

    def _format_posts_preview(self, posts: List[Dict]) -> str:
        """Format posts for preview display"""
        if not posts:
            return "No posts generated"

        preview = []
        for i, post in enumerate(posts, 1):
            preview.append(f"{'='*60}")
            preview.append(f"POST {i}: r/{post.get('subreddit', 'unknown')}")
            preview.append(f"Framing: {post.get('framing', 'N/A')}")
            preview.append(f"Why: {post.get('why_this_subreddit', 'N/A')}")
            preview.append(f"{'='*60}")
            preview.append(f"\nTitle: {post.get('title', 'No title')}\n")
            preview.append(post.get('body', 'No body'))
            preview.append(f"\nFlair: {post.get('flair', 'None suggested')}")
            preview.append("\n")

        return "\n".join(preview)

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Reddit content"""
        warnings = []
        errors = []
        suggestions = []

        posts = content.metadata.get("posts", [])

        if not posts:
            errors.append("No Reddit posts generated")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings, suggestions=suggestions)

        for post in posts:
            subreddit = post.get('subreddit', 'unknown')
            title = post.get('title', '')
            body = post.get('body', '')

            # Check title length
            if len(title) > 300:
                errors.append(f"r/{subreddit}: Title too long ({len(title)}/300)")

            # Check for self-promo red flags
            promo_flags = ['check out', 'i made', 'i built', 'my new', 'announcing', 'launching']
            for flag in promo_flags:
                if flag in title.lower():
                    warnings.append(f"r/{subreddit}: Title may sound self-promotional ('{flag}')")
                    break

            # Check body length
            if len(body) < 100:
                warnings.append(f"r/{subreddit}: Body seems too short for Reddit")
            if len(body) > 10000:
                warnings.append(f"r/{subreddit}: Body very long - consider condensing")

            # Check for emoji (Reddit culture dislikes them)
            import re
            emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]')
            if emoji_pattern.search(body) or emoji_pattern.search(title):
                warnings.append(f"r/{subreddit}: Contains emoji - not typical for Reddit")

            # Check for link placement
            if body.strip().startswith('http'):
                warnings.append(f"r/{subreddit}: Body starts with link - put context first")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
