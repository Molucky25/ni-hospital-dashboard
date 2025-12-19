# Trend Stats Integration Guide 🔄

## Changes Implemented ✅

### **1. Branding Added**
Footer now displays:
```
⚡ Powered by NI Emergency Response Vids
```

### **2. Stats Replaced**
**Removed:**
- ❌ Longest Wait
- ❌ Shortest Wait
- ❌ Under 60m
- ❌ Over 240m

**Added:**
- ✅ **Trend Direction**: "6 hospitals improving | 4 worsening"
- ✅ **Fastest Improvement**: "Ulster ED ↓ 21m"
- ✅ **Average Wait**: (kept)
- ✅ **Stat 3**: Placeholder (awaiting your next insight)
- ✅ **Stat 4**: Placeholder (awaiting your next insight)

---

## Python Integration

### **Step 1: Import the Cache System**

```python
from trend_cache_system import HospitalTrendCache

# Initialize once (at start of script)
trend_cache = HospitalTrendCache("hospital_wait_cache.json")
```

---

### **Step 2: Calculate Trends on Each Poll**

```python
def fetch_and_process_hospital_data():
    """Your existing function to fetch hospital data"""
    
    # Fetch current wait times (your existing code)
    hospitals = fetch_from_ni_direct()  # Your function
    
    # Example format:
    current_waits = {
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
    
    # Calculate trends (compares with cached previous data)
    trends = trend_cache.calculate_trends(current_waits)
    
    # Format for dashboard display
    trend_stats = {
        'trend_direction': trend_cache.format_trend_direction(trends),
        'fastest_improvement': trend_cache.format_fastest_improvement(trends)
    }
    
    # Update cache for next poll
    trend_cache.update_cache(current_waits)
    
    return current_waits, trend_stats
```

---

### **Step 3: Pass to Dashboard**

```python
def generate_dashboard_image():
    """Your dashboard generation function"""
    
    # Get data with trends
    hospitals, trend_stats = fetch_and_process_hospital_data()
    
    # Prepare dashboard data
    dashboard_data = {
        'updateTime': datetime.now().strftime('%I:%M %p, %a %d %b %Y'),
        'hospitals': format_hospital_table(hospitals),  # Your function
        'avgWait': calculate_average(hospitals),
        
        # NEW: Trend stats
        'trendDirection': trend_stats['trend_direction'],
        'fastestImprovement': trend_stats['fastest_improvement'],
        
        # Your existing data...
    }
    
    # Render dashboard (your existing code)
    render_html_to_image(dashboard_data)
```

---

### **Step 4: Update JavaScript (Already Done!)**

The HTML already has the elements:
```javascript
// In your updateDashboard(data) function:

// Trend Direction
document.getElementById('trend-direction').innerHTML = 
    formatTrendDirection(data.trendDirection);

// Fastest Improvement
document.getElementById('fastest-improvement').innerHTML = 
    formatFastestImprovement(data.fastestImprovement);
```

---

## Cache File Structure

**File:** `hospital_wait_cache.json`

```json
{
  "timestamp": "2025-10-17T03:00:00.123456",
  "data": {
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
}
```

---

## How It Works

### **First Run (No Cache):**
```python
trends = cache.calculate_trends(current_hospitals)
# Result:
{
    'improving_count': 0,
    'worsening_count': 0,
    'unchanged_count': 10,
    'fastest_improvement': None,
    'has_previous_data': False
}

# Display: "No previous data"
```

### **Second Run (With Cache):**
```python
# Previous poll: Ulster ED = 259m
# Current poll: Ulster ED = 238m
# Diff: -21m (improved!)

trends = cache.calculate_trends(current_hospitals)
# Result:
{
    'improving_count': 6,
    'worsening_count': 4,
    'fastest_improvement': {
        'hospital': 'Ulster ED',
        'diff': 21,
        'current': 238,
        'previous': 259
    }
}

# Display: "6 hospitals improving | 4 worsening"
#          "Ulster ED ↓ 21m"
```

---

## Trend Calculation Logic

### **For Each Hospital:**
```python
diff = current_wait - previous_wait

if diff < 0:
    # Wait time DECREASED (good! ✅)
    # Example: 259 → 238 = -21 (improved by 21m)
    status = "improving"

elif diff > 0:
    # Wait time INCREASED (bad ❌)
    # Example: 150 → 175 = +25 (worsened by 25m)
    status = "worsening"

else:
    # Wait time UNCHANGED
    status = "unchanged"
```

