from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class TimingSuggestion:
    """Timing recommendation for a platform"""
    platform: str
    best_days: List[str]
    best_hours_utc: List[int]
    avoid: List[str]
    notes: str
    current_is_good: bool  # Is right now a good time?
    next_good_window: Optional[str]  # Human readable


class TimingAdvisor:
    """Knows when to post on each platform"""

    TIMING_DATA = {
        "hackernews": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [14, 15, 16],  # 9-11am EST
            "avoid": ["Saturday", "Sunday", "Monday morning"],
            "notes": "HN peaks mid-week, mid-morning US East Coast. Avoid weekends - lower traffic and different crowd. Major tech news days will bury your post."
        },
        "twitter": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [13, 14, 17, 18],  # Morning + afternoon US
            "avoid": ["Late night US time", "Major news events"],
            "notes": "Depends heavily on YOUR followers' timezones. Check your Twitter analytics. Threads do well mid-morning. Avoid posting during breaking news."
        },
        "reddit": {
            "best_days": ["Monday", "Tuesday", "Wednesday"],
            "best_hours_utc": [13, 14, 15],  # US morning
            "avoid": ["Friday afternoon", "Weekends for professional subs"],
            "notes": "Varies wildly by subreddit. r/programming peaks weekday mornings. Hobby subs do better on weekends. Check subreddit traffic stats."
        },
        "linkedin": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [12, 13, 14],  # Business hours
            "avoid": ["Weekends", "Friday afternoon", "Monday morning"],
            "notes": "LinkedIn is a workday platform. Tuesday-Thursday mid-morning performs best. Algorithm favors posts that get early engagement from your network."
        },
        "producthunt": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [8],  # 00:01 PST = 08:00 UTC
            "avoid": ["Monday", "Friday", "Weekends"],
            "notes": "PH resets at 00:01 PST. Launch at exactly that time for maximum runway. Tuesday-Thursday are the competitive days with most traffic. Avoid Mondays (people catching up) and Fridays (people checked out)."
        },
        "devto": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [14, 15, 16],
            "avoid": ["Weekends"],
            "notes": "Dev.to is forgiving on timing. Good content surfaces regardless. But weekday mornings US time tend to get more initial engagement."
        },
        "medium": {
            "best_days": ["Tuesday", "Wednesday", "Sunday"],
            "best_hours_utc": [13, 14, 15],
            "avoid": ["Friday", "Saturday"],
            "notes": "Medium readers browse on weekday mornings and Sunday evenings. Sunday can be good for thoughtful long-form. Friday posts often get lost."
        },
        "hashnode": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [6, 7, 14, 15],  # Includes India morning
            "avoid": ["Weekends"],
            "notes": "Hashnode has strong Indian developer community. Consider posting during India morning hours (UTC+5:30) for that audience."
        },
        "indiehackers": {
            "best_days": ["Monday", "Tuesday", "Wednesday"],
            "best_hours_utc": [14, 15, 16],
            "avoid": ["Weekends"],
            "notes": "IH community is global but US-heavy. Monday posts about weekend work do well. Milestone posts perform any day."
        },
        "lobsters": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [14, 15, 16],
            "avoid": ["Weekends"],
            "notes": "Similar to HN but smaller, more technical. Less timing-dependent since lower volume means your post stays visible longer."
        },
        "substack": {
            "best_days": ["Tuesday", "Wednesday", "Thursday", "Sunday"],
            "best_hours_utc": [14, 15],  # Morning US
            "avoid": ["Saturday"],
            "notes": "Email open rates peak Tuesday-Thursday mornings. Sunday evening can work for thoughtful pieces. Your audience's timezone matters most."
        },
        "peerlist": {
            "best_days": ["Monday", "Tuesday", "Wednesday"],
            "best_hours_utc": [4, 5, 6, 14, 15],  # India + US
            "avoid": ["Weekends"],
            "notes": "Strong Indian tech professional community. Consider India timezone (UTC+5:30 morning = 4-6 UTC)."
        }
    }

    def get_suggestion(self, platform: str) -> TimingSuggestion:
        """Get timing suggestion for a platform"""
        data = self.TIMING_DATA.get(platform, {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_hours_utc": [14, 15],
            "avoid": ["Weekends"],
            "notes": "No specific data. Weekday mornings US time are generally safe."
        })

        now = datetime.now(timezone.utc)
        current_day = now.strftime("%A")
        current_hour = now.hour

        is_good_day = current_day in data["best_days"]
        is_good_hour = current_hour in data["best_hours_utc"]
        current_is_good = is_good_day and is_good_hour

        # Calculate next good window
        next_window = self._calculate_next_window(data, now)

        return TimingSuggestion(
            platform=platform,
            best_days=data["best_days"],
            best_hours_utc=data["best_hours_utc"],
            avoid=data["avoid"],
            notes=data["notes"],
            current_is_good=current_is_good,
            next_good_window=next_window
        )

    def _calculate_next_window(self, data: dict, now: datetime) -> str:
        """Calculate human-readable next good posting window"""
        current_day = now.strftime("%A")
        current_hour = now.hour

        best_days = data["best_days"]
        best_hours = data["best_hours_utc"]

        if not best_days or not best_hours:
            return "Any time"

        # Check if today is good and there's a good hour left
        if current_day in best_days:
            future_hours = [h for h in best_hours if h > current_hour]
            if future_hours:
                return f"Today at {future_hours[0]}:00 UTC"

        # Find next good day
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_idx = days_order.index(current_day)

        for i in range(1, 8):
            next_idx = (current_idx + i) % 7
            next_day = days_order[next_idx]
            if next_day in best_days:
                return f"{next_day} at {best_hours[0]}:00 UTC"

        return "Check timing data"

    def get_all_suggestions(self) -> dict:
        """Get timing suggestions for all platforms"""
        return {platform: self.get_suggestion(platform) for platform in self.TIMING_DATA}

    def format_for_display(self, suggestion: TimingSuggestion) -> str:
        """Format suggestion for CLI display"""
        status = "✅ Good time to post!" if suggestion.current_is_good else f"⏰ Next window: {suggestion.next_good_window}"
        return f"""
{suggestion.platform.upper()} Timing:
  Best days: {', '.join(suggestion.best_days)}
  Best hours (UTC): {', '.join(f'{h}:00' for h in suggestion.best_hours_utc)}
  Avoid: {', '.join(suggestion.avoid)}
  {status}
  💡 {suggestion.notes}
"""
