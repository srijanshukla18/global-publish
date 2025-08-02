# Platform-Aware Launch Pipeline Redesign Plan

## Executive Summary
Transform the current monolithic launch script into an intelligent, platform-aware publishing system that respects each platform's unique culture and requirements while maintaining elegant simplicity.

## Core Philosophy
"Write once, adapt intelligently" - Like a skilled communicator who knows how to speak to different audiences, our system will understand and respect each platform's culture.

## Key Insights from Research

### Hacker News Requirements
- **Title**: Factual, no superlatives, ≤60 chars, "Show HN: [What it does]" format
- **Content**: Technical depth, honest limitations, no marketing fluff
- **Timing**: 9 AM-12 PM PT optimal
- **Engagement**: Be ready to respond to comments within first hour
- **Never**: Share direct links for upvotes, use sockpuppets, hide affiliations

### Platform-Specific Cultures
- **Reddit**: Each subreddit has unique rules, karma requirements, and peak times
- **Twitter/X**: Visual content crucial, thread structure matters, hashtag strategy
- **Medium**: SEO-optimized titles, storytelling format, strategic keyword use
- **dev.to**: Developer-focused, tutorials perform well, code snippets essential
- **Peerlist**: Professional angle, thought leadership, career focus

## Architecture Design

### Directory Structure
```
publish/
├── main.py                      # Elegant orchestrator
├── core/
│   ├── content_analyzer.py      # Extracts content DNA from original post
│   ├── platform_engine.py       # Base class for platform adapters
│   ├── scheduler.py             # Optimal timing calculations
│   └── validator.py             # Content validation framework
├── platforms/
│   ├── hackernews/
│   │   ├── adapter.py          # HN-specific posting logic
│   │   ├── profile.yaml        # Cultural rules, examples, guidelines
│   │   ├── prompts/            # HN-specific prompt templates
│   │   └── validator.py        # Pre-flight validation
│   ├── twitter/
│   │   ├── adapter.py          
│   │   ├── profile.yaml        
│   │   └── thread_optimizer.py # Thread structure optimization
│   ├── reddit/
│   │   ├── adapter.py
│   │   ├── subreddit_analyzer.py
│   │   └── subreddits/         # Per-subreddit profiles
│   │       ├── programming.yaml
│   │       ├── webdev.yaml
│   │       └── [others].yaml
│   ├── medium/
│   ├── devto/
│   └── peerlist/
├── prompts/
│   └── base_analysis.txt       # Content DNA extraction prompt
├── cache/                      # Generated content & recovery
│   └── [timestamp]/            # Session-specific cache
└── config/
    ├── platforms.yaml          # Platform registry
    └── settings.yaml           # Global settings
```

### Core Components

#### 1. Content Analyzer (`content_analyzer.py`)
Extracts the "DNA" of the content:
- Core value proposition
- Technical details and depth
- Target audience
- Key metrics and results
- Problem being solved
- Unique selling points

#### 2. Platform Engine (`platform_engine.py`)
Base class providing:
- Common interface for all platforms
- Content transformation pipeline
- Validation framework
- Error handling and recovery
- Performance tracking

#### 3. Platform Adapters
Each platform gets a custom adapter with:
- Platform-specific prompt generation
- Content validation rules
- API integration or browser automation
- Optimal timing calculation
- Success metrics tracking

#### 4. Smart Scheduler (`scheduler.py`)
- Platform-specific peak time database
- Time zone aware scheduling
- Staggered posting to avoid spam detection
- Dependency management (HN → Screenshot → Twitter)

## Implementation Details

### Phase 1: Two-Stage LLM Process

#### Stage 1: Content Analysis
```python
def analyze_content(markdown: str) -> ContentDNA:
    """Extract core elements from original content"""
    prompt = """
    Analyze this content and extract:
    1. Core value proposition (one sentence)
    2. Technical implementation details
    3. Problem being solved
    4. Target audience
    5. Key metrics/results
    6. Unique aspects
    7. Potential controversies or limitations
    
    Return as structured JSON.
    """
    # Returns ContentDNA object
```

