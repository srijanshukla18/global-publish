from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class PostStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    POSTED = "posted"
    FAILED = "failed"


@dataclass
class ContentDNA:
    """Core content analysis extracted from original post"""
    value_proposition: str
    technical_details: List[str]
    problem_solved: str
    target_audience: str
    key_metrics: List[str]
    unique_aspects: List[str]
    limitations: List[str]
    content_type: str  # "tool_launch", "tutorial", "opinion", "case_study", "announcement"
    # Distribution-relevant fields
    controversy_potential: str = "low"  # low/medium/high - sparks debate?
    novelty_score: str = "incremental"  # incremental/notable/breakthrough
    show_dont_tell: str = "none"  # none/some/strong - demos, screenshots, metrics?
    best_fit_communities: List[str] = None  # specific subreddits/communities that would care
    # Visual opportunities
    visual_opportunities: List[str] = None  # "ASCII architecture diagram", "terminal output demo", etc.
    # Platform constraints
    platform_constraints: List[str] = None  # "macOS only", "Linux 6.12+", "Apple Silicon required"
    # User-provided context (filled by interview)
    project_stage: str = "unknown"  # experiment/mvp/beta/production
    founder_story: str = ""  # Why you built this, personal narrative

    def __post_init__(self):
        if self.best_fit_communities is None:
            self.best_fit_communities = []
        if self.visual_opportunities is None:
            self.visual_opportunities = []
        if self.platform_constraints is None:
            self.platform_constraints = []


@dataclass
class UserProfile:
    """User's professional identity for platform targeting"""
    professional_roles: List[str]  # ["SRE", "Backend Engineer", "Founder"]
    linkedin_audience: str  # "DevOps engineers and SREs" - who follows you
    active_platforms: List[str]  # platforms where user has reputation

    def __post_init__(self):
        if self.professional_roles is None:
            self.professional_roles = []
        if self.active_platforms is None:
            self.active_platforms = []


@dataclass
class ValidationResult:
    """Result of content validation"""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]


@dataclass
class PlatformContent:
    """Generated content for a specific platform"""
    platform: str
    title: str
    body: str
    metadata: Dict[str, Any]  # tags, keywords, etc.
    validation: ValidationResult
    scheduled_time: Optional[str] = None


@dataclass
class PublishResult:
    """Result of posting to a platform"""
    platform: str
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None