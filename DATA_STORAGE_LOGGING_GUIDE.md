# Data Storage & Logging System - Complete Guide

## 📊 Overview

Your system stores data in **4 JSON files** with different purposes and retention policies.

---

## 📁 File 1: `state.json` - Current State

### **Purpose**
Tracks the current state for change detection and Telegram message tracking.

### **Location**
`c:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\state.json`

### **Data Stored**
```json
{
  "digest": "3956a469920ab9175b1191e017cb279ef712d92f1a22979bdf95574017946b8b",
  "last_sent": "2025-10-18 20:45:15 GMT Summer Time",
  "last_message_id": 373,
  "previous_waits": {
    "Antrim AreaED": 293,
    "Royal Victoria ED": 205,
    "Craigavon AreaED": 182,
    "South West Acute ED": 139,
    "Royal Children's ED": 135,
    "Mater ED": 116,
    "Causeway AreaED": 113,
    "Ulster ED": 103,
    "Altnagelvin AreaED": 94,
    "Daisy Hill ED": 80
  }
}
```

### **Fields Explained**

| Field | Type | Purpose |
|-------|------|---------|
| `digest` | String (SHA256) | Hash of current data to detect changes |
| `last_sent` | Timestamp | When last Telegram message was sent |
| `last_message_id` | Integer | Telegram message ID for threading |
| `previous_waits` | Object | Last known wait times for each hospital |

### **Update Frequency**
- **Every poll** (every 5 minutes)
- Overwrites previous data
- Only keeps **current state** (no history)

### **Retention**
- **1 snapshot only** (always current)
- No historical data
- Replaced on every run

---

## 📁 File 2: `hospital_wait_cache.json` - Trend Cache

### **Purpose**
Stores the most recent wait times with timestamp for trend calculations (hourly changes).

### **Location**
`c:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\hospital_wait_cache.json`

### **Data Stored**
```json
{
  "timestamp": "2025-10-18T20:45:15.574027",
  "data": {
    "Antrim AreaED": 293,
    "Royal Victoria ED": 205,
    "Craigavon AreaED": 182,
    "South West Acute ED": 139,
    "Royal Children's ED": 135,
    "Mater ED": 116,
    "Causeway AreaED": 113,
    "Ulster ED": 103,
    "Altnagelvin AreaED": 94,
    "Daisy Hill ED": 80
  }
}
```

### **Fields Explained**

| Field | Type | Purpose |
|-------|------|---------|
| `timestamp` | ISO 8601 | When this data was captured |
| `data` | Object | Current wait times for all hospitals |

### **Update Frequency**
- **Every successful dashboard generation**
- Overwrites previous data
- Used for **hourly trend** calculations

### **Retention**
- **1 snapshot only** (most recent)
- Compared with current data to calculate hourly change
- Example: "↓ 8% vs 1h ago"

---

## 📁 File 3: `hospital_wait_history.json` - Rolling History

### **Purpose**
Maintains a **rolling window** of the last 6 readings per hospital for stability calculations.

### **Location**
`c:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\hospital_wait_history.json`

### **Data Stored**
```json
{
  "hospitals": {
    "Antrim AreaED": [293, 293, 293, 293, 293, 293],
    "Causeway AreaED": [113, 113, 113, 113, 113, 113],
    "South West Acute ED": [139, 139, 139, 139, 139, 139],
    "Altnagelvin AreaED": [94, 94, 94, 94, 94, 94],
    "Royal Victoria ED": [205, 205, 205, 205, 205, 205],
    "Mater ED": [116, 116, 116, 116, 116, 116],
    "Craigavon AreaED": [182, 182, 182, 182, 182, 182],
    "Daisy Hill ED": [80, 80, 80, 80, 80, 80],
    "Ulster ED": [103, 103, 103, 103, 103, 103],
    "Royal Children's ED": [135, 135, 135, 135, 135, 135]
  }
}
```

### **Fields Explained**

| Field | Type | Purpose |
|-------|------|---------|
| `hospitals` | Object | Maps hospital names to arrays of wait times |
| Each array | Integer[] | Last 6 wait time readings (oldest to newest) |

### **Update Frequency**
- **Every successful dashboard generation**
- Appends new reading
- Keeps only **last 6 readings** (FIFO queue)

