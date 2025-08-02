
import json
import os
from typing import Dict, Any
import openai

from .models import ContentDNA

class ContentAnalyzer:
    """Analyzes raw content to extract its persistent 'DNA'"""
    
    def __init__(self, model: str = None):
        self.model = model or "gpt-4o"
        # LiteLLM will handle clients dynamically
        
    def analyze(self, raw_content: str) -> ContentDNA:
        """Extract ContentDNA from raw markdown"""
        from litellm import completion
        prompt = f"""
        Analyze the following content and extract its core "DNA".
        This DNA will be used to rewrite the content for various platforms (Hacker News, Twitter, LinkedIn, etc.).

        CONTENT:
        {raw_content}

        TASK:
        Extract the following fields into a precise JSON structure.

        1. value_proposition: A single, compelling sentence describing the core value.
        2. technical_details: A list of specific technical languages, frameworks, or architectural patterns mentioned or implied.
        3. problem_solved: What pain point does this solve?
        4. target_audience: Who is this specifically for? (e.g. "Frontend Devs", "DevOps Engineers")
        5. key_metrics: Any numbers, benchmarks, or results mentioned.
        6. unique_aspects: What makes this different from existing solutions?
        7. limitations: Any mentioned trade-offs or missing features.
        8. content_type: One of ["tool_launch", "tutorial", "opinion", "case_study", "announcement"]
        9. controversy_potential: Would this spark debate? "low" (factual/neutral), "medium" (some may disagree), "high" (provocative take)
        10. novelty_score: How new is this? "incremental" (small improvement), "notable" (interesting approach), "breakthrough" (genuinely new)
        11. show_dont_tell: Does content have demos/screenshots/metrics? "none", "some" (mentioned but not shown), "strong" (clear evidence)
        12. best_fit_communities: List 3-5 specific communities that would care (e.g. "r/golang", "r/selfhosted", "Rust Discord", "DevOps Twitter")

        JSON OUTPUT FORMAT:
        {{
            "value_proposition": "...",
            "technical_details": ["...", "..."],
            "problem_solved": "...",
            "target_audience": "...",
            "key_metrics": ["...", "..."],
            "unique_aspects": ["...", "..."],
            "limitations": ["...", "..."],
            "content_type": "...",
            "controversy_potential": "low|medium|high",
            "novelty_score": "incremental|notable|breakthrough",
            "show_dont_tell": "none|some|strong",
            "best_fit_communities": ["...", "..."]
        }}
        """
        
        try:
            import re
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            content = response.choices[0].message.content
            # Extract JSON from response (handles markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                content = json_match.group(1).strip()
            data = json.loads(content)
            
            return ContentDNA(
                value_proposition=data.get("value_proposition", ""),
                technical_details=data.get("technical_details", []),
                problem_solved=data.get("problem_solved", ""),
                target_audience=data.get("target_audience", ""),
                key_metrics=data.get("key_metrics", []),
                unique_aspects=data.get("unique_aspects", []),
                limitations=data.get("limitations", []),
                content_type=data.get("content_type", "announcement"),
                controversy_potential=data.get("controversy_potential", "low"),
                novelty_score=data.get("novelty_score", "incremental"),
                show_dont_tell=data.get("show_dont_tell", "none"),
                best_fit_communities=data.get("best_fit_communities", [])
            )
            
        except Exception as e:
            print(f"Error in content analysis: {e}")
            # Return empty DNA on failure
            return ContentDNA(
                value_proposition="Error analyzing content",
                technical_details=[],
                problem_solved="",
                target_audience="",
                key_metrics=[],
                unique_aspects=[],
                limitations=[],
                content_type="announcement"
            )
