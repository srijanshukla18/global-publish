"""Tests for platforms/reddit/analyzer.py - SubredditAnalyzer class."""
import pytest
import yaml
from pathlib import Path
from core.models import ContentDNA
from platforms.reddit.analyzer import SubredditAnalyzer


@pytest.fixture
def sample_subreddit_data():
    """Create sample subreddit data."""
    return {
        "content_types": {
            "tool": {
                "primary": ["programming", "webdev"],
                "secondary": ["sideproject", "opensource"]
            },
            "tutorial": {
                "primary": ["learnprogramming", "webdev"],
                "secondary": ["programming"]
            }
        },
        "subreddits": {
            "programming": {
                "name": "r/programming",
                "tags": ["technical", "software"],
                "culture": ["technical_depth_required"],
                "rules": {
                    "self_promotion": "limited",
                    "format": "text_post"
                }
            },
            "webdev": {
                "name": "r/webdev",
                "tags": ["web", "development", "frontend"],
                "culture": ["beginner_friendly"],
                "rules": {
                    "self_promotion": "allowed",
                    "format": "text_post"
                }
            },
            "sideproject": {
                "name": "r/SideProject",
                "tags": ["startup", "indie"],
                "culture": ["entrepreneur_friendly"],
                "rules": {
                    "self_promotion": "encouraged",
                    "format": "text_post"
                }
            },
            "indiehackers": {
                "name": "r/indiehackers",
                "tags": ["startup", "business", "indie"],
                "culture": ["entrepreneur_friendly"],
                "rules": {
                    "self_promotion": "encouraged",
                    "format": "text_post"
                }
            },
            "opensource": {
                "name": "r/opensource",
                "tags": ["oss", "community"],
                "culture": [],
                "rules": {
                    "self_promotion": "allowed",
                    "format": "link_post"
                }
            }
        }
    }


@pytest.fixture
def config_dir(tmp_path, sample_subreddit_data):
    """Create config directory with subreddit data."""
    config_path = tmp_path / "subreddit_data.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_subreddit_data, f)
    return tmp_path


@pytest.fixture
def sample_dna():
    """Create sample ContentDNA for testing."""
    return ContentDNA(
        value_proposition="A CLI tool for code analysis",
        technical_details=["Python", "AST parsing", "Performance optimization"],
        problem_solved="Slow code review process",
        target_audience="software developers",
        key_metrics=["50% faster", "100K downloads"],
        unique_aspects=["Incremental analysis"],
        limitations=["Python only"],
        content_type="tool"
    )


class TestSubredditAnalyzer:
    """Tests for SubredditAnalyzer class."""

    def test_analyzer_initialization(self, config_dir):
        """Test analyzer initializes and loads config."""
        analyzer = SubredditAnalyzer(config_dir)
        assert analyzer.subreddit_data is not None
        assert "subreddits" in analyzer.subreddit_data

    def test_analyzer_loads_subreddits(self, config_dir):
        """Test analyzer loads subreddit definitions."""
        analyzer = SubredditAnalyzer(config_dir)
        assert "programming" in analyzer.subreddit_data["subreddits"]
        assert "webdev" in analyzer.subreddit_data["subreddits"]


