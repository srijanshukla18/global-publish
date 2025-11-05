
import litellm
from dotenv import load_dotenv
import os

load_dotenv()

# Universal quality guidelines applied to all platforms
QUALITY_TONE_GUIDELINES = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL TONE REQUIREMENTS - READ CAREFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BANNED PHRASES (DO NOT USE THESE UNDER ANY CIRCUMSTANCES):
❌ "revolutionary" "game-changing" "amazing" "incredible" "perfect" "best"
❌ "unlock" "empower" "leverage" "seamless" "cutting-edge" "next-generation"
❌ "transform your" "supercharge" "unprecedented" "industry-leading"
❌ "Don't miss out" "Limited time" "Sign up now" "Take your X to the next level"

REQUIRED TONE:
✓ Authentic - Write like a real person, not a marketer
✓ Specific - Use concrete details, numbers, actual features (not vague claims)
✓ Humble - Honest about limitations and trade-offs
✓ Natural - Conversational language, as if explaining to a colleague
✓ Story-focused - Why you built it, what problem it solves

BAD EXAMPLE (Marketing fluff):
"Revolutionize your workflow with our game-changing platform! Unlock unprecedented
productivity with our seamless, cutting-edge solution!"

GOOD EXAMPLE (Authentic & Clear):
"I built this because I was frustrated switching between 5 tools to track tasks.
It combines kanban with time tracking. Saves me about 2 hours/week. Still working
on mobile support, but desktop version is solid."

REMEMBER: Be authentic. Be specific. Avoid hype. Tell a story.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

class PlatformAdapter:
    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.enhance_quality = True  # Enable quality enhancement by default

    def adapt_content(self, full_prompt, enhance_quality=True):
        """
        Adapts the content to a specific platform based on the full prompt.
        Automatically enhances prompts with quality guidelines.
        """
        # Enhance prompt with quality guidelines
        if enhance_quality and self.enhance_quality:
            enhanced_prompt = f"{QUALITY_TONE_GUIDELINES}\n\n{full_prompt}\n\nREMINDER: Follow the tone guidelines above strictly."
        else:
            enhanced_prompt = full_prompt

        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": enhanced_prompt}],
            api_key=self.api_key
        )
        return response.choices[0].message.content


class Validator:
    """Base class for platform-specific content validators"""

    def validate(self, content):
        """
        Validate content for platform requirements.
        Should be overridden by specific validators.
        """
        raise NotImplementedError("Subclasses must implement validate()")
