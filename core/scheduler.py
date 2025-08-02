import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class OptimalTime:
    """Represents an optimal posting time for a platform"""
    platform: str
    hour_utc: int
    reason: str
    confidence: str  # "high", "medium", "low"


@dataclass
class ScheduleWarning:
    """Warning about suboptimal posting time"""
    platform: str
    message: str
    severity: str  # "warning", "error", "info"
    suggestion: str


class SmartScheduler:
    """Intelligent scheduling system with time zone awareness"""
    
    def __init__(self):
        self.optimal_times = self._load_optimal_times()
    
    def _load_optimal_times(self) -> Dict[str, List[OptimalTime]]:
        """Load optimal posting times for each platform"""
        return {
            "hackernews": [
                OptimalTime("hackernews", 16, "9 AM PT - Peak tech professional hours", "high"),
                OptimalTime("hackernews", 17, "10 AM PT - High engagement window", "high"),
                OptimalTime("hackernews", 18, "11 AM PT - Strong activity period", "medium"),
                OptimalTime("hackernews", 19, "12 PM PT - Lunch break browsing", "medium")
            ],
            "reddit": [
                OptimalTime("reddit", 13, "Early afternoon EST - Peak Reddit hours", "high"),
                OptimalTime("reddit", 14, "Mid-afternoon EST - High activity", "high"),
                OptimalTime("reddit", 20, "Evening EST - After work browsing", "medium"),
                OptimalTime("reddit", 21, "Prime time EST - Peak engagement", "high")
            ],
            "twitter": [
                OptimalTime("twitter", 13, "Early afternoon - Peak engagement", "high"),
                OptimalTime("twitter", 14, "Mid-afternoon - Strong activity", "high"),
                OptimalTime("twitter", 15, "Late afternoon - Good reach", "medium"),
                OptimalTime("twitter", 17, "Evening start - Secondary peak", "medium"),
                OptimalTime("twitter", 18, "Early evening - Active users", "medium")
            ],
            "medium": [
                OptimalTime("medium", 14, "Afternoon reading time", "medium"),
                OptimalTime("medium", 19, "Evening long-form reading", "high"),
                OptimalTime("medium", 20, "Prime reading hours", "high"),
                OptimalTime("medium", 15, "Mid-afternoon professionals", "medium")
            ],
            "devto": [
                OptimalTime("devto", 14, "Developer afternoon break", "high"),
                OptimalTime("devto", 15, "Mid-afternoon coding break", "high"),
                OptimalTime("devto", 18, "After work learning time", "medium"),
                OptimalTime("devto", 19, "Evening study time", "medium")
            ],
            "peerlist": [
                OptimalTime("peerlist", 15, "Professional networking hours", "medium"),
                OptimalTime("peerlist", 16, "End of workday sharing", "high"),
                OptimalTime("peerlist", 17, "After work networking", "medium"),
                OptimalTime("peerlist", 19, "Evening professional time", "medium")
            ]
        }
    
    def check_current_time(self, platforms: List[str]) -> List[ScheduleWarning]:
        """Check if current time is optimal for posting to specified platforms"""
        warnings = []
        current_utc = datetime.now(timezone.utc)
        current_hour = current_utc.hour
        current_day = current_utc.strftime("%A").lower()
        
        # Check if it's weekend
        is_weekend = current_day in ["saturday", "sunday"]
        
        for platform in platforms:
            platform_warnings = self._check_platform_timing(
                platform, current_hour, current_day, is_weekend
            )
            warnings.extend(platform_warnings)
        
        return warnings
    
    def _check_platform_timing(self, platform: str, hour: int, day: str, is_weekend: bool) -> List[ScheduleWarning]:
        """Check timing for a specific platform"""
        warnings = []
        
        if platform not in self.optimal_times:
            warnings.append(ScheduleWarning(
                platform=platform,
                message=f"No timing data available for {platform}",
                severity="info",
                suggestion="Posting at any time should be fine"
            ))
            return warnings
        
        optimal_hours = [opt.hour_utc for opt in self.optimal_times[platform]]
        current_optimal = [opt for opt in self.optimal_times[platform] if opt.hour_utc == hour]
        
        # Check if current time is optimal
        if hour in optimal_hours:
            if current_optimal:
                opt = current_optimal[0]
                if opt.confidence == "high":
                    warnings.append(ScheduleWarning(
                        platform=platform,
                        message=f"✅ Optimal time for {platform}! {opt.reason}",
                        severity="info",
                        suggestion="Great time to post"
                    ))
                else:
                    warnings.append(ScheduleWarning(
                        platform=platform,
                        message=f"✅ Good time for {platform}: {opt.reason}",
                        severity="info",
                        suggestion="Decent time to post"
                    ))
        else:
            # Not optimal - provide guidance
            next_optimal = self._find_next_optimal_time(platform, hour)
            
            if is_weekend and platform == "hackernews":
                warnings.append(ScheduleWarning(
                    platform=platform,
                    message="⚠️  Weekend posting to HN typically gets lower engagement",
                    severity="warning",
                    suggestion="Consider waiting until Monday-Thursday for better reach"
                ))
            
            if hour < 6 or hour > 23:  # Very early morning or late night UTC
                warnings.append(ScheduleWarning(
                    platform=platform,
                    message=f"⚠️  Suboptimal time for {platform} (current: {hour:02d}:00 UTC)",
                    severity="warning",
                    suggestion=f"Next optimal time: {next_optimal}"
                ))
            else:
                warnings.append(ScheduleWarning(
                    platform=platform,
                    message=f"ℹ️  Non-peak time for {platform} (current: {hour:02d}:00 UTC)",
                    severity="info",
                    suggestion=f"For better engagement, try: {next_optimal}"
                ))
        
        return warnings
    
    def _find_next_optimal_time(self, platform: str, current_hour: int) -> str:
        """Find the next optimal posting time for a platform"""
        if platform not in self.optimal_times:
            return "No specific recommendations available"
        
        optimal_times = self.optimal_times[platform]
        
        # Find the next optimal time
        next_times = [opt for opt in optimal_times if opt.hour_utc > current_hour]
        
        if next_times:
            next_optimal = min(next_times, key=lambda x: x.hour_utc)
            return f"{next_optimal.hour_utc:02d}:00 UTC ({next_optimal.reason})"
        else:
            # Next day
            earliest = min(optimal_times, key=lambda x: x.hour_utc)
            return f"Tomorrow at {earliest.hour_utc:02d}:00 UTC ({earliest.reason})"
    
    def get_optimal_schedule(self, platforms: List[str]) -> Dict[str, str]:
        """Get optimal posting schedule for all platforms"""
        schedule = {}
        
        for platform in platforms:
            if platform in self.optimal_times:
                best_time = max(
                    self.optimal_times[platform], 
                    key=lambda x: {"high": 3, "medium": 2, "low": 1}[x.confidence]
                )
                schedule[platform] = f"{best_time.hour_utc:02d}:00 UTC - {best_time.reason}"
            else:
                schedule[platform] = "No specific timing recommendations"
        
        return schedule
    
    def should_warn_user(self, warnings: List[ScheduleWarning]) -> bool:
        """Determine if user should be warned about timing"""
        # Warn if any platform has warning or error severity
        return any(w.severity in ["warning", "error"] for w in warnings)
    
    def format_warnings(self, warnings: List[ScheduleWarning]) -> str:
        """Format warnings for display to user"""
        if not warnings:
            return "✅ All platforms have optimal timing"
        
        formatted = []
        formatted.append("⏰ POSTING TIME ANALYSIS")
        formatted.append("=" * 50)
        
        for warning in warnings:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}[warning.severity]
            formatted.append(f"{icon} {warning.platform.title()}: {warning.message}")
            formatted.append(f"   💡 {warning.suggestion}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def get_user_confirmation(self, warnings: List[ScheduleWarning]) -> bool:
        """Get user confirmation to proceed with posting"""
        if not self.should_warn_user(warnings):
            return True
        
        print(self.format_warnings(warnings))
        print("=" * 50)
        
        while True:
            response = input("⚠️  Some platforms may have suboptimal timing. Continue anyway? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def get_local_time_info(self) -> str:
        """Get current local time information"""
        local_time = datetime.now()
        utc_time = datetime.now(timezone.utc)
        
        return f"""
🕐 CURRENT TIME INFO
Local Time: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
UTC Time: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}
Day: {local_time.strftime('%A')}
"""