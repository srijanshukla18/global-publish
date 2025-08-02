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
    content_type: str  # "tool", "tutorial", "analysis", etc.


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