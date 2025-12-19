# Daily Statistics System - Complete Guide

## 📊 **Overview**

Comprehensive daily statistics system that tracks A&E wait times throughout the day and sends formatted updates at scheduled times.

---

## ⏰ **Update Schedule**

Daily statistics are sent **8 times per day** at:

| Time | 24h Format | Description |
|------|------------|-------------|
| 12:00 AM | 00:00 | Midnight update |
| 3:00 AM | 03:00 | Early morning |
| 6:00 AM | 06:00 | Morning shift start |
| 9:00 AM | 09:00 | Mid-morning |
| 12:00 PM | 12:00 | Noon update |
| 3:00 PM | 15:00 | Afternoon |
| 6:00 PM | 18:00 | Evening peak |
| 9:00 PM | 21:00 | Night update |

**Total**: 8 updates per day, every 3 hours

---

## 📈 **Statistics Collected**

### **1. Daily Regional Average Wait**

**What**: Average wait time across all NI hospitals

**Format**: `"NI A&E Average Wait: 162m (↓ 18m vs yesterday)"`

**Purpose**: 
- Single most important headline metric
- Shows overall system health
- Compares with yesterday's average

**Example**:
```
NI A&E Average Wait: 162m (↓ 18m vs yesterday)
NI A&E Average Wait: 185m (↑ 12m vs yesterday)
NI A&E Average Wait: 162m (→ unchanged vs yesterday)
```

---

### **2. Regional Pressure Index**

**What**: Percentage of hospitals with wait times ≥ 2 hours (120 minutes)

**Format**: `"68% of hospitals currently over 2 hours — moderate strain"`

**Pressure Levels**:
- **0-29%**: Low strain
- **30-49%**: Moderate strain
- **50-74%**: High strain
- **75-100%**: Critical strain

**Example**:
```
🔹 Pressure: 68% of hospitals currently over 2 hours — moderate strain.
🔹 Pressure: 90% of hospitals currently over 2 hours — critical strain.
🔹 Pressure: 20% of hospitals currently over 2 hours — low strain.
```

---

### **3. Longest Recorded Wait**

**What**: Highest wait time recorded today with hospital name and time

**Format**: `"Antrim ED — 434m at 17:00"`

**Purpose**:
- Shows peak pressure point
- Gives a "face" to the day's crisis
- Drives engagement and emotional reaction

**Example**:
```
🔹 Longest recorded wait: Antrim ED — 434m at 17:00
🔹 Longest recorded wait: Royal Victoria ED — 389m at 14:23
```

---

### **4. Top 3 Longest Waits**

**What**: Current top 3 hospitals with longest wait times

**Format**: Medal emoji + hospital name + wait time

**Purpose**:
- Visual, competitive, easy to understand
- Great for social media
- Shows current hotspots

**Example**:
```
Top 3 Longest Waits:
🥇 Antrim — 434m
🥈 Royal — 305m
🥉 Craigavon — 284m
```

---

### **5. Fastest Improvement**

**What**: Hospital with biggest wait time decrease since earlier today

**Format**: `"Ulster ED ↓ 36m since earlier"`

**Purpose**:
- Positive counterweight to red numbers
- Humanizes progress
- Encourages looking for bright spots

**Example**:
```
🔹 Fastest improvement: Ulster ED ↓ 36m since earlier
🔹 Fastest improvement: Mater ED ↓ 42m since earlier
```

---

### **6. Daily Peak Hour**

**What**: Hour with highest regional average wait time today

**Format**: `"Peak congestion at 6 PM, regional avg 224m"`

**Purpose**:
- Shows when pressure builds
- Adds rhythm to reporting
- Helps predict future patterns

**Example**:
```
🔹 Peak congestion: 6 PM, regional avg 224m
🔹 Peak congestion: 2 PM, regional avg 198m
🔹 Peak congestion: 9 AM, regional avg 176m
```

---

### **7. Hours Above Critical Threshold**

**What**: Number of hours today where any hospital had wait ≥ 240 minutes

**Format**: `"3 hours ≥ 240m today"`

**Purpose**:
- Time-based severity indicator
- Easy for public to grasp
- Shows duration of crisis

**Example**:
```
🔹 Red zone duration: 3 hours ≥ 240m today
🔹 Red zone duration: 0 hours ≥ 240m today
🔹 Red zone duration: 8 hours ≥ 240m today
```

---

## 📱 **Message Format**

### **Complete Example**

