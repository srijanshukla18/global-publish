"""Tests for platforms/medium/adapter.py - MediumAdapter."""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.medium.adapter import MediumAdapter


class TestMediumAdapter:
    """Tests for MediumAdapter class."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "medium"
        config_dir.mkdir()
        return MediumAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="A guide to building scalable systems",
            technical_details=["Kubernetes", "Docker", "Microservices"],
            problem_solved="Complex deployment pipelines",
            target_audience="Backend engineers",
            key_metrics=["50% deployment time reduction"],
            unique_aspects=["GitOps workflow"],
            limitations=["Requires K8s knowledge"],
            content_type="tutorial"
        )

    def test_adapter_initialization(self, adapter, tmp_path):
        """Test adapter initializes correctly."""
        assert adapter.config_dir == tmp_path / "medium"
        assert adapter.model == "gpt-4o"


class TestMediumAdapterValidation:
    """Tests for MediumAdapter validate_content method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "medium"
        config_dir.mkdir()
        return MediumAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="medium",
            title="",
            body="Article body content here.",
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("title" in e.lower() and "required" in e.lower() for e in result.errors)

    def test_validate_title_too_long(self, adapter):
        """Test validation catches overly long title."""
        content = PlatformContent(
            platform="medium",
            title="x" * 150,
            body="Article body content here.",
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("100" in e for e in result.errors)

    def test_validate_title_too_short(self, adapter):
        """Test validation warns about very short title."""
        content = PlatformContent(
            platform="medium",
            title="Test",
            body="Article body content here with enough words.",
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_missing_body(self, adapter):
        """Test validation catches missing body."""
        content = PlatformContent(
            platform="medium",
            title="Good Title Here",
            body="",
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("body" in e.lower() for e in result.errors)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        content = PlatformContent(
            platform="medium",
            title="Good Title Here",
            body="Short content.",
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_missing_headers_suggestion(self, adapter):
        """Test validation suggests adding headers."""
        content = PlatformContent(
            platform="medium",
            title="Good Title Here",
            body="This is a paragraph without any headers. Just plain text. " * 20,
            metadata={"tags": ["python"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("header" in s.lower() for s in result.suggestions)

    def test_validate_too_many_tags(self, adapter):
        """Test validation warns about too many tags."""
        content = PlatformContent(
            platform="medium",
            title="Good Title Here",
            body="# Section\n\nArticle body content here.",
            metadata={"tags": ["one", "two", "three", "four", "five", "six"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("5" in w or "tag" in w.lower() for w in result.warnings)

    def test_validate_no_tags(self, adapter):
        """Test validation warns about missing tags."""
        content = PlatformContent(
            platform="medium",
            title="Good Title Here",
            body="# Section\n\nArticle body content here.",
            metadata={"tags": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("tag" in w.lower() for w in result.warnings)

    def test_validate_missing_personal_voice(self, adapter):
        """Test validation suggests adding personal insights."""
        content = PlatformContent(
            platform="medium",
            title="Technical Guide",
            body="""# Guide

            The system works as follows. Data flows through the pipeline.
            Components are configured automatically. Results are processed.""",
            metadata={"tags": ["tech"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("personal" in s.lower() for s in result.suggestions)

    def test_validate_has_personal_voice(self, adapter):
        """Test validation recognizes personal voice."""
        content = PlatformContent(
            platform="medium",
            title="My Journey Building a System",
            body="""# My Experience

            I spent weeks learning about this topic. My approach was different
            because I focused on simplicity. We built the system from scratch.""",
            metadata={"tags": ["tech"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        # Should not suggest personal insights since they're present
        personal_suggestions = [s for s in result.suggestions if "personal" in s.lower()]
        assert len(personal_suggestions) == 0

    def test_validate_valid_article(self, adapter):
        """Test validation passes for valid article."""
        content = PlatformContent(
            platform="medium",
            title="How I Built a Scalable System in Two Weeks",
            body="""# Introduction

            I've always been fascinated by distributed systems. My journey
            started when I realized the existing solutions weren't working.

            ## The Problem

            We faced significant challenges with our deployment pipeline.
            I tried multiple approaches before finding what worked.

            ## The Solution

            After experimenting, I discovered a simpler approach.""",
            metadata={"tags": ["programming", "devops", "kubernetes"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestMediumAdapterGeneration:
    """Tests for MediumAdapter content generation."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "medium"
        config_dir.mkdir()
        return MediumAdapter(config_dir)

    @pytest.fixture
    def sample_dna(self):
        return ContentDNA(
            value_proposition="Developer tool",
            technical_details=["Python"],
            problem_solved="Problem",
            target_audience="Developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

    @patch.object(MediumAdapter, '_make_llm_call')
    def test_generate_content_returns_platform_content(self, mock_llm, adapter, sample_dna):
        """Test generate_content returns PlatformContent."""
        mock_llm.return_value = {
            "title": "Article Title",
            "body": "# Content\n\nBody here.",
            "tags": ["python", "tutorial"],
            "subtitle": "A deep dive"
        }

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.platform == "medium"
        assert result.title == "Article Title"

    @patch.object(MediumAdapter, '_make_llm_call')
    def test_generate_content_includes_metadata(self, mock_llm, adapter, sample_dna):
        """Test generate_content includes proper metadata."""
        mock_llm.return_value = {
            "title": "Title",
            "body": "Body",
            "tags": ["tag1", "tag2"],
            "subtitle": "Subtitle"
        }

        result = adapter.generate_content(sample_dna)

        assert "tags" in result.metadata
        assert "subtitle" in result.metadata
        assert result.metadata["seo_optimized"] is True

    @patch.object(MediumAdapter, '_make_llm_call')
    def test_generate_content_handles_empty_response(self, mock_llm, adapter, sample_dna):
        """Test generate_content handles empty LLM response."""
        mock_llm.return_value = {}

        result = adapter.generate_content(sample_dna)

        assert isinstance(result, PlatformContent)
        assert result.title == ""
        assert result.body == ""
