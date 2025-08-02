"""Tests for platforms/linkedin/adapter.py - LinkedinAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.linkedin.adapter import LinkedinAdapter


class TestLinkedinAdapter:
    """Tests for LinkedinAdapter class."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "linkedin"
        config_dir.mkdir()
        return LinkedinAdapter(config_dir)

    def test_adapter_initialization(self, adapter, tmp_path):
        """Test adapter initializes correctly."""
        assert adapter.config_dir == tmp_path / "linkedin"
        assert adapter.model == "gpt-4o"


class TestLinkedinAdapterValidation:
    """Tests for LinkedinAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "linkedin"
        config_dir.mkdir()
        return LinkedinAdapter(config_dir)

    def test_validate_missing_body(self, adapter):
        """Test validation catches missing body."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("body" in e.lower() and "required" in e.lower() for e in result.errors)

    def test_validate_body_too_long(self, adapter):
        """Test validation catches body over 3000 chars."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="x" * 3500,
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("3000" in e for e in result.errors)

    def test_validate_body_over_1300_warning(self, adapter):
        """Test validation warns about body over 1300 chars."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="x" * 1500 + "\n\nParagraph two.\n\nParagraph three.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("see more" in w.lower() or "truncated" in w.lower() for w in result.warnings)

    def test_validate_external_link_error(self, adapter):
        """Test validation catches external links in body."""
        links = [
            "Check out https://example.com for more",
            "Visit http://mysite.com today",
            "Link: https://github.com/example"
        ]
        for link_text in links:
            content = PlatformContent(
                platform="linkedin",
                title="Hook",
                body=link_text + "\n\nMore content.\n\nAnother paragraph.",
                metadata={},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = adapter.validate_content(content)
            assert result.is_valid is False, f"Should catch link in: {link_text}"
            assert any("link" in e.lower() for e in result.errors)

    def test_validate_overused_phrases(self, adapter):
        """Test validation warns about overused phrases."""
        overused = [
            "I'm excited to announce",
            "Thrilled to share this news",
            "Proud to announce our",
            "Delighted to present"
        ]
        for phrase in overused:
            content = PlatformContent(
                platform="linkedin",
                title="Hook",
                body=f"{phrase}!\n\nMore content here.\n\nAnother paragraph.",
                metadata={},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = adapter.validate_content(content)
            assert any("overused" in w.lower() for w in result.warnings), f"Should warn for: {phrase}"

    def test_validate_missing_line_breaks(self, adapter):
        """Test validation suggests line breaks."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="Single long paragraph without any breaks at all continuing on and on.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("line break" in s.lower() or "paragraph" in s.lower() for s in result.suggestions)

    def test_validate_missing_question(self, adapter):
        """Test validation suggests ending with question."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="Paragraph one.\n\nParagraph two.\n\nParagraph three ending with statement.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("question" in s.lower() for s in result.suggestions)

    def test_validate_hashtag_at_start(self, adapter):
        """Test validation warns about hashtags at start."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="#programming #tech\n\nSome content.\n\nMore content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("hashtag" in w.lower() and "end" in w.lower() for w in result.warnings)

    def test_validate_valid_post(self, adapter):
        """Test validation passes for valid post."""
        content = PlatformContent(
            platform="linkedin",
            title="Hook",
            body="""The third time my script crashed at 3 AM, I realized something had to change.

After spending weeks optimizing our deployment pipeline, I learned that simplicity beats complexity every time.

Here's what I discovered: The best solutions aren't always the most sophisticated.

We reduced our deployment time by 50% by removing complexity, not adding it.

What's your experience with over-engineered solutions?

#devops #programming""",
            metadata={"hashtags": ["#devops", "#programming"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestLinkedinAdapterGeneration:
    """Tests for LinkedinAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "linkedin"
        config_dir.mkdir()
        return LinkedinAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="DevOps automation tool",
            technical_details=["Python", "Docker"],
            problem_solved="Manual deployment processes",
            target_audience="DevOps engineers",
            key_metrics=["50% time saved"],
            unique_aspects=["One-click deployment"],
            limitations=["Linux only"],
            content_type="tool_launch"
        )

    @patch.object(LinkedinAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "hook": "Something changed when...",
            "body": "Post body.\n\nMore content.\n\n#hashtag",
            "hashtags": ["#devops"],
            "comment_with_link": "Link: https://example.com",
            "engagement_hook": "What's your experience?"
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "linkedin"

    @patch.object(LinkedinAdapter, '_make_llm_call')
    def test_generate_content_uses_hook_as_title(self, mock_llm, adapter, sample_dna):
        """Test generate_content uses hook as title."""
        mock_llm.return_value = {
            "hook": "The hook line",
            "body": "Body content.\n\nMore.\n\nFinal.",
            "hashtags": [],
            "comment_with_link": "",
            "engagement_hook": ""
        }

        result = adapter.generate_content(sample_dna)

        assert result.title == "The hook line"

    @patch.object(LinkedinAdapter, '_make_llm_call')
    def test_generate_content_includes_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes proper metadata."""
        mock_llm.return_value = {
            "hook": "Hook",
            "body": "Body.\n\nMore.\n\nEnd?",
            "hashtags": ["#one", "#two"],
            "comment_with_link": "Link in comment",
            "engagement_hook": "Question here?"
        }

        result = adapter.generate_content(sample_dna)

        assert "hashtags" in result.metadata
        assert "comment_with_link" in result.metadata
        assert "engagement_hook" in result.metadata

    @patch.object(LinkedinAdapter, '_make_llm_call')
    def test_generate_content_handles_empty_response(self, mock_llm, adapter, sample_dna):
        """Test generate_content handles empty LLM response."""
        mock_llm.return_value = {}

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.title == "LinkedIn Post"  # Default fallback
