"""Tests for platforms/producthunt/adapter.py - ProducthuntAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.producthunt.adapter import ProducthuntAdapter


class TestProducthuntAdapter:
    """Tests for ProducthuntAdapter class."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "producthunt"
        config_dir.mkdir()
        return ProducthuntAdapter(config_dir)

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.model == "gpt-4o"


class TestProducthuntAdapterValidation:
    """Tests for ProducthuntAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "producthunt"
        config_dir.mkdir()
        return ProducthuntAdapter(config_dir)

    def test_validate_missing_tagline(self, adapter):
        """Test validation catches missing tagline."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={"tagline": "", "description": "Desc", "first_comment": "Comment", "topics": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("tagline" in e.lower() for e in result.errors)

    def test_validate_tagline_too_long(self, adapter):
        """Test validation catches overly long tagline."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "x" * 100,
                "description": "Desc",
                "first_comment": "Comment here",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("80" in e for e in result.errors)

    def test_validate_tagline_too_short(self, adapter):
        """Test validation warns about very short tagline."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Short",
                "description": "Description here",
                "first_comment": "This is my maker comment with enough content.",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_description_too_long(self, adapter):
        """Test validation catches description over 260 chars."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "x" * 300,
                "first_comment": "Maker comment here.",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("260" in e for e in result.errors)

    def test_validate_missing_first_comment(self, adapter):
        """Test validation catches missing first comment."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("first comment" in e.lower() or "maker" in e.lower() for e in result.errors)

    def test_validate_first_comment_too_short(self, adapter):
        """Test validation warns about short first comment."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Short comment.",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_first_comment_too_long(self, adapter):
        """Test validation warns about very long first comment."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "x" * 1200,
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_missing_question_in_comment(self, adapter):
        """Test validation suggests question in first comment."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Here is my maker story. I built this tool because reasons. It helps with things.",
                "topics": ["DevTools"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("question" in s.lower() for s in result.suggestions)

    def test_validate_no_topics(self, adapter):
        """Test validation warns about missing topics."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Maker comment here with enough content?",
                "topics": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("topic" in w.lower() for w in result.warnings)

    def test_validate_too_many_topics(self, adapter):
        """Test validation warns about too many topics."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Maker comment here?",
                "topics": ["One", "Two", "Three", "Four", "Five"]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("topic" in w.lower() for w in result.warnings)

    def test_validate_no_media_suggestions(self, adapter):
        """Test validation warns about missing media."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Maker comment?",
                "topics": ["DevTools"],
                "media_suggestions": []
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("media" in w.lower() for w in result.warnings)

    def test_validate_missing_gif_suggestion(self, adapter):
        """Test validation suggests GIF if not present."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "Good tagline for the product",
                "description": "Description",
                "first_comment": "Maker comment?",
                "topics": ["DevTools"],
                "media_suggestions": [{"type": "screenshot", "description": "Main view"}]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("gif" in s.lower() for s in result.suggestions)

    def test_validate_valid_content(self, adapter):
        """Test validation passes for valid content."""
        content = PlatformContent(
            platform="producthunt",
            title="",
            body="",
            metadata={
                "tagline": "The keyboard for coders who hate leaving the home row",
                "description": "A productivity tool that helps developers write code faster using vim-style navigation everywhere.",
                "first_comment": """Hey Product Hunt! I built this because I was tired of reaching for my mouse. What started as a side project turned into something I use every day. Would love to hear what features you'd want to see next?""",
                "topics": ["Developer Tools", "Productivity"],
                "media_suggestions": [
                    {"type": "gif", "description": "Main workflow demo"}
                ]
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestProducthuntAdapterGeneration:
    """Tests for ProducthuntAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "producthunt"
        config_dir.mkdir()
        return ProducthuntAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="CLI tool for faster deployments",
            technical_details=["Go", "Docker"],
            problem_solved="Slow deployment pipelines",
            target_audience="DevOps engineers",
            key_metrics=["10x faster"],
            unique_aspects=["Zero config"],
            limitations=["Linux only"],
            content_type="tool_launch"
        )

    @patch.object(ProducthuntAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "name": "DeployFast",
            "tagline": "Deploy in seconds, not minutes",
            "description": "Fast deployment tool",
            "first_comment": "Hey PH! I built this...",
            "topics": ["DevTools"],
            "media_suggestions": [],
            "launch_tips": "Launch on Tuesday"
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "producthunt"

    @patch.object(ProducthuntAdapter, '_make_llm_call')
    def test_generate_content_formats_body(self, mock_llm, adapter, sample_dna):
        """Test generate_content formats body preview."""
        mock_llm.return_value = {
            "name": "TestProduct",
            "tagline": "Test tagline",
            "description": "Test description",
            "first_comment": "Maker story here",
            "topics": ["Topic1", "Topic2"],
            "media_suggestions": [{"type": "gif", "description": "Demo"}],
            "launch_tips": "Tips here"
        }

        result = adapter.generate_content(sample_dna)

        assert "PRODUCT HUNT" in result.body
        assert "TestProduct" in result.body
        assert "Maker Story" in result.body or "Comment" in result.body

    @patch.object(ProducthuntAdapter, '_make_llm_call')
    def test_generate_content_includes_all_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes all metadata fields."""
        mock_llm.return_value = {
            "name": "Product",
            "tagline": "Tagline",
            "description": "Desc",
            "first_comment": "Comment",
            "topics": ["T1"],
            "media_suggestions": [{"type": "gif", "description": "D"}],
            "launch_tips": "Tips"
        }

        result = adapter.generate_content(sample_dna)

        assert "name" in result.metadata
        assert "tagline" in result.metadata
        assert "description" in result.metadata
        assert "first_comment" in result.metadata
        assert "topics" in result.metadata
        assert "media_suggestions" in result.metadata
