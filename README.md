# Global Publisher

Generates platform-native content from a single source. Analyzes your content's DNA (value prop, audience, technical details) and rebuilds it for each platform's culture and rules.

**What it does:** Takes your README/docs → outputs copy-paste ready posts for 12 platforms that fit your content.

**What it doesn't do:** Auto-publish. You copy the generated content and post manually.

## Supported Platforms

| Platform | Content Type | Key Features |
|----------|--------------|--------------|
| **Hacker News** | Show HN | Technical depth, honesty emphasis, anti-marketing |
| **Twitter/X** | Threads | 5-8 tweet threads, visual hooks, engagement timing |
| **Reddit** | Self-posts | Subreddit-specific framing, value-first approach |
| **LinkedIn** | Professional | Personal narrative, no external links in body |
| **Medium** | Long-form | 1600-2000 word articles, SEO-optimized |
| **Dev.to** | Tutorial | Code-focused, beginner-friendly, tagged |
| **Product Hunt** | Launch | Tagline, maker story, media suggestions |
| **Indie Hackers** | Founder story | Metrics, lessons learned, building in public |
| **Substack** | Newsletter | Distinctive voice, deep dives |
| **Hashnode** | Dev blog | SEO-optimized, series support |
| **Lobsters** | Technical | Invite-only community, programming focus |
| **Peerlist** | Professional | Achievement-focused, portfolio building |


## Before You Use This Tool

**This tool generates content. It doesn't generate reputation.**

Good content on a platform where you have no presence = ignored content. Each platform's algorithm and community prioritizes established members.

### Platform Pre-requisites

| Platform | What You Need First |
|----------|---------------------|
| **Hacker News** | 30+ days account age, some karma from commenting on OTHER posts. Spend 2 weeks being helpful before your first Show HN. |
| **Reddit** | 30+ days account, 100+ karma in target subreddits. Many subs auto-remove posts from new accounts. Participate genuinely first. |
| **Lobsters** | Invite-only. You need an existing member to vouch for you. |
| **Twitter/X** | Followers who care about your topic. A 0-follower account posting a thread = talking to void. |
| **LinkedIn** | Connections in your target audience. Algorithm rewards engagement from your network. |
| **Product Hunt** | Hunter reputation helps. First-time makers with no history struggle. |
| **Dev.to / Hashnode** | More forgiving. Good content can surface without existing reputation. |
| **Medium** | Forgiving for first posts if content is good. |
| **IndieHackers** | Community appreciates newcomers sharing genuinely. Lower barrier. |

### The Honest Truth

If you're launching something and have **zero presence** on a platform:
1. The generated content will be well-formatted and culturally appropriate
2. It will probably still get ignored
3. You should have started building presence 3 months ago
4. But start now anyway - this launch won't be your last

**Best strategy:** Pick 1-2 platforms where you already have some presence. Go deep there. Ignore the rest for this launch.


## Why

I got bored editing posts for my side projects for each platform.
And you should talk about your work, you owe it to yourself.
But its a chore to talk about it.

## Usage

