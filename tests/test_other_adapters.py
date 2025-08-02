"""Tests for remaining platform adapters - Peerlist, Indiehackers, Substack, Hashnode, Lobsters."""
import pytest
from pathlib import Path
from unittest.mock import patch
from core.models import ContentDNA, ValidationResult, PlatformContent
from platforms.peerlist.adapter import PeerlistAdapter
from platforms.indiehackers.adapter import IndiehackersAdapter
from platforms.substack.adapter import SubstackAdapter
from platforms.hashnode.adapter import HashnodeAdapter
from platforms.lobsters.adapter import LobstersAdapter


class TestPeerlistAdapter:
    """Tests for PeerlistAdapter."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "peerlist"
        config_dir.mkdir()
        return PeerlistAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="peerlist",
            title="",
            body="Post content here.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation warns about long title."""
        content = PlatformContent(
            platform="peerlist",
            title="x" * 150,
            body="Post content here.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_missing_body(self, adapter):
        """Test validation catches missing body."""
        content = PlatformContent(
            platform="peerlist",
            title="Good Title",
            body="",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_body_too_long(self, adapter):
        """Test validation warns about very long body."""
        content = PlatformContent(
            platform="peerlist",
            title="Good Title",
            body="x" * 2500,
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about very short body."""
        content = PlatformContent(
            platform="peerlist",
            title="Good Title",
            body="Short",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_professional_indicators(self, adapter):
        """Test validation suggests professional language."""
        content = PlatformContent(
            platform="peerlist",
            title="New Project",
            body="This is some content about a thing that exists.",
            metadata={},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("professional" in s.lower() or "achievement" in s.lower() for s in result.suggestions)

    def test_validate_valid_post(self, adapter):
        """Test validation passes for valid post."""
        content = PlatformContent(
            platform="peerlist",
            title="Shipped a CLI Tool for Code Analysis",
            body="""Built and shipped a new development tool this week.

            The tool uses AST parsing to analyze code patterns. Implemented
            in Python with focus on performance optimization.

            Learned a lot about the technical challenges of static analysis.
            Looking forward to feedback from the community.""",
            metadata={"post_type": "project_launch"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True


class TestIndiehackersAdapter:
    """Tests for IndiehackersAdapter."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "indiehackers"
        config_dir.mkdir()
        return IndiehackersAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="indiehackers",
            title="",
            body="Post content.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation warns about long title."""
        content = PlatformContent(
            platform="indiehackers",
            title="x" * 250,
            body="Post content with enough words.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        content = PlatformContent(
            platform="indiehackers",
            title="Good Title",
            body="Short.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_missing_numbers(self, adapter):
        """Test validation suggests adding numbers."""
        content = PlatformContent(
            platform="indiehackers",
            title="My Startup Journey",
            body="I built a product. It took some time. Users like it. Will keep building.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("number" in s.lower() for s in result.suggestions)

    def test_validate_missing_structure(self, adapter):
        """Test validation suggests adding structure."""
        content = PlatformContent(
            platform="indiehackers",
            title="Lessons from 1 Year of Building",
            body="Plain text 42 users no headers or formatting just paragraphs.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("header" in s.lower() or "structure" in s.lower() for s in result.suggestions)

    def test_validate_missing_takeaways(self, adapter):
        """Test validation suggests key takeaways."""
        content = PlatformContent(
            platform="indiehackers",
            title="Building 100 Users",
            body="## Story\n\nBuilt to 100 users in 3 months.",
            metadata={"key_takeaways": []},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("takeaway" in s.lower() for s in result.suggestions)

    def test_validate_missing_question(self, adapter):
        """Test validation suggests ending with question."""
        content = PlatformContent(
            platform="indiehackers",
            title="My Journey to 100 MRR",
            body="## Story\n\nBuilt to $100 MRR in 3 months. Here's what I learned.",
            metadata={"key_takeaways": ["Lesson 1", "Lesson 2"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("question" in s.lower() for s in result.suggestions)

    def test_validate_valid_post(self, adapter):
        """Test validation passes for valid post."""
        content = PlatformContent(
            platform="indiehackers",
            title="From $0 to $1000 MRR in 6 Months",
            body="""## TL;DR
            Built a SaaS from 0 to $1000 MRR.

            ## The Journey
            Started with 5 beta users in January.

            ## What Worked
            - Cold outreach on LinkedIn
            - Building in public

            ## Key Numbers
            - 50 paying customers
            - $1000 MRR

            ## Takeaways
            **Focus on one channel at a time.**

            What's been your experience with cold outreach?""",
            metadata={"key_takeaways": ["Focus on one channel", "Build in public"]},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True


class TestSubstackAdapter:
    """Tests for SubstackAdapter."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "substack"
        config_dir.mkdir()
        return SubstackAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="substack",
            title="",
            body="Newsletter content.",
            metadata={"preview_text": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation warns about long title."""
        content = PlatformContent(
            platform="substack",
            title="x" * 100,
            body="Newsletter content goes here.",
            metadata={"preview_text": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        content = PlatformContent(
            platform="substack",
            title="Newsletter Title",
            body="Short.",
            metadata={"preview_text": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_body_too_long(self, adapter):
        """Test validation warns about very long body."""
        content = PlatformContent(
            platform="substack",
            title="Newsletter Title",
            body="x" * 6000,
            metadata={"preview_text": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("long" in w.lower() for w in result.warnings)

    def test_validate_missing_preview_text(self, adapter):
        """Test validation suggests preview text."""
        content = PlatformContent(
            platform="substack",
            title="Newsletter Title",
            body="Newsletter content with I personal voice here.",
            metadata={"preview_text": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("preview" in s.lower() for s in result.suggestions)

    def test_validate_preview_too_long(self, adapter):
        """Test validation warns about long preview text."""
        content = PlatformContent(
            platform="substack",
            title="Title",
            body="Content here I wrote.",
            metadata={"preview_text": "x" * 200},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("preview" in w.lower() and "truncated" in w.lower() for w in result.warnings)

    def test_validate_missing_personal_voice(self, adapter):
        """Test validation suggests personal voice."""
        content = PlatformContent(
            platform="substack",
            title="Newsletter Title",
            body="The topic is important. Data shows trends. Results are significant.",
            metadata={"preview_text": "Preview"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("personal" in s.lower() for s in result.suggestions)

    def test_validate_weak_opening(self, adapter):
        """Test validation suggests stronger opening."""
        weak_openers = [
            "In this newsletter, I will discuss...",
            "Today we'll look at...",
            "This week, let me share...",
            "Welcome to the newsletter!"
        ]
        for opener in weak_openers:
            content = PlatformContent(
                platform="substack",
                title="Title",
                body=f"{opener} And more content follows here with I personal touch.",
                metadata={"preview_text": "Preview"},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = adapter.validate_content(content)
            assert any("opening" in s.lower() for s in result.suggestions), f"Should warn for: {opener}"


class TestHashnodeAdapter:
    """Tests for HashnodeAdapter."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "hashnode"
        config_dir.mkdir()
        return HashnodeAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="hashnode",
            title="",
            body="Article content.",
            metadata={"tags": [], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation warns about long title."""
        content = PlatformContent(
            platform="hashnode",
            title="x" * 150,
            body="Article content here.",
            metadata={"tags": ["python"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("seo" in w.lower() for w in result.warnings)

    def test_validate_body_too_short(self, adapter):
        """Test validation warns about short body."""
        content = PlatformContent(
            platform="hashnode",
            title="Good Title",
            body="Short.",
            metadata={"tags": ["python"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("short" in w.lower() for w in result.warnings)

    def test_validate_missing_code_blocks(self, adapter):
        """Test validation suggests code examples."""
        content = PlatformContent(
            platform="hashnode",
            title="Building with Python",
            body="This is a tutorial about Python development without code.",
            metadata={"tags": ["python"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("code" in s.lower() for s in result.suggestions)

    def test_validate_missing_headers(self, adapter):
        """Test validation suggests headers."""
        content = PlatformContent(
            platform="hashnode",
            title="Good Title",
            body="```python\ncode\n```\nNo headers here just paragraphs.",
            metadata={"tags": ["python"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("header" in s.lower() for s in result.suggestions)

    def test_validate_no_tags(self, adapter):
        """Test validation warns about missing tags."""
        content = PlatformContent(
            platform="hashnode",
            title="Good Title",
            body="## Section\n\n```python\ncode\n```",
            metadata={"tags": [], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("tag" in w.lower() for w in result.warnings)

    def test_validate_too_many_tags(self, adapter):
        """Test validation warns about too many tags."""
        content = PlatformContent(
            platform="hashnode",
            title="Good Title",
            body="## Section\n\n```python\ncode\n```",
            metadata={"tags": ["a", "b", "c", "d", "e", "f"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("tag" in w.lower() for w in result.warnings)

    def test_validate_missing_cover_image(self, adapter):
        """Test validation suggests cover image."""
        content = PlatformContent(
            platform="hashnode",
            title="Good Title",
            body="## Section\n\n```python\ncode\n```",
            metadata={"tags": ["python"], "cover_image_prompt": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("cover" in s.lower() or "image" in s.lower() for s in result.suggestions)


class TestLobstersAdapter:
    """Tests for LobstersAdapter."""

    @pytest.fixture
    def adapter(self, tmp_path):
        config_dir = tmp_path / "lobsters"
        config_dir.mkdir()
        return LobstersAdapter(config_dir)

    def test_validate_missing_title(self, adapter):
        """Test validation catches missing title."""
        content = PlatformContent(
            platform="lobsters",
            title="",
            body="",
            metadata={"tags": ["python"], "author_note": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False

    def test_validate_title_too_long(self, adapter):
        """Test validation catches overly long title."""
        content = PlatformContent(
            platform="lobsters",
            title="x" * 150,
            body="",
            metadata={"tags": ["python"], "author_note": "I wrote this"},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("long" in e.lower() for e in result.errors)

    def test_validate_promotional_language(self, adapter):
        """Test validation warns about promotional language."""
        promo_titles = [
            "Check out my new tool",
            "Introducing MyAwesomeTool",
            "Announcing the best solution",
            "Excited to share my project",
            "I built this awesome thing"
        ]
        for title in promo_titles:
            content = PlatformContent(
                platform="lobsters",
                title=title,
                body="",
                metadata={"tags": ["show"], "author_note": "I wrote this"},
                validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
            )
            result = adapter.validate_content(content)
            assert any("promotional" in w.lower() for w in result.warnings), f"Should warn for: {title}"

    def test_validate_missing_tags(self, adapter):
        """Test validation catches missing tags."""
        content = PlatformContent(
            platform="lobsters",
            title="Technical Discussion Topic",
            body="",
            metadata={"tags": [], "author_note": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("tag" in e.lower() for e in result.errors)

    def test_validate_too_many_tags(self, adapter):
        """Test validation warns about too many tags."""
        content = PlatformContent(
            platform="lobsters",
            title="Technical Discussion Topic",
            body="",
            metadata={"tags": ["a", "b", "c", "d", "e"], "author_note": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("tag" in w.lower() for w in result.warnings)

    def test_validate_show_without_disclosure(self, adapter):
        """Test validation requires disclosure for show submissions."""
        content = PlatformContent(
            platform="lobsters",
            title="Technical tool for analysis",
            body="",
            metadata={"tags": ["show", "python"], "author_note": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is False
        assert any("disclosure" in e.lower() for e in result.errors)

    def test_validate_generic_title_suggestion(self, adapter):
        """Test validation suggests more specific title."""
        content = PlatformContent(
            platform="lobsters",
            title="New tool",
            body="",
            metadata={"tags": ["python"], "author_note": ""},
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert any("specific" in s.lower() for s in result.suggestions)

    def test_validate_valid_submission(self, adapter):
        """Test validation passes for valid submission."""
        content = PlatformContent(
            platform="lobsters",
            title="pgx v5.0: Pure Go PostgreSQL driver with generics",
            body="",
            metadata={
                "tags": ["go", "databases", "show"],
                "author_note": "I'm the author of this library"
            },
            validation=ValidationResult(is_valid=False, warnings=[], errors=[], suggestions=[])
        )
        result = adapter.validate_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0
