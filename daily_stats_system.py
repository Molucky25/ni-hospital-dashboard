"""
Daily Statistics System for NI A&E Wait Times
Collects and formats comprehensive daily statistics for scheduled updates
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class DailyStatsTracker:
    """Tracks daily statistics for A&E wait times"""
    
    def __init__(self, stats_file: str = "daily_stats.json"):
        self.stats_file = Path(stats_file)
        self.daily_data = self._load_daily_data()
        self.last_update_times = self._load_update_times()
    
    def _load_daily_data(self) -> dict:
        """Load daily statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    # Validate and migrate old data structure
                    if "readings" not in data:
                        data["readings"] = []
                    if "peak_hour" not in data:
                        data["peak_hour"] = None
                    if "peak_avg" not in data:
                        data["peak_avg"] = 0
                    if "longest_wait" not in data:
                        data["longest_wait"] = {"hospital": None, "wait": 0, "time": None}
                    if "hours_critical" not in data:
                        data["hours_critical"] = 0
                    if "yesterday_avg" not in data:
                        data["yesterday_avg"] = None
                    return data
            except (json.JSONDecodeError, IOError):
                return self._empty_daily_data()
        return self._empty_daily_data()
    
    def _empty_daily_data(self) -> dict:
        """Create empty daily data structure"""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "date": today,
            "readings": [],  # List of all readings today
            "peak_hour": None,
            "peak_avg": 0,
            "longest_wait": {"hospital": None, "wait": 0, "time": None},
            "hours_critical": 0,  # Hours with any hospital ≥240m
            "yesterday_avg": None  # For comparison
        }
    
    def _load_update_times(self) -> dict:
        """Load last update times"""
        update_file = Path("daily_update_times.json")
        if update_file.exists():
            try:
                with open(update_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_update_times(self):
        """Save last update times"""
        update_file = Path("daily_update_times.json")
        with open(update_file, 'w') as f:
            json.dump(self.last_update_times, f, indent=2)
    
    def _save_daily_data(self):
        """Save daily statistics to file"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.daily_data, f, indent=2)
    
    def _check_new_day(self):
        """Check if it's a new day and reset if needed"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_data["date"] != today:
            # Save yesterday's average for comparison
            if self.daily_data["readings"]:
                yesterday_avg = sum(r["avg_wait"] for r in self.daily_data["readings"]) / len(self.daily_data["readings"])
            else:
                yesterday_avg = None
            
            # Reset for new day
            self.daily_data = self._empty_daily_data()
            self.daily_data["yesterday_avg"] = yesterday_avg
            self._save_daily_data()
    
    def record_reading(self, hospitals_dict: Dict[str, int], source_updated: str = None):
        """
        Record a reading for daily statistics
        
        Args:
            hospitals_dict: Dict mapping hospital names to wait times
            source_updated: When NI Direct last updated (from their webpage)
        """
        self._check_new_day()
        
        now = datetime.now()
        fetched_at = now.isoformat()
        hour = now.hour
        
        # Calculate average wait
        avg_wait = sum(hospitals_dict.values()) / len(hospitals_dict) if hospitals_dict else 0
        
        # Find longest wait
        longest_hospital = max(hospitals_dict.items(), key=lambda x: x[1]) if hospitals_dict else (None, 0)
        
        # Check if any hospital is critical (≥240m)
        has_critical = any(wait >= 240 for wait in hospitals_dict.values())
        
        # Record reading
        reading = {
            "fetched_at": fetched_at,
            "source_updated": source_updated,
            "hour": hour,
            "avg_wait": int(avg_wait),
            "hospitals": hospitals_dict.copy(),
            "longest": {"hospital": longest_hospital[0], "wait": longest_hospital[1]},
            "has_critical": has_critical
        }
        
        self.daily_data["readings"].append(reading)
        
        # Update longest wait if this is a new record
        if longest_hospital[1] > self.daily_data["longest_wait"]["wait"]:
            self.daily_data["longest_wait"] = {
                "hospital": longest_hospital[0],
                "wait": longest_hospital[1],
                "time": now.strftime("%H:%M")
            }
        
        # Update peak hour if this is higher average
        if avg_wait > self.daily_data["peak_avg"]:
            self.daily_data["peak_avg"] = int(avg_wait)
            self.daily_data["peak_hour"] = hour
        
        # Count critical hours (deduplicate by hour)
        critical_hours = set()
        for r in self.daily_data["readings"]:
            if r["has_critical"]:
                critical_hours.add(r["hour"])
        self.daily_data["hours_critical"] = len(critical_hours)
        
        self._save_daily_data()
    
    def should_send_update(self) -> bool:
        """
        Check if it's time to send a daily update
        
        Update times: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
        """
        now = datetime.now()
        current_hour = now.hour
        today = now.strftime("%Y-%m-%d")
        
        # Update hours (24-hour format)
        update_hours = [0, 3, 6, 9, 12, 15, 18, 21]
        
        if current_hour not in update_hours:
            return False
        
        # Check if we've already sent for this hour today
        update_key = f"{today}_{current_hour:02d}"
        if update_key in self.last_update_times:
            return False
        
        # Mark this hour as sent
        self.last_update_times[update_key] = now.isoformat()
        self._save_update_times()
        
        return True
    
    def calculate_daily_stats(self, current_hospitals: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate comprehensive daily statistics
        
        Args:
            current_hospitals: Current hospital wait times
            
        Returns:
            Dict containing all daily statistics
        """
        self._check_new_day()
        
        if not self.daily_data["readings"]:
            # No data yet today
            return None
        
        # Current average
        current_avg = sum(current_hospitals.values()) / len(current_hospitals) if current_hospitals else 0
        
        # Yesterday's average (for comparison)
        yesterday_avg = self.daily_data.get("yesterday_avg")
        avg_change = None
        if yesterday_avg:
            avg_change = int(current_avg - yesterday_avg)
        
        # Regional pressure (% of hospitals over 2h)
        hospitals_over_2h = sum(1 for wait in current_hospitals.values() if wait >= 120)
        pressure_pct = int((hospitals_over_2h / len(current_hospitals)) * 100) if current_hospitals else 0
        
        # Pressure level
        if pressure_pct >= 75:
            pressure_level = "critical strain"
        elif pressure_pct >= 50:
            pressure_level = "high strain"
        elif pressure_pct >= 30:
            pressure_level = "moderate strain"
        else:
            pressure_level = "low strain"
        
        # Top 3 longest current waits
        top_3 = sorted(current_hospitals.items(), key=lambda x: -x[1])[:3]
        
        # Fastest improvement (compare current with yesterday's readings)
        fastest_improvement = self._calculate_fastest_improvement(current_hospitals)
        
        # Peak hour info
        peak_hour = self.daily_data.get("peak_hour")
        peak_hour_str = None
        if peak_hour is not None:
            # Convert 24h to 12h format
            if peak_hour == 0:
                peak_hour_str = "12 AM"
            elif peak_hour < 12:
                peak_hour_str = f"{peak_hour} AM"
            elif peak_hour == 12:
                peak_hour_str = "12 PM"
            else:
                peak_hour_str = f"{peak_hour - 12} PM"
        
        return {
            "current_avg": int(current_avg),
            "avg_change": avg_change,
            "pressure_pct": pressure_pct,
            "pressure_level": pressure_level,
            "longest_wait": self.daily_data["longest_wait"],
            "top_3": top_3,
            "fastest_improvement": fastest_improvement,
            "peak_hour": peak_hour_str,
            "peak_avg": self.daily_data["peak_avg"],
            "hours_critical": self.daily_data["hours_critical"]
        }
    
    def _calculate_fastest_improvement(self, current_hospitals: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Calculate fastest improvement since yesterday"""
        if not self.daily_data["readings"]:
            return None
        
        # Get yesterday's data (if available)
        # For now, compare with first reading of today as a proxy
        # TODO: Could enhance this to compare with actual yesterday's data
        if len(self.daily_data["readings"]) < 2:
            return None
        
        first_reading = self.daily_data["readings"][0]["hospitals"]
        
        improvements = []
        for hospital, current_wait in current_hospitals.items():
            if hospital in first_reading:
                change = current_wait - first_reading[hospital]
                if change < 0:  # Improvement (decrease)
                    improvements.append({
                        "hospital": hospital,
                        "change": abs(change)
                    })
        
        if improvements:
            fastest = max(improvements, key=lambda x: x["change"])
            return fastest
        
        return None
    
    def format_daily_update(self, stats: Dict[str, Any]) -> str:
        """
        Format daily statistics into a Telegram message
        
        Args:
            stats: Dictionary of daily statistics
            
        Returns:
            Formatted message string
        """
        if not stats:
            return "Still Waiting NI — Daily Update\n\nInsufficient data for daily summary."
        
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        
        # Build message
        lines = []
        
        # Header
        lines.append(f"📊 <b>Still Waiting NI — {time_str} Update</b>\n")
        
        # Average wait with change
        avg_line = f"<b>NI A&E Average Wait:</b> {stats['current_avg']}m"
        if stats['avg_change'] is not None:
            if stats['avg_change'] < 0:
                avg_line += f" (↓ {abs(stats['avg_change'])}m vs yesterday)"
            elif stats['avg_change'] > 0:
                avg_line += f" (↑ {stats['avg_change']}m vs yesterday)"
            else:
                avg_line += " (→ unchanged vs yesterday)"
        lines.append(avg_line)
        
        # Regional pressure
        lines.append(f"🔹 <b>Pressure:</b> {stats['pressure_pct']}% of hospitals currently over 2 hours — {stats['pressure_level']}.")
        
        # Longest recorded wait
        if stats['longest_wait']['hospital']:
            lines.append(f"🔹 <b>Longest recorded wait:</b> {stats['longest_wait']['hospital']} — {stats['longest_wait']['wait']}m at {stats['longest_wait']['time']}")
        
        # Fastest improvement
        if stats['fastest_improvement']:
            lines.append(f"🔹 <b>Fastest improvement:</b> {stats['fastest_improvement']['hospital']} ↓ {stats['fastest_improvement']['change']}m since earlier")
        
        # Peak congestion
        if stats['peak_hour']:
            lines.append(f"🔹 <b>Peak congestion:</b> {stats['peak_hour']}, regional avg {stats['peak_avg']}m")
        
        # Red zone duration
        lines.append(f"🔹 <b>Red zone duration:</b> {stats['hours_critical']} hours ≥ 240m today")
        
        # Top 3 longest waits
        lines.append("\n<b>Top 3 Longest Waits:</b>")
        medals = ["🥇", "🥈", "🥉"]
        for i, (hospital, wait) in enumerate(stats['top_3']):
            lines.append(f"{medals[i]} {hospital} — {wait}m")
        
        return "\n".join(lines)


# Global instance
daily_stats_tracker = DailyStatsTracker()
