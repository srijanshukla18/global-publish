import os
import json
import requests
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult, PublishResult


class MediumAdapter(PlatformAdapter):
    """Medium platform adapter with SEO optimization"""
    
    def __init__(self, config_dir: Path):
        super().__init__(config_dir)
        self.api_base = "https://api.medium.com/v1"
        
    def generate_content(self, content_dna: ContentDNA, api_key: str) -> PlatformContent:
        """Generate Medium article optimized for SEO and engagement"""
        prompt = self._build_medium_prompt(content_dna)
        
        result = self._make_llm_call(prompt, api_key)
        
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
        return f"""
You are writing for Medium, a platform that values:
- In-depth, thoughtful content
- Personal storytelling and insights
- Clear structure with headings
- Engaging introductions and conclusions
- SEO-optimized titles

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a Medium article that:
1. Has an SEO-optimized title (≤100 chars)
2. Includes a compelling subtitle
3. Uses personal narrative and insights
4. Has clear section headers
5. Includes actionable takeaways
6. Optimized for Medium's algorithm

Structure:
- Hook: Personal angle or surprising insight
- Problem: Why this matters to readers
- Solution: Your approach with details
- Results: Outcomes and benefits
- Lessons: What readers can apply
- Conclusion: Call to action or reflection

Return JSON:
{{
  "title": "SEO-optimized title under 100 chars",
  "subtitle": "Compelling subtitle that hooks readers",
  "body": "Full markdown article with headers and sections",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
"""
    
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
    
    def post_content(self, content: PlatformContent) -> PublishResult:
        """Post article to Medium (Note: Medium API is deprecated)"""
        try:
            medium_token = os.environ.get("MEDIUM_TOKEN")
            medium_user_id = os.environ.get("MEDIUM_USER_ID")
            
            if not medium_token or not medium_user_id:
                return PublishResult(
                    platform="medium",
                    success=False,
                    error="MEDIUM_TOKEN and MEDIUM_USER_ID environment variables required"
                )
            
            # Prepare article data
            article_data = {
                "title": content.title,
                "contentFormat": "markdown",
                "content": content.body,
                "publishStatus": "public"
            }
            
            # Add tags if available
            tags = content.metadata.get("tags", [])
            if tags:
                article_data["tags"] = tags[:5]  # Medium only uses first 5
            
            # Add canonical URL if available
            canonical_url = content.metadata.get("canonical_url")
            if canonical_url:
                article_data["canonicalUrl"] = canonical_url
            
            # Post to Medium
            headers = {
                "Authorization": f"Bearer {medium_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_base}/users/{medium_user_id}/posts",
                headers=headers,
                json=article_data
            )
            
            if response.status_code == 201:
                result = response.json()
                article_url = result["data"]["url"]
                
                return PublishResult(
                    platform="medium",
                    success=True,
                    url=article_url,
                    metadata={
                        "article_id": result["data"]["id"],
                        "published_at": result["data"]["publishedAt"]
                    }
                )
            else:
                error_msg = f"Medium API error: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('errors', [{}])[0].get('message', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text[:200]}"
                
                return PublishResult(
                    platform="medium",
                    success=False,
                    error=error_msg
                )
            
        except Exception as e:
            return PublishResult(
                platform="medium",
                success=False,
                error=f"Medium posting error: {str(e)}"
            )