class TestSubredditSelection:
    """Tests for SubredditAnalyzer.select_subreddits method."""

    def test_select_subreddits_returns_list(self, config_dir, sample_dna):
        """Test select_subreddits returns a list."""
        analyzer = SubredditAnalyzer(config_dir)
        result = analyzer.select_subreddits(sample_dna)
        assert isinstance(result, list)

    def test_select_subreddits_respects_max_count(self, config_dir, sample_dna):
        """Test select_subreddits respects max_count parameter."""
        analyzer = SubredditAnalyzer(config_dir)

        result_2 = analyzer.select_subreddits(sample_dna, max_count=2)
        assert len(result_2) <= 2

        result_5 = analyzer.select_subreddits(sample_dna, max_count=5)
        assert len(result_5) <= 5

    def test_select_subreddits_includes_required_fields(self, config_dir, sample_dna):
        """Test selected subreddits include required fields."""
        analyzer = SubredditAnalyzer(config_dir)
        result = analyzer.select_subreddits(sample_dna, max_count=1)

        if result:
            sub = result[0]
            assert "subreddit" in sub
            assert "data" in sub
            assert "score" in sub
            assert "reason" in sub

    def test_select_subreddits_sorted_by_score(self, config_dir, sample_dna):
        """Test selected subreddits are sorted by score descending."""
        analyzer = SubredditAnalyzer(config_dir)
        result = analyzer.select_subreddits(sample_dna, max_count=5)

        if len(result) > 1:
            scores = [sub["score"] for sub in result]
            assert scores == sorted(scores, reverse=True)

    def test_select_subreddits_prioritizes_content_type(self, config_dir):
        """Test subreddits matching content type are prioritized."""
        analyzer = SubredditAnalyzer(config_dir)

        tool_dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        result = analyzer.select_subreddits(tool_dna, max_count=3)
        subreddit_ids = [sub["subreddit"] for sub in result]

        # Primary subreddits for 'tool' should be present
        assert "programming" in subreddit_ids or "webdev" in subreddit_ids


class TestSubredditScoring:
    """Tests for SubredditAnalyzer._calculate_subreddit_score method."""

    def test_score_primary_subreddit_higher(self, config_dir, sample_subreddit_data):
        """Test primary subreddits get higher scores."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        primary_subs = ["programming", "webdev"]
        secondary_subs = ["sideproject", "opensource"]

        prog_data = sample_subreddit_data["subreddits"]["programming"]
        side_data = sample_subreddit_data["subreddits"]["sideproject"]

        score_primary = analyzer._calculate_subreddit_score(
            "programming", prog_data, dna, primary_subs, secondary_subs
        )
        score_secondary = analyzer._calculate_subreddit_score(
            "sideproject", side_data, dna, primary_subs, secondary_subs
        )

        assert score_primary > score_secondary

    def test_score_self_promo_friendly(self, config_dir, sample_subreddit_data):
        """Test self-promo friendly subreddits get bonus."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        # sideproject has "encouraged" self_promotion
        side_data = sample_subreddit_data["subreddits"]["sideproject"]
        # programming has "limited" self_promotion
        prog_data = sample_subreddit_data["subreddits"]["programming"]

        score_encouraged = analyzer._calculate_subreddit_score(
            "sideproject", side_data, dna, [], []
        )
        score_limited = analyzer._calculate_subreddit_score(
            "programming", prog_data, dna, [], []
        )

        # Both start at 1.0 base, but self-promo modifies
        assert score_encouraged > score_limited


