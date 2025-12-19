"""
Hospital Wait Time Trend Cache System
Tracks wait time changes between polls for trend analysis
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class HospitalTrendCache:
    """Manages caching and comparison of hospital wait times"""
    
    def __init__(self, cache_file: str = "hospital_wait_cache.json", history_file: str = "hospital_wait_history.json"):
        self.cache_file = Path(cache_file)
        self.history_file = Path(history_file)
        self.last_trends = {}  # Initialize before loading (will be overwritten if cache exists)
        self.cache_data = self._load_cache()
        self.history_data = self._load_history()
    
    def _load_cache(self) -> dict:
        """Load cached data from file"""
        print(f"[TREND CACHE] Loading cache from {self.cache_file}")
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    raw_content = f.read()
                    print(f"[TREND CACHE] Raw file size: {len(raw_content)} bytes")
                    print(f"[TREND CACHE] Raw file content (first 500 chars): {raw_content[:500]}")
                    cache = json.loads(raw_content)
                    print(f"[TREND CACHE] Cache file loaded successfully")
                    print(f"[TREND CACHE] Cache keys: {list(cache.keys())}")
                    
                    # Migrate old cache structure (timestamp -> fetched_at)
                    if "timestamp" in cache and "fetched_at" not in cache:
                        print(f"[TREND CACHE] Migrating old cache structure")
                        cache["fetched_at"] = cache.pop("timestamp")
                        cache["source_updated"] = None  # Not available in old cache
                    
                    # Load persisted last_trends if it exists
                    last_trends_raw = cache.get("last_trends", {})
                    print(f"[TREND CACHE] Raw last_trends type: {type(last_trends_raw)}")
                    print(f"[TREND CACHE] Raw last_trends value: {last_trends_raw}")
                    self.last_trends = last_trends_raw
                    print(f"[TREND CACHE] Loaded {len(self.last_trends)} persisted trends from cache")
                    if self.last_trends:
                        print(f"[TREND CACHE] Sample trends: {list(self.last_trends.items())[:3]}")
                    else:
                        print(f"[TREND CACHE] WARNING: last_trends is empty or missing from cache!")
                    return cache
            except (json.JSONDecodeError, IOError) as e:
                print(f"[TREND CACHE] ERROR loading cache: {e}")
                return self._empty_cache()
        else:
            print(f"[TREND CACHE] Cache file does not exist, creating empty cache")
        return self._empty_cache()
    
    def _empty_cache(self) -> dict:
        """Create empty cache structure"""
        return {
            "fetched_at": None,  # When our script fetched the data
            "source_updated": None,  # When NI Direct last updated (from their webpage)
            "data": {},
            "last_trends": {}  # Persist trend directions
        }
    
    def _load_history(self) -> dict:
        """Load historical data from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._empty_history()
        return self._empty_history()
    
    def _empty_history(self) -> dict:
        """Create empty history structure"""
        return {
            "hospitals": {}  # {hospital_name: [wait1, wait2, wait3, ...]}
        }
    
    def _save_history(self):
        """Save history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history_data, f, indent=2)
    
    def _save_cache(self):
        """Save cache to file with persisted last_trends"""
        # Include last_trends in the cache data
        cache_with_trends = {
            "fetched_at": self.cache_data.get("fetched_at"),
            "source_updated": self.cache_data.get("source_updated"),
            "data": self.cache_data.get("data", {}),
            "last_trends": self.last_trends  # Persist to disk
        }
        print(f"[TREND CACHE] Saving cache with {len(self.last_trends)} trends")
        if self.last_trends:
            print(f"[TREND CACHE] Sample trends being saved: {list(self.last_trends.items())[:3]}")
        with open(self.cache_file, 'w') as f:
            json.dump(cache_with_trends, f, indent=2)
    
    def update_cache(self, current_data: Dict[str, int], source_updated: str = None):
        """
        Update cache with current wait times
        
        Args:
            current_data: Dict mapping hospital names to wait times (minutes)
                         e.g., {"Altnagelvin Area ED": 317, ...}
            source_updated: When NI Direct last updated (from their webpage)
        """
        self.cache_data = {
            "fetched_at": datetime.now().isoformat(),
            "source_updated": source_updated,
            "data": current_data,
            "last_trends": self.last_trends  # Include in cache_data
        }
        self._save_cache()
        
        # Also update history
        self.update_history(current_data)
    
    def update_history(self, current_data: Dict[str, int], max_history: int = 6):
        """
        Update rolling history of wait times (keeps last N readings)
        
        Args:
            current_data: Dict mapping hospital names to current wait times
            max_history: Maximum number of historical readings to keep (default 6)
        """
        for hospital, wait_time in current_data.items():
            if hospital not in self.history_data["hospitals"]:
                self.history_data["hospitals"][hospital] = []
            
            # Append current wait time
            self.history_data["hospitals"][hospital].append(wait_time)
            
            # Keep only last N readings
            if len(self.history_data["hospitals"][hospital]) > max_history:
                self.history_data["hospitals"][hospital] = \
                    self.history_data["hospitals"][hospital][-max_history:]
        
        self._save_history()
    
    def calculate_trends(self, current_data: Dict[str, int]) -> dict:
        """
        Calculate trend statistics by comparing current vs 30-minute-ago data
        
        Uses history data (oldest reading in 6-reading window) for more meaningful trends.
        Falls back to cache data if insufficient history.
        
        Args:
            current_data: Dict mapping hospital names to current wait times
        
        Returns:
            Dict containing trend statistics:
            {
                'improving_count': int,
                'worsening_count': int,
                'unchanged_count': int,
                'fastest_improvement': {'hospital': str, 'diff': int} or None,
                'worst_decline': {'hospital': str, 'diff': int} or None,
                'changes': [{'hospital': str, 'current': int, 'previous': int, 'diff': int}, ...]
            }
        """
        # Check if we have any comparison data
        has_cache = bool(self.cache_data.get("data", {}))
        has_history = bool(self.history_data.get("hospitals", {}))
        
        if not has_cache and not has_history:
            # First run - no comparison possible
            return {
                'improving_count': 0,
                'worsening_count': 0,
                'unchanged_count': len(current_data),
                'fastest_improvement': None,
                'worst_decline': None,
                'changes': [],
                'last_trends': self.last_trends,
                'has_previous_data': False
            }
        
        # Calculate differences for each hospital
        changes = []
        for hospital, current_wait in current_data.items():
            # Try to get 30-minute-ago data from history (oldest reading)
            history = self.history_data.get("hospitals", {}).get(hospital, [])
            
            if len(history) >= 6:
                # Use oldest reading (30 minutes ago: 6 readings × 5 min = 30 min)
                previous_wait = history[0]
                comparison_window = "30min"
            elif len(history) >= 1:
                # Use oldest available reading (less than 30 min of history)
                previous_wait = history[0]
                comparison_window = f"{len(history) * 5}min"
            else:
                # Fall back to cache (5 minutes ago)
                previous_wait = self.cache_data.get("data", {}).get(hospital)
                comparison_window = "5min"
            
            if previous_wait is None:
                # New hospital, no comparison
                continue
            
            diff = current_wait - previous_wait  # Positive = worse, Negative = better
            changes.append({
                'hospital': hospital,
                'current': current_wait,
                'previous': previous_wait,
                'diff': diff,
                'comparison_window': comparison_window
            })
        
        # Count trends
        improving = [c for c in changes if c['diff'] < 0]
        worsening = [c for c in changes if c['diff'] > 0]
        unchanged = [c for c in changes if c['diff'] == 0]
        
        # Update last known trends (only update when there's actual change)
        # Keep existing trends for hospitals with diff == 0
        for change in changes:
            hospital = change['hospital']
            if change['diff'] != 0:
                # Store the trend direction for future reference
                self.last_trends[hospital] = 'up' if change['diff'] > 0 else 'down'
            # If diff == 0, keep the existing trend (don't remove it)
        
        # Debug: Log comparison windows and trend persistence
        if changes:
            sample = changes[0]
            print(f"[TREND DEBUG] Comparison window: {sample.get('comparison_window', 'unknown')}")
            print(f"[TREND DEBUG] Persisted trends count: {len(self.last_trends)}")
            if self.last_trends:
                print(f"[TREND DEBUG] Sample persisted trends: {list(self.last_trends.items())[:3]}")
        
        # Find fastest improvement (most negative diff)
        fastest_improvement = None
        if improving:
            best = min(improving, key=lambda x: x['diff'])
            fastest_improvement = {
                'hospital': best['hospital'],
                'diff': abs(best['diff']),  # Make positive for display
                'current': best['current'],
                'previous': best['previous']
            }
        
        # Find worst decline (most positive diff)
        worst_decline = None
        if worsening:
            worst = max(worsening, key=lambda x: x['diff'])
            worst_decline = {
                'hospital': worst['hospital'],
                'diff': worst['diff'],
                'current': worst['current'],
                'previous': worst['previous']
            }
        
        result = {
            'improving_count': len(improving),
            'worsening_count': len(worsening),
            'unchanged_count': len(unchanged),
            'fastest_improvement': fastest_improvement,
            'worst_decline': worst_decline,
            'changes': changes,
            'last_trends': self.last_trends,  # Include last known trends
            'has_previous_data': True
        }
        
        print(f"[TREND CALC] Returning trends with {len(self.last_trends)} persisted trends")
        print(f"[TREND CALC] Changes: {len(improving)} improving, {len(worsening)} worsening, {len(unchanged)} unchanged")
        
        return result
    
    def format_trend_direction(self, trends: dict) -> str:
        """
        Format trend direction stat for display
        
        Returns:
            String like "6 hospitals improving | 4 worsening"
        """
        if not trends.get('has_previous_data'):
            return "No previous data"
        
        improving = trends['improving_count']
        worsening = trends['worsening_count']
        
        if improving == 1:
            imp_text = "1 hospital improving"
        else:
            imp_text = f"{improving} hospitals improving"
        
        if worsening == 1:
            wors_text = "1 worsening"
        else:
            wors_text = f"{worsening} worsening"
        
        return f"{imp_text} | {wors_text}"
    
    def format_fastest_improvement(self, trends: dict) -> str:
        """
        Format fastest improvement stat for display
        
        Returns:
            String like "Ulster ED ↓ 21m" or "No improvements"
        """
        if not trends.get('has_previous_data'):
            return "No previous data"
        
        fastest = trends.get('fastest_improvement')
        if fastest is None:
            return "No improvements since last update"
        
        # Shorten hospital name (remove "ED" suffix for cleaner display)
        hospital = fastest['hospital'].replace(' Area ED', '').replace(' ED', '')
        diff = fastest['diff']
        
        return f"{hospital} ↓ {diff}m"
    
    def calculate_most_stable(self, min_readings: int = 4) -> Optional[dict]:
        """
        Calculate which hospital has the most stable wait times
        
        Args:
            min_readings: Minimum number of historical readings required (default 4)
        
        Returns:
            Dict with:
            {
                'hospital': str,
                'std_dev': float,
                'readings': int,
                'avg': float
            }
            or None if insufficient data
        """
        import statistics
        
        stable_scores = {}
        
        for hospital, history in self.history_data["hospitals"].items():
            if len(history) < min_readings:
                continue
            
            # Calculate standard deviation (lower = more stable)
            std_dev = statistics.stdev(history)
            avg = statistics.mean(history)
            
            stable_scores[hospital] = {
                'hospital': hospital,
                'std_dev': round(std_dev, 1),
                'readings': len(history),
                'avg': round(avg, 0)
            }
        
        if not stable_scores:
            return None
        
        # Find hospital with smallest standard deviation
        most_stable = min(stable_scores.values(), key=lambda x: x['std_dev'])
        return most_stable
    
    def format_most_stable(self, stable_data: Optional[dict]) -> str:
        """
        Format most stable hospital stat for display
        
        Returns:
            String like "Daisy Hill — ±7m (past 4h)" or "Insufficient data"
        """
        if stable_data is None:
            return "Insufficient data (need 4+ readings)"
        
        hospital = stable_data['hospital'].replace(' Area ED', '').replace(' ED', '')
        std_dev = stable_data['std_dev']
        readings = stable_data['readings']
        
        return f"{hospital} — ±{std_dev:.0f}m (past {readings}h)"
    
    def calculate_pressure_index(self, current_data: Dict[str, int], threshold: int = 120) -> dict:
        """
        Calculate regional pressure index (% of hospitals over threshold)
        
        Args:
            current_data: Dict mapping hospital names to current wait times
            threshold: Wait time threshold in minutes (default 120 = 2 hours)
        
        Returns:
            Dict with:
            {
                'percentage': int,
                'over_threshold': int,
                'total': int,
                'severity': str  # 'High', 'Moderate', or 'Stable'
            }
        """
        waits = list(current_data.values())
        total = len(waits)
        over_threshold = sum(1 for w in waits if w >= threshold)
        
        percentage = round((over_threshold / total) * 100) if total > 0 else 0
        
        # Determine severity
        if percentage >= 80:
            severity = "High strain"
        elif percentage >= 50:
            severity = "Moderate strain"
        else:
            severity = "Stable"
        
        return {
            'percentage': percentage,
            'over_threshold': over_threshold,
            'total': total,
            'severity': severity,
            'threshold': threshold
        }
    
    def format_pressure_index(self, pressure_data: dict) -> str:
        """
        Format regional pressure index for display
        
        Returns:
            String like "72% hospitals over 2h"
        """
        percentage = pressure_data['percentage']
        threshold_hours = pressure_data['threshold'] // 60
        
        return f"{percentage}% hospitals over {threshold_hours}h"
    
    def calculate_biggest_24h_change(self, current_data: Dict[str, int]) -> Optional[dict]:
        """
        Calculate biggest increase and decrease over 24 hours
        
        Args:
            current_data: Dict mapping hospital names to current wait times
        
        Returns:
            Dict with:
            {
                'biggest_increase': {
                    'hospital': str,
                    'change': int,  # positive number
                    'previous': int,
                    'current': int
                },
                'biggest_decrease': {
                    'hospital': str,
                    'change': int,  # positive number (absolute value)
                    'previous': int,
                    'current': int
                }
            }
            or None if insufficient data
        """
        # Check if we have 24h history (assuming 5-minute polls = 288 readings per day)
        # For practical purposes, we'll use the oldest available reading as "24h ago"
        
        if not self.history_data["hospitals"]:
            return None
        
        increases = []
        decreases = []
        
        for hospital, history in self.history_data["hospitals"].items():
            if len(history) < 2:  # Need at least 2 readings
                continue
            
            # Get current wait time
            if hospital not in current_data:
                continue
            
            current_wait = current_data[hospital]
            # Use oldest reading as "24h ago" (or as far back as we have)
            oldest_wait = history[0]
            
            change = current_wait - oldest_wait
            
            if change > 0:  # Increase
                increases.append({
                    'hospital': hospital,
                    'change': change,
                    'previous': oldest_wait,
                    'current': current_wait
                })
            elif change < 0:  # Decrease
                decreases.append({
                    'hospital': hospital,
                    'change': abs(change),
                    'previous': oldest_wait,
                    'current': current_wait
                })
        
        if not increases and not decreases:
            return None
        
        result = {}
        
        if increases:
            result['biggest_increase'] = max(increases, key=lambda x: x['change'])
        else:
            result['biggest_increase'] = None
        
        if decreases:
            result['biggest_decrease'] = max(decreases, key=lambda x: x['change'])
        else:
            result['biggest_decrease'] = None
        
        return result
    
    def format_biggest_24h_change(self, change_data: Optional[dict]) -> dict:
        """
        Format biggest 24h change for display
        
        Returns:
            Dict with:
            {
                'increase': str,  # "Antrim ↑ +92m vs yesterday"
                'decrease': str   # "Ulster ↓ −36m vs yesterday"
            }
        """
        if change_data is None:
            return {
                'increase': "Insufficient data",
                'decrease': "Insufficient data"
            }
        
        result = {}
        
        if change_data['biggest_increase']:
            inc = change_data['biggest_increase']
            hospital = inc['hospital'].replace(' Area ED', '').replace(' ED', '')
            # Use inline SVG for up arrow
            result['increase'] = f'{hospital} <svg class="inline h-4 w-4 -mt-0.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg> +{inc["change"]}m'
        else:
            result['increase'] = "No increases"
        
        if change_data['biggest_decrease']:
            dec = change_data['biggest_decrease']
            hospital = dec['hospital'].replace(' Area ED', '').replace(' ED', '')
            # Use inline SVG for down arrow
            result['decrease'] = f'{hospital} <svg class="inline h-4 w-4 -mt-0.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg> −{dec["change"]}m'
        else:
            result['decrease'] = "No decreases"
        
        return result
    
    def get_timestamps(self) -> dict:
        """
        Get both timestamps from cache
        
        Returns:
            Dict with:
            {
                'fetched_at': str,  # ISO format timestamp of when we fetched
                'source_updated': str  # Human-readable timestamp from NI Direct
            }
        """
        return {
            'fetched_at': self.cache_data.get('fetched_at'),
            'source_updated': self.cache_data.get('source_updated')
        }


# Example usage
def example_usage():
    """Example of how to use the trend cache system"""
    
    # Initialize cache
    cache = HospitalTrendCache("hospital_wait_cache.json")
    
    # Simulate current poll data
    current_hospitals = {
        "Altnagelvin Area ED": 317,
        "Royal Victoria ED": 281,
        "Ulster ED": 238,
        "Mater ED": 220,
        "Antrim Area ED": 162,
        "Craigavon Area ED": 157,
        "Causeway ED": 152,
        "South West Acute ED": 131,
        "Royal Children's ED": 119,
        "Daisy Hill ED": 86
    }
    
    # Calculate trends (compare with previous data)
    trends = cache.calculate_trends(current_hospitals)
    
    # Format for display
    trend_direction = cache.format_trend_direction(trends)
    fastest_improvement = cache.format_fastest_improvement(trends)
    
    print("Trend Direction:", trend_direction)
    print("Fastest Improvement:", fastest_improvement)
    print("\nDetailed changes:")
    for change in trends['changes']:
        direction = "↓" if change['diff'] < 0 else "↑" if change['diff'] > 0 else "→"
        print(f"  {change['hospital']}: {change['previous']}m → {change['current']}m ({direction} {abs(change['diff'])}m)")
    
    # Update cache for next poll
    cache.update_cache(current_hospitals)
    
    return trends


if __name__ == "__main__":
    example_usage()
