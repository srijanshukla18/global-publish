import yaml
from pathlib import Path
from typing import List, Dict, Any
from core.models import ContentDNA


class SubredditAnalyzer:
    """Analyzes and selects optimal subreddits for content"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path / "subreddit_data.yaml"
        self.subreddit_data = self._load_subreddit_data()
    
    def _load_subreddit_data(self) -> Dict[str, Any]:
        """Load subreddit rules and culture data"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def select_subreddits(self, content_dna: ContentDNA, max_count: int = 3) -> List[Dict[str, Any]]:
        """Select best subreddits based on content DNA"""
        content_type = content_dna.content_type
        target_audience = content_dna.target_audience.lower()
        
        # Get primary and secondary subreddits for content type
        type_mapping = self.subreddit_data.get('content_types', {})
        primary_subs = type_mapping.get(content_type, {}).get('primary', [])
        secondary_subs = type_mapping.get(content_type, {}).get('secondary', [])
        
        # Score subreddits
        scored_subreddits = []
        
        for sub_id, sub_data in self.subreddit_data['subreddits'].items():
            score = self._calculate_subreddit_score(
                sub_id, sub_data, content_dna, primary_subs, secondary_subs
            )
            
            if score > 0:
                scored_subreddits.append({
                    'subreddit': sub_id,
                    'data': sub_data,
                    'score': score,
                    'reason': self._get_selection_reason(sub_id, sub_data, content_dna)
                })
        
        # Sort by score and return top results
        scored_subreddits.sort(key=lambda x: x['score'], reverse=True)
        return scored_subreddits[:max_count]
    
    def _calculate_subreddit_score(self, sub_id: str, sub_data: Dict, content_dna: ContentDNA, 
                                 primary_subs: List[str], secondary_subs: List[str]) -> float:
        """Calculate relevance score for a subreddit"""
        score = 0.0
        
        # Base score for content type match
        if sub_id in primary_subs:
            score += 10.0
        elif sub_id in secondary_subs:
            score += 5.0
        else:
            score += 1.0
        
        # Audience alignment
        audience_keywords = content_dna.target_audience.lower().split()
        sub_tags = sub_data.get('tags', [])
        
        for keyword in audience_keywords:
            for tag in sub_tags:
                if keyword in tag or tag in keyword:
                    score += 2.0
        
        # Technical depth alignment
        if 'technical' in content_dna.technical_details or len(content_dna.technical_details) > 2:
            if 'technical_depth_required' in sub_data.get('culture', []):
                score += 3.0
        
        # Startup/business alignment
        business_indicators = ['startup', 'business', 'entrepreneur', 'revenue', 'saas']
        content_text = (content_dna.value_proposition + ' ' + content_dna.problem_solved).lower()
        
        if any(indicator in content_text for indicator in business_indicators):
            business_subs = ['sideproject', 'indiehackers', 'entrepreneur', 'saas']
            if sub_id in business_subs:
                score += 4.0
        
        # Self-promotion friendliness
        self_promo = sub_data.get('rules', {}).get('self_promotion', '')
        if 'encouraged' in self_promo:
            score += 2.0
        elif 'allowed' in self_promo:
            score += 1.0
        elif 'limited' in self_promo:
            score -= 1.0
        
        return score
    
    def _get_selection_reason(self, sub_id: str, sub_data: Dict, content_dna: ContentDNA) -> str:
        """Generate human-readable reason for subreddit selection"""
        reasons = []
        
        if content_dna.content_type == 'tool':
            if sub_id in ['programming', 'webdev']:
                reasons.append("technical tool showcase")
            elif sub_id in ['sideproject', 'indiehackers']:
                reasons.append("indie project launch")
        
        culture = sub_data.get('culture', [])
        if 'beginner_friendly' in culture:
            reasons.append("welcoming community")
        if 'entrepreneur_friendly' in culture:
            reasons.append("business-focused audience")
        if 'technical_depth_required' in culture:
            reasons.append("appreciates technical depth")
        
        self_promo = sub_data.get('rules', {}).get('self_promotion', '')
        if 'encouraged' in self_promo:
            reasons.append("encourages self-promotion")
        
        return "; ".join(reasons) if reasons else "general relevance"
    
    def generate_reddit_variants(self, content_dna: ContentDNA, selected_subs: List[Dict]) -> List[Dict[str, str]]:
        """Generate subreddit-specific post variants"""
        variants = []
        
        for sub_info in selected_subs:
            sub_data = sub_info['data']
            sub_id = sub_info['subreddit']
            
            # Customize title and body based on subreddit culture
            if sub_id == 'programming':
                variant = self._generate_programming_variant(content_dna)
            elif sub_id == 'webdev':
                variant = self._generate_webdev_variant(content_dna)
            elif sub_id == 'sideproject':
                variant = self._generate_sideproject_variant(content_dna)
            elif sub_id == 'indiehackers':
                variant = self._generate_indiehackers_variant(content_dna)
            else:
                variant = self._generate_generic_variant(content_dna, sub_data)
            
            variant['subreddit'] = sub_data['name']
            variant['format'] = sub_data.get('rules', {}).get('format', 'text_post')
            variants.append(variant)
        
        return variants
    
    def _generate_programming_variant(self, content_dna: ContentDNA) -> Dict[str, str]:
        """Generate r/programming specific variant"""
        return {
            'title': f"Built {content_dna.value_proposition.split()[0]} - {content_dna.problem_solved}",
            'body': f"Technical implementation: {' '.join(content_dna.technical_details[:2])}\n\n"
                   f"Problem solved: {content_dna.problem_solved}\n\n"
                   f"Key challenges: {' '.join(content_dna.limitations)}\n\n"
                   f"Open to technical feedback and discussion."
        }
    
    def _generate_webdev_variant(self, content_dna: ContentDNA) -> Dict[str, str]:
        """Generate r/webdev specific variant"""
        return {
            'title': f"Show-off: {content_dna.value_proposition}",
            'body': f"Built this tool: {content_dna.problem_solved}\n\n"
                   f"Tech stack: {' '.join(content_dna.technical_details[:3])}\n\n"
                   f"What I learned: {' '.join(content_dna.unique_aspects)}\n\n"
                   f"Happy to answer questions about the implementation!"
        }
    
    def _generate_sideproject_variant(self, content_dna: ContentDNA) -> Dict[str, str]:
        """Generate r/SideProject specific variant"""
        return {
            'title': f"Launched: {content_dna.value_proposition}",
            'body': f"Problem I'm solving: {content_dna.problem_solved}\n\n"
                   f"What makes it different: {' '.join(content_dna.unique_aspects)}\n\n"
                   f"Current status: {' '.join(content_dna.key_metrics) if content_dna.key_metrics else 'Just launched'}\n\n"
                   f"Would love feedback from the community!"
        }
    
    def _generate_indiehackers_variant(self, content_dna: ContentDNA) -> Dict[str, str]:
        """Generate r/indiehackers specific variant"""
        return {
            'title': f"Bootstrapped {content_dna.value_proposition.split()[0]} to solve {content_dna.problem_solved}",
            'body': f"Journey: Started with {content_dna.problem_solved}\n\n"
                   f"Solution: {content_dna.value_proposition}\n\n"
                   f"Metrics: {' '.join(content_dna.key_metrics) if content_dna.key_metrics else 'Early stage'}\n\n"
                   f"What I'd do differently: {' '.join(content_dna.limitations)}\n\n"
                   f"AMA about the journey!"
        }
    
    def _generate_generic_variant(self, content_dna: ContentDNA, sub_data: Dict) -> Dict[str, str]:
        """Generate generic variant for other subreddits"""
        return {
            'title': content_dna.value_proposition,
            'body': f"{content_dna.problem_solved}\n\n"
                   f"Key features: {' '.join(content_dna.unique_aspects)}\n\n"
                   f"Technical approach: {' '.join(content_dna.technical_details[:2])}"
        }