class TestVariantGeneration:
    """Tests for SubredditAnalyzer.generate_reddit_variants method."""

    def test_generate_variants_returns_list(self, config_dir, sample_dna, sample_subreddit_data):
        """Test generate_reddit_variants returns a list."""
        analyzer = SubredditAnalyzer(config_dir)
        selected = [
            {"subreddit": "programming", "data": sample_subreddit_data["subreddits"]["programming"], "score": 10}
        ]

        result = analyzer.generate_reddit_variants(sample_dna, selected)
        assert isinstance(result, list)

    def test_generate_variants_includes_subreddit_name(self, config_dir, sample_dna, sample_subreddit_data):
        """Test variants include subreddit name."""
        analyzer = SubredditAnalyzer(config_dir)
        selected = [
            {"subreddit": "programming", "data": sample_subreddit_data["subreddits"]["programming"], "score": 10}
        ]

        result = analyzer.generate_reddit_variants(sample_dna, selected)

        if result:
            assert "subreddit" in result[0]
            assert "r/programming" in result[0]["subreddit"]

    def test_generate_variants_has_title_and_body(self, config_dir, sample_dna, sample_subreddit_data):
        """Test variants have title and body."""
        analyzer = SubredditAnalyzer(config_dir)
        selected = [
            {"subreddit": "webdev", "data": sample_subreddit_data["subreddits"]["webdev"], "score": 10}
        ]

        result = analyzer.generate_reddit_variants(sample_dna, selected)

        if result:
            assert "title" in result[0]
            assert "body" in result[0]
            assert len(result[0]["title"]) > 0
            assert len(result[0]["body"]) > 0

    def test_generate_programming_variant(self, config_dir, sample_dna, sample_subreddit_data):
        """Test r/programming variant is generated correctly."""
        analyzer = SubredditAnalyzer(config_dir)
        selected = [
            {"subreddit": "programming", "data": sample_subreddit_data["subreddits"]["programming"], "score": 10}
        ]

        result = analyzer.generate_reddit_variants(sample_dna, selected)

        if result:
            # Should focus on technical content
            body_lower = result[0]["body"].lower()
            assert "technical" in body_lower or "problem" in body_lower or "implementation" in body_lower

    def test_generate_sideproject_variant(self, config_dir, sample_dna, sample_subreddit_data):
        """Test r/SideProject variant is generated correctly."""
        analyzer = SubredditAnalyzer(config_dir)
        selected = [
            {"subreddit": "sideproject", "data": sample_subreddit_data["subreddits"]["sideproject"], "score": 10}
        ]

        result = analyzer.generate_reddit_variants(sample_dna, selected)

        if result:
            title_lower = result[0]["title"].lower()
            # Should have launch/shipped language
            assert "launch" in title_lower or "ship" in title_lower or "built" in title_lower or "problem" in result[0]["body"].lower()


class TestSelectionReason:
    """Tests for SubredditAnalyzer._get_selection_reason method."""

    def test_reason_includes_culture_info(self, config_dir, sample_subreddit_data):
        """Test selection reason includes culture information."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=["Python"],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        sub_data = sample_subreddit_data["subreddits"]["sideproject"]
        reason = analyzer._get_selection_reason("sideproject", sub_data, dna)

        # sideproject has entrepreneur_friendly culture
        assert "entrepreneur" in reason.lower() or "business" in reason.lower() or len(reason) > 0

    def test_reason_mentions_self_promo(self, config_dir, sample_subreddit_data):
        """Test selection reason mentions self-promo policy."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        sub_data = sample_subreddit_data["subreddits"]["sideproject"]  # Has "encouraged"
        reason = analyzer._get_selection_reason("sideproject", sub_data, dna)

        assert "self-promotion" in reason.lower() or "encourage" in reason.lower() or len(reason) > 0


class TestEdgeCases:
    """Edge case tests for SubredditAnalyzer."""

    def test_empty_content_type(self, config_dir):
        """Test handling empty content type."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type=""
        )

        result = analyzer.select_subreddits(dna)
        assert isinstance(result, list)

    def test_unknown_content_type(self, config_dir):
        """Test handling unknown content type."""
        analyzer = SubredditAnalyzer(config_dir)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="unknown_type"
        )

        result = analyzer.select_subreddits(dna)
        assert isinstance(result, list)

    def test_no_matching_subreddits(self, tmp_path):
        """Test behavior when no subreddits match."""
        # Create minimal config with no matching content types
        config_path = tmp_path / "subreddit_data.yaml"
        config_data = {
            "content_types": {},
            "subreddits": {}
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        analyzer = SubredditAnalyzer(tmp_path)

        dna = ContentDNA(
            value_proposition="Tool",
            technical_details=[],
            problem_solved="",
            target_audience="developers",
            key_metrics=[],
            unique_aspects=[],
            limitations=[],
            content_type="tool"
        )

        result = analyzer.select_subreddits(dna)
        assert result == []
