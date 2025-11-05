#!/usr/bin/env python3
"""
Global Publisher - Multi-platform content generator
"""
import argparse
import json
import os
import sys
from importlib import import_module
from pathlib import Path

from core.dna_extractor import DNAExtractor
from core.models import ContentDNA, PlatformContent
from core.quality_enhancer import QualityEnhancer


# Platform adapter registry
PLATFORM_ADAPTERS = {
    "devto": ("platforms.devto.adapter", "DevtoAdapter"),
    "reddit": ("platforms.reddit.adapter", "RedditAdapter"),
    "twitter": ("platforms.twitter.adapter", "TwitterAdapter"),
    "medium": ("platforms.medium.adapter", "MediumAdapter"),
    "hackernews": ("platforms.hackernews.adapter", "HackernewsAdapter"),
    "peerlist": ("platforms.peerlist.adapter", "PeerlistAdapter"),
}


def load_platform_adapter(platform_name: str, model: str, api_key: str = None):
    """Dynamically load a platform adapter"""
    if platform_name not in PLATFORM_ADAPTERS:
        return None

    module_path, class_name = PLATFORM_ADAPTERS[platform_name]

    try:
        module = import_module(module_path)
        adapter_class = getattr(module, class_name)
        return adapter_class(model=model, api_key=api_key)
    except Exception as e:
        print(f"Error loading adapter for {platform_name}: {e}")
        return None


def save_platform_content(content: PlatformContent, output_dir: str):
    """Save generated content to file"""
    platform = content.platform
    output_path = os.path.join(output_dir, f"{platform}_post.md")

    with open(output_path, 'w') as f:
        f.write(f"# {content.title}\n\n")
        f.write(f"**Platform:** {platform}\n\n")

        # Write metadata
        if content.metadata:
            f.write("## Metadata\n")
            for key, value in content.metadata.items():
                if isinstance(value, list):
                    f.write(f"- **{key}:** {', '.join(str(v) for v in value)}\n")
                else:
                    f.write(f"- **{key}:** {value}\n")
            f.write("\n")

        # Write main content
        f.write("## Content\n\n")
        f.write(content.body)
        f.write("\n\n")

        # Write validation results
        validation = content.validation
        if not validation.is_valid or validation.warnings or validation.suggestions:
            f.write("## Validation\n\n")

            if not validation.is_valid:
                f.write("### ❌ Errors\n")
                for error in validation.errors:
                    f.write(f"- {error}\n")
                f.write("\n")

            if validation.warnings:
                f.write("### ⚠️  Warnings\n")
                for warning in validation.warnings:
                    f.write(f"- {warning}\n")
                f.write("\n")

            if validation.suggestions:
                f.write("### 💡 Suggestions\n")
                for suggestion in validation.suggestions:
                    f.write(f"- {suggestion}\n")
                f.write("\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate platform-specific content from source material.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s content.md                          # Generate for all platforms
  %(prog)s content.md --platforms reddit twitter  # Generate for specific platforms
  %(prog)s content.md --model claude-3-opus    # Use different model
        """
    )

    parser.add_argument("content_file", help="Path to the content file")
    parser.add_argument("--model", default="gemini/gemini-2.5-pro",
                       help="LLM model to use (default: gemini/gemini-2.5-pro)")
    parser.add_argument("--platforms", nargs="+",
                       help="Specific platforms to generate content for (default: all)")
    parser.add_argument("--output-dir", default="manual_content",
                       help="Output directory for generated content (default: manual_content)")

    args = parser.parse_args()

    # Validate content file
    if not os.path.exists(args.content_file):
        print(f"Error: Content file '{args.content_file}' not found")
        sys.exit(1)

    # Read source content
    print(f"Reading content from {args.content_file}...")
    with open(args.content_file, 'r') as f:
        content = f.read()

    # Extract content DNA
    print("Extracting content DNA...")
    extractor = DNAExtractor(model=args.model)
    try:
        content_dna = extractor.extract_dna(content)
        print(f"✓ DNA extracted - Type: {content_dna.content_type}, Audience: {content_dna.target_audience}")
    except Exception as e:
        print(f"Error extracting content DNA: {e}")
        sys.exit(1)

    # Determine platforms to generate for
    if args.platforms:
        platforms = args.platforms
        # Validate platform names
        invalid = [p for p in platforms if p not in PLATFORM_ADAPTERS]
        if invalid:
            print(f"Error: Unknown platforms: {', '.join(invalid)}")
            print(f"Available platforms: {', '.join(PLATFORM_ADAPTERS.keys())}")
            sys.exit(1)
    else:
        platforms = list(PLATFORM_ADAPTERS.keys())

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate content for each platform
    print(f"\nGenerating content for {len(platforms)} platforms...")
    print("=" * 60)

    results = []
    for platform_name in platforms:
        print(f"\n📝 {platform_name.upper()}")

        # Load adapter
        adapter = load_platform_adapter(platform_name, args.model)
        if not adapter:
            print(f"  ❌ Failed to load adapter")
            continue

        # Generate content
        try:
            platform_content = adapter.generate_content(content_dna)

            # Validate content structure
            validation = adapter.validate_content(platform_content)
            platform_content.validation = validation

            # Check tone quality
            enhancer = QualityEnhancer()
            tone_analysis = enhancer.validate_tone_quality(platform_content.body)

            # Add tone warnings to validation
            if tone_analysis['issues']:
                for issue in tone_analysis['issues']:
                    validation.warnings.append(f"TONE: {issue}")

            # Save content
            output_path = save_platform_content(platform_content, args.output_dir)

            # Print summary
            status = "✓" if validation.is_valid else "⚠"
            quality_score = tone_analysis['quality_score']
            quality_badge = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"

            print(f"  {status} Generated: {output_path}")
            print(f"     {quality_badge} Tone Quality: {quality_score}/100")

            if validation.errors:
                print(f"    ❌ {len(validation.errors)} error(s)")
            if validation.warnings:
                print(f"    ⚠️  {len(validation.warnings)} warning(s)")
            if tone_analysis['issues']:
                print(f"    🎯 Tone issues detected - review output carefully")

            results.append({
                "platform": platform_name,
                "success": True,
                "output": output_path,
                "valid": validation.is_valid
            })

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parsing error: {e}")
            print(f"     The LLM may have returned invalid JSON. Try again or use a different model.")
            results.append({"platform": platform_name, "success": False, "error": "JSON parsing error"})

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({"platform": platform_name, "success": False, "error": str(e)})

    # Print final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"✓ {len(successful)}/{len(results)} platforms generated successfully")

    if failed:
        print(f"\n❌ Failed platforms:")
        for r in failed:
            print(f"  - {r['platform']}: {r.get('error', 'Unknown error')}")

    print(f"\nAll content saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
