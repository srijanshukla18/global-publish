"""Tests for platforms/devto/adapter.py - DevtoAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.devto.adapter import DevtoAdapter


class TestDevtoAdapter:
    """Tests for DevtoAdapter class."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "devto"
        config_dir.mkdir()
        return DevtoAdapter(config_dir)

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.model == "gpt-4o"


class TestDevtoAdapterValidation:
    """Tests for DevtoAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "devto"
        config_dir.mkdir()
        return DevtoAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="devto",
            title="",
            body="Article content here.",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("title" in e.lower() for e in result.errors)

    def test_validate_title_too_long(self, adapter):
        """Test validation catches overly long title."""
        content = PlatformContent(
            platform="devto",
            title="x" * 260,
            body="Article content here.",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("250" in e for e in result.errors)

    def test_validate_description_too_long(self, adapter):
        """Test validation warns about long description."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="Article content here with code and details.",
            metadata={"tags": ["python"], "description": "x" * 200},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("160" in w for w in result.warnings)

    def test_validate_missing_body(self, adapter):
        """Test validation catches missing body."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("body" in e.lower() for e in result.errors)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="Short.",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_missing_code_blocks(self, adapter):
        """Test validation suggests code examples."""
        content = PlatformContent(
            platform="devto",
            title="Building a Python Tool",
            body="""# Introduction

            This is a tutorial about building tools. We'll cover the basics
            and then move on to more advanced topics. The process involves
            setting up the environment and writing the code.""",
            metadata={"tags": ["python", "tutorial"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("code" in s.lower() for s in result.suggestions)

    def test_validate_missing_headers(self, adapter):
        """Test validation warns about missing headers."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="""This is just plain text without any structure.
            No headers to break up the content.
            Just paragraphs of text continuing on.""",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("header" in w.lower() for w in result.warnings)

    def test_validate_too_many_tags(self, adapter):
        """Test validation warns about too many tags."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="# Section\n\n```python\ncode\n```",
            metadata={"tags": ["one", "two", "three", "four", "five", "six"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("4" in w or "tag" in w.lower() for w in result.warnings)

    def test_validate_no_tags(self, adapter):
        """Test validation warns about missing tags."""
        content = PlatformContent(
            platform="devto",
            title="Good Title",
            body="# Section\n\n```python\ncode\n```",
            metadata={"tags": [], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("tag" in w.lower() for w in result.warnings)

    def test_validate_beginner_friendly_suggestion(self, adapter):
        """Test validation suggests beginner-friendly content."""
        content = PlatformContent(
            platform="devto",
            title="Advanced Metaprogramming",
            body="""# Advanced Concepts

            The metaclass pattern involves complex inheritance hierarchies.
            ```python
            class Meta(type):
                pass
            ```
            This technique is powerful.""",
            metadata={"tags": ["python"], "description": "Desc"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("beginner" in s.lower() for s in result.suggestions)

    def test_validate_valid_article(self, adapter):
        """Test validation passes for valid article."""
        content = PlatformContent(
            platform="devto",
            title="Building Your First Python CLI Tool",
            body="""# Introduction

            Let's build a simple CLI tool together step by step.

            ## Prerequisites

            First, make sure you have Python installed.

            ## Step 1: Setup

            We'll start by creating our project structure.

            ```python
            import click

            @click.command()
            def hello():
                click.echo('Hello World!')

            if __name__ == '__main__':
                hello()
            ```

            ## Conclusion

            That's the basic setup! Have questions?""",
            metadata={"tags": ["python", "cli", "tutorial"], "description": "A beginner guide to CLI tools"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestDevtoAdapterGeneration:
    """Tests for DevtoAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "devto"
        config_dir.mkdir()
        return DevtoAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Database migration tool",
            technical_details=["PostgreSQL", "Python", "SQLAlchemy"],
            problem_solved="Complex migration workflows",
            target_audience="Backend developers",
            key_metrics=["Zero downtime"],
            unique_aspects=["Rollback support"],
            limitations=["PostgreSQL only"],
            content_type="tutorial"
        )

    @patch.object(DevtoAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "title": "Building Database Migrations with Python",
            "body": "# Guide\n\n```python\ncode\n```",
            "tags": ["python", "database"],
            "description": "A guide to migrations",
            "cover_image_prompt": "Database diagram",
            "series": None
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "devto"

    @patch.object(DevtoAdapter, '_make_llm_call')
    def test_generate_content_includes_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes all metadata."""
        mock_llm.return_value = {
            "title": "Title",
            "body": "Body",
            "tags": ["tag1", "tag2"],
            "description": "Desc",
            "cover_image": "image.png",
            "series": "Python Series"
        }

        result = adapter.generate_content(sample_dna)

        assert "tags" in result.metadata
        assert "description" in result.metadata
        assert "series" in result.metadata

    @patch.object(DevtoAdapter, '_make_llm_call')
    def test_generate_content_handles_empty_response(self, mock_llm, adapter, sample_dna):
        """Test generate_content handles empty response."""
        mock_llm.return_value = {}

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.title == ""
