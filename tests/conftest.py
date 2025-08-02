"""Pytest configuration and fixtures for global-publish tests."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.models import ContentDNA, ValidationResult, PlatformContent, PublishResult, PostStatus


@pytest.fixture
def sample_content_dna():
    """Create a sample ContentDNA for testing."""
    return ContentDNA(
        value_proposition="A CLI tool that converts markdown to multi-platform social posts",
        technical_details=["Python", "LiteLLM", "OpenAI API"],
        problem_solved="Tedious manual rewriting of content for different platforms",
        target_audience="Indie hackers and developers who want to promote their projects",
        key_metrics=["50% time saved", "10 platforms supported"],
        unique_aspects=["Platform-specific tone matching", "Automated validation"],
        limitations=["Requires API key", "English only"],
        content_type="tool_launch"
    )


@pytest.fixture
def minimal_content_dna():
    """Create a minimal ContentDNA with empty fields."""
    return ContentDNA(
        value_proposition="Simple tool",
        technical_details=[],
        problem_solved="",
        target_audience="general",
        key_metrics=[],
        unique_aspects=[],
        limitations=[],
        content_type="general"
    )


@pytest.fixture
def sample_validation_result():
    """Create a sample ValidationResult."""
    return ValidationResult(
        is_valid=True,
        warnings=["Consider adding more details"],
        errors=[],
        suggestions=["Add technical specifics"]
    )


@pytest.fixture
def failing_validation_result():
    """Create a failing ValidationResult."""
    return ValidationResult(
        is_valid=False,
        warnings=["Title is too long"],
        errors=["Missing required field", "Contains forbidden words"],
        suggestions=["Consider rephrasing"]
    )


@pytest.fixture
def sample_platform_content(sample_validation_result):
    """Create a sample PlatformContent."""
    return PlatformContent(
        platform="hackernews",
        title="Show HN: Global Publisher - Multi-platform content generation",
        body="I built this tool to solve my own problem...",
        metadata={"tags": ["python", "cli"], "engagement_strategy": "technical"},
        validation=sample_validation_result
    )


@pytest.fixture
def sample_publish_result():
    """Create a sample PublishResult."""
    return PublishResult(
        platform="hackernews",
        success=True,
        url="https://news.ycombinator.com/item?id=12345",
        error=None,
        metadata={"upvotes": 10}
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"title": "Test", "body": "Test body"}'
    return mock_response


@pytest.fixture
def mock_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_profile_yaml(mock_config_dir):
    """Create a mock profile.yaml file."""
    profile_path = mock_config_dir / "profile.yaml"
    profile_path.write_text("""
platform_name: Test Platform
max_title_length: 100
forbidden_words:
  - spam
  - scam
""")
    return mock_config_dir
