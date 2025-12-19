# Hospital Wait Times - Trend Tracking System

## Overview

The dashboard now includes automatic trend tracking that shows:
1. **24-hour sparkline graph** - Visual trend of average wait times
2. **Hospital trend indicators** - "↑ rising" or "↓ improving" badges
3. **Logo branding** - Your NIERV logo in corner + subtle watermark

## How Trend Tracking Works

### Data Storage

All trend data is stored in `hospital_wait_trends.jsonl` (JSON Lines format):

```json
{"timestamp": "2025-10-17T00:15:00+00:00", "avg_wait": 187, "hospitals": {"Altnagelvin...": 317, "Royal Victoria...": 281, ...}}
{"timestamp": "2025-10-17T00:20:00+00:00", "avg_wait": 189, "hospitals": {...}}
```

Each line represents a snapshot containing:
- **timestamp**: When the data was captured (ISO 8601 format)
- **avg_wait**: Average wait time across all hospitals
- **hospitals**: Dictionary mapping hospital names to their wait times

### Automatic Data Collection

Every time `generate_dashboard_image()` is called:
1. Current data is saved as a new snapshot
2. Historical data from last 24 hours is loaded
3. Trends are calculated based on historical comparison
4. Old data (>7 days) is automatically cleaned up

### Sparkline Graph (24-Hour Trend)

**What it shows:** Average wait time trend over the past 24 hours

**How it's calculated:**
1. Groups historical snapshots by hour
2. Calculates average wait time for each hour
3. Displays up to 24 data points (hourly intervals)

**Visual indicators:**
- **Red line**: Average wait times are rising (last > first)
- **Green line**: Average wait times are falling (last < first)
- Small dots mark each hourly data point

**Example:**
```
📈 24-Hour Average Trend
↑ +23m over 24h   [shows red sparkline going up]
```

### Hospital Trend Indicators

**What they show:** Whether individual hospitals are getting worse or better

**Calculation method:**
1. Takes current wait time for a hospital
2. Compares with average from 4-8 hours ago (baseline)
3. If difference is significant (>15 minutes), shows indicator

**Indicators:**
- **↑ rising** (red) - Wait time increased by more than 15 minutes
- **↓ improving** (green) - Wait time decreased by more than 15 minutes
- **No indicator** - Change is less than 15 minutes (not significant)

**Example in dashboard:**
```
🔴 317 m — Altnagelvin Area ED ↑ rising
🟠 152 m — Causeway ED ↓ improving
```

### Logo Integration

**Logo locations:**
1. **Top-right corner**: 80x80px rounded logo
2. **Background watermark**: Large, centered, 5% opacity

**Logo path:** `C:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\NIERV Logo.jpg`

Change the path in `generate_dashboard_image.py`:
```python
LOGO_PATH = r"your\path\to\logo.jpg"
```

## Timeline for Trend Features

### First Run (No Historical Data)
- ✅ Logo displays
- ✅ Current wait times shown
- ❌ No sparkline (hidden - need 2+ snapshots)
- ❌ No trend indicators (hidden - need history)
- ✅ Snapshot saved to trend file

### After 2-3 Hours (Some History)
- ✅ Logo displays
- ✅ Current wait times shown
- ✅ Sparkline appears (2-3 data points)
- ❌ No trend indicators (need 4+ hours for baseline)

### After 4-8 Hours (Baseline Established)
- ✅ Logo displays
- ✅ Current wait times shown
- ✅ Sparkline with 4-8 data points
- ✅ Trend indicators start appearing (if changes >15min)

### After 24+ Hours (Full History)
- ✅ Logo displays
- ✅ Current wait times shown
- ✅ Full 24-hour sparkline (24 data points)
- ✅ Reliable trend indicators

## Configuration

### Trend Sensitivity

Change how sensitive trend indicators are by editing `calculate_hospital_trends()` in `generate_dashboard_image.py`:

```python
# Only mark as trend if change is significant (>15 minutes)
if diff > 15:      # Change this threshold
    trends[hospital] = "up"
elif diff < -15:   # Change this threshold
    trends[hospital] = "down"
```

**Recommendations:**
- **15 minutes** (default): Balanced, shows meaningful changes
- **30 minutes**: Only very significant changes
- **10 minutes**: More sensitive, shows smaller fluctuations

### Data Retention

