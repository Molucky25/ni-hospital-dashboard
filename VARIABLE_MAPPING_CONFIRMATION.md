# Variable Mapping Confirmation ✅

## Comparison: Required Variables vs Available Data

| Your Variable | Definition | Available in Script? | Source | Notes |
|--------------|------------|---------------------|--------|-------|
| `avg_wait` | Current regional average wait | ✅ YES | `sum(hospitals_dict.values()) // len(hospitals_dict)` | Already calculated |
| `avg_change` | Change in average wait since last hour | ✅ YES | `change_minutes` (line 527) | Calculated in hourly_trend section |
| `improving` | Number of hospitals improving | ✅ YES | `trends['improving_count']` | From calculate_trends() |
| `worsening` | Number of hospitals worsening | ✅ YES | `trends['worsening_count']` | From calculate_trends() |
| `pressure_index` | % hospitals ≥120m | ✅ YES | `pressure['percentage']` | From calculate_pressure_index() |
| `fastest_improvement` | Name and drop | ✅ YES | `trends['fastest_improvement']` | Dict with 'hospital' and 'diff' |
| `longest_wait` | Hospital with max wait | ✅ YES | `sorted_hospitals[0]` | First item in sorted list |
| `most_stable` | Hospital with lowest variance | ✅ YES | `stable` | From calculate_most_stable() |

## Available Data Structures

### 1. `trends` object (from `calculate_trends()`)
```python
{
    'improving_count': int,           # Number improving
    'worsening_count': int,           # Number worsening
    'unchanged_count': int,           # Number unchanged
    'fastest_improvement': {          # Best improvement
        'hospital': str,
        'diff': int,                  # Positive value (improvement amount)
        'current': int,
        'previous': int
    } or None,
    'worst_decline': {                # Worst decline
        'hospital': str,
        'diff': int,
        'current': int,
        'previous': int
    } or None,
    'changes': [                      # All changes
        {
            'hospital': str,
            'current': int,
            'previous': int,
            'diff': int               # Negative = better, Positive = worse
        }
    ],
    'has_previous_data': bool
}
```

### 2. `pressure` object (from `calculate_pressure_index()`)
```python
{
    'percentage': int,                # % over threshold (120m)
    'over_threshold': int,            # Count over threshold
    'total': int,                     # Total hospitals
    'severity': str                   # "High strain", "Moderate strain", or "Stable"
}
```

### 3. `stable` object (from `calculate_most_stable()`)
```python
{
    'hospital': str,                  # Hospital name
    'std_dev': float,                 # Standard deviation
    'readings': int                   # Number of readings
} or None
```

### 4. Already calculated variables
```python
current_avg = sum(hospitals_dict.values()) / len(hospitals_dict)  # Line 523
change_minutes = current_avg - previous_avg                       # Line 527
sorted_hospitals = [(name, wait), ...]                            # Line 488
```

## Variable Extraction Examples

### For Headlines:

```python
# avg_wait
avg_wait = int(current_avg)  # or sum(hospitals_dict.values()) // len(hospitals_dict)

# avg_change
avg_change = int(change_minutes)  # Already calculated

# improving / worsening
improving = trends['improving_count']
worsening = trends['worsening_count']

# pressure_index
pressure_index = pressure['percentage']

# fastest_improvement (name only)
fastest_improvement_name = trends['fastest_improvement']['hospital'].split()[0] if trends['fastest_improvement'] else None
fastest_improvement_drop = trends['fastest_improvement']['diff'] if trends['fastest_improvement'] else 0

# longest_wait (name and value)
longest_wait_name = sorted_hospitals[0][0].split()[0] if sorted_hospitals else None
longest_wait_value = sorted_hospitals[0][1] if sorted_hospitals else 0

# most_stable (name and variance)
most_stable_name = stable['hospital'].split()[0] if stable else None
most_stable_variance = int(stable['std_dev']) if stable else 0
```

## ✅ CONFIRMATION

**ALL REQUIRED VARIABLES ARE AVAILABLE** in the existing script. We can proceed with implementation.

### Implementation Plan:

1. **Extract variables** from existing data structures
2. **Create headline logic** based on conditions
3. **Add to `dashboard_data`** dict
4. **Update HTML** to display headline with SVG icon
5. **Style** with appropriate colors and formatting

Ready to implement! 🚀
