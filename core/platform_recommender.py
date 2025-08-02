from dataclasses import dataclass
from typing import List, Dict
from .models import ContentDNA


@dataclass
class PlatformRecommendation:
    """Recommendation for a single platform"""
    platform: str
    fit: str  # "strong", "moderate", "weak", "skip"
    reason: str


class PlatformRecommender:
    """Decides which platforms fit the content - used by LLM, not hardcoded rules"""

    PLATFORM_PROFILES = {
        "hackernews": {
            "audience": "engineers, founders, intellectually curious hackers",
            "sweet_spot": ["tool_launch", "case_study", "opinion"],
            "content_types_avoid": ["tutorial"],  # tutorials rarely do well
            "needs": "technical depth, novelty, honest trade-offs",
            "red_flags": "marketing speak, no technical substance, beginner content"
        },
        "twitter": {
            "audience": "tech twitter, founders, developers",
            "sweet_spot": ["tool_launch", "opinion", "announcement"],
            "content_types_avoid": [],
            "needs": "punchy hooks, visual content, thread-worthy insights",
            "red_flags": "dry content, no hook, nothing quotable"
        },
        "reddit": {
            "audience": "varies wildly by subreddit",
            "sweet_spot": ["tool_launch", "tutorial", "case_study"],
            "content_types_avoid": [],
            "needs": "genuine value, subreddit-specific framing, not self-promo",
            "red_flags": "obvious marketing, wrong subreddit, no community fit"
        },
        "medium": {
            "audience": "general tech readers, professionals",
            "sweet_spot": ["tutorial", "case_study", "opinion"],
            "content_types_avoid": ["announcement"],
            "needs": "personal narrative, lessons learned, 1500+ words",
            "red_flags": "too short, no personal angle, pure announcement"
        },
        "devto": {
            "audience": "developers, beginners welcome",
            "sweet_spot": ["tutorial", "tool_launch", "case_study"],
            "content_types_avoid": [],
            "needs": "code examples, beginner-friendly, practical",
            "red_flags": "no code, too theoretical, gatekeeping tone"
        },
        "linkedin": {
            "audience": "professionals, b2b, career-focused",
            "sweet_spot": ["announcement", "case_study", "opinion"],
            "content_types_avoid": ["tutorial"],
            "needs": "professional angle, lessons, achievement framing",
            "red_flags": "too technical, no professional relevance"
        },
        "producthunt": {
            "audience": "early adopters, product people, makers",
            "sweet_spot": ["tool_launch"],
            "content_types_avoid": ["tutorial", "opinion", "case_study"],
            "needs": "launchable product, visuals, clear value prop",
            "red_flags": "not a product, no demo, just an article"
        },
        "indiehackers": {
            "audience": "indie founders, bootstrappers, solopreneurs",
            "sweet_spot": ["tool_launch", "case_study"],
            "content_types_avoid": [],
            "needs": "founder story, metrics transparency, lessons",
            "red_flags": "no founder angle, VC-speak, no indie relevance"
        },
        "substack": {
            "audience": "newsletter readers, thought leadership seekers",
            "sweet_spot": ["opinion", "case_study"],
            "content_types_avoid": ["announcement"],
            "needs": "distinctive voice, deep insights, email-worthy",
            "red_flags": "shallow, no unique perspective, pure promo"
        },
        "hashnode": {
            "audience": "developers, technical bloggers",
            "sweet_spot": ["tutorial", "tool_launch", "case_study"],
            "content_types_avoid": [],
            "needs": "technical depth, code, practical value",
            "red_flags": "no code, not developer-focused"
        },
        "lobsters": {
            "audience": "senior engineers, systems programmers, strict quality",
            "sweet_spot": ["tool_launch", "case_study"],
            "content_types_avoid": ["opinion", "announcement"],
            "needs": "technical excellence, programming focus, novel approach",
            "red_flags": "marketing, business focus, not programming-related"
        },
        "peerlist": {
            "audience": "indian tech professionals, career showcasing",
            "sweet_spot": ["tool_launch", "announcement", "case_study"],
            "content_types_avoid": [],
            "needs": "professional achievement angle, brevity",
            "red_flags": "too long, no professional relevance"
        }
    }

    def build_recommendation_prompt(self, dna: ContentDNA) -> str:
        """Build prompt for LLM to decide platform fit"""

        platform_descriptions = "\n".join([
            f"- **{name}**: {profile['audience']}. Best for: {', '.join(profile['sweet_spot'])}. Needs: {profile['needs']}. Avoid if: {profile['red_flags']}"
            for name, profile in self.PLATFORM_PROFILES.items()
        ])

        return f"""Analyze this content and decide which platforms are a good fit.

=== CONTENT DNA ===
Type: {dna.content_type}
Value Proposition: {dna.value_proposition}
Target Audience: {dna.target_audience}
Technical Details: {', '.join(dna.technical_details) if dna.technical_details else 'None specified'}
Problem Solved: {dna.problem_solved}
Unique Aspects: {', '.join(dna.unique_aspects) if dna.unique_aspects else 'None specified'}
Limitations: {', '.join(dna.limitations) if dna.limitations else 'None mentioned'}
Key Metrics: {', '.join(dna.key_metrics) if dna.key_metrics else 'None'}
Controversy Potential: {dna.controversy_potential}
Novelty: {dna.novelty_score}
Show Don't Tell (demos/screenshots/metrics): {dna.show_dont_tell}
Best Fit Communities Suggested: {', '.join(dna.best_fit_communities) if dna.best_fit_communities else 'Not specified'}

=== PLATFORMS ===
{platform_descriptions}

=== TASK ===
For each platform, decide:
- "strong" = Great fit, definitely generate content
- "moderate" = Decent fit, worth generating
- "skip" = Poor fit, don't waste time

Be ruthless. If content type doesn't match platform, skip it.
A tool_launch doesn't belong on Substack. A tutorial doesn't belong on Product Hunt.

Return JSON array:
[
  {{"platform": "hackernews", "fit": "strong|moderate|skip", "reason": "one sentence why"}},
  {{"platform": "twitter", "fit": "strong|moderate|skip", "reason": "..."}},
  ...for all 12 platforms
]

Only return the JSON array, no other text."""

    def parse_recommendations(self, llm_response: str) -> List[PlatformRecommendation]:
        """Parse LLM response into recommendations"""
        import json
        import re

        # Extract JSON from potential markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', llm_response)
        if json_match:
            llm_response = json_match.group(1).strip()

        try:
            data = json.loads(llm_response)
            return [
                PlatformRecommendation(
                    platform=item.get("platform", ""),
                    fit=item.get("fit", "skip"),
                    reason=item.get("reason", "")
                )
                for item in data
            ]
        except json.JSONDecodeError:
            # Fallback: return all as moderate
            return [
                PlatformRecommendation(platform=p, fit="moderate", reason="Failed to parse, defaulting")
                for p in self.PLATFORM_PROFILES.keys()
            ]

    def get_platforms_to_generate(self, recommendations: List[PlatformRecommendation]) -> List[str]:
        """Filter to only strong and moderate fits"""
        return [r.platform for r in recommendations if r.fit in ("strong", "moderate")]

    def get_skipped_platforms(self, recommendations: List[PlatformRecommendation]) -> List[PlatformRecommendation]:
        """Get platforms that were skipped with reasons"""
        return [r for r in recommendations if r.fit == "skip"]
