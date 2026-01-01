
import os
import argparse
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Type

from core.content_analyzer import ContentAnalyzer
from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, UserProfile
from core.platform_recommender import PlatformRecommender
from core.story_interview import run_interview, load_saved_profile, save_profile, quick_stage_prompt

# Import Adapters explicitly for robustness
from platforms.hackernews.adapter import HackernewsAdapter
from platforms.twitter.adapter import TwitterAdapter
from platforms.reddit.adapter import RedditAdapter
from platforms.medium.adapter import MediumAdapter
from platforms.devto.adapter import DevtoAdapter
from platforms.peerlist.adapter import PeerlistAdapter
from platforms.linkedin.adapter import LinkedinAdapter
from platforms.producthunt.adapter import ProducthuntAdapter
from platforms.indiehackers.adapter import IndiehackersAdapter
from platforms.substack.adapter import SubstackAdapter
from platforms.hashnode.adapter import HashnodeAdapter
from platforms.lobsters.adapter import LobstersAdapter

# Registry of supported platforms
ADAPTER_REGISTRY: Dict[str, Type[PlatformAdapter]] = {
    "hackernews": HackernewsAdapter,
    "twitter": TwitterAdapter,
    "reddit": RedditAdapter,
    "medium": MediumAdapter,
    "devto": DevtoAdapter,
    "peerlist": PeerlistAdapter,
    "linkedin": LinkedinAdapter,
    "producthunt": ProducthuntAdapter,
    "indiehackers": IndiehackersAdapter,
    "substack": SubstackAdapter,
    "hashnode": HashnodeAdapter,
    "lobsters": LobstersAdapter,
}

def setup_environment():
    """Load environment variables and check for API keys"""
    load_dotenv()
    
    # Check for keys
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openai_key and not openrouter_key:
        print("❌ Error: No API key found.")
        print("Please set OPENROUTER_API_KEY (recommended) or OPENAI_API_KEY in your .env file.")
        sys.exit(1)
        
    # Configure LiteLLM for OpenRouter if available
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key
        # Default base URL for OpenRouter/LiteLLM usage
        if not os.getenv("OPENROUTER_API_BASE"):
             os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

MAX_CONTENT_FILE_SIZE = 1024 * 1024  # 1MB limit for content files
ALLOWED_EXTENSIONS = {'.md', '.txt', '.markdown'}

def load_content(file_path: str) -> str:
    """Read content from file with security validations"""
    path = Path(file_path).resolve()

    # Validate file extension
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        print(f"❌ Error: Unsupported file type '{path.suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
        sys.exit(1)

    if not path.exists():
        print(f"❌ Error: Content file '{file_path}' not found.")
        sys.exit(1)

    # Validate file size
    file_size = path.stat().st_size
    if file_size > MAX_CONTENT_FILE_SIZE:
        print(f"❌ Error: File too large ({file_size} bytes). Max: {MAX_CONTENT_FILE_SIZE} bytes")
        sys.exit(1)

    return path.read_text()

PLATFORM_NAME_PATTERN = re.compile(r'^[a-z0-9_]+$')
MAX_ARTIFACT_SIZE = 512 * 1024  # 512KB limit for artifacts

def validate_platform_name(platform: str) -> bool:
    """Validate platform name to prevent path traversal"""
    return bool(PLATFORM_NAME_PATTERN.match(platform))

def save_artifact(platform: str, content: str, metadata: Dict = None):
    """Save generated content to artifacts directory"""
    if not validate_platform_name(platform):
        print(f"   ❌ Invalid platform name: {platform}")
        return

    if len(content.encode('utf-8')) > MAX_ARTIFACT_SIZE:
        print(f"   ❌ Content too large. Max: {MAX_ARTIFACT_SIZE} bytes")
        return

    output_dir = Path("artifacts")
    output_dir.mkdir(exist_ok=True)

    filename = f"{platform}_post.md"
    file_path = output_dir / filename

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"   📄 Saved to artifacts/{filename}")

def print_validation_report(validation):
    """Print validation results prettily"""
    if not validation.is_valid:
        print(f"   ⚠️  Validation Issues:")
        for error in validation.errors:
            print(f"      - 🔴 {error}")
    
    if validation.warnings:
        for warning in validation.warnings:
            print(f"      - 🔸 {warning}")
            
    if validation.suggestions:
        for suggestion in validation.suggestions:
            print(f"      - 💡 {suggestion}")

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

def load_config() -> Dict:
    """Load configuration from config.toml"""
    config_path = Path("config.toml")
    if not config_path.exists():
        # Fallback default config
        return {"llm": {"default_model": "gpt-4o"}}
    
    with open(config_path, "rb") as f:
        return toml.load(f)

