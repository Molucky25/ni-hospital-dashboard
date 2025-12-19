# Trend Direction Issue - Diagnosis & Solution

## 🔍 **Problem Identified**

Recent dashboard images show **no trend arrows** (↑↓→) in the hospital table.

---

## 🕵️ **Root Cause Analysis**

### **Investigation Steps**

1. ✅ Checked `hospital_wait_cache.json` - **Has data** (last updated 21:27:49)
2. ✅ Checked `hospital_wait_history.json` - **Has data** (6 readings per hospital)
3. ✅ Checked trend calculation logic - **Working correctly**
4. ❌ **Found the issue**: All 6 historical readings are **identical**

---

### **The Real Problem**

Looking at `hospital_wait_history.json`:

```json
"Ulster ED": [103, 103, 103, 103, 103, 103],
"Royal Children's ED": [149, 149, 149, 149, 149, 149],
"Altnagelvin AreaED": [99, 99, 99, 99, 99, 99]
```

**All readings are identical!** This means:
- No wait time changes between polls
- `diff == 0` for all hospitals
- No trends to display

---

## 📊 **Why This Happens**

### **Scenario 1: NI Direct Website Not Updating**

The NI Direct website may not be updating wait times frequently enough.

**Evidence**:
- History shows 6 identical readings
- Readings span ~30 minutes (6 × 5 min intervals)
- Wait times frozen for 30+ minutes

**Likely causes**:
- Weekend/night hours (less frequent updates)
- System maintenance
- Data feed delay from hospitals

---

### **Scenario 2: Polling Too Frequently**

Your script polls every 5 minutes, but NI Direct might update every 15-30 minutes.

**Result**:
- Multiple polls capture same data
- No changes detected
- No trends shown

---

### **Scenario 3: Change Detection Skipping Updates**

Your script has change detection:

```python
digest = compute_digest(rows)
if state.get("digest") == digest:
    print("No change detected. Skipping send.")
    return
```

**If data doesn't change**:
- Script skips sending
- Cache doesn't update
- Trends stay stale

**But wait...** Looking at your history, the cache IS updating (timestamp shows recent updates), so this isn't the issue.

---

## 🎯 **Actual Root Cause**

**The NI Direct website data is static for extended periods.**

Your system is working correctly:
1. ✅ Fetches data every 5 minutes
2. ✅ Compares with previous data
3. ✅ Calculates trends (diff = 0)
4. ✅ Shows no arrows when diff == 0

**The issue**: When all hospitals have `diff == 0`, no trend arrows appear because there's literally no trend to show!

---

## 🔧 **How Trend Logic Works**

### **Current Logic** (from `app_with_dashboard.py` line 524-542)

```python
def get_trend(name):
    # Look for hospital in the changes list
    if 'changes' in trends:
        for change in trends['changes']:
            if change['hospital'] == name:
                diff = change['diff']
                if diff > 0:
                    return 'up'  # Wait time increased (worsening)
                elif diff < 0:
                    return 'down'  # Wait time decreased (improving)
                # If diff == 0, check last known trend
                elif 'last_trends' in trends and name in trends['last_trends']:
                    return trends['last_trends'][name]
    
    # Fallback to last known trend if hospital not in changes
    if 'last_trends' in trends and name in trends['last_trends']:
        return trends['last_trends'][name]
    
    return None  # No change or no data
```

**When `diff == 0`**:
- Checks `last_trends` (persisted from previous non-zero changes)
- If no `last_trends` exists → returns `None`
- `None` = no arrow displayed

---

## 🔍 **Verification**

Let me check if `last_trends` is being persisted:

**From `trend_cache_system.py` lines 157-162**:

```python
# Update last known trends (persist even when diff == 0)
for change in changes:
    hospital = change['hospital']
    if change['diff'] != 0:
        # Store the trend direction for future reference
        self.last_trends[hospital] = 'up' if change['diff'] > 0 else 'down'
```

**This stores trends in memory** (`self.last_trends`), but:
- ❌ **NOT saved to disk**
- ❌ **Lost on script restart**
- ❌ **Only persists during single run**

---

## 🚨 **The Actual Bug**

`last_trends` is stored in **memory only** and is **lost between script runs**.

**Workflow**:
1. Script starts → `self.last_trends = {}` (empty)
2. First poll → No previous data → No trends
3. Second poll → Data unchanged (diff == 0) → No trends
4. Third poll → Data unchanged (diff == 0) → No trends
5. Script restarts → `last_trends` lost → Back to step 1

