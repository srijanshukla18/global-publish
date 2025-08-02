"""Tests for platforms/reddit/adapter.py - RedditAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.reddit.adapter import RedditAdapter


class TestRedditAdapter:
    """Tests for RedditAdapter class."""

    @pytest.fixture
    def mock_config_dir(self, tmp_path):
        config_dir = tmp_path / "reddit"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def adapter(self, mock_config_dir):
        return RedditAdapter(mock_config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Open source CLI for code analysis",
            technical_details=["Rust", "LLVM", "AST parsing"],
            problem_solved="Slow static analysis tools",
            target_audience="Systems programmers",
            key_metrics=["10x faster", "100K lines analyzed"],
            unique_aspects=["Incremental analysis"],
            limitations=["Linux only"],
            content_type="tool_launch"
        )

    def test_adapter_initialization(self, adapter, mock_config_dir):
        """Test adapter initializes correctly."""
        assert adapter.config_dir == mock_config_dir
        assert adapter.model == "gpt-4o"

    def test_format_posts_preview_empty(self, adapter):
        """Test _format_posts_preview with empty posts."""
        result = adapter._format_posts_preview([])
        assert result == "No posts generated"

    def test_format_posts_preview_single_post(self, adapter):
        """Test _format_posts_preview with single post."""
        posts = [{
            "subreddit": "programming",
            "title": "New static analysis tool",
            "body": "I built this tool...",
            "framing": "show_and_tell",
            "why_this_subreddit": "Technical audience",
            "flair": "Project"
        }]
        result = adapter._format_posts_preview(posts)
        assert "r/programming" in result
        assert "show_and_tell" in result
        assert "Technical audience" in result
        assert "New static analysis tool" in result

    def test_format_posts_preview_multiple_posts(self, adapter):
        """Test _format_posts_preview with multiple posts."""
        posts = [
            {"subreddit": "programming", "title": "T1", "body": "B1",
             "framing": "discovery", "why_this_subreddit": "Why1", "flair": "F1"},
            {"subreddit": "rust", "title": "T2", "body": "B2",
             "framing": "discussion", "why_this_subreddit": "Why2", "flair": "F2"},
            {"subreddit": "opensource", "title": "T3", "body": "B3",
             "framing": "show_and_tell", "why_this_subreddit": "Why3", "flair": "F3"}
        ]
        result = adapter._format_posts_preview(posts)
        assert "POST 1" in result
        assert "POST 2" in result
        assert "POST 3" in result
        assert "r/programming" in result
        assert "r/rust" in result
        assert "r/opensource" in result


class TestRedditAdapterValidation:
    """Tests for RedditAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "reddit"
        config_dir.mkdir()
        return RedditAdapter(config_dir)

    def test_validate_no_posts(self, adapter):
        """Test validation with no posts."""
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("no" in e.lower() and "post" in e.lower() for e in result.errors)

    def test_validate_missing_posts_key(self, adapter):
        """Test validation with missing posts in metadata."""
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation catches titles over 300 chars."""
        posts = [{
            "subreddit": "programming",
            "title": "x" * 350,
            "body": "Valid body content here.",
            "framing": "discovery",
            "why_this_subreddit": "Technical",
            "flair": "Project"
        }]
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("300" in e for e in result.errors)

    def test_validate_self_promo_language_warning(self, adapter):
        """Test validation warns about self-promotional language."""
        promo_titles = [
            "Check out my new tool",
            "I made a cool app",
            "I built something awesome",
            "My new project for developers",
            "Announcing my latest work"
        ]
        for title in promo_titles:
            posts = [{
                "subreddit": "programming",
                "title": title,
                "body": "Valid body content with good length.",
                "framing": "discovery",
                "why_this_subreddit": "Technical",
                "flair": "Project"
            }]
            content = PlatformContent(
                platform="reddit",
                title="Strategy",
                body="",
                metadata={"posts": posts},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = adapter.validate_content(content)
            assert any("promotional" in w.lower() for w in result.warnings), f"Should warn for: {title}"

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        posts = [{
            "subreddit": "programming",
            "title": "A technical discussion about tools",
            "body": "Short.",
            "framing": "discovery",
            "why_this_subreddit": "Technical",
            "flair": "Project"
        }]
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_body_too_long(self, adapter):
        """Test validation warns about very long body."""
        posts = [{
            "subreddit": "programming",
            "title": "Technical discussion",
            "body": "x" * 12000,
            "framing": "discovery",
            "why_this_subreddit": "Technical",
            "flair": "Project"
        }]
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_emoji_in_content(self, adapter):
        """Test validation warns about emoji."""
        posts = [{
            "subreddit": "programming",
            "title": "Cool tool check it out",
            "body": "This is a great tool for developers! ",
            "framing": "discovery",
            "why_this_subreddit": "Technical",
            "flair": "Project"
        }]
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("emoji" in w.lower() for w in result.warnings)

    def test_validate_link_at_start(self, adapter):
        """Test validation warns about body starting with link."""
        posts = [{
            "subreddit": "programming",
            "title": "New analysis tool",
            "body": "https://github.com/example/tool - check this out!",
            "framing": "discovery",
            "why_this_subreddit": "Technical",
            "flair": "Project"
        }]
        content = PlatformContent(
            platform="reddit",
            title="Strategy",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("link" in w.lower() and "start" in w.lower() for w in result.warnings)

    def test_validate_valid_posts(self, adapter):
        """Test validation passes for valid posts."""
        posts = [
            {
                "subreddit": "programming",
                "title": "Discovered an interesting static analysis approach",
                "body": """I've been exploring different ways to do static analysis
                and came across some interesting techniques. The approach uses
                incremental parsing which seems to significantly improve performance.

                Has anyone else experimented with similar techniques? I'd love to
                hear about your experiences with static analysis tools.""",
                "framing": "discussion",
                "why_this_subreddit": "Technical audience interested in tools",
                "flair": "Discussion"
            },
            {
                "subreddit": "rust",
                "title": "Exploring Rust for static analysis tooling",
                "body": """Been working on understanding how Rust's ownership model
                can help build more reliable static analysis tools. The memory
                safety guarantees seem particularly useful for this domain.

                Looking for feedback on this approach from the Rust community.""",
                "framing": "discussion",
                "why_this_subreddit": "Rust-specific implementation details",
                "flair": "Discussion"
            }
        ]
        content = PlatformContent(
            platform="reddit",
            title="Strategy: 2 posts",
            body="",
            metadata={"posts": posts},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestRedditAdapterPromptBuilding:
    """Tests for RedditAdapter prompt building."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "reddit"
        config_dir.mkdir()
        return RedditAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Open source database tool",
            technical_details=["PostgreSQL", "Go", "RAFT consensus"],
            problem_solved="Database replication complexity",
            target_audience="DevOps engineers",
            key_metrics=["99.9% uptime"],
            unique_aspects=["Simple configuration"],
            limitations=["PostgreSQL only"],
            content_type="tool_launch"
        )

    def test_build_prompt_includes_culture(self, adapter, sample_dna):
        """Test prompt includes Reddit culture guidance."""
        prompt = adapter._build_reddit_prompt(sample_dna)
        assert "REDDIT" in prompt.upper() or "culture" in prompt.lower()
        assert "downvote" in prompt.lower() or "self-promotion" in prompt.lower()

    def test_build_prompt_includes_subreddit_guidance(self, adapter, sample_dna):
        """Test prompt includes subreddit-specific guidance."""
        prompt = adapter._build_reddit_prompt(sample_dna)
        assert "r/programming" in prompt or "subreddit" in prompt.lower()

    def test_build_prompt_includes_dna(self, adapter, sample_dna):
        """Test prompt includes content DNA values."""
        prompt = adapter._build_reddit_prompt(sample_dna)
        assert "PostgreSQL" in prompt or "database" in prompt.lower()

    def test_build_prompt_with_empty_lists(self, adapter):
        """Test prompt handles empty lists in DNA."""
        dna = ContentDNA(
            value_proposition="Simple tool",
            technical_details=[],
            problem_solved="",
            target_audience="general",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="general"
        )
        prompt = adapter._build_reddit_prompt(dna)
        assert len(prompt) > 0


class TestRedditAdapterGeneration:
    """Tests for RedditAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "reddit"
        config_dir.mkdir()
        return RedditAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Tool for developers",
            technical_details=["Python"],
            problem_solved="Problem",
            target_audience="Developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

    @patch.object(RedditAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "posts": [
                {"subreddit": "python", "title": "T", "body": "B",
                 "framing": "discussion", "why_this_subreddit": "Why", "flair": "F"}
            ],
            "strategy": "Post to r/python"
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "reddit"

    @patch.object(RedditAdapter, '_make_llm_call')
    def test_generate_content_includes_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes proper metadata."""
        mock_llm.return_value = {
            "posts": [
                {"subreddit": "programming", "title": "T1", "body": "B1",
                 "framing": "discovery", "why_this_subreddit": "W1", "flair": "F1"},
                {"subreddit": "python", "title": "T2", "body": "B2",
                 "framing": "discussion", "why_this_subreddit": "W2", "flair": "F2"}
            ],
            "strategy": "Cross-post strategy"
        }

        result = adapter.generate_content(sample_dna)

        assert "posts" in result.metadata
        assert len(result.metadata["posts"]) == 2
        assert result.metadata["subreddit_count"] == 2
        assert result.metadata["strategy"] == "Cross-post strategy"

    @patch.object(RedditAdapter, '_make_llm_call')
    def test_generate_content_handles_empty_response(self, mock_llm, adapter, sample_dna):
        """Test generate_content handles empty LLM response."""
        mock_llm.return_value = {}

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.body == "No posts generated"

    @patch.object(RedditAdapter, '_make_llm_call')
    def test_generate_content_title_includes_count(self, mock_llm, adapter, sample_dna):
        """Test generate_content title includes post count."""
        mock_llm.return_value = {
            "posts": [
                {"subreddit": "a", "title": "T", "body": "B", "framing": "d",
                 "why_this_subreddit": "W", "flair": "F"},
                {"subreddit": "b", "title": "T", "body": "B", "framing": "d",
                 "why_this_subreddit": "W", "flair": "F"},
                {"subreddit": "c", "title": "T", "body": "B", "framing": "d",
                 "why_this_subreddit": "W", "flair": "F"}
            ],
            "strategy": "Strategy"
        }

        result = adapter.generate_content(sample_dna)

        assert "3" in result.title
