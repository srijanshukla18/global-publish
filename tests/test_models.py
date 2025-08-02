"""Tests for core/models.py - Data models."""
import pytest
from core.models import ContentDNA, ValidationResult, PlatformContent, PublishResult, PostStatus


class TestPostStatus:
    """Tests for PostStatus enum."""

    def test_post_status_values(self):
        """Test all PostStatus enum values exist."""
        assert PostStatus.PENDING.value == "pending"
        assert PostStatus.PROCESSING.value == "processing"
        assert PostStatus.POSTED.value == "posted"
        assert PostStatus.FAILED.value == "failed"

    def test_post_status_comparison(self):
        """Test PostStatus enum comparison."""
        assert PostStatus.PENDING == PostStatus.PENDING
        assert PostStatus.PENDING != PostStatus.POSTED

    def test_post_status_from_value(self):
        """Test creating PostStatus from string value."""
        assert PostStatus("pending") == PostStatus.PENDING
        assert PostStatus("posted") == PostStatus.POSTED


class TestContentDNA:
    """Tests for ContentDNA dataclass."""

    def test_content_dna_creation(self, sample_content_dna):
        """Test ContentDNA creation with all fields."""
        dna = sample_content_dna
        assert dna.value_proposition == "A CLI tool that converts markdown to multi-platform social posts"
        assert dna.content_type == "tool_launch"
        assert "Python" in dna.technical_details
        assert len(dna.key_metrics) == 2

    def test_content_dna_minimal(self, minimal_content_dna):
        """Test ContentDNA with minimal/empty fields."""
        dna = minimal_content_dna
        assert dna.value_proposition == "Simple tool"
        assert dna.technical_details == []
        assert dna.problem_solved == ""

    def test_content_dna_all_fields(self):
        """Test ContentDNA with all fields specified."""
        dna = ContentDNA(
            value_proposition="Test value",
            technical_details=["Tech1", "Tech2"],
            problem_solved="Test problem",
            target_audience="Test audience",
            key_metrics=["Metric1"],
            unique_aspects=["Unique1"],
            limitations=["Limit1"],
            content_type="tutorial"
        )
        assert len(dna.technical_details) == 2
        assert dna.content_type == "tutorial"

    def test_content_dna_field_types(self):
        """Test ContentDNA field types are correct."""
        dna = ContentDNA(
            value_proposition="",
            technical_details=[],
            problem_solved="",
            target_audience="",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type=""
        )
        assert isinstance(dna.value_proposition, str)
        assert isinstance(dna.technical_details, list)
        assert isinstance(dna.key_metrics, list)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_valid(self, sample_validation_result):
        """Test valid ValidationResult."""
        result = sample_validation_result
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1

    def test_validation_result_invalid(self, failing_validation_result):
        """Test invalid ValidationResult."""
        result = failing_validation_result
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "Missing required field" in result.errors

    def test_validation_result_empty(self):
        """Test ValidationResult with empty lists."""
        result = ValidationResult(
            is_valid=True,
            warnings=[],
            errors=[],
            suggestions=[]
        )
        assert result.is_valid is True
        assert result.warnings == []
        assert result.errors == []
        assert result.suggestions == []

    def test_validation_result_all_types(self):
        """Test ValidationResult with all types populated."""
        result = ValidationResult(
            is_valid=False,
            warnings=["warn1", "warn2"],
            errors=["error1"],
            suggestions=["sugg1", "sugg2", "sugg3"]
        )
        assert len(result.warnings) == 2
        assert len(result.errors) == 1
        assert len(result.suggestions) == 3


class TestPlatformContent:
    """Tests for PlatformContent dataclass."""

    def test_platform_content_creation(self, sample_platform_content):
        """Test PlatformContent creation."""
        content = sample_platform_content
        assert content.platform == "hackernews"
        assert "Show HN" in content.title
        assert content.metadata["tags"] == ["python", "cli"]

    def test_platform_content_with_scheduled_time(self):
        """Test PlatformContent with scheduled time."""
        validation = ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="Tweet body",
            metadata={},
            validation=validation,
            scheduled_time="2024-01-15T10:00:00Z"
        )
        assert content.scheduled_time == "2024-01-15T10:00:00Z"

    def test_platform_content_without_scheduled_time(self):
        """Test PlatformContent without scheduled time defaults to None."""
        validation = ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        content = PlatformContent(
            platform="twitter",
            title="Thread",
            body="Tweet body",
            metadata={},
            validation=validation
        )
        assert content.scheduled_time is None

    def test_platform_content_metadata_types(self):
        """Test PlatformContent with various metadata types."""
        validation = ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        metadata = {
            "tags": ["tag1", "tag2"],
            "count": 42,
            "enabled": True,
            "nested": {"key": "value"}
        }
        content = PlatformContent(
            platform="medium",
            title="Article",
            body="Content",
            metadata=metadata,
            validation=validation
        )
        assert content.metadata["count"] == 42
        assert content.metadata["enabled"] is True
        assert content.metadata["nested"]["key"] == "value"


class TestPublishResult:
    """Tests for PublishResult dataclass."""

    def test_publish_result_success(self, sample_publish_result):
        """Test successful PublishResult."""
        result = sample_publish_result
        assert result.success is True
        assert result.platform == "hackernews"
        assert "ycombinator" in result.url
        assert result.error is None

    def test_publish_result_failure(self):
        """Test failed PublishResult."""
        result = PublishResult(
            platform="twitter",
            success=False,
            url=None,
            error="Rate limit exceeded",
            metadata=None
        )
        assert result.success is False
        assert result.url is None
        assert result.error == "Rate limit exceeded"

    def test_publish_result_with_metadata(self):
        """Test PublishResult with metadata."""
        result = PublishResult(
            platform="reddit",
            success=True,
            url="https://reddit.com/r/test/123",
            error=None,
            metadata={"upvotes": 100, "comments": 5, "subreddit": "programming"}
        )
        assert result.metadata["upvotes"] == 100
        assert result.metadata["subreddit"] == "programming"

    def test_publish_result_defaults(self):
        """Test PublishResult default values."""
        result = PublishResult(
            platform="test",
            success=True
        )
        assert result.url is None
        assert result.error is None
        assert result.metadata is None


class TestModelIntegration:
    """Integration tests between models."""

    def test_content_dna_to_platform_content_flow(self, sample_content_dna):
        """Test that ContentDNA can be used to inform PlatformContent."""
        dna = sample_content_dna
        validation = ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        content = PlatformContent(
            platform="hackernews",
            title=f"Show HN: {dna.value_proposition[:50]}",
            body=f"Problem: {dna.problem_solved}\n\nSolution: {dna.value_proposition}",
            metadata={"content_type": dna.content_type, "tech": dna.technical_details},
            validation=validation
        )
        assert content.metadata["content_type"] == "tool_launch"
        assert "Python" in content.metadata["tech"]

    def test_validation_affects_platform_content(self):
        """Test that validation result affects platform content validity."""
        valid_result = ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        invalid_result = ValidationResult(is_valid=False, warnings=[], errors=["Error"], suggestions=[])

        valid_content = PlatformContent(
            platform="test",
            title="Test",
            body="Body",
            metadata={},
            validation=valid_result
        )
        invalid_content = PlatformContent(
            platform="test",
            title="Test",
            body="Body",
            metadata={},
            validation=invalid_result
        )

        assert valid_content.validation.is_valid is True
        assert invalid_content.validation.is_valid is False
