import json
from typing import Dict, Any, List
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class TwitterAdapter(PlatformAdapter):
    """Twitter/X platform adapter with thread optimization"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        super().__init__(model, api_key)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Twitter thread content optimized for engagement"""
        prompt = self._build_twitter_prompt(content_dna)

        result_text = self.adapt_content(prompt)
        result = json.loads(result_text)
        
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
        return f"""
You are a Twitter engagement expert creating viral thread content.

Twitter Culture:
- Fast-paced, attention-grabbing content
- Emphasizes engagement, retweets, and replies
- Values authenticity and personality
- Prefers threads for complex topics
- Visual content performs well

Thread Structure Best Practices:
- Hook tweet must grab attention immediately
- Use numbered threads for clarity
- Include questions to drive engagement
- End with clear call-to-action
- Mix information with personality

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a Twitter thread that:
1. HOOK tweet: Grab attention with surprising fact or bold claim (240 chars max)
2. PROBLEM tweets: Amplify the pain point (2-3 tweets)
3. SOLUTION tweets: Introduce your approach (2-3 tweets)
4. RESULTS tweets: Share outcomes/benefits (1-2 tweets)
5. CTA tweet: Subtle call-to-action with engagement driver (260 chars max)

Rules:
- Each tweet ≤280 characters
- Include visual content suggestions
- Add relevant hashtags (max 3 per thread)
- Create conversation starters
- Include engagement hooks (questions, bold claims)

Return JSON:
{{
  "thread": [
    {{"tweet_number": 1, "content": "hook tweet", "type": "hook", "visual_suggestion": "screenshot of problem"}},
    {{"tweet_number": 2, "content": "problem amplification", "type": "problem", "visual_suggestion": null}},
    ...
  ],
  "tweet_count": 6,
  "hashtags": ["#buildinpublic", "#indiehacker"],
  "engagement_strategy": "Ask followers to share their experience in replies"
}}
"""
    
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