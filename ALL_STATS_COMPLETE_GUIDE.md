# Complete Stats Integration Guide ✅

## All 5 Stats Implemented!

### **Dashboard Layout**

```
┌────────────────────────────────────────────────────┐
│  Still Waiting NI         ↓ 8% since last hour    │
│  Tracking A&E Times       Regional avg: 187m ↑    │
├──────────────────────┬─────────────────────────────┤
│                      │  📈 TREND DIRECTION         │
│  Hospital Table      │  6 improving | 4 worsening  │
│  (10 rows)           ├─────────────────────────────┤
│                      │  🕐 AVERAGE WAIT            │
│                      │  187m                       │
│                      ├─────────────────────────────┤
│                      │  ⚡ FASTEST IMPROVEMENT     │
│                      │  Ulster ED ↓ 21m            │
│                      ├─────────────────────────────┤
│                      │  🏥 MOST STABLE HOSPITAL    │
│                      │  Daisy Hill — ±7m (past 4h) │
│                      ├─────────────────────────────┤
│                      │  📊 REGIONAL PRESSURE       │
│                      │  72% hospitals over 2h      │
└──────────────────────┴─────────────────────────────┘
│         ⚡ Powered by NI Emergency Response Vids   │
│  📊 Data Source  |  🩺 Severity  |  ℹ️ + 📘 fb    │
└────────────────────────────────────────────────────┘
```

---

## Stat Breakdown

### **1. 📈 Trend Direction** (Blue Card)
**Shows:** "6 hospitals improving | 4 worsening"

**Calculation:**
```python
# Compare current vs previous wait time for each hospital
for hospital in hospitals:
    diff = current_wait - previous_wait
    if diff < 0:
        improving += 1  # Wait time decreased
    elif diff > 0:
        worsening += 1  # Wait time increased
```

**Requires:** Previous poll data (1 data point)

---

### **2. 🕐 Average Wait** (Yellow/Orange Card)
**Shows:** "187m"

**Calculation:**
```python
avg = sum(all_wait_times) / len(all_wait_times)
```

**Requires:** Current data only

---

### **3. ⚡ Fastest Improvement** (Green Card)
**Shows:** "Ulster ED ↓ 21m"

**Calculation:**
```python
# Find hospital with biggest decrease
improvements = [h for h in hospitals if h.diff < 0]
fastest = min(improvements, key=lambda h: h.diff)
# Example: Ulster ED 259m → 238m = -21m
```

**Requires:** Previous poll data (1 data point)

---

### **4. 🏥 Most Stable Hospital** (Purple/Pink Card)
**Shows:** "Daisy Hill — ±7m (past 4h)"

**Calculation:**
```python
import statistics

# Need last 4-6 readings per hospital
# Example: Daisy Hill = [85, 86, 87, 86]
std_dev = statistics.stdev([85, 86, 87, 86])  # = 0.8

# Find hospital with lowest std_dev (most consistent)
```

**Requires:** Historical data (4-6 readings, ~4 hours if polling every hour)

---

### **5. 📊 Regional Pressure Index** (Amber Card)
**Shows:** "72% hospitals over 2h"

**Calculation:**
```python
threshold = 120  # 2 hours in minutes
over = sum(1 for wait in waits if wait >= threshold)
percentage = (over / total) * 100

# Example: 7 out of 10 hospitals ≥120m = 70%
```

**Requires:** Current data only

**Severity Levels:**
- ≥80%: 🔴 High strain
- ≥50%: 🟠 Moderate strain
- <50%: 🟢 Stable

---

## Python Integration

### **Complete Example:**

```python
from trend_cache_system import HospitalTrendCache

# Initialize
cache = HospitalTrendCache()

def generate_dashboard():
    """Main function - called every poll"""
    
    # 1. Fetch current hospital data
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
    
    # 2. Calculate all stats
    
    # Stat 1 & 3: Trend Direction & Fastest Improvement
    trends = cache.calculate_trends(current_hospitals)
    trend_direction = cache.format_trend_direction(trends)
    fastest_improvement = cache.format_fastest_improvement(trends)
    
    # Stat 2: Average Wait
    avg_wait = round(sum(current_hospitals.values()) / len(current_hospitals))
    
    # Stat 4: Most Stable Hospital
    stable_data = cache.calculate_most_stable(min_readings=4)
    most_stable = cache.format_most_stable(stable_data)
    
    # Stat 5: Regional Pressure Index
    pressure_data = cache.calculate_pressure_index(current_hospitals, threshold=120)
    pressure_index = cache.format_pressure_index(pressure_data)
    
    # 3. Update cache for next time
    cache.update_cache(current_hospitals)  # Also updates history
    
    # 4. Prepare dashboard data
    dashboard_data = {
        'updateTime': datetime.now().strftime('%I:%M %p, %a %d %b %Y'),
        'hospitals': format_hospital_table(current_hospitals),
        
        # All 5 stats
        'trendDirection': trend_direction,
        'avgWait': f"{avg_wait}m",
        'fastestImprovement': fastest_improvement,
        'mostStable': most_stable,
        'pressureIndex': pressure_index,
        
        # Optional: severity for color coding
        'pressureSeverity': pressure_data['severity'],
    }
    
    # 5. Render dashboard
    render_html_to_image(dashboard_data)
    post_to_social_media('dashboard.png')
```

---

## Data Files