### **Retention**
- **6 readings per hospital**
- At 5-minute intervals = **30 minutes of history**
- Used for calculating **standard deviation** (stability)

### **Usage**
- Calculate "Most Stable Hospital" (lowest std dev)
- Calculate "Biggest Change (24h)" by comparing oldest vs newest
- Trend arrow calculations

---

## 📁 File 4: `hospital_wait_trends.jsonl` - Long-Term Log

### **Purpose**
Append-only log file storing **every single reading** for long-term analysis.

### **Location**
`c:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\hospital_wait_trends.jsonl`

### **Format**
JSONL (JSON Lines) - one JSON object per line

### **Data Stored**
```json
{"timestamp": "2025-10-17T00:20:41.906218+00:00", "avg_wait": 186, "hospitals": {"Altnagelvin Area Hospital Emergency Department": 317, "Royal Victoria Hospital Emergency Department": 281, ...}}
{"timestamp": "2025-10-17T00:22:59.188108+00:00", "avg_wait": 186, "hospitals": {"Altnagelvin Area Hospital Emergency Department": 317, ...}}
{"timestamp": "2025-10-17T00:30:49.839486+00:00", "avg_wait": 186, "hospitals": {"Altnagelvin Area Hospital Emergency Department": 317, ...}}
```

### **Fields Explained**

| Field | Type | Purpose |
|-------|------|---------|
| `timestamp` | ISO 8601 | When this reading was taken |
| `avg_wait` | Integer | Average wait time across all hospitals |
| `hospitals` | Object | All hospital wait times at this moment |

### **Update Frequency**
- **Every successful dashboard generation**
- **Appends** new line (never overwrites)
- Grows indefinitely

### **Retention**
- **Unlimited** (append-only)
- Never deleted automatically
- Grows over time

### **Usage**
- Long-term trend analysis
- Historical data mining
- Debugging
- Future analytics

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Every 5 Minutes                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Fetch data from NI Direct website                       │
│     (10 hospitals, wait times in minutes)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Check for changes (compare digest with state.json)      │
│     If no change → Skip send                                │
│     If changed → Continue                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Send text message to Telegram                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Generate dashboard image                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Send dashboard to Telegram                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Update all data files:                                  │
│     ├─ state.json (current state)                           │
│     ├─ hospital_wait_cache.json (for hourly trends)         │
│     ├─ hospital_wait_history.json (rolling 6 readings)      │
│     └─ hospital_wait_trends.jsonl (append log entry)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Delete dashboard images (auto-cleanup)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 What Metrics Are Logged?

### **✅ Logged Every Poll (5 minutes)**

1. **Hospital wait times** (all 10 hospitals)
2. **Timestamp** (when data was fetched)
3. **Average wait time** (calculated)
4. **Digest** (SHA256 hash for change detection)
5. **Telegram message ID** (for threading)

### **✅ Calculated & Displayed (Not Stored)**

These are calculated on-the-fly from stored data:

1. **Hourly trend** (% change vs 1h ago)
2. **Trend direction** (improving/worsening count)
3. **Fastest improvement** (biggest drop)
4. **Worst decline** (biggest increase)
5. **Longest wait** (max wait time)
6. **Shortest wait** (min wait time)
7. **Regional pressure** (% over 2h threshold)
8. **Most stable hospital** (lowest std dev)
9. **Biggest change (24h)** (vs 24h ago)

### **❌ NOT Logged**

1. **Individual trend arrows** (↑↓→) - calculated live
2. **Severity colors** (red/orange/yellow/green) - calculated live
3. **Dashboard images** - deleted after send
4. **Debug HTML** - deleted after send
5. **Telegram messages** - stored by Telegram, not locally

---

## 💾 Storage Requirements

### **Current Usage**

| File | Size | Growth Rate |
|------|------|-------------|
| `state.json` | ~500 bytes | **0** (fixed size) |
| `hospital_wait_cache.json` | ~350 bytes | **0** (fixed size) |
| `hospital_wait_history.json` | ~2.4 KB | **0** (fixed size, rolling) |
| `hospital_wait_trends.jsonl` | ~6 KB | **~500 bytes/day** |