```
📊 Still Waiting NI — 18:00 Update

NI A&E Average Wait: 162m (↓ 18m vs yesterday)
🔹 Pressure: 68% of hospitals currently over 2 hours — moderate strain.
🔹 Longest recorded wait: Antrim ED — 434m at 17:00
🔹 Fastest improvement: Ulster ED ↓ 36m since earlier
🔹 Peak congestion: 6 PM, regional avg 224m
🔹 Red zone duration: 3 hours ≥ 240m today

Top 3 Longest Waits:
🥇 Antrim — 434m
🥈 Royal — 305m
🥉 Craigavon — 284m
```

---

## 🗂️ **Data Storage**

### **File 1: `daily_stats.json`**

**Purpose**: Stores all readings and statistics for current day

**Structure**:
```json
{
  "date": "2025-10-18",
  "readings": [
    {
      "timestamp": "2025-10-18T06:15:00",
      "hour": 6,
      "avg_wait": 145,
      "hospitals": {
        "Antrim AreaED": 234,
        "Royal Victoria ED": 189,
        ...
      },
      "longest": {
        "hospital": "Antrim AreaED",
        "wait": 234
      },
      "has_critical": false
    },
    ...
  ],
  "peak_hour": 18,
  "peak_avg": 224,
  "longest_wait": {
    "hospital": "Antrim ED",
    "wait": 434,
    "time": "17:00"
  },
  "hours_critical": 3,
  "yesterday_avg": 180
}
```

**Retention**: Resets daily at midnight, saves yesterday's average for comparison

---

### **File 2: `daily_update_times.json`**

**Purpose**: Tracks which update times have been sent to prevent duplicates

**Structure**:
```json
{
  "2025-10-18_06": "2025-10-18T06:00:12",
  "2025-10-18_09": "2025-10-18T09:00:08",
  "2025-10-18_12": "2025-10-18T12:00:15",
  ...
}
```

**Key format**: `YYYY-MM-DD_HH` (date + hour)

**Retention**: Grows indefinitely (can be cleaned periodically)

---

## 🔄 **Data Flow**

```
Every 5 minutes:
├─ Fetch hospital data
├─ Send regular update (if changed)
├─ Generate dashboard
├─ Record reading for daily stats
│  ├─ Calculate average wait
│  ├─ Find longest wait
│  ├─ Check for critical hospitals
│  ├─ Update peak hour if higher
│  └─ Save to daily_stats.json
│
└─ Check if update time (00, 03, 06, 09, 12, 15, 18, 21)
   ├─ If yes and not sent yet:
   │  ├─ Calculate all daily stats
   │  ├─ Format message
   │  ├─ Send to Telegram
   │  └─ Mark hour as sent
   └─ If no or already sent: skip
```

---

## ⏰ **Update Timing Logic**

### **How It Works**

1. **Every 5 minutes**, script checks current hour
2. **If current hour** is in `[0, 3, 6, 9, 12, 15, 18, 21]`:
   - Check if update already sent for this hour today
   - If not sent: Calculate stats, send message, mark as sent
   - If sent: Skip
3. **At midnight**, daily data resets for new day

### **Example Timeline**

```
05:55 - Regular poll, no daily update (not update hour)
06:00 - Regular poll, SEND DAILY UPDATE (06:00 hour)
06:05 - Regular poll, no daily update (already sent for 06:00)
06:10 - Regular poll, no daily update (already sent for 06:00)
...
08:55 - Regular poll, no daily update (not update hour)
09:00 - Regular poll, SEND DAILY UPDATE (09:00 hour)
09:05 - Regular poll, no daily update (already sent for 09:00)
```

---

## 📊 **Statistics Calculation Details**

### **Daily Average**

```python
# Sum all current hospital wait times
total = sum(hospitals_dict.values())
# Divide by number of hospitals
current_avg = total / len(hospitals_dict)
```

---

### **Average Change vs Yesterday**

```python
# Compare with yesterday's average (saved at midnight)
if yesterday_avg:
    avg_change = current_avg - yesterday_avg
    # Positive = worse, Negative = better
```

---

### **Regional Pressure**

```python
# Count hospitals with wait ≥ 120 minutes
hospitals_over_2h = sum(1 for wait in hospitals_dict.values() if wait >= 120)
# Calculate percentage
pressure_pct = (hospitals_over_2h / total_hospitals) * 100
```

---

### **Longest Wait**

```python
# Track maximum wait time throughout the day
for each reading:
    if reading.longest_wait > daily_max:
        daily_max = reading.longest_wait
        record_time = reading.timestamp
```

---

### **Peak Hour**

```python
# Track hour with highest average wait
for each reading:
    if reading.avg_wait > peak_avg:
        peak_avg = reading.avg_wait
        peak_hour = reading.hour
```

---

### **Critical Hours**

```python
# Count unique hours where any hospital ≥ 240m
critical_hours = set()
for reading in daily_readings:
    if any(wait >= 240 for wait in reading.hospitals.values()):
        critical_hours.add(reading.hour)
hours_critical = len(critical_hours)
```