### **1. hospital_wait_cache.json** (Previous Poll)
```json
{
  "timestamp": "2025-10-17T03:00:00",
  "data": {
    "Altnagelvin Area ED": 317,
    "Royal Victoria ED": 281,
    ...
  }
}
```

### **2. hospital_wait_history.json** (Rolling History)
```json
{
  "hospitals": {
    "Altnagelvin Area ED": [312, 317, 316, 319, 320, 317],
    "Royal Victoria ED": [274, 281, 279, 283, 285, 281],
    "Daisy Hill ED": [85, 86, 87, 86, 85, 86],
    ...
  }
}
```

**Note:** History keeps last 6 readings (configurable)

---

## Timeline of Data Availability

### **First Poll (12:00 PM):**
```python
# Can calculate:
✅ Average Wait (187m)
✅ Regional Pressure (72% over 2h)

# Cannot calculate yet:
❌ Trend Direction (no previous data)
❌ Fastest Improvement (no previous data)
❌ Most Stable (need 4+ readings)
```

### **Second Poll (12:30 PM):**
```python
# Can now calculate:
✅ Average Wait
✅ Regional Pressure
✅ Trend Direction (6 improving | 4 worsening)
✅ Fastest Improvement (Ulster ↓ 21m)

# Still need more data:
❌ Most Stable (only 2 readings, need 4+)
```

### **After 4th Poll (~2 Hours):**
```python
# All stats available!
✅ Average Wait
✅ Regional Pressure
✅ Trend Direction
✅ Fastest Improvement
✅ Most Stable (Daisy Hill ± 7m)
```

---

## Stat Calculation Methods

### **All Methods in `HospitalTrendCache` Class:**

```python
# Trend stats
trends = cache.calculate_trends(current_data)
trend_direction = cache.format_trend_direction(trends)
fastest_improvement = cache.format_fastest_improvement(trends)

# Stability stat
stable_data = cache.calculate_most_stable(min_readings=4)
most_stable = cache.format_most_stable(stable_data)

# Pressure stat
pressure_data = cache.calculate_pressure_index(current_data, threshold=120)
pressure_index = cache.format_pressure_index(pressure_data)

# Update cache & history
cache.update_cache(current_data)
```

---

## Handling Missing Data

### **Before 4 Readings (Most Stable):**
```python
stable_data = cache.calculate_most_stable()
if stable_data is None:
    display = "Insufficient data (need 4+ readings)"
else:
    display = cache.format_most_stable(stable_data)
```

### **No Previous Data (Trends):**
```python
trends = cache.calculate_trends(current_data)
if not trends.get('has_previous_data'):
    trend_direction = "No previous data"
else:
    trend_direction = cache.format_trend_direction(trends)
```

---

## Color Coding (Optional Enhancement)

### **Regional Pressure Severity:**
```python
pressure_data = cache.calculate_pressure_index(current_data)

if pressure_data['severity'] == "High strain":
    color_class = "text-red-600"
    icon = "🔴"
elif pressure_data['severity'] == "Moderate strain":
    color_class = "text-orange-600"
    icon = "🟠"
else:
    color_class = "text-green-600"
    icon = "🟢"

display = f"{icon} {pressure_data['percentage']}% hospitals over 2h"
```

---

## Testing Your Integration

### **Test Script:**

```python
from trend_cache_system import HospitalTrendCache
import json

# Initialize
cache = HospitalTrendCache("test_cache.json", "test_history.json")

# Simulate 4 polls with changing data
polls = [
    {"Altnagelvin Area ED": 320, "Ulster ED": 259, "Daisy Hill ED": 85},
    {"Altnagelvin Area ED": 317, "Ulster ED": 238, "Daisy Hill ED": 86},
    {"Altnagelvin Area ED": 315, "Ulster ED": 240, "Daisy Hill ED": 87},
    {"Altnagelvin Area ED": 319, "Ulster ED": 241, "Daisy Hill ED": 86},
]

for i, poll in enumerate(polls, 1):
    print(f"\n--- Poll {i} ---")
    
    # Calculate stats
    trends = cache.calculate_trends(poll)
    stable = cache.calculate_most_stable()
    pressure = cache.calculate_pressure_index(poll, threshold=120)
    
    # Display
    print("Trend Direction:", cache.format_trend_direction(trends))
    print("Fastest Improvement:", cache.format_fastest_improvement(trends))
    print("Average:", sum(poll.values()) // len(poll), "m")
    print("Most Stable:", cache.format_most_stable(stable))
    print("Pressure:", cache.format_pressure_index(pressure))
    
    # Update for next poll
    cache.update_cache(poll)
```

---

## Summary

### ✅ **All Stats Implemented:**
1. 📈 Trend Direction
2. 🕐 Average Wait
3. ⚡ Fastest Improvement
4. 🏥 Most Stable Hospital
5. 📊 Regional Pressure Index

### ✅ **Files Updated:**
- `dashboard.html` - All 5 stats with placeholders replaced
- `trend_cache_system.py` - Complete calculation logic
- Branding centered and enlarged in footer

### ✅ **Data Management:**
- `hospital_wait_cache.json` - Stores previous poll
- `hospital_wait_history.json` - Stores rolling history (6 readings)
- Auto-saves after each update

### 🔜 **Next:**
- Dark theme implementation (`data-theme="dark"`)
- Waiting for your dark theme image!

---

**Your dashboard now has all 5 intelligent, data-driven stats!** 🎉