```bash
# Setup
uv sync
cp .env.example .env  # Add your OPENROUTER_API_KEY

# First run: Set up your professional profile (saved for future runs)
# This helps with LinkedIn targeting - your network matters
uv run python main.py content.md

# Run with story interview (gathers founder narrative)
uv run python main.py content.md --interview

# Force specific platforms (override smart selection)
uv run python main.py content.md --platforms hackernews twitter

# Generate for ALL platforms (ignore fit analysis)
uv run python main.py content.md --all

# Override default LLM model
uv run python main.py content.md --model gpt-4o

# Update your profile
uv run python main.py content.md --setup-profile
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `--interview` | Interactive story interview for founder narrative |
| `--platforms` | Force specific platforms (space-separated) |
| `--all` | Generate for all 12 platforms |
| `--model` | Override LLM model (default: claude-opus-4.5) |
| `--setup-profile` | Re-run professional profile setup |

### What Happens

1. **Load your profile** — Roles, LinkedIn audience, active platforms
2. **Extract content DNA** — Type, audience, novelty, constraints, visual opportunities
3. **Ask project stage** — experiment / MVP / beta / production
4. **Smart platform selection** — LLM decides which platforms fit your content
5. **Generate & validate** — Platform-native content with validation checks
6. **Timing advice** — Best posting windows for each platform

### Features

**Professional Profile** — Saved to `~/.config/global-publish/profile.json`:
- Your roles (e.g., "SRE", "Backend Engineer") influence platform targeting
- LinkedIn audience definition for better professional content
- Active platforms track where you have existing reputation

**Story Interview** — `--interview` flag:
- Interactive Q&A capturing your founder narrative
- Why you built it, what you learned, honest limitations
- Enriches generated content with authentic voice

**Visual Opportunities** — Auto-detected from your content:
- ASCII diagrams → "Screenshot the architecture diagram"
- Terminal outputs → "Record with asciinema"
- Code examples → "Create a GIF demo"
- Included as checklist in each artifact

**Platform Constraints** — Auto-detected requirements:
- OS requirements (macOS only, Linux only)
- Hardware requirements (Apple Silicon, GPU)
- Version requirements (Python 3.11+, Linux 6.12+)
- Warns about incompatible communities

**Validation System** — Per-platform rules:
- Character limits (Twitter 280/tweet, HN 60-char title)
- Forbidden words (marketing buzzwords, self-promo language)
- Format requirements (Reddit title structure, LinkedIn link placement)
- Returns warnings, errors, and suggestions

**Timing Advisor** — Optimal posting windows:
- Platform-specific best days/hours (UTC)
- Current window status (good/moderate/avoid)
- Next good posting window prediction

## Output

```
artifacts/
├── hackernews_post.md   # Show HN format with technical depth
├── twitter_post.md      # Thread with hooks
├── reddit_post.md       # Multi-subreddit with different framings
├── medium_post.md       # Long-form article
├── devto_post.md        # Developer blog with tags
├── linkedin_post.md     # Professional angle
├── producthunt_post.md  # Launch copy + first comment
├── indiehackers_post.md # Founder story
├── substack_post.md     # Newsletter format
├── hashnode_post.md     # Dev blog
├── lobsters_post.md     # Tech community
└── peerlist_post.md     # Professional showcase
```

Each artifact includes:
- The generated content (copy-paste ready)
- **Visual asset checklist**: What screenshots/asciinema to create
- **Platform constraints**: Requirements to mention in your post
- **Timing advice**: Best days/hours to post, current status
- **Reality check**: Prerequisites and honest expectations
- Validation warnings (character limits, forbidden words, etc.)

## How It Works

1. **Profile Loading** — Loads your professional identity (roles, LinkedIn audience, active platforms)
2. **Content DNA Extraction** — LLM analyzes your source to extract: value proposition, technical details, target audience, limitations, novelty, visual opportunities, platform constraints
3. **Project Stage** — Quick prompt: experiment/mvp/beta/production (affects messaging)
4. **Smart Platform Selection** — LLM decides which platforms fit, considering:
   - Content type (tutorials skip ProductHunt)
   - Your professional identity (SRE → LinkedIn strong for infra tools)
   - Platform constraints (macOS-only → skip r/linux)
5. **Platform Adaptation** — Each adapter has cultural rules baked in (e.g., HN hates marketing speak, Reddit needs subreddit-specific framing)
6. **Artifact Generation** — Includes content + visual checklists + constraints + timing

## Architecture

```
main.py                      # CLI + orchestration
core/
├── models.py                # ContentDNA, UserProfile, PlatformContent
├── content_analyzer.py      # Extracts ContentDNA from source
├── platform_engine.py       # Base PlatformAdapter class + LLM utilities
├── platform_recommender.py  # Smart platform selection with user profile
├── timing_advisor.py        # Best posting times per platform
├── story_interview.py       # Founder narrative interview mode
└── quality_enhancer.py      # Tone validation, forbidden phrase detection
platforms/
├── hackernews/
│   ├── adapter.py           # Generation logic + prompts
│   ├── profile.yaml         # Cultural rules
│   └── validator.py         # HN-specific validation
├── reddit/
│   ├── adapter.py
│   ├── analyzer.py          # Subreddit matching
│   └── subreddit_data.yaml  # Subreddit profiles
└── [other platforms]/
    └── adapter.py           # Most platforms are single-file
tests/                       # 17 test files (~85% coverage)
~/.config/global-publish/
└── profile.json             # Your saved professional profile
```

## Configuration

### config.toml

```toml
[llm]
default_model = "openrouter/anthropic/claude-opus-4.5"

[system]
artifacts_dir = "artifacts"
```

### Environment Variables

```bash
# Required: LLM API (one of these)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# Or fallback to OpenAI
OPENAI_API_KEY=sk-...

# Optional: For future direct posting (not currently used)
TWITTER_BEARER_TOKEN=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
MEDIUM_TOKEN=...
DEVTO_API_KEY=...
```

## Security

Input validation and safety measures:

- **File validation**: Extension whitelist (`.md`, `.txt`, `.markdown`)
- **Size limits**: 1MB input files, 512KB artifacts, 256KB LLM responses
- **Path traversal prevention**: Absolute path resolution, no `..` escapes
- **Platform name validation**: Alphanumeric + underscore only
- **YAML safety**: `yaml.safe_load()` for all config parsing
- **No arbitrary code execution**: All user input is treated as data

## LLM Integration

Resilient API handling:

- **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Timeout**: 120 seconds per LLM call
- **Graceful degradation**: Falls back to defaults on API failure
- **JSON extraction**: Robust parsing from markdown code blocks
- **Model flexibility**: Override via `--model` flag or config.toml

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=core --cov=platforms

# Run specific test file
uv run pytest tests/test_hackernews_validator.py -v
```

Test coverage: ~85% across 17 test files. Key areas tested:
- Content DNA extraction
- Platform-specific validation rules
- LLM response parsing
- Edge cases (empty input, Unicode, oversized content)

## Dependencies

```
Python >= 3.11

litellm>=1.80.11      # LLM abstraction layer
openai>=2.14.0        # OpenAI client
python-dotenv>=1.2.1  # Environment variable loading
pyyaml>=6.0.3         # YAML parsing
tomli>=2.3.0          # TOML parsing
```

## Adding Platforms

1. Create `platforms/yourplatform/adapter.py`
2. Inherit from `PlatformAdapter`
3. Implement `generate_content()` and `validate_content()`
4. Register in `main.py` ADAPTER_REGISTRY

Example minimal adapter:

```python
from core.platform_engine import PlatformAdapter
from core.models import ContentDNA, PlatformContent, ValidationResult

class YourPlatformAdapter(PlatformAdapter):
    def generate_content(self, dna: ContentDNA) -> PlatformContent:
        prompt = self._build_prompt(dna)
        response = self._make_llm_call(prompt)
        return PlatformContent(
            platform="yourplatform",
            title=response.get("title", ""),
            body=response.get("body", ""),
            metadata=response.get("metadata", {})
        )

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        errors, warnings, suggestions = [], [], []
        # Add your validation rules
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
```

## License

MIT
