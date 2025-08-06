# Global Publisher 🚀

An intelligent multi-platform content generator that adapts your content to each platform's unique culture and requirements.

## What Problem Does It Solve?

Manually tailoring content for different social media platforms is a tedious and time-consuming process. A technical blog post written for Medium or Dev.to cannot be simply copy-pasted to Twitter, Reddit, or Hacker News. Each platform has its own unique culture, formatting constraints, and audience expectations.

- **Twitter** requires concise threads with engaging hooks.
- **Reddit** demands adherence to specific subreddit rules and community etiquette.
- **Hacker News** values technical depth and intellectual honesty.
- **LinkedIn** prefers a professional tone and focuses on career-related insights.

Rewriting the same core message for each platform is a repetitive task that stifles creativity and slows down content velocity. This project solves that problem by automating the adaptation process. It takes a single piece of content and intelligently generates optimized versions for multiple platforms, saving you hours of manual work.

## ✨ Features

- **Two-Phase LLM Architecture**: Extract content DNA, then generate platform-optimized versions
- **Platform-Aware Adaptation**: Each platform has its own cultural profile and optimization rules
- **Intelligent Caching**: Avoid re-generating content with smart caching
- **Manual Mode**: LLM generates tailored content, you copy and paste to each platform

## 🏗️ Architecture

```
Content File → DNA Extraction → Platform Adapters → Manual Instructions
                     ↓
              Intelligent Caching System
```

### Supported Platforms

- **Hacker News**: Technical depth, intellectual honesty
- **Reddit**: Smart subreddit selection, community rules compliance  
- **Twitter/X**: Thread optimization, engagement hooks
- **Medium**: SEO optimization, personal narrative, long-form structure
- **Dev.to**: Beginner-friendly tutorials, code examples, community focus
- **Peerlist**: Professional achievements, technical showcases

## 🚀 Getting Started

### 1. Installation

```bash
# Install uv (if you don't have it)
pip install uv

# Create a virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt
```

### 2. Configuration

Set up your API key by creating a `.env` file. You can copy the example file first.

```bash
# Set up your API key
echo "GEMINI_API_KEY='your-api-key-here'" > .env
```

### 3. Basic Usage

To generate content for all supported platforms, provide a markdown file as an argument to the `run.sh` script.

```bash
# Generate content for all platforms
./run.sh content.md
```

You can also specify which platforms to generate content for:

```bash
# Generate content for specific platforms
./run.sh content.md --platforms hackernews reddit twitter
```

Or use a different LLM model:

```bash
# Use a different LLM model
./run.sh content.md --model claude-3-opus
```

The generated content will be saved in the `manual_content/` directory.

## 📝 Content Format

Your content file can be markdown with any structure. This will be provided to the LLM along with the platform-specific guidelines.

Example content structure:
```markdown
# How I Built X

## The Problem
[Description of problem and pain points]

## The Solution  
[Your approach and key insights]

## Technical Implementation
[Code examples, architecture, tools used]

## Results
[Outcomes, metrics, lessons learned]
```

## 🎯 Platform Guidelines

The system uses markdown files in the `platforms_content/` directory to define the guidelines for each platform. Each file (e.g., `platforms_content/twitter.md`) contains instructions on how to adapt the input content for that specific platform.

## 🧠 How It Works

### Manual Content Generation
1. The system reads your input content file.
2. For each platform markdown file in `platforms_content/`, it combines your input content with the platform's guidelines into a single prompt.
3. This combined prompt is sent to the LLM (via LiteLLM) to generate the platform-specific post.
4. Clear instructions are provided for manual posting on each platform.
5. Content is saved to `manual_content/` directory for easy access.

## 🔧 Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY="your-api-key-here"
```

## 🛠️ Development

### Adding New Platforms

1. Create a new markdown file in `platforms_content/` (e.g., `platforms_content/new_platform.md`).
2. Add the specific guidelines and rules for that platform within the markdown file.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-platform`
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- OpenAI GPT-4 for content adaptation
- Python 3.11+
- Modern Python tooling

---

**🚀 Transform your content workflow from manual adaptation to intelligent generation.**