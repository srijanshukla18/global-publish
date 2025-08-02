import json
from typing import Dict, Any, List
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class TwitterAdapter(PlatformAdapter):
    """Twitter/X platform adapter with thread optimization"""
    
    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)
        
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Twitter thread content optimized for engagement"""
        prompt = self._build_twitter_prompt(content_dna)
        
        result = self._make_llm_call(prompt)
        
        return PlatformContent(
            platform="twitter",
            title=f"Twitter Thread ({result.get('tweet_count', 1)} tweets)",
            body=self._format_thread_preview(result.get("thread", [])),
            metadata={
                "thread": result.get("thread", []),
                "tweet_count": len(result.get("thread", [])),
                "hashtags": result.get("hashtags", []),
                "engagement_strategy": result.get("engagement_strategy", "")
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_twitter_prompt(self, content_dna: ContentDNA) -> str:
        """Build Twitter-specific prompt for thread generation"""

        # Intelligent DNA transformation for Twitter - compress to punchy one-liners
        value_hook = content_dna.value_proposition.split('.')[0] if content_dna.value_proposition else ''
        problem_hook = content_dna.problem_solved.split('.')[0] if content_dna.problem_solved else ''
        tech_stack = ', '.join(content_dna.technical_details[:3]) if content_dna.technical_details else ''
        metrics = content_dna.key_metrics[0] if content_dna.key_metrics else ''
        unique = content_dna.unique_aspects[0] if content_dna.unique_aspects else ''

        return f"""You are writing a Twitter/X thread to announce a tool/project. Twitter rewards punchy, scannable content with strong hooks and genuine engagement.

=== TWITTER/X CULTURE ===
What works:
- Pattern interrupts in the first line (stop the scroll)
- One idea per tweet, white space between thoughts
- Authenticity over polish - write like a human, not a brand
- Specific numbers and concrete outcomes
- Visual content dramatically increases engagement
- Questions at the end drive replies
- Building in public narrative resonates

What fails:
- Wall of text (instant scroll-past)
- Generic claims without specifics
- Hashtag spam (max 2-3 for entire thread, at end)
- Hard sells or pushy CTAs
- Corporate voice or marketing speak
- Starting with "I'm excited to announce..."

=== CONTENT TO TRANSFORM ===
Core hook (compress this): {value_hook}
Problem (make relatable): {problem_hook}
Technical differentiator: {tech_stack}
Key metric/proof: {metrics}
Unique angle: {unique}
Who it's for: {content_dna.target_audience}

=== THREAD STRUCTURE (5-8 tweets) ===

Tweet 1 - THE HOOK (most important):
- First line must stop the scroll
- Pattern interrupt, surprising claim, or relatable pain
- Make reader think "wait, what?"
- Max 240 chars to leave room for engagement

Tweet 2-3 - THE PROBLEM:
- Amplify the pain point everyone knows but nobody talks about
- Make it personal: "Every time I..." or "You know that feeling when..."
- Build tension before revealing solution

Tweet 4-5 - THE SOLUTION:
- Reveal what you built and how it works
- Focus on the "aha moment" not feature list
- Include technical credibility without jargon

Tweet 6 - THE PROOF:
- Specific results, metrics, or outcomes
- Before/after comparison works well
- Screenshots or demos suggested here

Tweet 7-8 - THE CTA:
- End with genuine question (drives replies)
- Make it easy to engage: "What's your experience with X?"
- Don't ask for follows/RTs directly
- Link in final tweet only, or mention "link in bio"

=== RULES ===
- Each tweet MUST be ≤280 characters
- Use line breaks for readability (one thought per line)
- Suggest a visual for tweets where it would help (screenshot, diagram, GIF)
- Only 2-3 hashtags total, placed in final tweet
- Thread should feel like a story, not a listicle

Return JSON:
{{
  "thread": [
    {{
      "tweet_number": 1,
      "content": "[Tweet text with line breaks as \\n]",
      "type": "hook|problem|solution|proof|cta",
      "visual_suggestion": "[Description of suggested image/screenshot/GIF or null]"
    }}
  ],
  "tweet_count": [number],
  "hashtags": ["#tag1", "#tag2"],
  "engagement_strategy": "[One sentence: what response are you optimizing for?]"
}}"""
    
    def _format_thread_preview(self, thread: List[Dict]) -> str:
        """Format thread for preview display"""
        if not thread:
            return "No thread generated"
        
        preview = []
        for tweet in thread:
            tweet_num = tweet.get('tweet_number', '?')
            content = tweet.get('content', '')
            tweet_type = tweet.get('type', '')
            visual = tweet.get('visual_suggestion')
            
            preview.append(f"Tweet {tweet_num} ({tweet_type}):")
            preview.append(f"  {content}")
            if visual:
                preview.append(f"  📷 Visual: {visual}")
            preview.append("")
        
        return "\n".join(preview)
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Twitter thread content"""
        errors = []
        warnings = []
        suggestions = []
        
        thread = content.metadata.get("thread", [])
        
        if not thread:
            errors.append("No thread content generated")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings, suggestions=suggestions)
        
        # Validate each tweet
        for tweet in thread:
            tweet_content = tweet.get('content', '')
            tweet_num = tweet.get('tweet_number', '?')
            
            # Check length
            if len(tweet_content) > 280:
                errors.append(f"Tweet {tweet_num} exceeds 280 characters ({len(tweet_content)})")
            
            if len(tweet_content) > 260:
                warnings.append(f"Tweet {tweet_num} is very long ({len(tweet_content)}/280)")
            
            # Check for engagement elements
            if not any(char in tweet_content for char in ['?', '!', ':']):
                suggestions.append(f"Tweet {tweet_num} could use more engaging punctuation")
        
        # Check thread structure
        hook_tweets = [t for t in thread if t.get('type') == 'hook']
        if not hook_tweets:
            warnings.append("No hook tweet found - first tweet should grab attention")
        
        cta_tweets = [t for t in thread if t.get('type') == 'cta']
        if not cta_tweets:
            warnings.append("No call-to-action tweet found - consider adding engagement driver")
        
        # Check hashtag count
        hashtags = content.metadata.get("hashtags", [])
        if len(hashtags) > 3:
            warnings.append(f"Too many hashtags ({len(hashtags)}) - Twitter recommends max 3 per thread")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )