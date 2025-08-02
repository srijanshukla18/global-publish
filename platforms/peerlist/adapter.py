from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult


class PeerlistAdapter(PlatformAdapter):
    """Peerlist platform adapter using headless browser automation"""
    
    def __init__(self, config_dir: Path, model: str = None):
        super().__init__(config_dir, model)
        
    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        """Generate Peerlist post content focused on professional achievements"""
        prompt = self._build_peerlist_prompt(content_dna)
        
        result = self._make_llm_call(prompt)
        
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

        # Intelligent DNA transformation for Peerlist - emphasize professional growth and metrics
        achievement = content_dna.value_proposition
        skills_used = content_dna.technical_details[:3] if content_dna.technical_details else []
        metrics = content_dna.key_metrics if content_dna.key_metrics else []
        learning = content_dna.limitations  # Reframe as lessons learned

        return f"""You are writing for Peerlist, a professional network popular in the Indian tech/startup ecosystem and growing globally. It's where developers, designers, and founders showcase their work and build professional presence.

=== PEERLIST CULTURE ===
What works:
- Project launches and milestones ("Shipped X this week")
- Building in public updates with real progress
- Professional achievements without bragging
- Technical depth that demonstrates expertise
- Honest learning moments and pivots
- Concise, impactful updates (not long-form)
- Celebrating others' work (community-minded)

What doesn't work:
- Pure self-promotion without value
- Vague "excited to announce" posts
- Too formal/corporate LinkedIn tone
- Too casual Twitter shitposting tone
- Lengthy posts (Peerlist favors brevity)
- Asking for engagement explicitly

=== AUDIENCE ===
- Developers, designers, PMs in tech
- Startup founders and indie hackers
- Heavy Indian tech scene presence
- Career-focused professionals
- People actively building portfolios
- Recruiters and hiring managers browse

=== CONTENT TO TRANSFORM ===
What you shipped: {achievement}
Skills demonstrated: {', '.join(skills_used)}
Metrics/outcomes: {', '.join(metrics) if metrics else 'Early stage'}
Lessons learned: {', '.join(learning) if learning else 'Not specified'}

=== POST STRUCTURE ===

Peerlist posts are SHORT. Think 100-300 words max.

**Opening line:**
- What you built/shipped/achieved
- Be specific, not generic
- Good: "Shipped a real-time transcription tool for macOS"
- Bad: "Excited to share my latest project"

**The Work (2-3 sentences):**
- What problem does it solve?
- Key technical decisions or challenges
- What makes it interesting?

**The Proof (1-2 sentences):**
- Metrics if you have them
- User feedback if early stage
- Technical achievement (performance, scale)

**The Learning (1-2 sentences):**
- What surprised you?
- What would you do differently?
- Frame as professional growth

**Closing:**
- Link to project (if applicable)
- Genuine question or invitation to connect
- NOT "Follow for more" or "Like if you agree"

=== TONE ===
- Professional but human
- Confident but not arrogant
- Between LinkedIn formal and Twitter casual
- First person, active voice
- Show don't tell

=== FORMATTING ===
- Short paragraphs (1-3 sentences)
- Line breaks for readability
- Minimal emoji (0-2 max, professional ones)
- No hashtags (Peerlist doesn't use them like Twitter)

Return JSON:
{{
  "title": "[Short, punchy title - what you shipped/achieved]",
  "body": "[Concise post, 100-300 words, with line breaks between sections]",
  "post_type": "project_launch|milestone|learning|thought_leadership",
  "skills_highlighted": ["[skill1]", "[skill2]", "[skill3]"],
  "project_link": "[URL if applicable, else null]"
}}"""
    
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