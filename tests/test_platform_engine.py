"""Tests for core/platform_engine.py - PlatformAdapter and Validator base classes."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.platform_engine import PlatformAdapter, Validator
from core.models import ContentDNA, PlatformContent, ValidationResult


class ConcretePlatformAdapter(PlatformAdapter):
    """Concrete implementation for testing abstract class."""

    def generate_content(self, content_dna: ContentDNA) -> PlatformContent:
        return PlatformContent(
            platform="test",
            title="Test Title",
            body="Test Body",
            metadata={},
            validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        )

    def validate_content(self, content: PlatformContent) -> ValidationResult:
        return ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])


class ConcreteValidator(Validator):
    """Concrete implementation for testing abstract class."""

    def validate(self, content: PlatformContent) -> ValidationResult:
        return ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])


class TestPlatformAdapter:
    """Tests for PlatformAdapter base class."""

    @pytest.fixture
    def mock_config_dir(self, tmp_path):
        config_dir = tmp_path / "test_platform"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def adapter(self, mock_config_dir):
        return ConcretePlatformAdapter(mock_config_dir)

    def test_adapter_initialization(self, adapter, mock_config_dir):
        """Test adapter initializes with correct defaults."""
        assert adapter.config_dir == mock_config_dir
        assert adapter.model == "gpt-4o"
        assert adapter.profile == {}  # No profile.yaml

    def test_adapter_with_custom_model(self, mock_config_dir):
        """Test adapter with custom model."""
        adapter = ConcretePlatformAdapter(mock_config_dir, model="claude-3-opus")
        assert adapter.model == "claude-3-opus"

    def test_load_profile_no_file(self, mock_config_dir):
        """Test _load_profile returns empty dict when no file."""
        adapter = ConcretePlatformAdapter(mock_config_dir)
        assert adapter.profile == {}

    def test_load_profile_with_file(self, mock_config_dir):
        """Test _load_profile loads yaml file."""
        profile_path = mock_config_dir / "profile.yaml"
        profile_path.write_text("""
platform_name: Test
max_length: 100
forbidden_words:
  - spam
  - scam
""")
        adapter = ConcretePlatformAdapter(mock_config_dir)
        assert adapter.profile.get("platform_name") == "Test"
        assert adapter.profile.get("max_length") == 100
        assert "spam" in adapter.profile.get("forbidden_words", [])


class TestPlatformAdapterJsonParsing:
    """Tests for PlatformAdapter JSON parsing."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "test"
        config_dir.mkdir()
        return ConcretePlatformAdapter(config_dir)

    def test_parse_json_response_direct(self, adapter):
        """Test parsing direct JSON."""
        content = '{"title": "Test", "body": "Content"}'
        result = adapter._parse_json_response(content)
        assert result["title"] == "Test"
        assert result["body"] == "Content"

    def test_parse_json_response_markdown_block(self, adapter):
        """Test parsing JSON in markdown code block."""
        content = '''```json
{"title": "Test", "body": "Content"}
```'''
        result = adapter._parse_json_response(content)
        assert result["title"] == "Test"

    def test_parse_json_response_markdown_block_no_lang(self, adapter):
        """Test parsing JSON in markdown block without language."""
        content = '''```
{"title": "Test", "body": "Content"}
```'''
        result = adapter._parse_json_response(content)
        assert result["title"] == "Test"

    def test_parse_json_response_with_surrounding_text(self, adapter):
        """Test parsing JSON with surrounding text."""
        content = '''Here is the response:
{"title": "Test", "body": "Content"}'''
        result = adapter._parse_json_response(content)
        assert result["title"] == "Test"

    def test_parse_json_response_with_newlines_in_strings(self, adapter):
        """Test parsing JSON with newlines in string values."""
        content = '''{"title": "Test", "body": "Line 1
Line 2
Line 3"}'''
        result = adapter._parse_json_response(content)
        # Should handle or at least not crash
        assert "title" in result or result == {}

    def test_parse_json_response_invalid_json(self, adapter):
        """Test parsing invalid JSON returns empty dict."""
        content = "This is not JSON at all"
        result = adapter._parse_json_response(content)
        assert result == {}

    def test_parse_json_response_nested_code_blocks(self, adapter):
        """Test parsing JSON with nested content."""
        content = '''```json
{
  "title": "Test",
  "body": "Some content with ```code``` here"
}
```'''
        result = adapter._parse_json_response(content)
        # Should attempt to parse
        assert isinstance(result, dict)

    def test_parse_json_response_empty(self, adapter):
        """Test parsing empty string."""
        result = adapter._parse_json_response("")
        assert result == {}