#### Stage 2: Platform-Specific Generation
```python
def generate_platform_content(content_dna: ContentDNA, platform: Platform) -> PlatformContent:
    """Generate platform-specific content using cultural knowledge"""
    platform_profile = load_platform_profile(platform)
    prompt = build_platform_prompt(content_dna, platform_profile)
    # Returns validated, platform-optimized content
```

### Phase 2: Platform Profiles

Example `platforms/hackernews/profile.yaml`:
```yaml
name: "Hacker News"
culture:
  values:
    - technical_depth
    - intellectual_honesty
    - substance_over_style
  anti_patterns:
    - marketing_language
    - clickbait
    - emoji
    - excessive_punctuation
    
content_rules:
  title:
    format: "Show HN: {tool_name} - {one_line_description}"
    max_length: 60
    forbidden_words: ["revolutionary", "game-changing", "disrupt"]
    
  submission:
    structure:
      - technical_problem
      - solution_approach
      - implementation_details
      - results_metrics
      - honest_limitations
      
timing:
  optimal_hours_pt: [9, 10, 11, 12]
  avoid_days: ["saturday", "sunday"]
  
examples:
  successful:
    - title: "Show HN: SQLite-based job queue with 1M jobs/sec"
      url: "https://news.ycombinator.com/item?id=123"
    - title: "Show HN: Open-source alternative to Datadog"
      url: "https://news.ycombinator.com/item?id=456"
```

### Phase 3: Validation System

Each platform has validators:
```python
class HackerNewsValidator:
    def validate_title(self, title: str) -> ValidationResult:
        # Check length, forbidden words, format
        
    def validate_content(self, content: str) -> ValidationResult:
        # Check for marketing language, technical depth
        
    def pre_flight_check(self, post: HNPost) -> List[Warning]:
        # Final checks before posting
```

### Phase 4: User Experience

#### CLI Interface
```bash
# Simple default usage
python publish.py

# Preview all generated content
python publish.py --preview

# Post to specific platforms
python publish.py --platforms hackernews,twitter

# Schedule for optimal times
python publish.py --schedule

# Dry run with validation
python publish.py --dry-run

# Use local LLM
python publish.py --llm ollama
```

#### Progress Indicators
```
🔍 Analyzing content...
🧬 Extracted content DNA
🎯 Generating platform-specific content...
  ✅ Hacker News (validated)
  ✅ Twitter thread (5 tweets)
  ✅ Reddit (3 subreddits selected)
📅 Scheduling posts...
  🕐 HN: Today 9:00 AM PT
  🕑 Twitter: Today 9:30 AM PT
  🕒 Reddit: Staggered 10 AM - 12 PM PT
```

## Success Metrics

1. **Platform Reception**
   - HN: Front page rate, comment quality
   - Reddit: Upvote ratio, engagement rate
   - Twitter: Retweets, click-through rate

2. **Content Quality**
   - Validation pass rate
   - Platform-specific guideline adherence
   - User satisfaction with generated content

3. **System Performance**
   - Success rate per platform
   - Recovery rate from failures
   - Time to publish all platforms

## Migration Strategy

1. **Phase 1**: Refactor existing code into modular structure
2. **Phase 2**: Implement platform profiles and validators
3. **Phase 3**: Build two-phase LLM system
4. **Phase 4**: Add scheduling and preview features
5. **Phase 5**: Implement feedback loop and learning

## Future Enhancements

1. **Learning System**: Track what works and improve prompts
2. **A/B Testing**: Test different approaches automatically
3. **Community Profiles**: Allow users to share platform profiles
4. **Analytics Dashboard**: Track cross-platform performance
5. **Webhook Integration**: Notify when posts go live

## Risk Mitigation

1. **Platform API Changes**: Modular design allows easy updates
2. **Rate Limiting**: Built-in backoff and scheduling
3. **Content Rejection**: Validation catches issues early
4. **LLM Failures**: Cache generated content for manual posting

## Conclusion

This redesign transforms a simple script into an intelligent publishing system that respects each platform's unique culture while maintaining the simplicity users love. The modular architecture ensures maintainability and extensibility as platforms evolve.