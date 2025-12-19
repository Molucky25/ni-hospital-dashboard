# Trend Arrow Disappearing Issue - Analysis

## Problem
Trend arrows appear in some screenshots and disappear in others, even though the script has been running for hours with data available.

## Root Cause

### Current Behavior
The trend arrows are calculated by comparing **current** wait times with **previous** wait times:

```python
def get_trend(name):
    if 'changes' in trends:
        for change in trends['changes']:
            if change['hospital'] == name:
                diff = change['diff']  # current - previous
                if diff > 0:
                    return 'up'    # Worsening
                elif diff < 0:
                    return 'down'  # Improving
    return None  # No change or no data
```

### The Issue
When `diff == 0` (no change between current and previous), the function returns `None`, so **no arrow is displayed**.

### Why This Happens
1. **NI Direct updates infrequently**: The source website may not update wait times every 5 minutes
2. **Polling too frequently**: Your script polls every 5 minutes, but data might update every 15-30 minutes
3. **Same data, no diff**: When data hasn't changed, `diff = 0`, arrows disappear

### Example Timeline
```
09:00 - Run 1: No previous data → No arrows
09:05 - Run 2: Data changed → Arrows appear (3 up, 2 down)
09:10 - Run 3: Data unchanged → Arrows disappear (diff = 0)
09:15 - Run 4: Data unchanged → Arrows disappear (diff = 0)
09:20 - Run 5: Data changed → Arrows appear (4 up, 1 down)
09:25 - Run 6: Data unchanged → Arrows disappear (diff = 0)
```

## Solutions

### Option 1: Show Last Known Trend (Recommended)
Keep track of the last non-zero trend for each hospital and display it until a new change occurs.

**Pros**:
- Always shows trend information
- More informative for users
- Reflects recent direction

**Cons**:
- May show "stale" trends if data doesn't update for a long time
- Need to add timestamp to know how old the trend is

### Option 2: Show "No Change" Indicator
Display a different icon (e.g., horizontal line) when `diff == 0`.

**Pros**:
- Accurate representation of current state
- Clear indication of stability

**Cons**:
- Less visually interesting
- Doesn't show recent trend direction

### Option 3: Use Longer Comparison Window
Compare current data with data from 15-30 minutes ago instead of the immediate previous run.

**Pros**:
- More stable trends
- Less affected by data update frequency

**Cons**:
- Requires storing multiple historical snapshots
- More complex implementation

### Option 4: Only Update Cache When Data Changes
Don't update the cache if the data is identical to the previous run.

**Pros**:
- Trends persist until actual changes occur
- Simple to implement

**Cons**:
- May not reflect true "no change" state
- Could be misleading

## Recommended Implementation: Option 1

### Enhanced Trend Tracking
Store the last known trend direction for each hospital:

```python
# In trend_cache_system.py
class HospitalTrendCache:
    def __init__(self):
        self.cache_file = Path("hospital_wait_cache.json")
        self.history_file = Path("hospital_wait_history.json")
        self.trend_file = Path("hospital_wait_trends.jsonl")
        self.last_trends = {}  # NEW: Store last known trends
        
    def calculate_trends(self, current_data):
        # ... existing code ...
        
        # Update last known trends
        for change in changes:
            hospital = change['hospital']
            if change['diff'] != 0:
                # Store the trend direction
                self.last_trends[hospital] = {
                    'direction': 'up' if change['diff'] > 0 else 'down',
                    'timestamp': datetime.now().isoformat(),
                    'diff': change['diff']
                }
        
        return {
            'improving_count': len(improving),
            'worsening_count': len(worsening),
            'unchanged_count': len(unchanged),
            'fastest_improvement': fastest_improvement,
            'worst_decline': worst_decline,
            'changes': changes,
            'last_trends': self.last_trends,  # NEW
            'has_previous_data': True
        }
```

### Updated get_trend Function
```python
def get_trend(name):
    # Look for hospital in the changes list
    if 'changes' in trends:
        for change in trends['changes']:
            if change['hospital'] == name:
                diff = change['diff']
                if diff > 0:
                    return 'up'
                elif diff < 0:
                    return 'down'
                # If diff == 0, check last known trend
                elif 'last_trends' in trends and name in trends['last_trends']:
                    return trends['last_trends'][name]['direction']
    
    # Fallback to last known trend
    if 'last_trends' in trends and name in trends['last_trends']:
        return trends['last_trends'][name]['direction']
    
    return None  # No data available
```

## Alternative: Simple Fix (Quick Implementation)

If you want a quick fix without major changes, simply show the last trend from the changes list even when diff == 0:

```python
def get_trend(name):
    if 'changes' in trends:
        for change in trends['changes']:
            if change['hospital'] == name:
                diff = change['diff']
                if diff != 0:  # Only update if there's a change
                    return 'up' if diff > 0 else 'down'
    
    # If no change, check if hospital exists in changes (meaning we have history)
    # and return the last known trend from previous runs
    # This requires storing last_trend in the cache
    
    return None
```

## Testing Strategy

### Verify the Fix
1. Run dashboard generator multiple times
2. Check that arrows persist even when data doesn't change
3. Verify arrows update when data actually changes
4. Confirm no "stale" arrows after long periods

### Debug Output
Add logging to track trend behavior:
```python
print(f"[DEBUG] Trend for {name}: diff={diff}, trend={trend}, last_trend={last_trend}")
```

## Status: Issue Identified

The trend arrows disappear because:
1. ✅ NI Direct data doesn't update every polling cycle
2. ✅ When data is unchanged, `diff = 0`, no arrow shown
3. ✅ This is expected behavior but not user-friendly

**Recommendation**: Implement Option 1 (Last Known Trend) to provide consistent trend information to users.