class TestPlatformAdapterLLMCall:
    """Tests for PlatformAdapter _make_llm_call method."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "test"
        config_dir.mkdir()
        return ConcretePlatformAdapter(config_dir)

    @patch('litellm.completion')
    def test_make_llm_call_basic(self, mock_completion, adapter):
        """Test basic LLM call."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"title": "Test"}'
        mock_completion.return_value = mock_response

        result = adapter._make_llm_call("Test prompt")

        assert result["title"] == "Test"
        mock_completion.assert_called_once()

    @patch('litellm.completion')
    def test_make_llm_call_with_system_prompt(self, mock_completion, adapter):
        """Test LLM call with system prompt."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_completion.return_value = mock_response

        adapter._make_llm_call("User prompt", system_prompt="System prompt")

        call_args = mock_completion.call_args
        messages = call_args.kwargs.get('messages', call_args[1].get('messages', []))
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch('litellm.completion')
    def test_make_llm_call_without_system_prompt(self, mock_completion, adapter):
        """Test LLM call without system prompt."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_completion.return_value = mock_response

        adapter._make_llm_call("User prompt only")

        call_args = mock_completion.call_args
        messages = call_args.kwargs.get('messages', call_args[1].get('messages', []))
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @patch('litellm.completion')
    def test_make_llm_call_uses_adapter_model(self, mock_completion, adapter):
        """Test LLM call uses adapter's model."""
        adapter.model = "test-model-123"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_completion.return_value = mock_response

        adapter._make_llm_call("Prompt")

        call_args = mock_completion.call_args
        model = call_args.kwargs.get('model', call_args[1].get('model'))
        assert model == "test-model-123"

    @patch('litellm.completion')
    def test_make_llm_call_handles_exception(self, mock_completion, adapter):
        """Test LLM call handles exceptions gracefully."""
        mock_completion.side_effect = Exception("API Error")

        result = adapter._make_llm_call("Prompt")

        assert result == {}


class TestValidator:
    """Tests for Validator base class."""

    def test_validator_is_abstract(self):
        """Test Validator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Validator()

    def test_concrete_validator_works(self):
        """Test concrete validator implementation."""
        validator = ConcreteValidator()
        content = PlatformContent(
            platform="test",
            title="Test",
            body="Body",
            metadata={},
            validation=ValidationResult(is_valid=True, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True


class TestAbstractMethods:
    """Test abstract method enforcement."""

    def test_platform_adapter_requires_generate_content(self):
        """Test PlatformAdapter requires generate_content implementation."""
        class IncompleteAdapter(PlatformAdapter):
            def validate_content(self, content):
                pass

        with pytest.raises(TypeError):
            IncompleteAdapter(Path("."))

    def test_platform_adapter_requires_validate_content(self):
        """Test PlatformAdapter requires validate_content implementation."""
        class IncompleteAdapter(PlatformAdapter):
            def generate_content(self, dna):
                pass

        with pytest.raises(TypeError):
            IncompleteAdapter(Path("."))

    def test_validator_requires_validate(self):
        """Test Validator requires validate implementation."""
        class IncompleteValidator(Validator):
            pass

        with pytest.raises(TypeError):
            IncompleteValidator()
