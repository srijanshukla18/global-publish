# Getting Started - Global Publisher 🚀

## 1. Clone & Setup (2 minutes)

```bash
git clone <repo-url>
cd global-publish
docker-compose build
```

## 2. Required API Keys

### 🔑 **Essential (Required)**
- **OpenAI API Key** - For content generation
  - Get: https://platform.openai.com/api-keys
  - Cost: ~$0.01-0.05 per post generation

### 📱 **Platform APIs (Choose what you need)**

| Platform | Required | How to Get | Notes |
|----------|----------|------------|-------|
| **OpenAI** | ✅ Yes | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Core system |
| **Twitter** | Optional | [developer.twitter.com](https://developer.twitter.com) | Need Bearer Token |
| **Reddit** | Optional | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) | Client ID + Secret |
| **Medium** | Optional | [medium.com/me/settings](https://medium.com/me/settings) | Integration Token |
| **Dev.to** | Optional | [dev.to/settings/extensions](https://dev.to/settings/extensions) | API Key |
| **Hacker News** | Optional | Manual login | Cookie from browser |
| **Peerlist** | Optional | Manual login | Browser automation |

## 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your keys
nano .env
```

**Minimum .env for testing:**
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

**Full .env for all platforms:**
```bash
OPENAI_API_KEY=sk-your-openai-key-here
TWITTER_BEARER_TOKEN=your-bearer-token
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret  
REDDIT_USERNAME=your-username
REDDIT_PASSWORD=your-password
MEDIUM_TOKEN=your-integration-token
MEDIUM_USER_ID=your-user-id
DEVTO_API_KEY=your-api-key
HN_COOKIE=your-session-cookie
```

## 4. Test Your Setup

```bash
# Test without API key (schedule/cache operations)
docker run --rm -v "$(pwd)":/app -w /app global-publisher python3 main.py sample_content.md --platforms hackernews reddit --schedule

# Test with API key (preview mode)
docker run --rm -v "$(pwd)":/app -w /app --env-file .env global-publisher python3 main.py sample_content.md --platforms hackernews reddit --preview
```

## 5. First Publish

```bash
# Create your content file
echo "# My First Post

I built something amazing and want to share it with the world.

## The Problem
[Describe the problem you solved]

## My Solution  
[Explain your approach]

## Results
[Share outcomes and lessons]" > my_content.md

# Generate and preview
docker run --rm -v "$(pwd)":/app -w /app --env-file .env global-publisher \
  python3 main.py my_content.md --all-platforms --preview

# Post for real (when ready)
docker run --rm -v "$(pwd)":/app -w /app --env-file .env global-publisher \
  python3 main.py my_content.md --platforms hackernews reddit twitter
```

## 🚀 Quick Commands

```bash
# Manual mode (DEFAULT - LLM tailors content, you copy-paste)
python3 main.py content.md --all-platforms

# Preview all platforms
python3 main.py content.md --all-platforms --preview

# Actually publish automatically (requires all API keys)
python3 main.py content.md --platforms hackernews reddit --publish

# Dry run (simulate posting)  
python3 main.py content.md --platforms hackernews reddit --dry-run

# Show optimal posting times
python3 main.py content.md --platforms twitter medium --schedule

# Retry failed posts
python3 main.py --retry

# Check cache stats
python3 main.py --cache-stats
```

## 💡 Pro Tips

1. **Default is Manual**: System generates tailored content but YOU post it manually
2. **Review First**: Always check the generated content before posting 
3. **Check Timing**: Use `--schedule` to see optimal posting times  
4. **Platform Priority**: Start with HN + Reddit, add others later
5. **Content Format**: Write in markdown, system adapts to each platform
6. **Auto Publishing**: Only use `--publish` when you trust the system completely

## ⚡ 30-Second Start

```bash
git clone <repo> && cd global-publish
echo "OPENAI_API_KEY=sk-your-key" > .env
docker-compose build
docker run --rm -v "$(pwd)":/app -w /app --env-file .env global-publisher \
  python3 main.py sample_content.md --platforms hackernews reddit
```
**Result**: LLM generates platform-tailored content with copy-paste instructions!

**That's it!** You're ready to publish intelligently across platforms. 🎯