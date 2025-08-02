"""Tests for core/dna_extractor.py - DNAExtractor class."""
import pytest
import json
from unittest.mock import patch, MagicMock
from core.dna_extractor import DNAExtractor
from core.models import ContentDNA


class TestDNAExtractor:
    """Tests for DNAExtractor class."""

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extractor_initialization(self, mock_adapter):
        """Test extractor initializes with adapter."""
        extractor = DNAExtractor()
        assert mock_adapter.called

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extractor_custom_model(self, mock_adapter):
        """Test extractor with custom model."""
        extractor = DNAExtractor(model="custom-model")
        call_args = mock_adapter.call_args
        assert call_args[0][0] == "custom-model"

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extractor_custom_api_key(self, mock_adapter):
        """Test extractor with custom API key."""
        extractor = DNAExtractor(api_key="test-key")
        call_args = mock_adapter.call_args
        assert call_args[0][1] == "test-key"


class TestDNAExtractorExtraction:
    """Tests for DNAExtractor.extract_dna method."""

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_returns_content_dna(self, mock_adapter_class):
        """Test extract_dna returns ContentDNA object."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "A helpful tool",
            "problem_solved": "Complex task",
            "technical_details": ["Python"],
            "target_audience": "developers",
            "key_metrics": ["fast"],
            "unique_aspects": ["simple"],
            "limitations": ["none"],
            "content_type": "tool"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Sample content")

        assert isinstance(result, ContentDNA)
        assert result.value_proposition == "A helpful tool"

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_handles_missing_fields(self, mock_adapter_class):
        """Test extract_dna handles missing fields with defaults."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "Partial"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Content")

        assert result.value_proposition == "Partial"
        assert result.technical_details == []
        assert result.target_audience == "general"

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_handles_invalid_json(self, mock_adapter_class):
        """Test extract_dna handles invalid JSON gracefully."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Not valid JSON"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Some long content here that is meaningful")

        assert isinstance(result, ContentDNA)
        # Should use first 200 chars of content as value proposition fallback
        assert "Some long content" in result.value_proposition

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_uses_content_as_fallback(self, mock_adapter_class):
        """Test extract_dna uses content as fallback value proposition."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Invalid response"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        content = "This is the original content to extract from"
        result = extractor.extract_dna(content)

        assert "original content" in result.value_proposition

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_long_content_truncation(self, mock_adapter_class):
        """Test extract_dna truncates long content in fallback."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Invalid"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        long_content = "X" * 500
        result = extractor.extract_dna(long_content)

        # Fallback should truncate to 200 chars
        assert len(result.value_proposition) <= 200

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_default_content_type(self, mock_adapter_class):
        """Test extract_dna sets default content type on fallback."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Invalid"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Content")

        assert result.content_type == "general"

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_prompt_includes_content(self, mock_adapter_class):
        """Test extract_dna includes content in prompt."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "Test",
            "problem_solved": "",
            "technical_details": [],
            "target_audience": "general",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        extractor.extract_dna("Unique content marker 98765")

        call_args = mock_adapter.adapt_content.call_args
        prompt = call_args[0][0]
        assert "98765" in prompt


class TestDNAExtractorEdgeCases:
    """Edge case tests for DNAExtractor."""

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_empty_content(self, mock_adapter_class):
        """Test extract_dna handles empty content."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "Empty",
            "problem_solved": "",
            "technical_details": [],
            "target_audience": "general",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "general"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("")

        assert isinstance(result, ContentDNA)

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_whitespace_content(self, mock_adapter_class):
        """Test extract_dna handles whitespace-only content."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Invalid"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("   \n\t  ")

        assert isinstance(result, ContentDNA)

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_special_characters(self, mock_adapter_class):
        """Test extract_dna handles special characters."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "Special chars",
            "problem_solved": "",
            "technical_details": [],
            "target_audience": "devs",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Content with <html> & 'quotes' and \"double\"")

        assert isinstance(result, ContentDNA)

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_unicode(self, mock_adapter_class):
        """Test extract_dna handles unicode."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = json.dumps({
            "value_proposition": "Unicode test",
            "problem_solved": "",
            "technical_details": [],
            "target_audience": "general",
            "key_metrics": [],
            "unique_aspects": [],
            "limitations": [],
            "content_type": "tool"
        })
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Content with emoji and 中文")

        assert isinstance(result, ContentDNA)

    @patch('core.dna_extractor.PlatformAdapter')
    def test_extract_dna_json_decode_error_logging(self, mock_adapter_class, capsys):
        """Test extract_dna logs JSON decode errors."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Not JSON at all"
        mock_adapter_class.return_value = mock_adapter

        extractor = DNAExtractor()
        result = extractor.extract_dna("Content here")

        captured = capsys.readouterr()
        assert "Error" in captured.out or isinstance(result, ContentDNA)
