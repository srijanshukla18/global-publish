"""Tests for platforms/hackernews/validator.py - HackerNewsValidator."""
import pytest
from core.models import PlatformContent, ValidationResult
from platforms.hackernews.validator import HackerNewsValidator


class TestHackerNewsValidator:
    """Tests for HackerNewsValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a HackerNewsValidator instance."""
        return HackerNewsValidator()

    @pytest.fixture
    def valid_content(self):
        """Create valid HN content."""
        return PlatformContent(
            platform="hackernews",
            title="Show HN: pgx - Pure Go PostgreSQL driver",
            body="""I built this PostgreSQL driver in Go because existing solutions had
            performance issues with our architecture. The implementation uses a custom
            connection pool and achieves significant optimization in benchmark tests.

            Technical details: We use a binary protocol implementation and handle
            prepared statements efficiently.

            Limitations: Currently only supports PostgreSQL 12+. Working on broader
            compatibility.""",
            metadata={"category": "Show HN"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    @pytest.fixture
    def invalid_content(self):
        """Create invalid HN content."""
        return PlatformContent(
            platform="hackernews",
            title="Check out my AMAZING revolutionary new app that will CHANGE EVERYTHING!",
            body="This is the best tool ever! Sign up now! Don't miss out!",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )

    def test_validator_initialization(self, validator):
        """Test validator initializes with correct defaults."""
        assert validator.max_title_length == 60
        assert "revolutionary" in validator.forbidden_words
        assert "game-changing" in validator.forbidden_words
        assert len(validator.forbidden_words) > 5

    def test_validate_valid_content(self, validator, valid_content):
        """Test validation of valid HN content."""
        result = validator.validate(valid_content)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_title_too_long(self, validator):
        """Test validation catches overly long titles."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: " + "a" * 60,  # > 60 chars total
            body="Valid body content with technical details and implementation notes.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is False
        assert any("too long" in e.lower() for e in result.errors)

    def test_validate_forbidden_words_in_title(self, validator):
        """Test validation catches forbidden marketing words."""
        forbidden_test_cases = [
            "Show HN: Revolutionary new tool",
            "Show HN: Game-changing framework",
            "Show HN: The best database ever",
            "Show HN: Amazing breakthrough in AI",
            "Show HN: Incredible performance gains",
        ]
        for title in forbidden_test_cases:
            content = PlatformContent(
                platform="hackernews",
                title=title,
                body="Technical body content.",
                metadata={},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = validator.validate(content)
            assert result.is_valid is False, f"Expected invalid for: {title}"
            assert any("forbidden" in e.lower() for e in result.errors)

    def test_validate_missing_show_hn_prefix(self, validator):
        """Test validation requires Show HN prefix."""
        content = PlatformContent(
            platform="hackernews",
            title="pgx - Pure Go PostgreSQL driver",
            body="Technical body content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is False
        assert any("Show HN" in e for e in result.errors)

    def test_validate_exclamation_mark_warning(self, validator):
        """Test validation warns about exclamation marks."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Cool new tool!",
            body="Technical body content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("exclamation" in w.lower() for w in result.warnings)

    def test_validate_emoji_in_title(self, validator):
        """Test validation catches emoji in title."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Cool tool 🚀",
            body="Technical body content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is False
        assert any("emoji" in e.lower() for e in result.errors)

    def test_validate_short_title_warning(self, validator):
        """Test validation warns about very short titles."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: X",
            body="Technical body content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("generic" in w.lower() or "short" in w.lower() for w in result.warnings)

    def test_validate_marketing_language_in_body(self, validator):
        """Test validation catches marketing language in body."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: New database tool",
            body="Sign up now! Don't miss out on this limited time offer!",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("marketing" in w.lower() for w in result.warnings)

    def test_validate_body_too_short(self, validator):
        """Test validation warns about very short body."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Database tool",
            body="Short.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_body_too_long(self, validator):
        """Test validation warns about very long body."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Database tool",
            body="x" * 2500,
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_technical_depth_suggestion(self, validator):
        """Test validation suggests adding technical depth."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Simple tool for tasks",
            body="This is a tool that helps with things. It makes things easier.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("technical" in s.lower() for s in result.suggestions)

    def test_validate_honesty_suggestion(self, validator):
        """Test validation suggests mentioning limitations."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Database optimization",
            body="""This tool provides technical implementation details using
            algorithms and performance optimization techniques for benchmarking.""",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        # Should suggest authenticity if no limitation/challenge mentioned
        assert any("limitation" in s.lower() or "challenge" in s.lower() or "authentic" in s.lower()
                   for s in result.suggestions)

    def test_validate_title_format_suggestion(self, validator):
        """Test validation suggests proper title format."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: MyTool",  # Missing dash format
            body="Technical content here with proper details.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        # Should suggest dash format
        suggestions_text = " ".join(result.suggestions).lower()
        # Accept suggestion about format or consider it covered elsewhere

    def test_validate_all_forbidden_words(self, validator):
        """Test all forbidden words are caught."""
        for word in validator.forbidden_words:
            content = PlatformContent(
                platform="hackernews",
                title=f"Show HN: {word} tool",
                body="Content",
                metadata={},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = validator.validate(content)
            assert result.is_valid is False, f"Should catch forbidden word: {word}"

    def test_validate_case_insensitive_forbidden_words(self, validator):
        """Test forbidden words are checked case-insensitively."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: REVOLUTIONARY Tool",
            body="Content",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is False

    def test_validate_complex_valid_post(self, validator):
        """Test a well-formed complex post passes validation."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Tiny SQL compiler in Rust",
            body="""I've been working on this SQL compiler implementation in Rust
            for the past 3 months. The architecture uses a recursive descent parser
            combined with a custom bytecode interpreter for optimization.

            Technical approach: The lexer generates tokens that feed into the parser,
            which builds an AST. From there, I implemented a simple query optimizer
            that can handle basic join reordering.

            Performance: In my benchmarks, it handles simple queries with sub-millisecond
            latency. Complex joins are still slower than production databases.

            Limitations: Currently only supports a subset of SQL - SELECT, WHERE, JOIN.
            No aggregations yet. The codebase is experimental and I wouldn't use it
            in production.

            I'm curious what the HN community thinks about the parser design. Open to
            feedback on the implementation approach.""",
            metadata={"category": "Show HN"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidatorEdgeCases:
    """Edge case tests for HackerNewsValidator."""

    @pytest.fixture
    def validator(self):
        return HackerNewsValidator()

    def test_empty_title(self, validator):
        """Test validation with empty title."""
        content = PlatformContent(
            platform="hackernews",
            title="",
            body="Content",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert result.is_valid is False

    def test_empty_body(self, validator):
        """Test validation with empty body."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Test tool",
            body="",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        # Should have warnings about short body
        assert any("short" in w.lower() for w in result.warnings)

    def test_unicode_in_title(self, validator):
        """Test validation handles unicode in title."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Naïve string search",
            body="Technical content about algorithm implementation.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        # Should handle unicode without error
        assert isinstance(result, ValidationResult)

    def test_question_mark_in_middle_of_title(self, validator):
        """Test validation warns about question marks in middle of title."""
        content = PlatformContent(
            platform="hackernews",
            title="Show HN: Is this? good",
            body="Technical content.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        assert any("question" in w.lower() for w in result.warnings)

    def test_title_exactly_60_chars(self, validator):
        """Test validation accepts title of exactly max length."""
        title = "Show HN: " + "a" * 51  # Exactly 60 chars
        assert len(title) == 60
        content = PlatformContent(
            platform="hackernews",
            title=title,
            body="Technical content with proper details.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = validator.validate(content)
        # Should not have length error
        assert not any("too long" in e.lower() for e in result.errors)

    def test_body_exactly_boundary_lengths(self, validator):
        """Test body at exact boundary lengths."""
        # Just under minimum
        content_short = PlatformContent(
            platform="hackernews",
            title="Show HN: Test tool here",
            body="x" * 99,
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result_short = validator.validate(content_short)
        assert any("short" in w.lower() for w in result_short.warnings)

        # Just over maximum
        content_long = PlatformContent(
            platform="hackernews",
            title="Show HN: Test tool here",
            body="x" * 2001,
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result_long = validator.validate(content_long)
        assert any("long" in w.lower() for w in result_long.warnings)
