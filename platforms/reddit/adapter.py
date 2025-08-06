import json
from typing import Dict, Any
from pathlib import Path

from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult
from .analyzer import SubredditAnalyzer


class RedditAdapter(PlatformAdapter):
    """Reddit platform adapter with smart subreddit selection"""
    
    def __init__(self, config_dir: Path):
        super().__init__(config_dir)
        self.analyzer = SubredditAnalyzer(config_dir)
    
    def generate_content(self, content_dna: ContentDNA, api_key: str) -> PlatformContent:
        """Generate Reddit content with smart subreddit selection"""
        
        # Select optimal subreddits
        suggested_subs = self.analyzer.select_subreddits(content_dna, max_count=3)
        
        # Get user confirmation for subreddit selection
        confirmed_subs = self._confirm_subreddit_selection(suggested_subs, content_dna)
        
        # Generate subreddit-specific variants
        variants = self.analyzer.generate_reddit_variants(content_dna, confirmed_subs)
        
        # Build summary for the main content
        subreddit_list = [sub['data']['name'] for sub in confirmed_subs]
        
        title = f"Reddit Strategy: {len(variants)} targeted subreddits"
        body = self._format_reddit_strategy(variants, confirmed_subs)
        
        metadata = {
            "subreddit_count": len(variants),
            "selected_subreddits": subreddit_list,
            "variants": variants,
            "selection_data": selected_subs
        }
        
        return PlatformContent(
            platform="reddit",
            title=title,
            body=body,
            metadata=metadata,
            validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        )
    
    def _format_reddit_strategy(self, variants: list, selected_subs: list) -> str:
        """Format Reddit posting strategy for preview"""
        strategy = []
        
        for i, (variant, sub_info) in enumerate(zip(variants, selected_subs), 1):
            strategy.append(f"Post {i}: {variant['subreddit']}")
            strategy.append(f"Reason: {sub_info['reason']}")
            strategy.append(f"Title: {variant['title']}")
            strategy.append(f"Body preview: {variant['body'][:100]}...")
            strategy.append(f"Format: {variant['format']}")
            strategy.append("")
        
        return "\n".join(strategy)
    
    def _confirm_subreddit_selection(self, suggested_subs: list, content_dna: ContentDNA) -> list:
        """Get user confirmation for subreddit selection"""
        print("\n" + "="*60)
        print("🎯 REDDIT SUBREDDIT SELECTION")
        print("="*60)
        print(f"Content Type: {content_dna.content_type}")
        print(f"Target Audience: {content_dna.target_audience}")
        print(f"Problem Solved: {content_dna.problem_solved[:100]}...")
        
        print(f"\n🤖 AI suggests posting to these {len(suggested_subs)} subreddits:")
        for i, sub in enumerate(suggested_subs, 1):
            sub_data = sub['data']
            print(f"{i}. r/{sub_data['name']} ({sub_data['members']:,} members)")
            print(f"   Reason: {sub['reason']}")
            print(f"   Rules: {sub_data['rules'][:80]}...")
            print()
        
        while True:
            choice = input("✅ Accept these subreddits? (y/n/edit): ").lower().strip()
            
            if choice == 'y' or choice == 'yes':
                print("✅ Proceeding with suggested subreddits\n")
                return suggested_subs
            
            elif choice == 'n' or choice == 'no':
                print("❌ Subreddit selection rejected.")
                return self._get_user_custom_subreddits(content_dna)
            
            elif choice == 'edit' or choice == 'e':
                return self._edit_subreddit_selection(suggested_subs, content_dna)
            
            else:
                print("Please enter 'y' (yes), 'n' (no), or 'edit'")
    
    def _get_user_custom_subreddits(self, content_dna: ContentDNA) -> list:
        """Let user specify their own subreddits"""
        print("\n📝 Enter your preferred subreddits (without r/ prefix):")
        print("Examples: productivity, sideproject, entrepreneur, startups")
        
        while True:
            user_input = input("Subreddits (comma-separated): ").strip()
            if user_input:
                break
            print("Please enter at least one subreddit")
        
        # Parse user input
        subreddit_names = [name.strip().lower() for name in user_input.split(",")]
        
        # Create basic subreddit data for user choices
        custom_subs = []
        for name in subreddit_names:
            custom_subs.append({
                'data': {
                    'name': name,
                    'members': 'Unknown',
                    'rules': 'User selected - please verify rules manually',
                    'optimal_times': [13, 14, 15, 16, 17]  # Default times
                },
                'reason': 'User specified'
            })
        
        print(f"✅ Using your custom subreddits: {', '.join([f'r/{s}' for s in subreddit_names])}\n")
        return custom_subs
    
    def _edit_subreddit_selection(self, suggested_subs: list, content_dna: ContentDNA) -> list:
        """Let user edit the suggested list"""
        print("\n✏️  Edit subreddit selection:")
        
        # Show current list with numbers
        current_subs = []
        for i, sub in enumerate(suggested_subs, 1):
            sub_name = sub['data']['name']
            current_subs.append(sub_name)
            print(f"{i}. r/{sub_name}")
        
        print(f"\nCurrent: {', '.join([f'r/{s}' for s in current_subs])}")
        print("Enter new list (comma-separated, without r/ prefix):")
        print("Or press Enter to keep current selection")
        
        user_input = input("New subreddits: ").strip()
        
        if not user_input:
            print("✅ Keeping original suggestions\n")
            return suggested_subs
        
        # Parse new selection
        new_names = [name.strip().lower() for name in user_input.split(",")]
        
        # Create edited list - try to preserve data from suggestions where possible
        edited_subs = []
        for name in new_names:
            # Check if this was in the original suggestions
            found = False
            for orig_sub in suggested_subs:
                if orig_sub['data']['name'].lower() == name:
                    edited_subs.append(orig_sub)
                    found = True
                    break
            
            # If not found, create basic entry
            if not found:
                edited_subs.append({
                    'data': {
                        'name': name,
                        'members': 'Unknown',
                        'rules': 'Please verify subreddit rules manually',
                        'optimal_times': [13, 14, 15, 16, 17]
                    },
                    'reason': 'User added'
                })
        
        print(f"✅ Updated subreddits: {', '.join([f'r/{s}' for s in new_names])}\n")
        return edited_subs
    
    def validate_content(self, content: PlatformContent) -> ValidationResult:
        """Validate Reddit content"""
        warnings = []
        errors = []
        suggestions = []
        
        variants = content.metadata.get("variants", [])
        
        for variant in variants:
            # Check title length
            if len(variant['title']) > 300:
                errors.append(f"Title too long for {variant['subreddit']}: {len(variant['title'])}/300")
            
            # Check body length
            if len(variant['body']) > 10000:
                warnings.append(f"Body very long for {variant['subreddit']}: {len(variant['body'])}/10000")
            
            # Check for spam indicators
            if variant['body'].count('http') > 2:
                warnings.append(f"Multiple links detected in {variant['subreddit']} - may trigger spam filters")
        
        # Check account requirements
        for sub_info in content.metadata.get("selection_data", []):
            sub_data = sub_info['data']
            karma_req = sub_data.get('rules', {}).get('karma_requirement', 0)
            age_req = sub_data.get('rules', {}).get('account_age_days', 0)
            
            if karma_req > 0:
                suggestions.append(f"{sub_data['name']} requires {karma_req} karma")
            if age_req > 0:
                suggestions.append(f"{sub_data['name']} requires {age_req} day old account")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )