"""Tests for platforms/twitter/adapter.py - TwitterAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.twitter.adapter import TwitterAdapter


class TestTwitterAdapter:
    """Tests for TwitterAdapter class."""

    @pytest.fixture
    def mock_config_dir(self, tmp_path):
        """Create a temporary config directory."""
        config_dir = tmp_path / "twitter"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def adapter(self, mock_config_dir):
        """Create a TwitterAdapter instance."""
        return TwitterAdapter(mock_config_dir)

    @pytest.fixture
    def sample_dna(self):
        """Create sample ContentDNA for testing."""
        return ContentDNA(
            value_proposition="A tool that helps developers write better code",
            technical_details=["Python", "Machine Learning"],
            problem_solved="Slow code review process",
            target_audience="Software developers",
            key_metrics=["50% faster reviews"],
            unique_aspects=["AI-powered suggestions"],
            limitations=["Requires Python 3.8+"],
            content_type="tool_launch"
        )

    def test_adapter_initialization(self, adapter, mock_config_dir):
        """Test adapter initializes correctly."""
        assert adapter.config_dir == mock_config_dir
        assert adapter.model == "gpt-4o"  # Default model

    def test_adapter_with_custom_model(self, mock_config_dir):
        """Test adapter with custom model."""
        adapter = TwitterAdapter(mock_config_dir, model="claude-3-opus")
        assert adapter.model == "claude-3-opus"

    def test_format_thread_preview_empty(self, adapter):
        """Test _format_thread_preview with empty thread."""
        result = adapter._format_thread_preview([])
        assert result == "No thread generated"

    def test_format_thread_preview_single_tweet(self, adapter):
        """Test _format_thread_preview with single tweet."""
        thread = [{
            "tweet_number": 1,
            "content": "This is tweet one",
            "type": "hook"
        }]
        result = adapter._format_thread_preview(thread)
        assert "Tweet 1" in result
        assert "hook" in result
        assert "This is tweet one" in result

    def test_format_thread_preview_with_visual(self, adapter):
        """Test _format_thread_preview with visual suggestion."""
        thread = [{
            "tweet_number": 1,
            "content": "Tweet content",
            "type": "solution",
            "visual_suggestion": "Screenshot of the tool in action"
        }]
        result = adapter._format_thread_preview(thread)
        assert "Visual" in result
        assert "Screenshot" in result

    def test_format_thread_preview_multiple_tweets(self, adapter):
        """Test _format_thread_preview with multiple tweets."""
        thread = [
            {"tweet_number": 1, "content": "First", "type": "hook"},
            {"tweet_number": 2, "content": "Second", "type": "problem"},
            {"tweet_number": 3, "content": "Third", "type": "solution"}
        ]
        result = adapter._format_thread_preview(thread)
        assert "Tweet 1" in result
        assert "Tweet 2" in result
        assert "Tweet 3" in result


class TestTwitterAdapterValidation:
    """Tests for TwitterAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "twitter"
        config_dir.mkdir()
        return TwitterAdapter(config_dir)

    def test_validate_empty_thread(self, adapter):
        """Test validation with empty thread."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={"thread": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("no thread" in e.lower() for e in result.errors)

    def test_validate_missing_thread(self, adapter):
        """Test validation with missing thread in metadata."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_tweet_over_280_chars(self, adapter):
        """Test validation catches tweets over 280 characters."""
        long_tweet = "x" * 300
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [{"tweet_number": 1, "content": long_tweet, "type": "hook"}],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("280" in e for e in result.errors)

    def test_validate_tweet_exactly_280_chars(self, adapter):
        """Test validation accepts tweet of exactly 280 characters."""
        exact_tweet = "x" * 280
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [{"tweet_number": 1, "content": exact_tweet, "type": "hook"}],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True

    def test_validate_long_tweet_warning(self, adapter):
        """Test validation warns about tweets close to limit."""
        long_tweet = "x" * 265
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [{"tweet_number": 1, "content": long_tweet, "type": "hook"}],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_missing_hook_tweet(self, adapter):
        """Test validation warns about missing hook tweet."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [
                    {"tweet_number": 1, "content": "Problem", "type": "problem"},
                    {"tweet_number": 2, "content": "Solution", "type": "solution"}
                ],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("hook" in w.lower() for w in result.warnings)

    def test_validate_missing_cta_tweet(self, adapter):
        """Test validation warns about missing CTA tweet."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [
                    {"tweet_number": 1, "content": "Hook!", "type": "hook"},
                    {"tweet_number": 2, "content": "Solution", "type": "solution"}
                ],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("call-to-action" in w.lower() or "cta" in w.lower() for w in result.warnings)

    def test_validate_too_many_hashtags(self, adapter):
        """Test validation warns about too many hashtags."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [{"tweet_number": 1, "content": "Tweet!", "type": "hook"}],
                "hashtags": ["#one", "#two", "#three", "#four", "#five"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("hashtag" in w.lower() for w in result.warnings)

    def test_validate_engagement_punctuation_suggestion(self, adapter):
        """Test validation suggests engaging punctuation."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [{"tweet_number": 1, "content": "Tweet with no special chars", "type": "hook"}],
                "hashtags": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("punctuation" in s.lower() or "engaging" in s.lower() for s in result.suggestions)

    def test_validate_valid_thread(self, adapter):
        """Test validation passes for valid thread."""
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="",
            metadata={
                "thread": [
                    {"tweet_number": 1, "content": "Hook: Something interesting!", "type": "hook"},
                    {"tweet_number": 2, "content": "The problem we all face?", "type": "problem"},
                    {"tweet_number": 3, "content": "Here's the solution:", "type": "solution"},
                    {"tweet_number": 4, "content": "What do you think?", "type": "cta"}
                ],
                "hashtags": ["#dev", "#tools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestTwitterAdapterPromptBuilding:
    """Tests for TwitterAdapter prompt building."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "twitter"
        config_dir.mkdir()
        return TwitterAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Developer productivity tool for code review",
            technical_details=["Python", "AST parsing", "LLM integration"],
            problem_solved="Code reviews take too long",
            target_audience="Software engineers",
            key_metrics=["50% faster", "10K users"],
            unique_aspects=["Context-aware suggestions"],
            limitations=["Python only"],
            content_type="tool_launch"
        )

    def test_build_prompt_includes_dna_values(self, adapter, sample_dna):
        """Test prompt includes content DNA values."""
        prompt = adapter._build_twitter_prompt(sample_dna)
        assert "Developer productivity" in prompt or "code review" in prompt.lower()

    def test_build_prompt_structure(self, adapter, sample_dna):
        """Test prompt has expected structure."""
        prompt = adapter._build_twitter_prompt(sample_dna)
        assert "TWITTER" in prompt.upper() or "CULTURE" in prompt
        assert "thread" in prompt.lower()
        assert "JSON" in prompt

    def test_build_prompt_with_empty_metrics(self, adapter):
        """Test prompt handles empty metrics gracefully."""
        dna = ContentDNA(
            value_proposition="Test tool",
            technical_details=[],
            problem_solved="Some problem",
            target_audience="Developers",
            key_metrics=[],  # Empty
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )
        prompt = adapter._build_twitter_prompt(dna)
        # Should not crash
        assert "thread" in prompt.lower()

    def test_build_prompt_with_long_value_proposition(self, adapter):
        """Test prompt handles long value proposition."""
        dna = ContentDNA(
            value_proposition="A" * 500,  # Very long
            technical_details=["Python"],
            problem_solved="Problem",
            target_audience="Devs",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )
        # Should extract just the first part
        prompt = adapter._build_twitter_prompt(dna)
        assert len(prompt) > 0


class TestTwitterAdapterGeneration:
    """Tests for TwitterAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "twitter"
        config_dir.mkdir()
        return TwitterAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Developer tool",
            technical_details=["Python"],
            problem_solved="Slow process",
            target_audience="Developers",
            key_metrics=["Fast"],
            unique_aspects=["Unique"],
            limitations=["Limit"],
            content_type="tool"
        )

    @patch.object(TwitterAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "thread": [{"tweet_number": 1, "content": "Test", "type": "hook"}],
            "tweet_count": 1,
            "hashtags": ["#test"],
            "engagement_strategy": "Drive comments"
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "twitter"

    @patch.object(TwitterAdapter, '_make_llm_call')
    def test_generate_content_includes_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes proper metadata."""
        mock_llm.return_value = {
            "thread": [
                {"tweet_number": 1, "content": "Hook!", "type": "hook"},
                {"tweet_number": 2, "content": "More!", "type": "cta"}
            ],
            "tweet_count": 2,
            "hashtags": ["#dev", "#tools"],
            "engagement_strategy": "Engage developers"
        }

        result = adapter.generate_content(sample_dna)

        assert "thread" in result.metadata
        assert len(result.metadata["thread"]) == 2
        assert result.metadata["hashtags"] == ["#dev", "#tools"]
        assert result.metadata["engagement_strategy"] == "Engage developers"

    @patch.object(TwitterAdapter, '_make_llm_call')
    def test_generate_content_handles_empty_response(self, mock_llm, adapter, sample_dna):
        """Test generate_content handles empty LLM response."""
        mock_llm.return_value = {}

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.metadata.get("thread", []) == []

    @patch.object(TwitterAdapter, '_make_llm_call')
    def test_generate_content_formats_body(self, mock_llm, adapter, sample_dna):
        """Test generate_content formats body from thread."""
        mock_llm.return_value = {
            "thread": [{"tweet_number": 1, "content": "Tweet content", "type": "hook"}],
            "tweet_count": 1,
            "hashtags": [],
            "engagement_strategy": ""
        }

        result = adapter.generate_content(sample_dna)

        assert "Tweet 1" in result.body
        assert "Tweet content" in result.body
