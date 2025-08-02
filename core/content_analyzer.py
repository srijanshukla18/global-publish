import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from .models import ContentDNA
from .cache_manager import CacheManager


class ContentAnalyzer:
    """Extracts the DNA of content for platform-specific adaptation"""
    
    def __init__(self, api_key: str = None, cache_manager: Optional[CacheManager] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.cache_manager = cache_manager
    
    def extract_content_dna(self, content: str, api_key: str = None) -> ContentDNA:
        """Extract content DNA with caching support"""
        if api_key:
            self.api_key = api_key
            self.client = OpenAI(api_key=api_key)
        
        # Check cache first
        if self.cache_manager:
            cached_dna = self.cache_manager.get_cached_dna(content)
            if cached_dna:
                return cached_dna
        
        # Require API key for actual analysis
        if not self.client:
            raise ValueError("OpenAI API key required for content analysis")
        
        # Extract DNA using LLM
        dna = self.analyze(content)
        
        # Cache the result
        if self.cache_manager:
            self.cache_manager.cache_content_dna(content, dna)
        
        return dna
    
    def analyze(self, markdown_content: str) -> ContentDNA:
        """Extract content DNA from markdown"""
        prompt = self._build_analysis_prompt(markdown_content)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._parse_result(result)
            
        except Exception as e:
            raise RuntimeError(f"Content analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, content: str) -> str:
        return f"""
Analyze this content and extract its core DNA. Return a JSON object with these exact keys:

{{
  "value_proposition": "One clear sentence describing the main value",
  "technical_details": ["detail1", "detail2", "detail3"],
  "problem_solved": "What problem this addresses",
  "target_audience": "Primary audience (developers, founders, etc.)",
  "key_metrics": ["metric1", "metric2"],
  "unique_aspects": ["what makes this different"],
  "limitations": ["honest limitations or caveats"],
  "content_type": "tool|tutorial|analysis|announcement|other"
}}

Content to analyze:
---
{content}
---
"""
    
    def _parse_result(self, result: Dict[str, Any]) -> ContentDNA:
        """Parse JSON result into ContentDNA object"""
        return ContentDNA(
            value_proposition=result.get("value_proposition", ""),
            technical_details=result.get("technical_details", []),
            problem_solved=result.get("problem_solved", ""),
            target_audience=result.get("target_audience", ""),
            key_metrics=result.get("key_metrics", []),
            unique_aspects=result.get("unique_aspects", []),
            limitations=result.get("limitations", []),
            content_type=result.get("content_type", "other")
        )