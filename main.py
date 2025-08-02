#!/usr/bin/env python3
"""
Global Publisher CLI - Intelligent multi-platform content publishing

Created by: Claude Code
Architecture: Two-phase LLM system with platform-aware content adaptation
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.content_analyzer import ContentAnalyzer
from core.scheduler import SmartScheduler
from core.cache_manager import CacheManager
from core.models import ContentDNA, PlatformContent, PublishResult

# Platform adapters
from platforms.hackernews.adapter import HackernewsAdapter
from platforms.reddit.adapter import RedditAdapter
from platforms.twitter.adapter import TwitterAdapter
from platforms.medium.adapter import MediumAdapter
from platforms.devto.adapter import DevtoAdapter
from platforms.peerlist.adapter import PeerlistAdapter


class GlobalPublisher:
    """Main CLI application for intelligent multi-platform publishing"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.analyzer = ContentAnalyzer(cache_manager=self.cache_manager)
        self.scheduler = SmartScheduler()
        self.platforms = self._initialize_platforms()
        
    def _initialize_platforms(self) -> Dict[str, Any]:
        """Initialize all platform adapters"""
        base_dir = Path(__file__).parent
        return {
            'hackernews': HackernewsAdapter(base_dir / 'platforms' / 'hackernews'),
            'reddit': RedditAdapter(base_dir / 'platforms' / 'reddit'),
            'twitter': TwitterAdapter(base_dir / 'platforms' / 'twitter'),
            'medium': MediumAdapter(base_dir / 'platforms' / 'medium'),
            'devto': DevtoAdapter(base_dir / 'platforms' / 'devto'),
            'peerlist': PeerlistAdapter(base_dir / 'platforms' / 'peerlist')
        }
    
    def analyze_content(self, content_file: str, api_key: str) -> ContentDNA:
        """Extract content DNA from source material"""
        print("🧬 Extracting content DNA...")
        
        # Read content from file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract DNA using LLM (with caching)
        content_dna = self.analyzer.extract_content_dna(content, api_key)
        
        print(f"✅ Content DNA extracted:")
        print(f"   Problem: {content_dna.problem_solved}")
        print(f"   Value: {content_dna.value_proposition}")
        print(f"   Audience: {content_dna.target_audience}")
        print(f"   Type: {content_dna.content_type}")
        
        return content_dna
    
    def generate_platform_content(self, content_dna: ContentDNA, platforms: List[str], api_key: str) -> Dict[str, PlatformContent]:
        """Generate platform-specific content from DNA"""
        generated_content = {}
        
        print(f"\n🎯 Generating content for {len(platforms)} platforms...")
        
        for platform in platforms:
            if platform not in self.platforms:
                print(f"❌ Unknown platform: {platform}")
                continue
                
            print(f"   📝 Generating {platform} content...")
            adapter = self.platforms[platform]
            
            try:
                platform_content = adapter.generate_content(content_dna, api_key)
                
                # Validate content
                validation = adapter.validate_content(platform_content)
                platform_content.validation = validation
                
                generated_content[platform] = platform_content
                
                # Show validation status
                if validation.is_valid:
                    print(f"   ✅ {platform} content validated")
                else:
                    print(f"   ⚠️  {platform} validation issues: {len(validation.errors)} errors")
                    
            except Exception as e:
                print(f"   ❌ Failed to generate {platform} content: {str(e)}")
        
        return generated_content
    
    def preview_content(self, platform_content: Dict[str, PlatformContent]):
        """Preview generated content for all platforms"""
        print("\n" + "="*60)
        print("📋 CONTENT PREVIEW")
        print("="*60)
        
        for platform, content in platform_content.items():
            print(f"\n🔸 {platform.upper()}")
            print("-" * 40)
            
            if content.title:
                print(f"Title: {content.title}")
            
            # Show body preview (first 300 chars)
            body_preview = content.body[:300]
            if len(content.body) > 300:
                body_preview += "..."
            print(f"Content: {body_preview}")
            
            # Show metadata highlights
            if content.metadata:
                meta_highlights = []
                if 'tags' in content.metadata:
                    tags = content.metadata['tags']
                    if tags:
                        meta_highlights.append(f"Tags: {', '.join(tags[:3])}")
                
                if 'thread' in content.metadata:
                    thread_count = len(content.metadata['thread'])
                    meta_highlights.append(f"Thread: {thread_count} tweets")
                
                if meta_highlights:
                    print(f"Meta: {' | '.join(meta_highlights)}")
            
            # Show validation status
            if content.validation:
                validation = content.validation
                if validation.is_valid:
                    print("✅ Validation: PASSED")
                else:
                    print(f"⚠️  Validation: {len(validation.errors)} errors, {len(validation.warnings)} warnings")
                    if validation.errors:
                        for error in validation.errors[:2]:  # Show first 2 errors
                            print(f"   ❌ {error}")
    
    def check_timing(self, platforms: List[str]) -> bool:
        """Check posting timing and get user confirmation"""
        warnings = self.scheduler.check_current_time(platforms)
        
        if warnings:
            print(f"\n{self.scheduler.get_local_time_info()}")
        
        return self.scheduler.get_user_confirmation(warnings)
    
    def publish_content(self, platform_content: Dict[str, PlatformContent], dry_run: bool = False) -> Dict[str, PublishResult]:
        """Publish content to platforms"""
        results = {}
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - No actual posting")
            print("="*50)
            
            for platform, content in platform_content.items():
                print(f"✅ Would post to {platform}")
                results[platform] = PublishResult(
                    platform=platform,
                    success=True,
                    url=f"https://{platform}.example.com/dry-run-post",
                    metadata={"dry_run": True}
                )
            return results
        
        print("\n🚀 Publishing content...")
        print("="*40)
        
        for platform, content in platform_content.items():
            print(f"   📤 Posting to {platform}...")
            
            if not content.validation.is_valid:
                print(f"   ❌ Skipping {platform} due to validation errors")
                results[platform] = PublishResult(
                    platform=platform,
                    success=False,
                    error="Content validation failed"
                )
                continue
            
            try:
                adapter = self.platforms[platform]
                result = adapter.post_content(content)
                results[platform] = result
                
                if result.success:
                    print(f"   ✅ {platform} posted: {result.url}")
                else:
                    print(f"   ❌ {platform} failed: {result.error}")
                    # Save failed post for retry
                    self.cache_manager.save_failed_post(platform, content, result.error)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ {platform} error: {error_msg}")
                results[platform] = PublishResult(
                    platform=platform,
                    success=False,
                    error=error_msg
                )
                # Save failed post for retry
                self.cache_manager.save_failed_post(platform, content, error_msg)
        
        return results
    
    def save_results(self, results: Dict[str, PublishResult], output_file: Optional[str] = None):
        """Save publishing results to file"""
        if not output_file:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"publish_results_{timestamp}.json"
        
        results_data = {}
        for platform, result in results.items():
            results_data[platform] = {
                'success': result.success,
                'url': result.url,
                'error': result.error,
                'metadata': result.metadata
            }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def retry_failed_posts(self) -> Dict[str, PublishResult]:
        """Retry failed posts that are ready for retry"""
        retry_ready = self.cache_manager.get_retry_ready_posts()
        
        if not retry_ready:
            print("No failed posts ready for retry")
            return {}
        
        print(f"🔄 Found {len(retry_ready)} posts ready for retry")
        results = {}
        
        for failed_post in retry_ready:
            platform = failed_post.platform
            content = failed_post.content
            
            print(f"   🔄 Retrying {platform}...")
            
            try:
                adapter = self.platforms[platform]
                result = adapter.post_content(content)
                results[platform] = result
                
                if result.success:
                    print(f"   ✅ {platform} retry successful: {result.url}")
                    # Remove from failed posts
                    failed_id = f"{platform}_{failed_post.created_at.strftime('%Y%m%d_%H%M%S')}"
                    self.cache_manager.remove_failed_post(failed_id)
                else:
                    print(f"   ❌ {platform} retry failed: {result.error}")
                    # Update attempt count
                    failed_id = f"{platform}_{failed_post.created_at.strftime('%Y%m%d_%H%M%S')}"
                    self.cache_manager.update_failed_post_attempt(failed_id, result.error)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"   ❌ {platform} retry error: {error_msg}")
                results[platform] = PublishResult(
                    platform=platform,
                    success=False,
                    error=error_msg
                )
                # Update attempt count
                failed_id = f"{platform}_{failed_post.created_at.strftime('%Y%m%d_%H%M%S')}"
                self.cache_manager.update_failed_post_attempt(failed_id, error_msg)
        
        return results
    
    def show_cache_stats(self):
        """Show cache statistics"""
        stats = self.cache_manager.get_cache_stats()
        
        print("📊 CACHE STATISTICS")
        print("="*40)
        print(f"Memory Cache: {stats['memory_cache_size']} entries")
        print(f"DNA Cache: {stats['dna_cache_files']} files")
        print(f"Content Cache: {stats['content_cache_files']} files")
        print(f"Failed Posts: {stats['failed_posts']} pending")
        print(f"Results Archive: {stats['results_files']} files")
        print(f"Total Cache Size: {stats['total_cache_size_mb']:.2f} MB")
        
        if stats['memory_cache_total_access'] > 0:
            print(f"Cache Hits: {stats['memory_cache_total_access']} total accesses")
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        removed = self.cache_manager.cleanup_expired_cache()
        print(f"🧹 Cache cleanup complete. Removed {removed} expired entries.")
    
    def manual_mode(self, platform_content: Dict[str, PlatformContent]):
        """Display content for manual copy-paste posting"""
        print("\n" + "="*80)
        print("📋 MANUAL POSTING MODE (Default) - Copy & Paste Instructions")
        print("="*80)
        print("The LLM has tailored your content for each platform.")
        print("Copy the content below and paste manually on each platform.")
        print("💡 Use --publish flag for automatic posting (requires all API keys)\n")
        
        for platform, content in platform_content.items():
            self._display_manual_instructions(platform, content)
        
        # Save to files for easy access
        self._save_manual_files(platform_content)
        
        print("\n" + "="*80)
        print("✅ Manual mode complete!")
        print("📁 Content saved to manual_content/ directory")
        print("🎯 Follow the step-by-step instructions above")
        print("="*80)
    
    def _display_manual_instructions(self, platform: str, content: PlatformContent):
        """Display platform-specific manual posting instructions"""
        print(f"\n🔸 {platform.upper()}")
        print("-" * 50)
        
        # Platform-specific instructions
        if platform == 'hackernews':
            print("📍 Go to: https://news.ycombinator.com/submit")
            print("📝 Instructions:")
            print("   1. Click 'submit' in top bar")
            print("   2. Paste URL or choose 'text' for self-post")
            if content.title:
                print(f"   3. Title: {content.title}")
            print("   4. Content:")
            
        elif platform == 'reddit':
            metadata = content.metadata or {}
            subreddits = metadata.get('selected_subreddits', ['appropriate_subreddit'])
            print(f"📍 Go to: https://reddit.com/r/{subreddits[0]}/submit")
            print("📝 Instructions:")
            print("   1. Choose 'Create Post' → 'Text'")
            if content.title:
                print(f"   2. Title: {content.title}")
            print("   3. Text content:")
            
        elif platform == 'twitter':
            print("📍 Go to: https://twitter.com/compose/tweet")
            print("📝 Instructions:")
            metadata = content.metadata or {}
            if 'thread' in metadata:
                print(f"   1. Create thread with {len(metadata['thread'])} tweets")
                print("   2. Copy each tweet below:")
            else:
                print("   1. Copy and paste the content below:")
                
        elif platform == 'medium':
            print("📍 Go to: https://medium.com/new-story")
            print("📝 Instructions:")
            print("   1. Click 'Write' button")
            if content.title:
                print(f"   2. Title: {content.title}")
            print("   3. Story content:")
            
        elif platform == 'devto':
            print("📍 Go to: https://dev.to/new")
            print("📝 Instructions:")
            print("   1. Click 'Create Post'")
            if content.title:
                print(f"   2. Title: {content.title}")
            print("   3. Add tags from metadata")
            print("   4. Post content:")
            
        elif platform == 'peerlist':
            print("📍 Go to: https://peerlist.io/new")
            print("📝 Instructions:")
            print("   1. Click 'Create Post'")
            print("   2. Choose appropriate post type")
            print("   3. Content:")
        
        # Display the actual content
        print(f"\n📄 CONTENT TO COPY:")
        print("┌" + "─" * 78 + "┐")
        
        # Format content for easy copying
        if platform == 'twitter' and content.metadata and 'thread' in content.metadata:
            # Display Twitter thread
            for i, tweet in enumerate(content.metadata['thread'], 1):
                print(f"│ Tweet {i}: {tweet[:74]}{'...' if len(tweet) > 74 else ''}")
                if len(tweet) > 74:
                    # Split long tweet across multiple lines
                    remaining = tweet[74:]
                    while remaining:
                        chunk = remaining[:76]
                        remaining = remaining[76:]
                        print(f"│         {chunk}")
                print("│" + " " * 78 + "│")
        else:
            # Display regular content
            lines = content.body.split('\n')
            for line in lines[:20]:  # Limit to first 20 lines for display
                if len(line) <= 76:
                    print(f"│ {line:<76} │")
                else:
                    # Wrap long lines
                    while line:
                        chunk = line[:76]
                        line = line[76:]
                        print(f"│ {chunk:<76} │")
            
            if len(lines) > 20:
                print(f"│ ... ({len(lines) - 20} more lines - see saved file) {'':30} │")
        
        print("└" + "─" * 78 + "┘")
        
        # Platform-specific tips
        self._display_platform_tips(platform, content)
        print()
    
    def _display_platform_tips(self, platform: str, content: PlatformContent):
        """Display platform-specific posting tips"""
        print(f"\n💡 {platform.title()} Tips:")
        
        if platform == 'hackernews':
            print("   • Post between 8-10 AM PT for best visibility")
            print("   • Avoid marketing language - focus on technical substance")
            print("   • Weekend posts get less traffic")
            
        elif platform == 'reddit':
            metadata = content.metadata or {}
            subreddits = metadata.get('selected_subreddits', [])
            if subreddits:
                print(f"   • Suggested subreddits: {', '.join([f'r/{s}' for s in subreddits])}")
            print("   • Read subreddit rules before posting")
            print("   • Best times: 1-3 PM EST")
            
        elif platform == 'twitter':
            print("   • Add relevant hashtags (not included in generated content)")
            print("   • Consider adding images/GIFs for engagement")
            print("   • Best times: 9 AM, 1-3 PM EST")
            
        elif platform == 'medium':
            print("   • Add a compelling featured image")
            print("   • Use proper formatting (headers, bullets)")
            print("   • Tag with relevant topics")
            
        elif platform == 'devto':
            print("   • Add cover image for better visibility")
            print("   • Use code syntax highlighting")
            print("   • Tag appropriately for discovery")
    
    def _save_manual_files(self, platform_content: Dict[str, PlatformContent]):
        """Save content to individual files for easy access"""
        manual_dir = Path("manual_content")
        manual_dir.mkdir(exist_ok=True)
        
        for platform, content in platform_content.items():
            # Save main content
            content_file = manual_dir / f"{platform}_content.txt"
            
            with open(content_file, 'w') as f:
                f.write(f"# {platform.upper()} Content\n\n")
                
                if content.title:
                    f.write(f"Title: {content.title}\n\n")
                
                if platform == 'twitter' and content.metadata and 'thread' in content.metadata:
                    f.write("Twitter Thread:\n")
                    for i, tweet in enumerate(content.metadata['thread'], 1):
                        f.write(f"Tweet {i}: {tweet}\n\n")
                else:
                    f.write("Content:\n")
                    f.write(content.body)
                
                # Add metadata if relevant
                if content.metadata:
                    f.write(f"\n\n--- Metadata ---\n")
                    for key, value in content.metadata.items():
                        if key != 'thread':  # Already handled above
                            f.write(f"{key}: {value}\n")
        
        print(f"\n💾 Content saved to manual_content/ directory")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Global Publisher - Intelligent multi-platform content publishing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py content.md --platforms hackernews reddit twitter (manual mode - default)
  python main.py content.md --platforms hackernews reddit twitter --preview
  python main.py content.md --platforms hackernews reddit twitter --publish
  python main.py blog_post.txt --platforms medium devto --schedule
  python main.py article.md --all-platforms --dry-run
        """
    )
    
    # Required arguments (except for cache operations)
    parser.add_argument('content_file', nargs='?', help='File containing content to publish')
    
    # Platform selection (not required for cache operations)
    platform_group = parser.add_mutually_exclusive_group(required=False)
    platform_group.add_argument(
        '--platforms', 
        nargs='+', 
        choices=['hackernews', 'reddit', 'twitter', 'medium', 'devto', 'peerlist'],
        help='Platforms to publish to'
    )
    platform_group.add_argument(
        '--all-platforms', 
        action='store_true',
        help='Publish to all available platforms'
    )
    
    # Operation modes
    parser.add_argument('--preview', action='store_true', help='Preview content without posting')
    parser.add_argument('--publish', action='store_true', help='Actually publish to platforms (default is manual mode)')
    parser.add_argument('--schedule', action='store_true', help='Show optimal posting schedule')
    parser.add_argument('--dry-run', action='store_true', help='Simulate posting without actually posting')
    parser.add_argument('--retry', action='store_true', help='Retry failed posts that are ready for retry')
    parser.add_argument('--cache-stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--cleanup-cache', action='store_true', help='Clean up expired cache entries')
    
    # Configuration
    parser.add_argument('--no-timing-check', action='store_true', help='Skip timing analysis and warnings')
    parser.add_argument('--output', help='Save results to specific file')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Initialize publisher for all operations
    publisher = GlobalPublisher()
    
    # Handle cache management operations
    if args.cache_stats:
        publisher.show_cache_stats()
        return
    
    if args.cleanup_cache:
        publisher.cleanup_cache()
        return
    
    if args.retry:
        results = publisher.retry_failed_posts()
        if results:
            successful = sum(1 for r in results.values() if r.success)
            total = len(results)
            print(f"\n📊 RETRY SUMMARY")
            print(f"✅ Successful: {successful}/{total}")
            if successful < total:
                print(f"❌ Still Failed: {total - successful}/{total}")
        return
    
    # Validate content file exists (for content operations)
    if not args.content_file:
        print("❌ Content file is required for publishing operations")
        sys.exit(1)
    
    if not os.path.exists(args.content_file):
        print(f"❌ Content file not found: {args.content_file}")
        sys.exit(1)
    
    # Get API key (not required for schedule-only operations)
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key and not args.schedule:
        print("❌ OpenAI API key required. Set OPENAI_API_KEY env var or use --api-key")
        sys.exit(1)
    
    # Determine platforms
    if args.all_platforms:
        platforms = ['hackernews', 'reddit', 'twitter', 'medium', 'devto', 'peerlist']
    elif args.platforms:
        platforms = args.platforms
    else:
        print("❌ Must specify either --platforms or --all-platforms")
        sys.exit(1)
    
    # Publisher already initialized above
    
    try:
        # Show schedule if requested
        if args.schedule:
            schedule = publisher.scheduler.get_optimal_schedule(platforms)
            print("📅 OPTIMAL POSTING SCHEDULE")
            print("="*50)
            for platform, timing in schedule.items():
                print(f"🔸 {platform.title()}: {timing}")
            print("\n💡 All times shown in UTC")
            return
        
        # Phase 1: Extract content DNA
        content_dna = publisher.analyze_content(args.content_file, api_key)
        
        # Phase 2: Generate platform-specific content
        platform_content = publisher.generate_platform_content(content_dna, platforms, api_key)
        
        if not platform_content:
            print("❌ No content generated for any platform")
            sys.exit(1)
        
        # Preview content
        publisher.preview_content(platform_content)
        
        # Exit if preview-only mode
        if args.preview:
            print("\n👁️  Preview mode - no posting performed")
            return
        
        # Default to manual mode unless --publish is specified
        if not args.publish and not args.dry_run:
            publisher.manual_mode(platform_content)
            return
        
        # Check timing (unless disabled)
        if not args.no_timing_check:
            if not publisher.check_timing(platforms):
                print("\n🛑 Publishing cancelled by user")
                return
        
        # Publish content
        results = publisher.publish_content(platform_content, dry_run=args.dry_run)
        
        # Save results (both to cache and custom file)
        publisher.cache_manager.save_publish_results(results)
        if args.output:
            publisher.save_results(results, args.output)
        
        # Summary
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        print(f"\n📊 PUBLISHING SUMMARY")
        print(f"✅ Successful: {successful}/{total}")
        if successful < total:
            print(f"❌ Failed: {total - successful}/{total}")
        
    except KeyboardInterrupt:
        print("\n🛑 Publishing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()