Change how long historical data is kept by editing `save_historical_snapshot()`:

```python
# Clean up old data (keep last 7 days)
cutoff = datetime.now(timezone.utc) - timedelta(days=7)  # Change days here
```

### Sparkline Hours

Change how many hours of data the sparkline shows by editing the function call:

```python
historical = load_historical_data(24)  # Change from 24 to other value
```

## Manual Trend Data Management

### View Current Trend Data

```python
import json

with open("hospital_wait_trends.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        print(f"Time: {data['timestamp']}, Avg: {data['avg_wait']}m")
```

### Clear Trend History (Start Fresh)

```python
from pathlib import Path

# Delete the trend file
Path("hospital_wait_trends.jsonl").unlink(missing_ok=True)
print("Trend history cleared")
```

### Export Trend Data to CSV

```python
import json
import csv

with open("hospital_wait_trends.jsonl", "r") as f:
    with open("trends.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Average Wait", "Hospital Count"])
        
        for line in f:
            data = json.loads(line)
            writer.writerow([
                data["timestamp"],
                data["avg_wait"],
                len(data["hospitals"])
            ])

print("Exported to trends.csv")
```

## Integration with Your Monitor

### Update app_with_images.py

The integrated monitoring script automatically:
1. Fetches data every 5 minutes
2. Saves snapshots to trend file
3. Generates images with all trend features
4. Posts to Telegram

### Update app.py (Text-Only)

If using the text-only monitor, you can still collect trend data:

```python
from generate_dashboard_image import save_historical_snapshot

# After fetching rows
save_historical_snapshot(rows)
```

This builds trend data even if you're not generating images yet.

## Troubleshooting

### Sparkline Not Showing

**Cause:** Not enough historical data (need at least 2 snapshots)

**Solution:** 
- Let the monitor run for a few hours
- Check if `hospital_wait_trends.jsonl` exists and has multiple lines
- Verify snapshots are being saved: `len(open('hospital_wait_trends.jsonl').readlines())`

### Trend Indicators Not Appearing

**Cause 1:** Not enough history (need 4+ hours for baseline)
**Solution:** Wait longer

**Cause 2:** Changes are too small (<15 minutes)
**Solution:** Lower the threshold in code

**Cause 3:** No historical data for that specific hospital
**Solution:** Hospital may be new or had gaps in reporting

### Logo Not Displaying

**Cause:** Incorrect file path

**Solution:**
1. Verify logo file exists: `Path(LOGO_PATH).exists()`
2. Check path uses raw string: `r"C:\Users\..."`
3. Use absolute path, not relative
4. Ensure PNG or JPG format

### File Growing Too Large

**Cause:** Auto-cleanup not working

**Solution:**
- Check if temp file creation has permission issues
- Manually delete old entries
- Reduce retention from 7 days to fewer

## Data Format Examples

### Full Dashboard Data Structure

```python
{
    "updateTime": "12:00 am, Fri 17 Oct 2025",
    "longestWait": "Altnagelvin — <span...>317m 🔴</span>",
    "avgWait": "<span...>187m 🟠</span>",
    "hospitalCount": 10,
    "hospitals": [
        {
            "emoji": "🔴",
            "wait": 317,
            "name": "Altnagelvin Area ED",
            "colorClass": "text-red-600",
            "trend": "up"  # or "down" or None
        },
        # ... more hospitals
    ],
    "trendData": [165, 170, 175, 180, 185, 187],  # Hourly averages
    "logoPath": "C:\\Users\\...\\NIERV Logo.jpg"
}
```

## Best Practices

1. **Run Monitor Consistently**: Trend data requires regular updates
2. **Don't Delete Trend File**: Unless you want to start fresh
3. **Monitor File Size**: Should stay under 1MB with auto-cleanup
4. **Back Up Trend Data**: If you want to keep long-term statistics
5. **Test Logo Path**: Run test script before going live

## Testing

Run the test script to verify all features:

```bash
python test_dashboard_features.py
```

This will:
- Generate a test image with your logo
- Create trend data file
- Show you what to expect

Run it multiple times to see trend features develop!

## Future Enhancements

Possible additions:
- Weekly/monthly trend graphs
- Peak hours detection
- Hospital comparison charts
- Predictive trend indicators
- Alert thresholds based on trends
- Export historical reports

---

**Questions?** Check the main README or contact via t.me/NIIncidentAlerts
