
import argparse
import json
import os

from core.platform_engine import PlatformAdapter

def main():
    parser = argparse.ArgumentParser(description="Generate platform-specific content.")
    parser.add_argument("content_file", help="Path to the content file.")
    
    parser.add_argument("--model", default="gemini/gemini-2.5-pro", help="The LLM model to use.")
    args = parser.parse_args()

    with open(args.content_file, 'r') as f:
        content = f.read()

    

    platform_content_dir = "platforms_content"
    if not os.path.exists(platform_content_dir):
        print(f"Error: Directory '{platform_content_dir}' not found. Please ensure your platform content files are in this directory.")
        return

    platforms = [f for f in os.listdir(platform_content_dir) if f.endswith(".md")]

    if not os.path.exists("manual_content"):
        os.makedirs("manual_content")

    for platform_file in platforms:
        platform_name = os.path.splitext(platform_file)[0]
        platform_prompt_path = os.path.join(platform_content_dir, platform_file)
        
        with open(platform_prompt_path, 'r') as f:
            platform_prompt = f.read()

        adapter = PlatformAdapter(model=args.model)
        # The prompt for the LLM will now include both the original content and the platform-specific prompt
        full_prompt = f"""
        Given the following project README and the platform-specific guidelines, generate a post tailored for that platform.

        Project README:
        {content}

        Platform Guidelines:
        {platform_prompt}

        Generate the post content as a string.
        """
        adapted_content = adapter.adapt_content(full_prompt)

        output_path = os.path.join("manual_content", f"{platform_name}_post.txt")
        with open(output_path, 'w') as f:
            f.write(adapted_content)
        print(f"Generated content for {platform_name} at {output_path}")

if __name__ == "__main__":
    main()
