# Trend Arrow Persistence Fix ✅

## Problem
Trend arrows were appearing and disappearing between dashboard generations, even though the script had been running for hours with data available.

## Root Cause
When NI Direct data didn't change between polling intervals, the difference (`diff`) was 0, causing the `get_trend()` function to return `None` and hide the arrows.

### Why This Happened
- **NI Direct updates infrequently**: The source website may update every 15-30 minutes
- **Script polls frequently**: Every 5 minutes (POLL_SECONDS = 300)
- **Same data = no arrows**: When `diff == 0`, no trend was shown

## Solution Implemented

### 1. **Trend Cache System** (`trend_cache_system.py`)

**Added last_trends tracking**:
```python
def __init__(self, ...):
    # ... existing code ...
    self.last_trends = {}  # Store last known trend directions
```

**Store trends when they change**:
```python
# Update last known trends (persist even when diff == 0)
for change in changes:
    hospital = change['hospital']
    if change['diff'] != 0:
        # Store the trend direction for future reference
        self.last_trends[hospital] = 'up' if change['diff'] > 0 else 'down'
```

**Include in return value**:
```python
return {
    'improving_count': len(improving),
    'worsening_count': len(worsening),
    'unchanged_count': len(unchanged),
    'fastest_improvement': fastest_improvement,
    'worst_decline': worst_decline,
    'changes': changes,
    'last_trends': self.last_trends,  # ← NEW
    'has_previous_data': True
}
```

### 2. **Dashboard Generator** (`app_with_dashboard.py`)

**Updated get_trend() function**:
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
                    return trends['last_trends'][name]  # ← NEW
    
    # Fallback to last known trend if hospital not in changes
    if 'last_trends' in trends and name in trends['last_trends']:
        return trends['last_trends'][name]  # ← NEW
    
    return None
```

## How It Works Now

### Before Fix
```
09:00 - Data changes → Arrows appear ✓
09:05 - Data same → Arrows disappear ✗
09:10 - Data same → Arrows disappear ✗
09:15 - Data changes → Arrows appear ✓
09:20 - Data same → Arrows disappear ✗
```

### After Fix
```
09:00 - Data changes → Arrows appear ✓
09:05 - Data same → Arrows persist ✓ (shows last known trend)
09:10 - Data same → Arrows persist ✓ (shows last known trend)
09:15 - Data changes → Arrows update ✓ (new trend direction)
09:20 - Data same → Arrows persist ✓ (shows last known trend)
```

## Behavior

### First Run (No Previous Data)
- No arrows shown (no history to compare)

### Second Run (First Comparison)
- Arrows appear based on actual changes
- Last trends stored in memory

### Subsequent Runs
- **Data changed**: Arrows update to new direction
- **Data unchanged**: Arrows persist showing last known direction
- **New hospital**: No arrow until first change detected

## Example

### Scenario: Altnagelvin Area ED

| Time | Wait Time | Diff | Arrow Shown | Reason |
|------|-----------|------|-------------|--------|
| 09:00 | 180m | N/A | None | No previous data |
| 09:05 | 195m | +15m | ↑ Up | Worsening |
| 09:10 | 195m | 0m | ↑ Up | **Last trend persists** |
| 09:15 | 195m | 0m | ↑ Up | **Last trend persists** |
| 09:20 | 175m | -20m | ↓ Down | Improving |
| 09:25 | 175m | 0m | ↓ Down | **Last trend persists** |

## Benefits

✅ **Consistent Display**: Arrows always visible after first change  
✅ **Better UX**: Users see trend direction even when data is stale  
✅ **Accurate**: Updates immediately when actual changes occur  
✅ **Memory Efficient**: Only stores direction string per hospital  
✅ **No Breaking Changes**: Backward compatible with existing code  

## Limitations

### Stale Trends
If NI Direct stops updating for a long time, arrows will show the last known trend indefinitely.

**Mitigation**: Could add timestamp and hide arrows after X hours of no updates (future enhancement).

### First Run
No arrows on first run (expected - no previous data to compare).

**Mitigation**: This is correct behavior and cannot be avoided.

## Testing

### Verify Fix Works
1. Run dashboard generator (first run - no arrows)
2. Wait 5 minutes, run again (arrows appear)
3. Run immediately again (arrows should persist)
4. Change data manually and run (arrows update)
5. Run again without changes (arrows persist)

### Debug Output
Check console for trend tracking:
```
[DEBUG] Trends data: {'last_trends': {'Altnagelvin Area ED': 'up', ...}}
```

## Status: ✅ FIXED

Trend arrows will now:
- ✅ Persist between dashboard generations
- ✅ Update when data actually changes
- ✅ Show last known direction when data is unchanged
- ✅ Provide consistent user experience

**Next Run**: Arrows will remain visible even when NI Direct data doesn't update between polling intervals.
