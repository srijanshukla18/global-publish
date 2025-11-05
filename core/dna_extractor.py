"""Extract content DNA from source material"""
import json
from core.models import ContentDNA
from core.platform_engine import PlatformAdapter


class DNAExtractor:
    """Extracts content DNA from source content"""

    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        self.adapter = PlatformAdapter(model, api_key)

    def extract_dna(self, content: str) -> ContentDNA:
        """Extract structured content DNA from raw content"""
        prompt = f"""
Analyze the following content and extract its core DNA in a structured format.

Content:
{content}

Extract and return JSON with these fields:
- value_proposition: Main value/benefit (1-2 sentences)
- problem_solved: Core problem being addressed
- technical_details: List of 3-5 key technical aspects
- target_audience: Who this is for
- key_metrics: Any metrics, numbers, or achievements mentioned
- unique_aspects: What makes this different/special
- limitations: Honest limitations or challenges (if any mentioned)
- content_type: Type of content (tool, tutorial, analysis, story, announcement, etc.)

Be concise and extract only what's actually present in the content.

Return JSON:
{{
  "value_proposition": "...",
  "problem_solved": "...",
  "technical_details": ["...", "..."],
  "target_audience": "...",
  "key_metrics": ["..."],
  "unique_aspects": ["..."],
  "limitations": ["..."],
  "content_type": "..."
}}
"""

        result_text = self.adapter.adapt_content(prompt)
        try:
            result = json.loads(result_text)

            return ContentDNA(
                value_proposition=result.get("value_proposition", ""),
                problem_solved=result.get("problem_solved", ""),
                technical_details=result.get("technical_details", []),
                target_audience=result.get("target_audience", "general"),
                key_metrics=result.get("key_metrics", []),
                unique_aspects=result.get("unique_aspects", []),
                limitations=result.get("limitations", []),
                content_type=result.get("content_type", "general")
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing DNA extraction result: {e}")
            print(f"Raw result: {result_text[:500]}")
            # Return a minimal DNA object
            return ContentDNA(
                value_proposition=content[:200],
                problem_solved="Content analysis",
                technical_details=[],
                target_audience="general",
                key_metrics=[],
                unique_aspects=[],
                limitations=[],
                content_type="general"
            )
