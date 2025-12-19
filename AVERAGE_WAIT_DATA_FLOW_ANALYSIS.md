# Average Wait Data Flow Analysis 🔍

## Issue Identified: ⚠️ DUAL UPDATE MECHANISM CONFLICT

The Average Wait is being updated **TWICE** with **DIFFERENT** calculations, causing inconsistency.

---

## Data Flow Analysis

### 1. **Backend Calculation (Python)** ✅

**File**: `app_with_dashboard.py` - Line 630

```python
'avgWait': f"{sum(hospitals_dict.values()) // len(hospitals_dict)}m" if hospitals_dict else "N/A"
```

**Calculation**:
- Sums all hospital wait times
- Divides by number of hospitals
- Uses integer division (`//`)
- Formats as string with "m" suffix

**Example**:
```python
hospitals_dict = {
    'Altnagelvin': 317,
    'Royal Victoria': 281,
    'Ulster': 238,
    'Antrim': 195,
    'Craigavon': 187,
    # ... more hospitals
}

avgWait = sum([317, 281, 238, 195, 187, ...]) // 10
avgWait = 2100 // 10 = 210
Result: "210m"
```

---

### 2. **Frontend Update #1 (JavaScript - safeUpdate)** ✅

**File**: `dashboard.html` - Line 961

```javascript
safeUpdate('avg-wait', data.avgWait, true);
```

**What This Does**:
- Takes the backend-calculated value (e.g., "210m")
- Updates the `#avg-wait` element's innerHTML
- Uses the Python calculation

**This is CORRECT** ✅

---

### 3. **Frontend Update #2 (JavaScript - updateAverageWaitGauge)** ⚠️ PROBLEM

**File**: `dashboard.html` - Lines 850-887, called at Line 964

```javascript
function updateAverageWaitGauge(hospitals) {
    // Filter valid wait times
    const validWaits = hospitals
        .filter(h => h.wait !== 'N/A' && typeof h.wait === 'number')
        .map(h => h.wait);
    
    if (validWaits.length === 0) return;
    
    // Calculate max and average
    const maxWait = Math.max(...validWaits);
    const avgWait = Math.round(validWaits.reduce((sum, w) => sum + w, 0) / validWaits.length);
    
    // Update the text display
    const avgWaitText = document.getElementById('avg-wait');
    if (avgWaitText) {
        avgWaitText.textContent = avgWait + 'm';  // ← OVERWRITES PREVIOUS VALUE
    }
    
    // Calculate percentage
    const percentage = (avgWait / maxWait) * 100;
    
    // Update bar width with animation
    const bar = document.getElementById('avg-wait-bar');
    const glow = document.getElementById('avg-wait-bar-glow');
    
    if (bar) {
        bar.style.width = percentage + '%';
    }
    if (glow) {
        glow.style.width = percentage + '%';
    }
    
    // Update context label
    const contextLabel = document.getElementById('avg-wait-context');
    if (contextLabel) {
        contextLabel.textContent = `${Math.round(percentage)}% of max (${maxWait}m)`;
    }
}
```

**What This Does**:
1. Recalculates average from hospital data
2. **OVERWRITES** the `#avg-wait` element (Line 865)
3. Updates the gauge bar and context

**This is the PROBLEM** ⚠️

---

## The Conflict

### Execution Order
```
1. safeUpdate('avg-wait', data.avgWait, true)
   → Sets #avg-wait to "210m" (from Python)

2. updateAverageWaitGauge(data.hospitals)
   → Recalculates average from hospitals array
   → OVERWRITES #avg-wait to "210m" (from JavaScript)
```

### Why It Might Show the Same Number

**Scenario 1**: Both calculations produce the same result
- Python: `sum(values) // len(values)`
- JavaScript: `Math.round(sum(values) / len(values))`
- If the average is exactly 210, both show "210m"

**Scenario 2**: JavaScript calculation is stuck
- If `hospitals` array is not updating
- JavaScript recalculates same old data
- Shows same number repeatedly

**Scenario 3**: Placeholder not being replaced
- HTML has placeholder "187m"
- If JavaScript doesn't run, placeholder remains
- Shows "187m" always

---

## Current Placeholder in HTML

**File**: `dashboard.html` - Line 508

```html
<span class="block text-3xl font-extrabold text-slate-100 drop-shadow-[0_0_12px_rgba(6,182,212,0.5)]" id="avg-wait">187m</span>
```

**Placeholder**: `187m`

**This will show if**:
- JavaScript doesn't execute
- `updateDashboard()` is not called
- Both update mechanisms fail

---

## Root Cause Analysis

### Why Average Wait Might Be Stuck

#### 1. **Data Not Changing**
```python
# Check if hospitals_dict is actually updating
print(f"[DEBUG] hospitals_dict: {hospitals_dict}")
print(f"[DEBUG] avgWait calculation: {sum(hospitals_dict.values()) // len(hospitals_dict)}")
```

#### 2. **JavaScript Not Executing**
- Dashboard image generation might not call `updateDashboard()`
- Selenium might capture before JavaScript runs

#### 3. **Dual Calculation Redundancy**
- Line 961: Sets value from Python
- Line 964: Recalculates and overwrites
- **Redundant and error-prone**

---

## Recommended Fix

### Option 1: Remove Redundant JavaScript Calculation (RECOMMENDED) ✅

