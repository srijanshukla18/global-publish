import re
from typing import List
from core.models import PlatformContent, ValidationResult
from core.platform_engine import Validator


class HackerNewsValidator(Validator):
    """Validates content for Hacker News submission"""
    
    def __init__(self, profile: dict):
        self.profile = profile
    
    def validate(self, content: PlatformContent) -> ValidationResult:
        """Comprehensive validation for HN content"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate title
        title_issues = self._validate_title(content.title)
        errors.extend(title_issues['errors'])
        warnings.extend(title_issues['warnings'])
        suggestions.extend(title_issues['suggestions'])
        
        # Validate body
        body_issues = self._validate_body(content.body)
        warnings.extend(body_issues['warnings'])
        suggestions.extend(body_issues['suggestions'])
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_title(self, title: str) -> dict:
        """Validate HN title against rules"""
        errors = []
        warnings = []
        suggestions = []
        
        rules = self.profile.get('content_rules', {}).get('title', {})
        
        # Check length
        max_length = rules.get('max_length', 60)
        if len(title) > max_length:
            errors.append(f"Title too long: {len(title)}/{max_length} chars")
        
        # Check forbidden words
        forbidden = rules.get('forbidden_words', [])
        for word in forbidden:
            if word.lower() in title.lower():
                errors.append(f"Contains forbidden marketing word: '{word}'")
        
        # Check for Show HN format
        if not title.startswith("Show HN:"):
            errors.append("Title should start with 'Show HN:' for tool submissions")
        
        # Check for excessive punctuation
        if '!' in title:
            warnings.append("Exclamation marks discouraged on HN")
        
        if '?' in title and not title.strip().endswith('?'):
            warnings.append("Question marks should only be at end for Ask HN")
        
        # Check for emoji
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]')
        if emoji_pattern.search(title):
            errors.append("Emoji not allowed in HN titles")
        
        # Check for technical specificity
        if len(title.split()) < 4:
            warnings.append("Title may be too generic - add more technical detail")
        
        # Suggestions for improvement
        if "Show HN:" in title and " - " not in title:
            suggestions.append("Consider format: 'Show HN: [Tool] - [What it does]'")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
    
    def _validate_body(self, body: str) -> dict:
        """Validate HN submission body"""
        warnings = []
        suggestions = []
        
        body_lower = body.lower()
        
        # Check for marketing language
        marketing_phrases = [
            'call to action', 'sign up now', 'get started today',
            'don\'t miss out', 'limited time', 'special offer'
        ]
        
        for phrase in marketing_phrases:
            if phrase in body_lower:
                warnings.append(f"Marketing language detected: '{phrase}'")
        
        # Check for technical depth indicators
        technical_indicators = [
            'algorithm', 'implementation', 'architecture', 'benchmark',
            'performance', 'optimization', 'code', 'technical'
        ]
        
        technical_score = sum(1 for indicator in technical_indicators if indicator in body_lower)
        if technical_score < 2:
            suggestions.append("Add more technical details - HN users appreciate depth")
        
        # Check for honesty indicators
        honesty_indicators = [
            'limitation', 'challenge', 'issue', 'problem', 'not yet',
            'working on', 'beta', 'experimental'
        ]
        
        honesty_score = sum(1 for indicator in honesty_indicators if indicator in body_lower)
        if honesty_score == 0:
            suggestions.append("Consider mentioning limitations or challenges for authenticity")
        
        # Check length
        if len(body) < 100:
            warnings.append("Body might be too short - HN users appreciate detailed explanations")
        
        if len(body) > 2000:
            warnings.append("Body might be too long - consider keeping it concise")
        
        return {
            'warnings': warnings,
            'suggestions': suggestions
        }