### **Trend Direction:**
```python
improving = count hospitals where diff < 0
worsening = count hospitals where diff > 0

display = f"{improving} hospitals improving | {worsening} worsening"
```

### **Fastest Improvement:**
```python
# Find hospital with most negative diff
improvements = [h for h in hospitals if h.diff < 0]
fastest = min(improvements, key=lambda h: h.diff)

# Example: Ulster ED went from 259m → 238m (diff = -21)
display = f"Ulster ED ↓ 21m"
```

---

## Complete Example

```python
from trend_cache_system import HospitalTrendCache
from datetime import datetime

# Initialize
cache = HospitalTrendCache()

# Poll 1 (12:00 PM)
hospitals_poll1 = {
    "Altnagelvin Area ED": 320,
    "Royal Victoria ED": 290,
    "Ulster ED": 259,
    # ... all 10 hospitals
}

trends1 = cache.calculate_trends(hospitals_poll1)
print(trends1['improving_count'])  # 0 (no previous data)

cache.update_cache(hospitals_poll1)  # Save for next time

# Poll 2 (12:30 PM) - 30 minutes later
hospitals_poll2 = {
    "Altnagelvin Area ED": 317,  # -3m (improved)
    "Royal Victoria ED": 281,     # -9m (improved)
    "Ulster ED": 238,             # -21m (improved!)
    # ... rest
}

trends2 = cache.calculate_trends(hospitals_poll2)
print(trends2['improving_count'])  # 6
print(trends2['worsening_count'])  # 4
print(trends2['fastest_improvement'])  
# {'hospital': 'Ulster ED', 'diff': 21, ...}

# Format for display
print(cache.format_trend_direction(trends2))
# "6 hospitals improving | 4 worsening"

print(cache.format_fastest_improvement(trends2))
# "Ulster ↓ 21m"

cache.update_cache(hospitals_poll2)  # Save for next poll
```

---

## Current Dashboard Layout

```
┌────────────────────────────────────────────────┐
│  Still Waiting NI          ↓ 8% since last    │
│  Tracking A&E Times        Regional: 187m ↑   │
├──────────────────────┬─────────────────────────┤
│                      │  📈 TREND DIRECTION     │
│   Hospital Table     │  6 improving | 4 worse  │
│   (10 rows)          ├─────────────────────────┤
│                      │  🕐 AVERAGE WAIT        │
│                      │  187m                   │
│                      ├─────────────────────────┤
│                      │  ⚡ FASTEST IMPROVEMENT │
│                      │  Ulster ED ↓ 21m        │
│                      ├─────────────────────────┤
│                      │  ⏰ STAT 3              │
│                      │  Coming soon            │
│                      ├─────────────────────────┤
│                      │  📊 STAT 4              │
│                      │  Coming soon            │
└──────────────────────┴─────────────────────────┘
│  📊 Source | 🩺 Severity | ℹ️ Triage + 📘 fb  │
│  ⚡ Powered by NI Emergency Response Vids     │
└────────────────────────────────────────────────┘
```

---

## Testing Your Integration

### **Test File: test_trends.py**

```python
from trend_cache_system import HospitalTrendCache
import json

# Create test data
poll1 = {
    "Altnagelvin Area ED": 320,
    "Ulster ED": 259,
    "Mater ED": 200
}

poll2 = {
    "Altnagelvin Area ED": 317,  # -3
    "Ulster ED": 238,             # -21 (fastest!)
    "Mater ED": 220               # +20
}

# Test
cache = HospitalTrendCache("test_cache.json")

# First poll
trends1 = cache.calculate_trends(poll1)
assert trends1['has_previous_data'] == False
cache.update_cache(poll1)

# Second poll
trends2 = cache.calculate_trends(poll2)
assert trends2['improving_count'] == 2
assert trends2['worsening_count'] == 1
assert trends2['fastest_improvement']['hospital'] == "Ulster ED"
assert trends2['fastest_improvement']['diff'] == 21

print("✅ All tests passed!")
```

---

## Summary

### ✅ **Completed:**
1. Branding added to footer
2. Old stats removed
3. New trend stats added (2/4)
4. Caching system created
5. Calculation logic implemented

### 🔄 **Next Steps:**
1. Integrate trend_cache_system.py into your main script
2. Test with real data
3. Share your next 2 stat insights
4. Implement those 2 stats
5. Then add dark theme!

---

**The trend system is ready to go! Just integrate the cache class into your polling script.** 🎉