---

### **Fastest Improvement**

```python
# Compare current with first reading of day
for hospital in current_hospitals:
    change = current_wait - first_reading_wait
    if change < 0:  # Improvement
        improvements.append((hospital, abs(change)))
fastest = max(improvements, key=lambda x: x[1])
```

---

## 🎯 **Benefits**

### **1. Comprehensive Daily View**
✅ Tracks all key metrics throughout the day  
✅ Shows trends and patterns  
✅ Provides context for current situation  

### **2. Scheduled Updates**
✅ Predictable timing (every 3 hours)  
✅ No spam (only 8 messages per day)  
✅ Covers all shifts (24-hour coverage)  

### **3. Rich Context**
✅ Compares with yesterday  
✅ Shows peak times  
✅ Highlights improvements  
✅ Tracks crisis duration  

### **4. Engaging Format**
✅ Medal emojis for top 3  
✅ Clear pressure indicators  
✅ Positive + negative metrics  
✅ Time-based context  

---

## 🔧 **Configuration**

### **Update Times**

To change update schedule, modify `daily_stats_system.py`:

```python
# Current: Every 3 hours
update_hours = [0, 3, 6, 9, 12, 15, 18, 21]

# Example: Every 6 hours
update_hours = [0, 6, 12, 18]

# Example: Business hours only
update_hours = [9, 12, 15, 18]
```

---

### **Critical Threshold**

To change critical threshold (currently 240m):

```python
# In daily_stats_system.py, line ~90
has_critical = any(wait >= 240 for wait in hospitals_dict.values())

# Change to 180m (3 hours)
has_critical = any(wait >= 180 for wait in hospitals_dict.values())
```

---

### **Pressure Levels**

To adjust pressure level thresholds:

```python
# Current thresholds
if pressure_pct >= 75:
    pressure_level = "critical strain"
elif pressure_pct >= 50:
    pressure_level = "high strain"
elif pressure_pct >= 30:
    pressure_level = "moderate strain"
else:
    pressure_level = "low strain"

# Adjust as needed
```

---

## 🧪 **Testing**

### **Manual Test**

To test daily update without waiting for scheduled time:

```python
# In Python console
from daily_stats_system import daily_stats_tracker

# Force an update
hospitals = {
    "Antrim AreaED": 293,
    "Royal Victoria ED": 205,
    ...
}

# Record some readings
for i in range(5):
    daily_stats_tracker.record_reading(hospitals)

# Calculate and format
stats = daily_stats_tracker.calculate_daily_stats(hospitals)
message = daily_stats_tracker.format_daily_update(stats)
print(message)
```

---

### **Verify Update Times**

Check `daily_update_times.json`:

```bash
cat daily_update_times.json
```

Should show entries like:
```json
{
  "2025-10-18_06": "2025-10-18T06:00:12",
  "2025-10-18_09": "2025-10-18T09:00:08"
}
```

---

## 📈 **Performance Impact**

### **Memory**

**Per reading**: ~500 bytes  
**Per day** (288 readings): ~144 KB  
**Impact**: Negligible

---

### **Disk I/O**

**Per poll** (every 5 min):
- Read: `daily_stats.json` + `daily_update_times.json` (~150 KB)
- Write: `daily_stats.json` (~150 KB)

**Per update** (8 times/day):
- Write: `daily_update_times.json` (~1 KB)

**Impact**: Minimal

---

### **Computation**

**Per poll**: <1ms (simple calculations)  
**Per update**: <5ms (format message)  
**Impact**: Negligible

---

## ✅ **Status: FULLY IMPLEMENTED**

Daily statistics system is now active:

✅ **8 scheduled updates per day** (every 3 hours)  
✅ **7 comprehensive statistics** tracked  
✅ **Formatted Telegram messages** with emojis  
✅ **Automatic daily reset** at midnight  
✅ **Duplicate prevention** (won't send twice)  
✅ **Yesterday comparison** for context  
✅ **Integrated with main app** (automatic)  

---

## 🚀 **Next Update**

The next daily update will be sent at the next scheduled hour:

**Update hours**: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00

**Console output**:
```
[2025-10-18 18:00:05] Sending daily statistics update...
[2025-10-18 18:00:07] Daily statistics update sent to Telegram
```

**Telegram message**: Full daily statistics with all 7 metrics! 📊

---

## 🎉 **Summary**

**What**: Comprehensive daily statistics system  
**When**: 8 times per day, every 3 hours  
**What's tracked**: 7 key metrics (average, pressure, longest, top 3, improvement, peak, critical hours)  
**Format**: Rich Telegram message with emojis and context  
**Status**: ✅ **READY TO GO** - Will send at next scheduled hour! 🚀
