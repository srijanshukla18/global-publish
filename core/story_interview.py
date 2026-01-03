"""
Story Interview Module

Interviews the user to extract:
1. Founder story (why they built this)
2. Project stage (experiment/mvp/beta/production)
3. User profile (professional identity for LinkedIn targeting)
"""

from dataclasses import dataclass
from typing import Optional
from .models import UserProfile


@dataclass
class StoryContext:
    """Context gathered from user interview"""
    project_stage: str  # experiment/mvp/beta/production
    founder_story: str  # Personal narrative
    why_built: str  # Motivation
    what_learned: str  # Lessons
    honest_limitations: str  # What doesn't work yet
    user_profile: Optional[UserProfile] = None


def run_interview(skip_profile: bool = False) -> StoryContext:
    """Interactive interview to gather story context"""
    print("\n" + "=" * 60)
    print("📝 STORY INTERVIEW")
    print("=" * 60)
    print("Let's gather context that will make your posts more engaging.")
    print("(Press Enter to skip any question)\n")

    # Project Stage
    print("1️⃣  PROJECT STAGE")
    print("   What stage is this project at?")
    print("   [1] Experiment - Just exploring, might not continue")
    print("   [2] MVP - Core works, looking for early feedback")
    print("   [3] Beta - Mostly complete, ironing out issues")
    print("   [4] Production - Battle-tested, ready for serious use")
    stage_input = input("   Enter 1-4 (default: 2 MVP): ").strip()
    stage_map = {"1": "experiment", "2": "mvp", "3": "beta", "4": "production", "": "mvp"}
    project_stage = stage_map.get(stage_input, "mvp")
    print(f"   → {project_stage.upper()}\n")

    # Why Built
    print("2️⃣  WHY DID YOU BUILD THIS?")
    print("   What frustrated you? What were you trying to solve for yourself?")
    print("   (One paragraph is fine)")
    why_built = input("   > ").strip()
    if not why_built:
        why_built = ""
    print()

    # What Learned
    print("3️⃣  WHAT DID YOU LEARN?")
    print("   Any surprising discoveries? Technical challenges? Things you'd do differently?")
    what_learned = input("   > ").strip()
    if not what_learned:
        what_learned = ""
    print()

    # Honest Limitations
    print("4️⃣  HONEST LIMITATIONS")
    print("   What doesn't work yet? What's hacky? What would you warn users about?")
    print("   (HN especially loves honesty here)")
    honest_limitations = input("   > ").strip()
    if not honest_limitations:
        honest_limitations = ""
    print()

    # Compose founder story
    founder_story = _compose_story(why_built, what_learned, honest_limitations)

    # User Profile (for LinkedIn targeting)
    user_profile = None
    if not skip_profile:
        print("5️⃣  YOUR PROFESSIONAL IDENTITY (for LinkedIn targeting)")
        print("   What's your day job? (e.g., 'SRE', 'Backend Engineer', 'Founder')")
        roles_input = input("   > ").strip()
        roles = [r.strip() for r in roles_input.split(",")] if roles_input else []

        print("\n   Who follows you on LinkedIn? (e.g., 'DevOps engineers and platform teams')")
        linkedin_audience = input("   > ").strip()

        print("\n   Which platforms do you already have reputation on?")
        print("   (e.g., 'hackernews, twitter, reddit' - comma separated)")
        platforms_input = input("   > ").strip()
        active_platforms = [p.strip() for p in platforms_input.split(",")] if platforms_input else []

        if roles or linkedin_audience or active_platforms:
            user_profile = UserProfile(
                professional_roles=roles,
                linkedin_audience=linkedin_audience or "general tech professionals",
                active_platforms=active_platforms
            )

    print("\n" + "=" * 60)
    print("✅ INTERVIEW COMPLETE")
    print("=" * 60 + "\n")

    return StoryContext(
        project_stage=project_stage,
        founder_story=founder_story,
        why_built=why_built,
        what_learned=what_learned,
        honest_limitations=honest_limitations,
        user_profile=user_profile
    )


def _compose_story(why_built: str, what_learned: str, limitations: str) -> str:
    """Compose a founder story from interview answers"""
    parts = []
    if why_built:
        parts.append(why_built)
    if what_learned:
        parts.append(f"Along the way, I learned: {what_learned}")
    if limitations:
        parts.append(f"Honest limitations: {limitations}")
    return " ".join(parts) if parts else ""


def load_saved_profile(profile_path: str = None) -> Optional[UserProfile]:
    """Load user profile from saved config"""
    import os
    import json
    from pathlib import Path

    if profile_path is None:
        profile_path = Path.home() / ".config" / "global-publish" / "profile.json"
    else:
        profile_path = Path(profile_path)

    if not profile_path.exists():
        return None

    try:
        with open(profile_path) as f:
            data = json.load(f)
        return UserProfile(
            professional_roles=data.get("professional_roles", []),
            linkedin_audience=data.get("linkedin_audience", ""),
            active_platforms=data.get("active_platforms", [])
        )
    except Exception:
        return None


def save_profile(profile: UserProfile, profile_path: str = None):
    """Save user profile for future runs"""
    import json
    from pathlib import Path

    if profile_path is None:
        profile_dir = Path.home() / ".config" / "global-publish"
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_path = profile_dir / "profile.json"
    else:
        profile_path = Path(profile_path)

    data = {
        "professional_roles": profile.professional_roles,
        "linkedin_audience": profile.linkedin_audience,
        "active_platforms": profile.active_platforms
    }

    with open(profile_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"   💾 Profile saved to {profile_path}")


def quick_stage_prompt() -> str:
    """Quick prompt for just project stage (non-interactive mode)"""
    print("\n📊 What stage is this project?")
    print("   [1] Experiment  [2] MVP  [3] Beta  [4] Production")
    stage_input = input("   Enter 1-4 (default: 2): ").strip()
    stage_map = {"1": "experiment", "2": "mvp", "3": "beta", "4": "production", "": "mvp"}
    return stage_map.get(stage_input, "mvp")