### **Projected Growth**

**hospital_wait_trends.jsonl** (only file that grows):
- Per entry: ~500 bytes
- Per day (288 entries): ~144 KB
- Per week: ~1 MB
- Per month: ~4.3 MB
- Per year: ~52 MB

**Total storage after 1 year**: ~55 MB (mostly trends.jsonl)

---

## 🔧 Data Management

### **Automatic Cleanup**

✅ **Dashboard images** - deleted after Telegram send  
✅ **Debug HTML** - deleted after Telegram send  
✅ **Rolling history** - automatically keeps only last 6 readings  

### **Manual Cleanup Needed**

⚠️ **hospital_wait_trends.jsonl** - grows indefinitely

**To clean up old data**:
```bash
# Keep only last 1000 lines (most recent)
tail -n 1000 hospital_wait_trends.jsonl > temp.jsonl
mv temp.jsonl hospital_wait_trends.jsonl
```

Or delete entirely:
```bash
rm hospital_wait_trends.jsonl
# Will be recreated on next run
```

---

## 📈 Data Analysis Examples

### **1. Calculate Average Wait Over Last Hour**

Read `hospital_wait_trends.jsonl`, filter last 12 entries (5 min × 12 = 1 hour):
```python
import json

with open('hospital_wait_trends.jsonl', 'r') as f:
    lines = f.readlines()[-12:]  # Last 12 entries
    
avg_waits = [json.loads(line)['avg_wait'] for line in lines]
hourly_avg = sum(avg_waits) / len(avg_waits)
print(f"Average wait over last hour: {hourly_avg}m")
```

---

### **2. Find Peak Wait Time Today**

```python
from datetime import datetime, timedelta

today = datetime.now().date()
max_wait = 0
max_hospital = None

with open('hospital_wait_trends.jsonl', 'r') as f:
    for line in f:
        entry = json.loads(line)
        timestamp = datetime.fromisoformat(entry['timestamp'])
        
        if timestamp.date() == today:
            for hospital, wait in entry['hospitals'].items():
                if wait > max_wait:
                    max_wait = wait
                    max_hospital = hospital

print(f"Peak wait today: {max_hospital} at {max_wait}m")
```

---

### **3. Calculate 24-Hour Change**

```python
# Read last entry (current)
with open('hospital_wait_trends.jsonl', 'r') as f:
    lines = f.readlines()
    current = json.loads(lines[-1])
    
    # 24h ago = 288 entries ago (5 min × 288 = 24h)
    if len(lines) >= 288:
        past_24h = json.loads(lines[-288])
        
        for hospital in current['hospitals']:
            current_wait = current['hospitals'][hospital]
            past_wait = past_24h['hospitals'].get(hospital, current_wait)
            change = current_wait - past_wait
            print(f"{hospital}: {change:+d}m (24h change)")
```

---

## 🎯 Summary

### **What's Logged**
✅ Every hospital wait time (every 5 minutes)  
✅ Timestamps for all readings  
✅ Average wait times  
✅ Change detection hashes  
✅ Telegram message IDs  

### **What's NOT Logged**
❌ Dashboard images (deleted after send)  
❌ Calculated metrics (computed on-the-fly)  
❌ Trend arrows (derived from data)  
❌ Severity colors (calculated live)  

### **Storage**
- **Fixed size**: 3 files (~3 KB total)
- **Growing**: 1 file (~52 MB/year)
- **Total**: ~55 MB after 1 year

### **Retention**
- **Current state**: 1 snapshot (state.json)
- **Hourly trends**: 1 snapshot (cache.json)
- **Rolling history**: 6 readings = 30 minutes (history.json)
- **Long-term log**: Unlimited (trends.jsonl)

---

## 🔍 Quick Reference

| File | Purpose | Retention | Size |
|------|---------|-----------|------|
| `state.json` | Change detection | Current only | ~500 B |
| `hospital_wait_cache.json` | Hourly trends | Current only | ~350 B |
| `hospital_wait_history.json` | Stability calc | Last 6 (30 min) | ~2.4 KB |
| `hospital_wait_trends.jsonl` | Long-term log | Unlimited | ~52 MB/year |

**All metrics are logged. Nothing is missed!** 📊✅
