# Automatic Trend Calculations Guide ✅

## YES - Calculations Happen Automatically Every Update! 🔄

### **How It Works:**

Every time your Python script polls for new hospital data (e.g., every 5-15 minutes), the trend calculations will automatically run and update the dashboard.

---

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Python Script Polls NI Direct (every X minutes)    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Get Current Hospital Wait Times                     │
│     - Altnagelvin: 317m                                 │
│     - Royal Victoria: 281m                              │
│     - ... (all 10 hospitals)                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Calculate Trend Summaries (AUTOMATIC)               │
│     ✓ Hourly change: Compare to last poll               │
│     ✓ Regional avg: Calculate from all hospitals       │
│     ✓ Daily comparison: Compare to 24h ago             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. Generate Dashboard HTML with New Data               │
│     - Populate hospital table                           │
│     - Update stat cards                                 │
│     - Update trend summaries (top-right)                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. Render Dashboard Image                              │
│     - Playwright/Puppeteer captures screenshot          │
│     - All trends visible and up-to-date                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  6. Post to Social Media                                │
│     - Telegram, Facebook, Twitter                       │
│     - Fresh data with live trends                       │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation in Your Python Script

### **Step 1: Store Historical Data**

You need to track previous values to calculate trends:

```python
import json
from datetime import datetime, timedelta
from pathlib import Path

# File to store historical data
HISTORY_FILE = Path("dashboard_history.json")

def load_history():
    """Load historical dashboard data"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {
        'polls': [],  # List of {timestamp, avg_wait, hospitals}
        'daily_averages': {}  # {date: avg_wait}
    }

def save_history(history):
    """Save historical data"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)
```

---

### **Step 2: Calculate Trends Automatically**

```python
def calculate_trend_summaries(current_data, history):
    """
    Calculate all trend summaries automatically
    
    Args:
        current_data: {
            'timestamp': '2025-10-17T02:00:00',
            'avg_wait': 187,
            'hospitals': [...]
        }
        history: Historical data from load_history()
    
    Returns:
        {
            'hourly_trend': {...},
            'regional_trend': {...},
            'daily_comparison': {...}
        }
    """
    trends = {}
    
    # 1. HOURLY TREND (compare to last poll)
    if len(history['polls']) > 0:
        last_poll = history['polls'][-1]
        prev_avg = last_poll['avg_wait']
        current_avg = current_data['avg_wait']
        
        change_pct = ((current_avg - prev_avg) / prev_avg) * 100
        
        if abs(change_pct) >= 1:  # Only show if ≥1% change
            direction = "↓" if change_pct < 0 else "↑"
            color = "text-green-600" if change_pct < 0 else "text-red-600"
            
            trends['hourly_trend'] = {
                'text': f'{direction} {abs(change_pct):.0f}% since last hour',
                'color': color,
                'value': change_pct
            }
    
    # 2. REGIONAL AVERAGE (compare to yesterday)
    today = datetime.now().date().isoformat()
    yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
    
    if yesterday in history['daily_averages']:
        yesterday_avg = history['daily_averages'][yesterday]
        current_avg = current_data['avg_wait']
        diff = current_avg - yesterday_avg
        
        direction = "↑" if diff > 0 else "↓"
        color = "text-red-500" if diff > 0 else "text-green-500"
        
        trends['regional_trend'] = {
            'current': current_avg,
            'yesterday': yesterday_avg,
            'comparison': f'({direction} from {yesterday_avg}m)',
            'color': color
        }
    
    # 3. DAILY COMPARISON (absolute difference)
    if yesterday in history['daily_averages']:
        yesterday_avg = history['daily_averages'][yesterday]
        current_avg = current_data['avg_wait']
        diff = current_avg - yesterday_avg
        sign = "+" if diff > 0 else ""
        
        trends['daily_comparison'] = {
            'text': f'{sign}{diff}m vs yesterday',
            'diff': diff
        }
    
    return trends
```

---

### **Step 3: Update History After Each Poll**

```python
def update_history(current_data, history):
    """Add current poll to history"""
    
    # Add to polls list
    history['polls'].append({
        'timestamp': current_data['timestamp'],
        'avg_wait': current_data['avg_wait'],
        'hospitals': current_data['hospitals']
    })
    
    # Keep only last 48 polls (24 hours if polling every 30 min)
    if len(history['polls']) > 48:
        history['polls'] = history['polls'][-48:]
    
    # Update daily average
    today = datetime.now().date().isoformat()
    
    # Calculate today's average from all polls today
    today_polls = [
        p for p in history['polls']
        if p['timestamp'].startswith(today)
    ]
    
    if today_polls:
        today_avg = sum(p['avg_wait'] for p in today_polls) / len(today_polls)
        history['daily_averages'][today] = int(today_avg)
    
    # Keep only last 7 days of daily averages
    cutoff_date = (datetime.now().date() - timedelta(days=7)).isoformat()
    history['daily_averages'] = {
        date: avg
        for date, avg in history['daily_averages'].items()
        if date >= cutoff_date
    }
    
    return history
```

