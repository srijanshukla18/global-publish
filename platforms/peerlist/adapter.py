from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class PeerlistAdapter(PlatformAdapter):
    """Peerlist platform adapter using headless browser automation"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        super().__init__(model, api_key)

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Peerlist post content focused on professional achievements"""
        prompt = self._build_peerlist_prompt(content_dna)

        result_text = self.adapt_content(prompt)
        import json
        result = json.loads(result_text)
        
        return PlatformContent(
            platform="peerlist",
            title=result.get("title", ""),
            body=result.get("body", ""),
            metadata={
                "post_type": result.get("post_type", "project"),
                "achievement_focus": result.get("achievement_focus", ""),
                "professional_tone": True
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
    
    def _build_peerlist_prompt(self, content_dna: ContentDNA) -> str:
        """Build Peerlist-specific prompt for professional content"""
        return f"""
You are writing for Peerlist, a professional network for tech professionals that values:
- Career achievements and milestones
- Technical project showcases
- Professional growth stories
- Thought leadership in tech
- Building in public narratives

Content DNA:
- Value Prop: {content_dna.value_proposition}
- Problem: {content_dna.problem_solved}
- Technical: {', '.join(content_dna.technical_details[:3])}
- Audience: {content_dna.target_audience}
- Unique: {', '.join(content_dna.unique_aspects)}
- Type: {content_dna.content_type}

Create a Peerlist post that:
1. Frames content as a professional achievement
2. Highlights technical skills and growth
3. Shows problem-solving capabilities
4. Demonstrates impact and results
5. Maintains professional but approachable tone

Structure:
- Opening: What you built/achieved
- Challenge: Technical/business problem tackled
- Approach: Your solution and skills used
- Impact: Results and what you learned
- Call-to-action: Invite connection/discussion

Keep it concise but impactful - focus on the professional value.

Return JSON:
{{
  "title": "Professional achievement title",
  "body": "Concise post highlighting professional accomplishment",
  "post_type": "project|achievement|learning|thought_leadership",
  "achievement_focus": "What professional value this demonstrates"
}}
"""
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Peerlist content"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate title
        title = content.title
        if not title:
            errors.append("Title is required")
        elif len(title) > 100:
            warnings.append(f"Title might be too long: {len(title)} characters")
        
        # Validate body
        body = content.body
        if not body:
            errors.append("Body content is required")
        elif len(body) > 2000:
            warnings.append("Post might be too long for Peerlist format")
        elif len(body) < 50:
            warnings.append("Post might be too short to be impactful")
        
        # Check for professional tone
        professional_indicators = ['built', 'achieved', 'implemented', 'solved', 'improved', 'learned']
        if not any(indicator in body.lower() for indicator in professional_indicators):
            suggestions.append("Consider emphasizing professional achievements and growth")
        
        # Check for technical details
        if not any(tech in body.lower() for tech in ['technical', 'technology', 'code', 'development', 'engineering']):
            suggestions.append("Add more technical context for Peerlist audience")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )