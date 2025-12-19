# Long-Term Data Retention & Historical Analytics Plan

## Executive Summary
Comprehensive plan to implement **daily, weekly, and monthly statistical tracking** for NI A&E Wait Times dashboard.

---

## Current State
- **File**: `hospital_wait_history.json`
- **Retention**: Last 6 readings (30 minutes)
- **Limitation**: No true 24h tracking, no historical comparisons

---

## Proposed Multi-Tier Storage

```
TIER 1: Real-Time (hospital_wait_cache.json) - Latest reading
TIER 2: 24h History (hospital_wait_history.json) - 288 readings
TIER 3: Daily Snapshots (data/daily/YYYY-MM-DD.json) - Permanent
TIER 4: Weekly Aggregates (data/weekly/YYYY-WW.json) - Permanent
TIER 5: Monthly Summaries (data/monthly/YYYY-MM.json) - Permanent
```

---

## Implementation Phases

### **Phase 1: Extend 24h History (Week 1)**
Change `max_history` from 6 to 288 in `trend_cache_system.py`

### **Phase 2: Daily Snapshots (Week 2)**
Create `daily_snapshot_system.py` to capture end-of-day stats

### **Phase 3: Weekly Aggregates (Week 3)**
Create `weekly_aggregate_system.py` to roll up daily data

### **Phase 4: Monthly Summaries (Week 4)**
Create `monthly_summary_system.py` for long-term trends

---

## Storage Requirements
- **Year 1**: ~77 MB
- **Year 5**: ~90 MB (negligible)

---

## New Statistics Enabled

### **Daily**
- Today vs yesterday comparisons
- Peak time identification
- Event detection (surges)

### **Weekly**
- Week-over-week trends
- Day-of-week patterns
- Weekend vs weekday analysis

### **Monthly**
- Month-over-month comparisons
- Seasonal patterns
- Year-over-year trends

---

## Status: PLANNED
Ready for implementation. See full technical specifications in separate implementation docs.