**Remove the duplicate calculation from `updateAverageWaitGauge()`**

```javascript
function updateAverageWaitGauge(hospitals) {
    // Filter valid wait times
    const validWaits = hospitals
        .filter(h => h.wait !== 'N/A' && typeof h.wait === 'number')
        .map(h => h.wait);
    
    if (validWaits.length === 0) return;
    
    // Calculate max and average
    const maxWait = Math.max(...validWaits);
    const avgWait = Math.round(validWaits.reduce((sum, w) => sum + w, 0) / validWaits.length);
    
    // REMOVE THIS BLOCK - Let safeUpdate handle it
    // const avgWaitText = document.getElementById('avg-wait');
    // if (avgWaitText) {
    //     avgWaitText.textContent = avgWait + 'm';
    // }
    
    // Calculate percentage
    const percentage = (avgWait / maxWait) * 100;
    
    // Update bar width with animation
    const bar = document.getElementById('avg-wait-bar');
    const glow = document.getElementById('avg-wait-bar-glow');
    
    if (bar) {
        bar.style.width = percentage + '%';
    }
    if (glow) {
        glow.style.width = percentage + '%';
    }
    
    // Update context label
    const contextLabel = document.getElementById('avg-wait-context');
    if (contextLabel) {
        contextLabel.textContent = `${Math.round(percentage)}% of max (${maxWait}m)`;
    }
}
```

**Benefits**:
- Single source of truth (Python calculation)
- No overwriting
- Cleaner code
- Easier to debug

---

### Option 2: Use JavaScript Calculation Only

**Remove Python calculation, rely on JavaScript**

```python
# Remove this line
'avgWait': f"{sum(hospitals_dict.values()) // len(hospitals_dict)}m" if hospitals_dict else "N/A",

# Replace with
'avgWait': None,  # Let JavaScript calculate
```

**Then update JavaScript**:
```javascript
// Don't call safeUpdate for avgWait
// safeUpdate('avg-wait', data.avgWait, true);  // REMOVE

// Let updateAverageWaitGauge handle everything
updateAverageWaitGauge(data.hospitals);
```

**Drawbacks**:
- Loses backend calculation
- More complex JavaScript
- Harder to debug

---

## Verification Steps

### 1. Check Backend Calculation
```python
# Add debug output in app_with_dashboard.py around line 630
hospitals_dict_values = list(hospitals_dict.values())
avg_calc = sum(hospitals_dict_values) // len(hospitals_dict_values)
print(f"[DEBUG] Hospital wait times: {hospitals_dict_values}")
print(f"[DEBUG] Average wait calculation: {sum(hospitals_dict_values)} // {len(hospitals_dict_values)} = {avg_calc}")
print(f"[DEBUG] avgWait in dashboard_data: {dashboard_data['avgWait']}")
```

### 2. Check JavaScript Execution
```javascript
// Add console logs in updateAverageWaitGauge
console.log('[updateAverageWaitGauge] Called with hospitals:', hospitals);
console.log('[updateAverageWaitGauge] Valid waits:', validWaits);
console.log('[updateAverageWaitGauge] Calculated avgWait:', avgWait);
```

### 3. Check HTML Placeholder
```bash
# Search for hardcoded values
grep -n "187m" dashboard.html
grep -n "id=\"avg-wait\"" dashboard.html
```

---

## Current State Summary

### ✅ Working Correctly
1. **Python calculation**: Calculates average from `hospitals_dict`
2. **Data injection**: Passes `avgWait` to JavaScript
3. **safeUpdate call**: Updates `#avg-wait` element

### ⚠️ Potential Issues
1. **Dual update**: JavaScript recalculates and overwrites
2. **Placeholder**: HTML has "187m" hardcoded
3. **Data staleness**: `hospitals_dict` might not be updating

### ❌ Confirmed Problems
1. **Redundant calculation**: Average calculated twice
2. **Overwriting**: Second calculation overwrites first
3. **Placeholder exists**: "187m" in HTML

---

## Recommended Action Plan

### Step 1: Remove Redundant Calculation
```javascript
// In updateAverageWaitGauge(), comment out lines 863-866
// const avgWaitText = document.getElementById('avg-wait');
// if (avgWaitText) {
//     avgWaitText.textContent = avgWait + 'm';
// }
```

### Step 2: Add Debug Logging
```python
# In app_with_dashboard.py
print(f"[DEBUG] Current hospitals_dict: {hospitals_dict}")
print(f"[DEBUG] Calculated avgWait: {dashboard_data['avgWait']}")
```

### Step 3: Verify Data Updates
- Run the script
- Check console output
- Confirm `hospitals_dict` changes between runs
- Verify `avgWait` reflects changes

### Step 4: Test Dashboard Generation
- Generate dashboard image
- Check if average wait updates
- Compare with console debug output

---

## Status: ⚠️ ISSUE IDENTIFIED

**Problem**: Dual update mechanism with redundant calculation  
**Impact**: Average wait might show stale data or be overwritten  
**Severity**: Medium (functionality works but unreliable)  
**Fix Required**: Remove redundant JavaScript calculation  

**Next Steps**:
1. Remove lines 863-866 from `updateAverageWaitGauge()`
2. Add debug logging to verify data flow
3. Test with live data updates
4. Confirm average wait changes correctly
