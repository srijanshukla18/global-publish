# Global Publisher 🚀

An intelligent multi-platform content publishing system that adapts your content to each platform's unique culture and requirements.

## ✨ Features

- **Two-Phase LLM Architecture**: Extract content DNA, then generate platform-optimized versions
- **Platform-Aware Adaptation**: Each platform has its own cultural profile and optimization rules
- **Smart Scheduling**: Timing analysis with warnings and user confirmation
- **Intelligent Caching**: Avoid re-generating content and enable failed post recovery
- **CLI Interface**: Full command-line interface with preview, dry-run, and scheduling modes

## 🏗️ Architecture

```
Content File → DNA Extraction → Platform Adapters → Validation → Publishing
                      ↓
               Intelligent Caching & Recovery System
```

### Supported Platforms

- **Hacker News**: Technical depth, intellectual honesty, weekend warnings
- **Reddit**: Smart subreddit selection, community rules compliance  
- **Twitter/X**: Thread optimization, engagement hooks, visual suggestions
- **Medium**: SEO optimization, personal narrative, long-form structure
- **Dev.to**: Beginner-friendly tutorials, code examples, community focus
- **Peerlist**: Professional achievements, technical showcases

## 🚀 Quick Start

### Installation

```bash
# Clone and install dependencies
git clone <repo-url>
cd global-publish
pip install -r requirements.txt

# Set up your API keys
export OPENAI_API_KEY="your-key"
export TWITTER_BEARER_TOKEN="your-token"
export REDDIT_CLIENT_ID="your-id"
export REDDIT_CLIENT_SECRET="your-secret"
export MEDIUM_TOKEN="your-token"
export DEVTO_API_KEY="your-key"
```

### Basic Usage

```bash
# Preview content for all platforms
python main.py sample_content.md --all-platforms --preview

# Post to specific platforms with timing check
python main.py content.md --platforms hackernews reddit twitter

# Show optimal posting schedule
python main.py content.md --platforms medium devto --schedule

# Dry run (no actual posting)
python main.py content.md --all-platforms --dry-run

# Skip timing warnings
python main.py content.md --platforms twitter --no-timing-check
```

### Cache and Recovery

```bash
# Show cache statistics
python main.py --cache-stats

# Retry failed posts
python main.py --retry

# Clean up expired cache
python main.py --cleanup-cache
```

## 📝 Content Format

Your content file can be markdown with any structure. The system extracts:

- **Value Proposition**: Core benefit/solution
- **Problem Solved**: What issue this addresses  
- **Technical Details**: Implementation specifics
- **Target Audience**: Who this is for
- **Unique Aspects**: What makes it different
- **Limitations**: Honest caveats

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

## 🎯 Platform Optimization

### Hacker News
- Technical depth over marketing fluff
- Substance-focused titles (≤60 chars)
- Weekend posting warnings
- Intellectual honesty emphasis

### Twitter/X
- Engagement-optimized threads
- Hook → Problem → Solution → Results → CTA structure
- Visual content suggestions
- Character limit validation

### Reddit
- Automatic subreddit selection based on content
- Community-specific tone adaptation
- Self-promotion rules compliance
- Optimal timing by subreddit

### Medium
- SEO-optimized titles and structure
- Personal narrative integration
- Long-form article formatting
- Canonical URL handling

### Dev.to
- Beginner-friendly explanations
- Code example requirements
- Tutorial structure optimization
- Community engagement focus

### Peerlist
- Professional achievement framing
- Technical skill highlights
- Career growth narratives
- Browser automation (no API)

## 🧠 Intelligent Features

### Content DNA Extraction
Analyzes your content to understand:
- Core value proposition
- Technical implementation details
- Problem being solved
- Target audience
- Unique differentiators
- Honest limitations

### Platform Cultural Profiles
Each platform has detailed cultural rules:
```yaml
culture:
  values:
    - technical_depth
    - intellectual_honesty
  anti_patterns:
    - marketing_fluff
    - clickbait_titles
  timing:
    optimal_hours: [16, 17, 18, 19]
    avoid_weekends: true
```

### Smart Scheduling
- Platform-specific optimal posting times
- Local time analysis and warnings
- Weekend posting recommendations
- User confirmation for suboptimal timing

### Caching System
- **DNA Cache**: Avoid re-analyzing same content (24h TTL)
- **Content Cache**: Store generated platform content (6h TTL)
- **Failed Post Recovery**: Automatic retry with exponential backoff
- **Results Archive**: Complete audit trail

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY="sk-..."

# Platform APIs (as needed)
TWITTER_BEARER_TOKEN="..."
REDDIT_CLIENT_ID="..."
REDDIT_CLIENT_SECRET="..."
REDDIT_USERNAME="..."
REDDIT_PASSWORD="..."
MEDIUM_TOKEN="..."
MEDIUM_USER_ID="..."
DEVTO_API_KEY="..."
HN_COOKIE="..."  # From browser after login
```

### Platform Configuration
Each platform has its own configuration in `platforms/{platform}/`:
- `profile.yaml`: Cultural rules and timing
- `adapter.py`: Platform-specific logic
- `subreddit_data.yaml`: Reddit-specific rules (for Reddit)

## 📊 Monitoring

### Cache Statistics
```bash
python main.py --cache-stats
```
Shows:
- Memory cache size and hit rate
- File cache sizes (DNA, content, results)
- Failed posts pending retry
- Total cache storage usage

### Failed Post Recovery
The system automatically:
1. Saves failed posts with error details
2. Calculates retry timing (1min → 5min → 30min)
3. Allows manual retry of ready posts
4. Tracks attempt count and max retries

### Results Archive
Every publishing session creates:
- Timestamped results file
- Success/failure status per platform
- Error messages and metadata
- Complete audit trail

## 🛠️ Development

### Adding New Platforms

1. Create platform directory: `platforms/newplatform/`
2. Add `profile.yaml` with cultural rules
3. Implement `adapter.py` extending `PlatformAdapter`
4. Add validation rules and posting logic
5. Update main CLI platform list

### Extending Features

- **New validation rules**: Add to platform adapter `validate_content()`
- **Custom prompts**: Modify `_build_platform_prompt()` methods
- **New cache types**: Extend `CacheManager` class
- **Scheduling rules**: Update `SmartScheduler` optimal times

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
- Platform APIs (Twitter, Reddit, Medium, Dev.to)
- Playwright for browser automation
- Modern Python tooling

---

**🚀 Transform your content publishing workflow from manual adaptation to intelligent automation.**