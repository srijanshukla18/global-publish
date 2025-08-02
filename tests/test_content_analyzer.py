"""Tests for core/content_analyzer.py - ContentAnalyzer class."""
import pytest
import json
from unittest.mock import patch, MagicMock
from core.content_analyzer import ContentAnalyzer
from core.models import ContentDNA


class TestContentAnalyzer:
    """Tests for ContentAnalyzer class."""

    def test_analyzer_initialization_default_model(self):
        """Test analyzer initializes with default model."""
        analyzer = ContentAnalyzer()
        assert analyzer.model == "gpt-4o"

    def test_analyzer_initialization_custom_model(self):
        """Test analyzer initializes with custom model."""
        analyzer = ContentAnalyzer(model="claude-3-opus")
        assert analyzer.model == "claude-3-opus"

    @patch('core.content_analyzer.completion')
    def test_analyze_returns_content_dna(self, mock_completion):
        """Test analyze returns ContentDNA object."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "A tool for developers",
            "technical_details": ["Python", "API"],
            "problem_solved": "Complex workflows",
            "target_audience": "Backend developers",
            "key_metrics": ["50% faster"],
            "unique_aspects": ["Simple interface"],
            "limitations": ["Requires Python 3.8+"],
            "content_type": "tool_launch"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Sample content to analyze")

        assert isinstance(result, ContentDNA)
        assert result.value_proposition == "A tool for developers"
        assert "Python" in result.technical_details

    @patch('core.content_analyzer.completion')
    def test_analyze_handles_markdown_json_response(self, mock_completion):
        """Test analyze handles JSON in markdown code blocks."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''```json
{
    "value_proposition": "Test value",
    "technical_details": [],
    "problem_solved": "Test problem",
    "target_audience": "Developers",
    "key_metrics": [],
    "unique_aspects": [],
    "limitations": [],
    "content_type": "tool_launch"
}
```'''
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Content")

        assert result.value_proposition == "Test value"

    @patch('core.content_analyzer.completion')
    def test_analyze_handles_missing_fields(self, mock_completion):
        """Test analyze handles missing fields with defaults."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Partial response"
            # Missing other fields
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Content")

        assert result.value_proposition == "Partial response"
        assert result.technical_details == []
        assert result.problem_solved == ""
        assert result.content_type == "announcement"  # Default

    @patch('core.content_analyzer.completion')
    def test_analyze_handles_exception(self, mock_completion):
        """Test analyze handles API exceptions gracefully."""
        mock_completion.side_effect = Exception("API Error")

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Content")

        assert isinstance(result, ContentDNA)
        assert "Error" in result.value_proposition
        assert result.technical_details == []

    @patch('core.content_analyzer.completion')
    def test_analyze_handles_invalid_json(self, mock_completion):
        """Test analyze handles invalid JSON response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not valid JSON at all"
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Content")

        assert isinstance(result, ContentDNA)
        assert "Error" in result.value_proposition

    @patch('core.content_analyzer.completion')
    def test_analyze_uses_correct_model(self, mock_completion):
        """Test analyze uses the configured model."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Test",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool_launch"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer(model="test-model")
        analyzer.analyze("Content")

        call_args = mock_completion.call_args
        assert call_args.kwargs.get('model') == "test-model"

    @patch('core.content_analyzer.completion')
    def test_analyze_uses_low_temperature(self, mock_completion):
        """Test analyze uses low temperature for consistency."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Test",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        analyzer.analyze("Content")

        call_args = mock_completion.call_args
        temperature = call_args.kwargs.get('temperature')
        assert temperature is not None
        assert temperature <= 0.3  # Low temperature for consistency

    @patch('core.content_analyzer.completion')
    def test_analyze_includes_content_in_prompt(self, mock_completion):
        """Test analyze includes raw content in prompt."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Test",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        analyzer.analyze("My unique content about a special tool 12345")

        call_args = mock_completion.call_args
        messages = call_args.kwargs.get('messages', [])
        prompt_content = messages[0]['content'] if messages else ""
        assert "12345" in prompt_content


class TestContentAnalyzerPrompt:
    """Tests for ContentAnalyzer prompt construction."""

    @patch('core.content_analyzer.completion')
    def test_prompt_requests_all_dna_fields(self, mock_completion):
        """Test prompt requests all ContentDNA fields."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Test",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        analyzer.analyze("Content")

        call_args = mock_completion.call_args
        messages = call_args.kwargs.get('messages', [])
        prompt = messages[0]['content'] if messages else ""

        expected_fields = [
            "value_proposition",
            "technical_details",
            "problem_solved",
            "target_audience",
            "key_metrics",
            "unique_aspects",
            "limitations",
            "content_type"
        ]

        for field in expected_fields:
            assert field in prompt, f"Prompt should request {field}"

    @patch('core.content_analyzer.completion')
    def test_prompt_requests_json_format(self, mock_completion):
        """Test prompt requests JSON output format."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Test",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        analyzer.analyze("Content")

        call_args = mock_completion.call_args
        messages = call_args.kwargs.get('messages', [])
        prompt = messages[0]['content'].lower() if messages else ""

        assert "json" in prompt


class TestContentAnalyzerEdgeCases:
    """Edge case tests for ContentAnalyzer."""

    @patch('core.content_analyzer.completion')
    def test_analyze_empty_content(self, mock_completion):
        """Test analyze handles empty content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Empty",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "general"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = analyzer.analyze("")

        assert isinstance(result, ContentDNA)

    @patch('core.content_analyzer.completion')
    def test_analyze_very_long_content(self, mock_completion):
        """Test analyze handles very long content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Long content",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "article"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        long_content = "A" * 10000
        result = analyzer.analyze(long_content)

        assert isinstance(result, ContentDNA)

    @patch('core.content_analyzer.completion')
    def test_analyze_unicode_content(self, mock_completion):
        """Test analyze handles unicode content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "value_proposition": "Unicode support",
            "technical_details": [],
            "problem_solved": "",
            "target_audience": "",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_completion.return_value = mock_response

        analyzer = ContentAnalyzer()
        unicode_content = "Content with emoji and 日本語 text"
        result = analyzer.analyze(unicode_content)

        assert isinstance(result, ContentDNA)