def main():
    setup_environment()
    config = load_config()
    default_model = config.get("llm", {}).get("default_model", "gpt-4o")
    
    parser = argparse.ArgumentParser(description="Professional Multi-Platform Content Publisher")
    parser.add_argument("content_file", help="Path to the source markdown content file")
    parser.add_argument("--platforms", nargs="+", help="Specific platforms to generate for (overrides smart selection)")
    parser.add_argument("--all", action="store_true", help="Generate for all platforms (ignores fit analysis)")
    parser.add_argument("--model", default=default_model, help=f"LLM model to use (default: {default_model})")
    parser.add_argument("--interview", action="store_true", help="Run story interview to gather founder narrative")
    parser.add_argument("--setup-profile", action="store_true", help="Set up or update your professional profile")

    args = parser.parse_args()

    # Validate explicitly requested platforms
    available_platforms = list(ADAPTER_REGISTRY.keys())
    if args.platforms:
        for p in args.platforms:
            if p not in ADAPTER_REGISTRY:
                print(f"❌ Error: Platform '{p}' is not supported. Available: {', '.join(available_platforms)}")
                sys.exit(1)

    print("\n🚀 Global Publisher: Professional Pipeline")
    print("==========================================")
    print(f"🤖 Model: {args.model}")

    # Load or set up user profile
    user_profile = load_saved_profile()
    if args.setup_profile or user_profile is None:
        print("\n👤 Setting up your professional profile...")
        print("   (This helps with LinkedIn targeting - your network matters)")
        print("\n   What's your day job? (e.g., 'SRE, Backend Engineer')")
        roles_input = input("   > ").strip()
        roles = [r.strip() for r in roles_input.split(",")] if roles_input else []

        print("\n   Who follows you on LinkedIn? (e.g., 'DevOps engineers and platform teams')")
        linkedin_audience = input("   > ").strip()

        print("\n   Which platforms do you have reputation on? (comma separated)")
        print("   (e.g., 'hackernews, twitter, reddit')")
        platforms_input = input("   > ").strip()
        active_platforms = [p.strip() for p in platforms_input.split(",")] if platforms_input else []

        user_profile = UserProfile(
            professional_roles=roles,
            linkedin_audience=linkedin_audience or "general tech professionals",
            active_platforms=active_platforms
        )
        save_profile(user_profile)
        print()

    if user_profile and user_profile.professional_roles:
        print(f"👤 Profile: {', '.join(user_profile.professional_roles)} | LinkedIn audience: {user_profile.linkedin_audience}")

    # 1. Analyze Content
    print(f"\n🧠 Analyzing Content DNA from '{args.content_file}'...")
    raw_content = load_content(args.content_file)
    analyzer = ContentAnalyzer(model=args.model)
    dna = analyzer.analyze(raw_content)

    print(f"   ✅ DNA Extracted: {dna.content_type} | {dna.target_audience}")
    print(f"   🎯 Value Prop: {dna.value_proposition}")
    print(f"   📊 Novelty: {dna.novelty_score} | Controversy: {dna.controversy_potential} | Evidence: {dna.show_dont_tell}")
    if dna.best_fit_communities:
        print(f"   🎯 Best Communities: {', '.join(dna.best_fit_communities[:5])}")

    # Show visual opportunities
    if dna.visual_opportunities:
        print(f"\n   📸 VISUAL OPPORTUNITIES (include these in your posts!):")
        for viz in dna.visual_opportunities:
            print(f"      • {viz}")

    # Show platform constraints
    if dna.platform_constraints:
        print(f"\n   ⚠️  PLATFORM CONSTRAINTS (limits audience):")
        for constraint in dna.platform_constraints:
            print(f"      • {constraint}")

    # Run story interview or quick stage prompt
    if args.interview:
        story_context = run_interview(skip_profile=True)
        dna.project_stage = story_context.project_stage
        dna.founder_story = story_context.founder_story
    else:
        # Quick stage prompt
        dna.project_stage = quick_stage_prompt()

    # 2. Determine target platforms
    if args.platforms:
        # User explicitly specified platforms - use those
        target_platforms = args.platforms
        print(f"\n📋 Using specified platforms: {', '.join(target_platforms)}")
        recommendations = None
    elif args.all:
        # User wants all platforms
        target_platforms = available_platforms
        print(f"\n📋 Generating for ALL {len(target_platforms)} platforms (--all flag)")
        recommendations = None
    else:
        # Smart selection (default behavior)
        print(f"\n🔍 Analyzing platform fit...")
        from litellm import completion
        recommender = PlatformRecommender()
        rec_prompt = recommender.build_recommendation_prompt(dna, user_profile)

        rec_response = completion(
            model=args.model,
            messages=[{"role": "user", "content": rec_prompt}],
            temperature=0.3
        )
        recommendations = recommender.parse_recommendations(rec_response.choices[0].message.content)

        target_platforms = recommender.get_platforms_to_generate(recommendations)
        skipped = recommender.get_skipped_platforms(recommendations)

        # Show what's being skipped and why
        if skipped:
            print(f"\n   ⏭️  Skipping {len(skipped)} platforms (poor fit):")
            for s in skipped:
                skip_msg = f"      • {s.platform}: {s.reason}"
                if s.constraint_warning:
                    skip_msg += f" ⚠️ {s.constraint_warning}"
                print(skip_msg)

        # Show what we're generating for
        strong_fits = [r for r in recommendations if r.fit == "strong"]
        moderate_fits = [r for r in recommendations if r.fit == "moderate"]

        if strong_fits:
            print(f"\n   ✅ Strong fit ({len(strong_fits)}): {', '.join(r.platform for r in strong_fits)}")
        if moderate_fits:
            print(f"   🔸 Moderate fit ({len(moderate_fits)}): {', '.join(r.platform for r in moderate_fits)}")

        # Show constraint warnings for selected platforms
        platforms_with_warnings = [r for r in recommendations if r.fit != "skip" and r.constraint_warning]
        if platforms_with_warnings:
            print(f"\n   ⚠️  Platform-specific warnings:")
            for r in platforms_with_warnings:
                print(f"      • {r.platform}: {r.constraint_warning}")

    if not target_platforms:
        print("\n❌ No platforms selected. Your content may not be a good fit for any platform.")
        print("   Try --all to force generation, or --platforms to specify manually.")
        sys.exit(1)

    # Initialize timing advisor
    from core.timing_advisor import TimingAdvisor
    timing_advisor = TimingAdvisor()

    # 3. Generate for Platforms
    print(f"\n🏭 Generating Content for {len(target_platforms)} Platforms...")

    for platform_name in target_platforms:
        print(f"\n🔸 Processing: {platform_name.upper()}")

        try:
            # Initialize Adapter with model override
            adapter_class = ADAPTER_REGISTRY[platform_name]
            config_dir = Path(f"platforms/{platform_name}")
            adapter = adapter_class(config_dir, model=args.model)

            # Get timing info
            timing = timing_advisor.get_suggestion(platform_name)

            # Generate
            print(f"   Thinking...")
            content = adapter.generate_content(dna)

            # Validate
            print(f"   Validating...")
            validation = adapter.validate_content(content)

            # Build timing section
            timing_status = "✅ Good time now!" if timing.current_is_good else f"⏰ Best: {timing.next_good_window}"
            timing_section = f"""## ⏰ When to Post
- Best days: {', '.join(timing.best_days)}
- Best hours (UTC): {', '.join(f'{h}:00' for h in timing.best_hours_utc)}
- Avoid: {', '.join(timing.avoid)}
- Status: {timing_status}
- 💡 {timing.notes}
"""

            # Build visual opportunities section
            visual_section = ""
            if dna.visual_opportunities:
                visual_section = "## 📸 Visual Assets to Include\n"
                for viz in dna.visual_opportunities:
                    visual_section += f"- [ ] {viz}\n"
                visual_section += "\n"

            # Build constraints section
            constraints_section = ""
            if dna.platform_constraints:
                constraints_section = "## ⚠️ Mention These Constraints\n"
                for constraint in dna.platform_constraints:
                    constraints_section += f"- {constraint}\n"
                constraints_section += "\n"

            # Save Artifact with all context
            final_output = f"""---
platform: {platform_name}
title: {content.title}
status: {'generated' if validation.is_valid else 'needs_review'}
model: {args.model}
project_stage: {dna.project_stage}
---

# {content.title}

{content.body}

---
{visual_section}{constraints_section}{timing_section}
---
## 🧠 Generation Metadata
- Project Stage: {dna.project_stage}
- Strategy: {content.metadata.get('engagement_strategy', 'Standard')}
- Tags: {', '.join(content.metadata.get('tags', []))}
- Reality Check: {content.metadata.get('reality_check', 'N/A')}
"""
            save_artifact(platform_name, final_output, content.metadata)
            
            # Report
            if validation.is_valid:
                print(f"   ✅ Success! Ready to publish.")
            else:
                print(f"   ⚠️  Generated with issues.")
            
            print_validation_report(validation)
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n✨ Done! Check the 'artifacts/' directory for your content.\n")

if __name__ == "__main__":
    main()