---

### **Step 4: Integrate into Your Main Script**

```python
def generate_dashboard():
    """Main function - runs every poll"""
    
    # 1. Fetch current hospital data
    current_data = fetch_hospital_data()  # Your existing function
    
    # 2. Load historical data
    history = load_history()
    
    # 3. Calculate trends AUTOMATICALLY
    trend_summaries = calculate_trend_summaries(current_data, history)
    
    # 4. Update history for next time
    history = update_history(current_data, history)
    save_history(history)
    
    # 5. Generate dashboard with trends
    dashboard_data = {
        'updateTime': current_data['timestamp'],
        'hospitals': current_data['hospitals'],
        'avgWait': current_data['avg_wait'],
        'trendSummaries': trend_summaries,  # ← NEW!
        # ... other data
    }
    
    # 6. Render dashboard
    render_dashboard_image(dashboard_data)
    
    # 7. Post to social media
    post_to_social_media('dashboard.png')
```

---

## JavaScript Updates (Already in dashboard.html)

The JavaScript will automatically use the trend data:

```javascript
function updateDashboard(data) {
    // ... existing code ...
    
    // Update trend summaries (AUTOMATIC)
    if (data.trendSummaries) {
        // Hourly trend
        if (data.trendSummaries.hourly_trend) {
            document.getElementById('hourly-trend').innerHTML = 
                `<span class="${data.trendSummaries.hourly_trend.color}">
                    ${data.trendSummaries.hourly_trend.text}
                </span>`;
        }
        
        // Regional average
        if (data.trendSummaries.regional_trend) {
            document.getElementById('regional-trend').innerHTML = 
                `Regional avg: <span class="font-bold">${data.trendSummaries.regional_trend.current}m</span> 
                <span class="${data.trendSummaries.regional_trend.color}">
                    ${data.trendSummaries.regional_trend.comparison}
                </span>`;
        }
        
        // Daily comparison
        if (data.trendSummaries.daily_comparison) {
            document.getElementById('daily-comparison').innerHTML = 
                `<span class="font-bold">${data.trendSummaries.daily_comparison.text}</span>`;
        }
    }
}
```

---

## Example Timeline

### **First Poll (10:00 AM):**
- No trends shown (no history yet)
- Saves current data to history

### **Second Poll (10:30 AM):**
- ✅ Hourly trend: "↑ 5% since last hour" (compared to 10:00 AM)
- ❌ Regional trend: Not shown (no yesterday data yet)
- ❌ Daily comparison: Not shown (no yesterday data yet)

### **After 24 Hours:**
- ✅ Hourly trend: "↓ 3% since last hour"
- ✅ Regional trend: "Regional avg: 187m (↑ from 175m)"
- ✅ Daily comparison: "+12m vs yesterday"

---

## Data Storage Example

**dashboard_history.json:**
```json
{
  "polls": [
    {
      "timestamp": "2025-10-17T10:00:00",
      "avg_wait": 180,
      "hospitals": [...]
    },
    {
      "timestamp": "2025-10-17T10:30:00",
      "avg_wait": 189,
      "hospitals": [...]
    }
  ],
  "daily_averages": {
    "2025-10-16": 175,
    "2025-10-17": 187
  }
}
```

---

## Summary

### ✅ **YES - Fully Automatic!**

1. **Every poll** → Trends calculated
2. **No manual work** → All automatic
3. **History tracked** → JSON file
4. **Dashboard updated** → Fresh trends every time
5. **Social media** → Always current

### **You Just Need To:**
1. Add the calculation functions to your Python script
2. Call `calculate_trend_summaries()` before rendering
3. Pass `trendSummaries` to the dashboard data
4. Done! Trends update automatically forever

---

## Fixes Applied

### ✅ **Trend Summary Size Increased**
- **Before:** `text-xs` (12px)
- **After:** `text-sm` (14px)
- **Result:** 17% larger, much more readable

### ✅ **10th Row Added (Daisy Hill)**
- All 10 hospitals now visible
- Yellow circle + green down arrow

### ✅ **Stat Cards Visible**
- Changed `overflow: hidden` → `overflow: visible`
- All 5 cards now show properly

---

**Your dashboard will now automatically calculate and display live trends with every update!** 🎉
