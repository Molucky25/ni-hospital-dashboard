# Dashboard Stat Cards - Detailed Explanations

## Overview
The dashboard displays 5 key statistical cards that provide real-time insights into Northern Ireland's A&E wait times. Each card presents a different analytical perspective on the current emergency department situation.

---

## 1. **Average Wait** ⏱️

### What It Displays
The **Average Wait** card shows the mean wait time across all Northern Ireland emergency departments at the current moment. This is calculated by summing all hospital wait times and dividing by the number of hospitals, giving you a single number that represents the typical wait time a patient might expect across the region.

### Key Information
- **Main Value**: The average wait time in minutes (e.g., "187m" = 187 minutes or 3 hours 7 minutes)
- **Gradient Bar**: Visual representation showing where the average sits relative to the maximum wait time (green = low, yellow = moderate, orange = high, red = critical)
- **Context Label**: Shows the percentage of maximum wait time (e.g., "59% of max (317m)" means the average is 59% of the longest current wait)
- **Trend Indicator**: "Improving" or "Worsening" status based on recent changes

### Why It Matters
This metric gives you an at-a-glance understanding of the overall pressure on the A&E system. A rising average indicates increasing strain across the region, while a falling average suggests conditions are improving. It's particularly useful for understanding whether current wait times are typical or exceptional.

---

## 2. **Trend Direction** 📊

### What It Displays
The **Trend Direction** card breaks down how many hospitals are currently experiencing **improving** wait times versus **worsening** wait times compared to the previous hour. It provides a split view showing the directional momentum of the entire A&E system.

### Key Information
- **Improving Count**: Number of hospitals where wait times have decreased since the last update (shown in green)
- **Worsening Count**: Number of hospitals where wait times have increased since the last update (shown in red)
- **Visual Bar**: Proportional representation showing the split between improving and worsening hospitals
- **Percentage Split**: The bar width reflects the ratio (e.g., 60% improving, 40% worsening)

### Why It Matters
This card answers the critical question: "Is the situation getting better or worse?" If 6 hospitals are improving and only 4 are worsening, you know the overall trend is positive even if some individual hospitals are struggling. It's particularly valuable for identifying whether pressure is building system-wide or if improvements are being made. This metric helps predict whether wait times are likely to continue rising or falling in the near future.

---

## 3. **Fastest Improvement** 🚀

### What It Displays
The **Fastest Improvement** card highlights which hospital has achieved the **largest reduction** in wait times since the previous update. It shows a before-and-after comparison, making it easy to see which emergency department has made the most progress in clearing their backlog.

### Key Information
- **Hospital Name**: The ED that has reduced wait times the most (e.g., "Ulster ED")
- **Before Time**: Wait time at the previous update (e.g., "127m")
- **After Time**: Current wait time (e.g., "106m")
- **Improvement Amount**: The reduction in minutes (e.g., "-21m" means 21 minutes faster)
- **Visual Arrow**: Downward arrow emphasizing the positive change

### Why It Matters
This card celebrates success and identifies which hospitals are effectively managing patient flow. It can indicate where best practices are being applied, where staffing is adequate, or where patient volumes have decreased. For patients, it shows which hospital is currently processing patients most efficiently. For healthcare administrators, it highlights potential models of success that could be replicated elsewhere.

---

## 4. **Biggest Change (24h)** 📈📉

### What It Displays
The **Biggest Change (24h)** card shows which emergency departments have experienced the **most dramatic shifts** in wait times over the past 24 hours. It displays both the **worst jump** (biggest increase) and the **best drop** (biggest decrease), providing a dual view of the most significant movements in the system.

### Key Information
- **Worst Jump**: Hospital with the largest wait time increase (e.g., "Antrim ↑ +92m vs yesterday") - shown in red
- **Best Drop**: Hospital with the largest wait time decrease (e.g., "Ulster ↓ −36m vs yesterday") - shown in green
- **Change Amount**: The magnitude of change in minutes (e.g., "+92m" or "−36m")
- **Time Reference**: "vs yesterday" indicates 24-hour comparison

### Why It Matters
This is a **pure movement metric** that highlights dramatic changes regardless of absolute wait times. A hospital with a 50-minute wait that jumps to 142 minutes (+92m) signals a crisis even if other hospitals have longer absolute waits. The **worst jump** indicates which ED is experiencing a surge, crisis, or sudden demand spike - possibly due to staff shortages, major incidents, or capacity issues. The **best drop** shows which hospital is successfully recovering or improving operations. These large numbers (+92m, −36m) are **visually dramatic** and perfect for social media, news headlines, and public awareness. For patients, avoid hospitals with worst jumps (likely overwhelmed) and consider those with best drops (improving flow). For administrators, investigate causes of worst jumps and replicate success strategies from best drops.

---

## 5. **Regional Pressure Index** 🌡️

### What It Displays
The **Regional Pressure Index** card shows what **percentage of hospitals** currently have wait times exceeding 2 hours (120 minutes). This is a system-wide health indicator that measures how many emergency departments are under significant strain simultaneously.

