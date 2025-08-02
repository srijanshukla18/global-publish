"""Output quality enhancement system"""
import json
from core.platform_engine import PlatformAdapter


class QualityEnhancer:
    """Improves output quality through prompt enhancement and refinement"""

    # Universal quality guidelines that apply to all platforms
    QUALITY_GUIDELINES = """
CRITICAL TONE & QUALITY REQUIREMENTS:

1. AUTHENTICITY OVER HYPE
   ❌ NEVER use: "revolutionary", "game-changing", "amazing", "incredible", "perfect"
   ✓ Instead: Be specific about what it does and why it matters

2. NATURAL LANGUAGE
   ❌ NEVER: "Unlock the power of", "Supercharge your", "Transform your life"
   ✓ Instead: Direct, conversational language like you're explaining to a colleague

3. SPECIFIC OVER VAGUE
   ❌ NEVER: "industry-leading solution", "cutting-edge technology", "next-generation"
   ✓ Instead: Concrete details, numbers, actual features

4. HUMBLE CONFIDENCE
   ❌ NEVER: Arrogant claims, excessive self-promotion, "best ever"
   ✓ Instead: Confident but honest about limitations and trade-offs

5. STORY OVER SALES PITCH
   ❌ NEVER: Pure feature lists, call-to-action spam, "sign up now"
   ✓ Instead: Why you built it, what problem it solves, how it works

6. TECHNICAL BUT ACCESSIBLE
   ❌ NEVER: Either too much jargon OR dumbing down everything
   ✓ Instead: Technical accuracy with clear explanations

AVOID THESE PHRASES ENTIRELY:
- "Empower users to..."
- "Seamless experience"
- "Leverage the power of..."
- "Unlock your potential"
- "Take your [X] to the next level"
- "Don't miss out"
- "Limited time"
- "Best solution for..."

TONE EXAMPLES:

❌ BAD TONE (Marketing Fluff):
"Revolutionize your workflow with our game-changing platform that empowers you to unlock
unprecedented productivity! Don't miss this amazing opportunity to transform your business."

✓ GOOD TONE (Authentic & Clear):
"I built this because I was tired of switching between 5 different tools just to track my tasks.
It combines a kanban board with time tracking. Not perfect, but it saves me about 2 hours per week."

❌ BAD TONE (Too Generic):
"Our innovative solution provides cutting-edge features that deliver exceptional results."

✓ GOOD TONE (Specific & Real):
"It uses PostgreSQL for storage and React for the UI. The main feature is real-time collaboration
— up to 10 people can edit the same document simultaneously. Still working on mobile support."
"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        self.adapter = PlatformAdapter(model, api_key)

    @staticmethod
    def enhance_prompt(base_prompt: str) -> str:
        """Add quality guidelines to any prompt"""
        return f"""
{QualityEnhancer.QUALITY_GUIDELINES}

{base_prompt}

REMINDER: Follow the tone guidelines above. Be authentic, specific, and avoid marketing language.
"""

    def refine_output(self, original_output: str, platform: str) -> str:
        """
        Use LLM to critique and improve the output quality
        Returns refined version with better tone
        """
        refinement_prompt = f"""
You are a content quality editor. Review the following {platform} post and improve its tone and quality.

Original post:
{original_output}

QUALITY CHECKLIST:
1. Remove all marketing buzzwords and hype language
2. Make language more natural and conversational
3. Add specific details where vague claims exist
4. Make it more authentic and less salesy
5. Ensure technical accuracy is maintained
6. Keep platform-specific guidelines in mind

{QualityEnhancer.QUALITY_GUIDELINES}

Return the IMPROVED version of the post maintaining the same structure but with significantly better tone.
Return ONLY the improved post text, no explanations.
"""

        try:
            refined = self.adapter.adapt_content(refinement_prompt)
            return refined
        except Exception as e:
            print(f"Warning: Refinement failed: {e}")
            return original_output

    def validate_tone_quality(self, text: str) -> dict:
        """
        Analyze text for tone quality issues
        Returns dict with warnings about tone problems
        """
        issues = []
        suggestions = []

        # Check for forbidden phrases
        forbidden_phrases = [
            "revolutionary", "game-changing", "amazing", "incredible", "perfect",
            "unlock", "empower", "leverage", "seamless", "cutting-edge",
            "next-generation", "industry-leading", "best solution", "don't miss",
            "transform your", "supercharge", "unprecedented"
        ]

        text_lower = text.lower()
        for phrase in forbidden_phrases:
            if phrase in text_lower:
                issues.append(f"Marketing buzzword detected: '{phrase}'")

        # Check for excessive enthusiasm
        exclamation_count = text.count('!')
        if exclamation_count > 3:
            issues.append(f"Too many exclamation marks ({exclamation_count}) - sounds overly enthusiastic")

        # Check for vague claims
        vague_phrases = ["solution", "platform", "experience", "ecosystem"]
        vague_count = sum(1 for phrase in vague_phrases if phrase in text_lower)
        if vague_count > 3:
            suggestions.append("Consider being more specific - detected generic tech jargon")

        # Check for authentic voice indicators
        authentic_indicators = ["i built", "i made", "we created", "struggled with", "limitation", "challenge"]
        if not any(indicator in text_lower for indicator in authentic_indicators):
            suggestions.append("Consider adding personal context or honest challenges faced")

        return {
            "issues": issues,
            "suggestions": suggestions,
            "quality_score": max(0, 100 - (len(issues) * 15) - (len(suggestions) * 5))
        }
