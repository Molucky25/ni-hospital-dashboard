# Dashboard Integration Setup Guide 🚀

## What's New

Your `app_with_dashboard.py` now:
- ✅ Sends text updates (your existing functionality)
- ✅ **Generates dashboard images** with all 5 stats
- ✅ **Posts dashboard images** to Telegram
- ✅ **Auto-detects theme** (dark 6PM-6AM, light 6AM-6PM)
- ✅ **Tracks trends** using the cache system
- ✅ Everything runs in one script!

---

## Quick Start

### **1. Install Dependencies**

```bash
# Install Playwright
pip install playwright beautifulsoup4 requests

# Install browser (one-time setup)
python -m playwright install chromium
```

### **2. Files Required**

Make sure these files are in the same directory:
- ✅ `app_with_dashboard.py` (main script - **NEW**)
- ✅ `dashboard.html` (template)
- ✅ `trend_cache_system.py` (stats calculator)

### **3. Run It!**

```bash
python app_with_dashboard.py
```

That's it! Every 5 minutes it will:
1. Check for hospital data changes
2. Send text update to Telegram
3. Generate dashboard image (light/dark based on time)
4. Send dashboard image to Telegram
5. Update trend cache

---

## Configuration

### **Enable/Disable Dashboard**

In `app_with_dashboard.py`:
```python
GENERATE_DASHBOARD = True   # Set to False to disable
```

### **Change Poll Interval**

```python
POLL_SECONDS = 300  # 5 minutes
```

### **Force Send Every Time (Testing)**

```python
FORCE_SEND = True  # Bypass change detection
```

---

## How It Works

### **Text Update (Your Existing Logic)**
```
🚑 NI Emergency Department Wait Times — Live Update

🕛 Updated: 10:30 AM, Fri 17 Oct 2025

📊 What's Changed
📉 Ulster ED: 259 m → 238 m (decreased by 21 m)

📊 Average over past 4 hours

Hospitals:
🔴 317 m — Altnagelvin Area ED
🔴 281 m — Royal Victoria ED
🟠 238 m — Ulster ED
...
```

### **Dashboard Image (NEW!)**
Visual dashboard with:
- All 10 hospitals with severity colors
- 5 intelligent stats:
  - 📈 Trend Direction
  - 🕐 Average Wait
  - ⚡ Fastest Improvement
  - 🏥 Most Stable Hospital
  - 📊 Regional Pressure Index
- Auto theme (dark at night, light during day)

---

## Theme Auto-Detection

The dashboard automatically switches themes based on time:

| Time | Theme | Why |
|------|-------|-----|
| **6AM - 6PM** | Light | Better visibility in daylight |
| **6PM - 6AM** | Dark | Easier on eyes at night |

**Example:**
```python
# 10:00 AM → Light theme
# 8:00 PM  → Dark theme
```

---

## Trend Stats Explained

### **1. Trend Direction**
```
"6 hospitals improving | 4 worsening"
```
- Compares current vs previous poll
- Improving = wait time decreased
- Worsening = wait time increased

### **2. Fastest Improvement**
```
"Ulster ED ↓ 21m"
```
- Hospital with biggest wait time decrease
- Shows hospital name + minutes dropped

### **3. Most Stable Hospital**
```
"Daisy Hill — ±7m (past 4h)"
```
- Hospital with most consistent wait times
- Calculated using standard deviation
- Requires 4+ historical readings

### **4. Regional Pressure Index**
```
"72% hospitals over 2h"
```
- Percentage of hospitals with 120+ min waits
- Quick system health indicator

### **5. Average Wait**
```
"187m"
```
- Mean of all current wait times

---

## File Structure

```
hospital wait/
├── app_with_dashboard.py     ← RUN THIS
├── dashboard.html             ← Dashboard template
├── trend_cache_system.py      ← Stats calculator
├── hospital_wait_cache.json   ← Auto-generated (trends)
├── hospital_wait_history.json ← Auto-generated (stability)
├── dashboard_current.png      ← Auto-generated (latest image)
└── state.json                 ← Auto-generated (change tracking)
```

---

## Output Example