### Key Information
- **Percentage Value**: Proportion of hospitals over the 2-hour threshold (e.g., "72%" means 72% of hospitals have waits > 2 hours)
- **Status Badge**: Quick visual indicator - "Low" (green), "Moderate" (amber), or "High" (red) pressure
- **Segmented Bar**: Three-zone visualization showing pressure level:
  - **Green zone (0-50%)**: Low pressure - half or fewer hospitals stressed
  - **Amber zone (50-75%)**: Moderate pressure - majority of hospitals stressed
  - **Red zone (75-100%)**: High pressure - nearly all hospitals overwhelmed

### Why It Matters
This is the most critical system-wide metric. When 70%+ of hospitals exceed 2 hours, it indicates **regional crisis** - not just isolated problems at one or two facilities. It tells you whether the A&E system as a whole is coping or failing. A high pressure index (>75%) suggests system-wide issues like flu outbreaks, staff shortages, or bed blocking. A low index (<50%) indicates the system has capacity. This metric is essential for understanding whether you're looking at a localized problem or a region-wide emergency.

---

## How These Cards Work Together

### Comprehensive Situational Awareness
Each card provides a different lens on the same data:

1. **Average Wait** = Overall magnitude of the problem
2. **Trend Direction** = Momentum (getting better or worse?)
3. **Fastest Improvement** = Best performer (success story)
4. **Biggest Change (24h)** = Dramatic movement (crisis or recovery signals)
5. **Regional Pressure** = System-wide health (crisis indicator)

### Example Scenario Analysis

**Scenario 1: System Under Control**
- Average Wait: 90m (low)
- Trend Direction: 8 improving, 2 worsening
- Fastest Improvement: Antrim (-30m)
- Biggest Change (24h): Ulster ↓ −25m (best drop)
- Regional Pressure: 30% (Low)

**Interpretation**: System is healthy. Most hospitals improving, low average wait, good stability, and only 30% over 2 hours. Safe to visit A&E if needed.

---

**Scenario 2: Building Crisis**
- Average Wait: 210m (high)
- Trend Direction: 2 improving, 8 worsening
- Fastest Improvement: Ulster (-10m) [only small gains]
- Biggest Change (24h): Antrim ↑ +92m (worst jump)
- Regional Pressure: 80% (High)

**Interpretation**: System in crisis. High average, most hospitals worsening, even "best" improvement is small, high instability, and 80% of hospitals overwhelmed. Avoid A&E unless absolutely necessary.

---

**Scenario 3: Recovery in Progress**
- Average Wait: 150m (moderate)
- Trend Direction: 7 improving, 3 worsening
- Fastest Improvement: Royal Victoria (-45m)
- Biggest Change (24h): Royal Victoria ↓ −58m (major recovery)
- Regional Pressure: 55% (Moderate)

**Interpretation**: System recovering from pressure. Average still elevated but improving trend is strong. Some hospitals making significant progress. Situation improving but not yet optimal.

---

## Data Sources & Calculations

### Average Wait
```python
avgWait = sum(all_hospital_waits) / number_of_hospitals
```
**Example**: (317 + 281 + 238 + 195 + 187 + ...) / 10 = 210 minutes

### Trend Direction
```python
for each hospital:
    if current_wait < previous_wait:
        improving_count += 1
    elif current_wait > previous_wait:
        worsening_count += 1
```

### Fastest Improvement
```python
improvements = []
for each hospital:
    change = previous_wait - current_wait
    if change > 0:
        improvements.append((hospital, change))
fastest = max(improvements, key=lambda x: x[1])
```

### Most Stable
```python
import statistics
for each hospital:
    std_dev = statistics.stdev(last_4_hours_of_data)
most_stable = min(hospitals, key=lambda x: x.std_dev)
```

### Regional Pressure
```python
hospitals_over_2h = count(hospitals where wait > 120)
pressure_index = (hospitals_over_2h / total_hospitals) * 100
```

---

## Update Frequency

All stat cards update in real-time based on the polling interval (typically every 5 minutes). Historical metrics like "Most Stable" require at least 4 data points (approximately 20 minutes of history) before they can be calculated.

---

## Visual Design Philosophy

Each card uses color psychology to convey urgency:
- **Green**: Positive, improving, low pressure
- **Amber/Yellow**: Moderate, caution, building pressure
- **Red**: Critical, worsening, high pressure
- **Purple**: Neutral, stability, consistency
- **Cyan/Blue**: Information, trends, analysis

The gradient bars, animated elements, and visual indicators are designed for quick comprehension - you should be able to understand the situation in under 5 seconds just by looking at the colors and shapes.

---

## Summary

These five stat cards transform raw wait time data into actionable intelligence. Together, they answer:
- **How long** will I wait? (Average Wait)
- **Is it getting better or worse?** (Trend Direction)
- **Which hospital is performing best?** (Fastest Improvement)
- **Which hospital is most reliable?** (Most Stable)
- **Is the whole system in crisis?** (Regional Pressure)

By combining magnitude, momentum, performance, reliability, and system health, the dashboard provides a complete picture of Northern Ireland's A&E situation at any given moment.
