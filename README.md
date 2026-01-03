# Global Publisher

Generates platform-native content from a single source. Analyzes your content's DNA (value prop, audience, technical details) and rebuilds it for each platform's culture and rules.

**What it does:** Takes your README/docs → outputs copy-paste ready posts for platforms that fit your content.

**What it doesn't do:** Auto-publish. You copy the generated content and post manually.


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

# This will:
# 1. Load your profile (roles, LinkedIn audience)
# 2. Extract content DNA (type, audience, novelty, constraints, visual opportunities)
# 3. Ask about project stage (experiment/mvp/beta/production)
# 4. Analyze which platforms fit (considers your professional identity)
# 5. Generate content with timing + visual asset checklists

# Force specific platforms (override smart selection)
uv run python main.py content.md --platforms hackernews twitter

# Generate for ALL platforms (ignore fit analysis)
uv run python main.py content.md --all

# Update your profile
uv run python main.py content.md --setup-profile
```

### New Features

**Professional Profile** (saved to `~/.config/global-publish/profile.json`):
- Your roles (e.g., "SRE", "Backend Engineer") help LinkedIn targeting
- If you're an SRE posting kernel tools, LinkedIn becomes a strong fit
- Your active platforms help prioritize where you have reputation

**Story Interview** (`--interview`):
- Gathers your founder narrative: why you built it, what you learned
- Captures honest limitations (HN loves this)
- Used to enrich generated content

**Visual Opportunities**:
- Extracts ASCII diagrams, terminal outputs, code examples from your README
- Suggests: "Record with asciinema", "Screenshot the architecture diagram"
- Included as checklist in each artifact

**Platform Constraints**:
- Detects: "macOS only", "Linux 6.12+", "Apple Silicon required"
- Warns about incompatible communities (r/linux won't care about macOS tools)
- Included in artifacts so you remember to mention them

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
├── content_analyzer.py      # Extracts ContentDNA from source
├── platform_engine.py       # Base PlatformAdapter class
├── platform_recommender.py  # Smart platform selection with user profile
├── timing_advisor.py        # Best posting times per platform
├── story_interview.py       # Founder narrative interview mode
└── models.py                # ContentDNA, UserProfile, PlatformContent
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

~/.config/global-publish/
└── profile.json             # Your saved professional profile
```

## Config

```toml
# config.toml
[llm]
default_model = "openrouter/anthropic/claude-opus-4.5"
```

## Adding Platforms

1. Create `platforms/yourplatform/adapter.py`
2. Inherit from `PlatformAdapter`
3. Implement `generate_content()` and `validate_content()`
4. Register in `main.py` ADAPTER_REGISTRY
