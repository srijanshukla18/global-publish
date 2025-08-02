"""Tests for core/quality_enhancer.py - QualityEnhancer class."""
import pytest
from unittest.mock import patch, MagicMock
from core.quality_enhancer import QualityEnhancer


class TestQualityEnhancer:
    """Tests for QualityEnhancer class."""

    def test_quality_guidelines_exist(self):
        """Test that QUALITY_GUIDELINES constant is defined."""
        assert QualityEnhancer.QUALITY_GUIDELINES
        assert len(QualityEnhancer.QUALITY_GUIDELINES) > 100
        assert "AUTHENTICITY" in QualityEnhancer.QUALITY_GUIDELINES

    def test_quality_guidelines_contains_bad_patterns(self):
        """Test that guidelines contain forbidden patterns."""
        guidelines = QualityEnhancer.QUALITY_GUIDELINES.lower()
        forbidden = ["revolutionary", "game-changing", "amazing", "incredible"]
        for word in forbidden:
            assert word in guidelines, f"Guidelines should mention forbidden word: {word}"

    def test_quality_guidelines_contains_good_examples(self):
        """Test that guidelines contain positive examples."""
        guidelines = QualityEnhancer.QUALITY_GUIDELINES
        assert "GOOD TONE" in guidelines
        assert "BAD TONE" in guidelines

    def test_enhance_prompt_adds_guidelines(self):
        """Test that enhance_prompt adds quality guidelines."""
        base_prompt = "Write a short post about my tool."
        enhanced = QualityEnhancer.enhance_prompt(base_prompt)

        assert QualityEnhancer.QUALITY_GUIDELINES in enhanced
        assert base_prompt in enhanced
        assert "REMINDER" in enhanced

    def test_enhance_prompt_static_method(self):
        """Test enhance_prompt is a static method."""
        result = QualityEnhancer.enhance_prompt("test")
        assert isinstance(result, str)

    def test_enhance_prompt_preserves_original(self):
        """Test that enhance_prompt preserves original prompt."""
        original = "My specific prompt with unique text 12345"
        enhanced = QualityEnhancer.enhance_prompt(original)
        assert original in enhanced

    @patch('core.quality_enhancer.PlatformAdapter')
    def test_init_creates_adapter(self, mock_adapter):
        """Test initialization creates PlatformAdapter."""
        enhancer = QualityEnhancer(model="test-model")
        assert mock_adapter.called

    def test_validate_tone_quality_clean_text(self):
        """Test validate_tone_quality with clean text."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        clean_text = """I built this tool because I struggled with the existing options.
        It uses Python and handles basic file processing. There's still a limitation
        with large files, but I'm working on it."""

        result = enhancer.validate_tone_quality(clean_text)

        assert "issues" in result
        assert "suggestions" in result
        assert "quality_score" in result
        assert len(result["issues"]) == 0

    def test_validate_tone_quality_with_buzzwords(self):
        """Test validate_tone_quality catches marketing buzzwords."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        text = """This revolutionary tool will transform your workflow!
        Leverage the power of our cutting-edge platform to unlock unprecedented
        productivity. Don't miss this game-changing opportunity!"""

        result = enhancer.validate_tone_quality(text)

        assert len(result["issues"]) > 0
        assert result["quality_score"] < 100

    def test_validate_tone_quality_excessive_exclamation(self):
        """Test validate_tone_quality catches excessive exclamation marks."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        text = "Great tool! Amazing features! Works well! Try it now! Best ever!"

        result = enhancer.validate_tone_quality(text)

        assert any("exclamation" in issue.lower() for issue in result["issues"])
        assert result["quality_score"] < 100

    def test_validate_tone_quality_vague_language(self):
        """Test validate_tone_quality suggests specificity for vague content."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        text = """This solution provides a seamless platform experience for your
        ecosystem. The solution integrates with your existing platform."""

        result = enhancer.validate_tone_quality(text)

        assert len(result["suggestions"]) > 0

    def test_validate_tone_quality_missing_personal_voice(self):
        """Test validate_tone_quality suggests personal context."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        text = """The software processes data efficiently. It handles multiple
        file formats. The architecture uses modern patterns."""

        result = enhancer.validate_tone_quality(text)

        assert any("personal" in s.lower() or "challenge" in s.lower()
                   for s in result["suggestions"])

    def test_validate_tone_quality_score_calculation(self):
        """Test quality score calculation."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)

        # Perfect text
        perfect = "I built this and faced challenges with the limitation."
        perfect_result = enhancer.validate_tone_quality(perfect)

        # Text with issues
        bad = "Revolutionary amazing incredible tool! Supercharge your work!"
        bad_result = enhancer.validate_tone_quality(bad)

        assert perfect_result["quality_score"] > bad_result["quality_score"]

    def test_validate_tone_quality_score_minimum(self):
        """Test quality score doesn't go below 0."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)
        terrible_text = """Revolutionary game-changing amazing incredible perfect
        unlock empower leverage seamless cutting-edge next-generation
        industry-leading best solution don't miss transform your supercharge
        unprecedented!!!!!!!!!!!"""

        result = enhancer.validate_tone_quality(terrible_text)

        assert result["quality_score"] >= 0

    def test_validate_tone_quality_with_authentic_indicators(self):
        """Test text with authentic indicators gets fewer suggestions."""
        enhancer = QualityEnhancer.__new__(QualityEnhancer)

        authentic = """I built this tool after struggling with existing solutions.
        We created a workaround for the limitation we faced."""

        generic = """The tool provides functionality. It works well."""

        authentic_result = enhancer.validate_tone_quality(authentic)
        generic_result = enhancer.validate_tone_quality(generic)

        # Authentic text should have fewer suggestions about adding personal context
        authentic_suggestions = [s for s in authentic_result["suggestions"]
                                if "personal" in s.lower()]
        generic_suggestions = [s for s in generic_result["suggestions"]
                              if "personal" in s.lower()]

        assert len(authentic_suggestions) <= len(generic_suggestions)

    @patch('core.quality_enhancer.PlatformAdapter')
    def test_refine_output_calls_adapter(self, mock_adapter_class):
        """Test refine_output calls adapter.adapt_content."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Refined content"
        mock_adapter_class.return_value = mock_adapter

        enhancer = QualityEnhancer(model="test")
        result = enhancer.refine_output("Original content", "hackernews")

        assert mock_adapter.adapt_content.called
        assert result == "Refined content"

    @patch('core.quality_enhancer.PlatformAdapter')
    def test_refine_output_handles_error(self, mock_adapter_class):
        """Test refine_output handles errors gracefully."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.side_effect = Exception("API Error")
        mock_adapter_class.return_value = mock_adapter

        enhancer = QualityEnhancer(model="test")
        result = enhancer.refine_output("Original content", "hackernews")

        # Should return original on error
        assert result == "Original content"

    @patch('core.quality_enhancer.PlatformAdapter')
    def test_refine_output_includes_platform_in_prompt(self, mock_adapter_class):
        """Test refine_output includes platform name in refinement prompt."""
        mock_adapter = MagicMock()
        mock_adapter.adapt_content.return_value = "Refined"
        mock_adapter_class.return_value = mock_adapter

        enhancer = QualityEnhancer(model="test")
        enhancer.refine_output("Content", "twitter")

        call_args = mock_adapter.adapt_content.call_args[0][0]
        assert "twitter" in call_args.lower()


class TestQualityEnhancerForbiddenPhrases:
    """Tests specifically for forbidden phrase detection."""

    @pytest.fixture
    def enhancer(self):
        return QualityEnhancer.__new__(QualityEnhancer)

    def test_all_forbidden_phrases_detected(self, enhancer):
        """Test all defined forbidden phrases are detected."""
        forbidden_phrases = [
            "revolutionary", "game-changing", "amazing", "incredible", "perfect",
            "unlock", "empower", "leverage", "seamless", "cutting-edge",
            "next-generation", "industry-leading", "best solution", "don't miss",
            "transform your", "supercharge", "unprecedented"
        ]

        for phrase in forbidden_phrases:
            text = f"This is a test with {phrase} included."
            result = enhancer.validate_tone_quality(text)
            assert len(result["issues"]) > 0, f"Should detect: {phrase}"

    def test_case_insensitive_detection(self, enhancer):
        """Test forbidden phrases detected case-insensitively."""
        variations = [
            "REVOLUTIONARY",
            "Revolutionary",
            "revolutionary",
            "GAME-CHANGING",
            "Game-Changing"
        ]

        for phrase in variations:
            text = f"Test with {phrase} here."
            result = enhancer.validate_tone_quality(text)
            assert len(result["issues"]) > 0, f"Should detect: {phrase}"

    def test_partial_phrase_handling(self, enhancer):
        """Test that partial matches work as expected."""
        # 'unlock' should be detected in 'unlocking'
        text = "Unlocking new potential through our platform."
        result = enhancer.validate_tone_quality(text)
        assert len(result["issues"]) > 0


class TestQualityEnhancerEdgeCases:
    """Edge case tests for QualityEnhancer."""

    @pytest.fixture
    def enhancer(self):
        return QualityEnhancer.__new__(QualityEnhancer)

    def test_empty_text(self, enhancer):
        """Test validate_tone_quality with empty text."""
        result = enhancer.validate_tone_quality("")
        assert "quality_score" in result
        assert isinstance(result["issues"], list)
        assert isinstance(result["suggestions"], list)

    def test_very_short_text(self, enhancer):
        """Test validate_tone_quality with very short text."""
        result = enhancer.validate_tone_quality("Hi")
        assert "quality_score" in result

    def test_very_long_text(self, enhancer):
        """Test validate_tone_quality with very long text."""
        long_text = "This is a sentence. " * 1000
        result = enhancer.validate_tone_quality(long_text)
        assert "quality_score" in result

    def test_unicode_text(self, enhancer):
        """Test validate_tone_quality with unicode characters."""
        unicode_text = "I built this café-style naïve implementation."
        result = enhancer.validate_tone_quality(unicode_text)
        assert "quality_score" in result

    def test_text_with_only_exclamation_marks(self, enhancer):
        """Test text that's almost all exclamation marks."""
        text = "! ! ! ! !"
        result = enhancer.validate_tone_quality(text)
        assert any("exclamation" in issue.lower() for issue in result["issues"])

    def test_text_with_exactly_three_exclamation_marks(self, enhancer):
        """Test boundary condition for exclamation marks."""
        text = "Good! Great! Excellent!"  # Exactly 3
        result = enhancer.validate_tone_quality(text)
        # Should not trigger warning for exactly 3
        assert not any("exclamation" in issue.lower() for issue in result["issues"])

    def test_text_with_four_exclamation_marks(self, enhancer):
        """Test boundary condition for exclamation marks."""
        text = "Good! Great! Excellent! Amazing!"  # 4
        result = enhancer.validate_tone_quality(text)
        assert any("exclamation" in issue.lower() for issue in result["issues"])