**Result**: If data doesn't change for several polls, trends never appear!

---

## ✅ **Solution**

### **Option 1: Persist `last_trends` to Disk**

Save `last_trends` to the cache file so it survives script restarts.

**Implementation**:

```python
# In trend_cache_system.py

def _save_cache(self):
    """Save cache to file"""
    with open(self.cache_file, 'w') as f:
        json.dump({
            "timestamp": self.cache_data.get("timestamp"),
            "data": self.cache_data.get("data", {}),
            "last_trends": self.last_trends  # ADD THIS
        }, f, indent=2)

def _load_cache(self) -> dict:
    """Load cached data from file"""
    if self.cache_file.exists():
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                # Load last_trends if it exists
                self.last_trends = cache.get("last_trends", {})  # ADD THIS
                return cache
        except (json.JSONDecodeError, IOError):
            return self._empty_cache()
    return self._empty_cache()
```

---

### **Option 2: Show Horizontal Arrow When No Change**

Always show an arrow, even when `diff == 0`.

**Implementation**:

```python
def get_trend(name):
    # ... existing logic ...
    
    # If diff == 0 and no last_trends, show horizontal arrow
    if diff == 0:
        return 'stable'  # New state for no change
    
    return None
```

Then in dashboard HTML, handle `trend === 'stable'`:

```javascript
if (hospital.trend === 'up') {
    // Red up arrow
} else if (hospital.trend === 'down') {
    // Green down arrow
} else if (hospital.trend === 'stable') {
    // Gray horizontal arrow
} else {
    // No arrow
}
```

---

### **Option 3: Use Longer Comparison Window**

Instead of comparing with last poll (5 min ago), compare with data from 30-60 minutes ago.

**Implementation**:

Use `hospital_wait_history.json` (which keeps 6 readings = 30 min):

```python
def calculate_trends(self, current_data: Dict[str, int]) -> dict:
    # Compare with OLDEST reading in history (30 min ago)
    # instead of most recent cache (5 min ago)
    
    for hospital, current_wait in current_data.items():
        history = self.history_data["hospitals"].get(hospital, [])
        if len(history) >= 6:
            # Compare with 30 minutes ago (oldest reading)
            previous_wait = history[0]
        else:
            # Not enough history, use cache
            previous_wait = self.cache_data.get("data", {}).get(hospital)
        
        # ... rest of logic ...
```

This would show trends over 30 minutes instead of 5 minutes, making changes more visible.

---

## 🎯 **Recommended Solution**

**Implement Option 1 + Option 3 combined**:

1. ✅ **Persist `last_trends` to disk** (Option 1)
   - Survives script restarts
   - Shows last known trend when data is static

2. ✅ **Use 30-minute comparison window** (Option 3)
   - More meaningful trends (30 min vs 5 min)
   - Less affected by short-term data freezes
   - Matches the "hourly trend" concept better

---

## 📊 **Expected Behavior After Fix**

### **Before (Current)**
```
Data unchanged for 30 min → No trends shown → Empty arrows
```

### **After (Fixed)**
```
Data unchanged for 30 min → Show last known trend → Arrows persist
OR
Compare with 30 min ago → Show longer-term trend → More stable arrows
```

---

## 🔍 **Verification Steps**

After implementing the fix:

1. **Check cache file** - should contain `last_trends`:
   ```json
   {
     "timestamp": "...",
     "data": {...},
     "last_trends": {
       "Ulster ED": "down",
       "Antrim AreaED": "up"
     }
   }
   ```

2. **Restart script** - trends should persist

3. **Wait for data change** - trends should update correctly

4. **Check dashboard** - arrows should appear consistently

---

## 🎯 **Summary**

**Problem**: No trend arrows in recent dashboards

**Root Cause**: 
- Data unchanged between polls (diff == 0)
- `last_trends` stored in memory only (lost on restart)
- Short comparison window (5 min) too sensitive to static data

**Solution**:
- Persist `last_trends` to disk
- Use 30-minute comparison window
- Show last known trend when data is static

**Status**: ⚠️ **Needs implementation** - I can implement this fix if you'd like!

---

## 🚀 **Next Steps**

1. Implement `last_trends` persistence (5 min)
2. Implement 30-minute comparison window (10 min)
3. Test with static data (verify arrows persist)
4. Test with changing data (verify arrows update)
5. Deploy and monitor

**Would you like me to implement these fixes now?** 🔧