### **Console Output:**
```
[2025-10-17 10:00:00 BST] Starting NI ED wait monitor with dashboard generation
  Poll interval: 300s
  FORCE_SEND: OFF
  Dashboard: ENABLED
  Theme: Auto-detect (6PM-6AM = dark, 6AM-6PM = light)

[2025-10-17 10:00:05 BST] Text update sent to Telegram. Rows: 10 | Changes: 2
[2025-10-17 10:00:05 BST] Generating dashboard (theme: light)...
[2025-10-17 10:00:07 BST] Dashboard generated: dashboard_current.png
[2025-10-17 10:00:08 BST] Dashboard image sent to Telegram

[2025-10-17 10:05:00 BST] No change detected. Skipping send.
```

---

## Telegram Output

Every update sends **TWO messages**:

### **Message 1: Text Update**
```
🚑 NI Emergency Department Wait Times — Live Update

🕛 Updated: 10:00 AM, Fri 17 Oct 2025

📊 What's Changed
📉 Ulster ED: 259 m → 238 m (decreased by 21 m)
📈 Mater ED: 200 m → 220 m (increased by 20 m)

📊 Average over past 4 hours

Hospitals:
🔴 317 m — Altnagelvin Area ED
🔴 281 m — Royal Victoria ED
...
```

### **Message 2: Dashboard Image**
![Dashboard with all stats and visual representation]

---

## Troubleshooting

### **Error: "Dashboard template not found"**
```
Solution: Make sure dashboard.html is in the same folder as app_with_dashboard.py
```

### **Error: "ModuleNotFoundError: No module named 'playwright'"**
```bash
Solution: pip install playwright
          python -m playwright install chromium
```

### **Error: "ModuleNotFoundError: No module named 'trend_cache_system'"**
```
Solution: Make sure trend_cache_system.py is in the same folder
```

### **Dashboard not sending but text works**
```python
Check: GENERATE_DASHBOARD = True in app_with_dashboard.py
```

### **Want to test immediately?**
```python
Set: FORCE_SEND = True  # Sends every poll regardless of changes
```

---

## Comparing Old vs New

### **Your Old `app.py`:**
- ✅ Monitors hospital wait times
- ✅ Sends text updates
- ✅ Detects changes
- ❌ No dashboard images
- ❌ No trend stats

### **New `app_with_dashboard.py`:**
- ✅ Monitors hospital wait times
- ✅ Sends text updates
- ✅ Detects changes
- ✅ **Generates dashboard images**
- ✅ **Sends dashboard images**
- ✅ **5 intelligent stats**
- ✅ **Auto theme switching**
- ✅ **Trend tracking**

---

## Advanced Configuration

### **Change Dashboard Resolution**
In `generate_dashboard_image()`:
```python
viewport={'width': 1280, 'height': 720}  # Default
viewport={'width': 1920, 'height': 1080}  # HD
```

### **Force Specific Theme**
```python
# In run_once_async()
theme = 'dark'  # Always dark
theme = 'light'  # Always light
theme = get_auto_theme()  # Auto-detect (default)
```

### **Change Dashboard Caption**
```python
telegram_send_photo(
    dashboard_path,
    caption="🚑 <b>Your Custom Caption Here</b>"
)
```

### **Generate Dashboard Less Frequently**
```python
# Add counter at top of file
dashboard_counter = 0
DASHBOARD_EVERY_N = 6  # Generate every 6th poll (30 min if polling every 5 min)

# In run_once_async(), after text update:
global dashboard_counter
dashboard_counter += 1
if dashboard_counter >= DASHBOARD_EVERY_N:
    dashboard_counter = 0
    # Generate dashboard here
```

---

## Migration from app.py

**Option 1: Test New Version (Recommended)**
```bash
# Keep your old app.py running
# Test the new one separately
python app_with_dashboard.py
```

**Option 2: Replace Old Version**
```bash
# Stop old app.py (Ctrl+C)
# Rename for backup
mv app.py app_old.py
mv app_with_dashboard.py app.py
# Run new version
python app.py
```

---

## Summary

### **To Run:**
```bash
python app_with_dashboard.py
```

### **What Happens:**
1. Polls NI Direct every 5 minutes
2. Detects changes in wait times
3. Sends text update to Telegram
4. Generates dashboard image (auto theme)
5. Sends dashboard image to Telegram
6. Updates trend cache
7. Repeat

### **Result:**
Your Telegram channel gets:
- ✅ Text updates with changes
- ✅ Beautiful dashboard images
- ✅ Intelligent trend statistics
- ✅ Auto day/night themes

---

**You're all set! Run the script and watch it post both text and images to your Telegram channel!** 🎉
