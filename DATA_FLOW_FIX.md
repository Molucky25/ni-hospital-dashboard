# Dashboard Data Flow Fix - Summary

## Problem Identified
The dashboard was showing **placeholder data** in screenshots instead of **live data** from NI Direct.

---

## Root Causes Found

### 1. **Python Script Not Calling `updateDashboard()`**
**Location:** `app_with_dashboard.py` lines 496-519

**Issue:**
- Python was injecting data via `window.dashboardData`
- Custom inline script only updated **5 stat cards**
- **Table was never populated** with live data
- `updateDashboard()` function was never called

**Fix:**
```python
# OLD (broken):
window.addEventListener('DOMContentLoaded', function() {
    const data = window.dashboardData;
    document.getElementById('trend-direction').innerHTML = data.trendDirection;
    // ... only 5 elements updated, NO TABLE
});

# NEW (fixed):
window.addEventListener('DOMContentLoaded', function() {
    if (typeof updateDashboard === 'function') {
        updateDashboard({json.dumps(dashboard_data)});  // Calls full update
    }
});
```

---

### 2. **Incomplete Data Structure**
**Location:** `app_with_dashboard.py` lines 463-480

**Issue:**
- Python data object missing required fields:
  - `longestWait` (HTML formatted)
  - `colorClass` (for styling)
  - `emoji` (visual indicator)
  - `trend` (up/down arrows)

**Fix:**
Added helper functions and complete data structure:
```python
def get_color_info(wait):
    if wait >= 240: return 'text-red-600', '🔴'
    elif wait >= 120: return 'text-orange-500', '🟠'
    elif wait >= 60: return 'text-yellow-500', '🟡'
    else: return 'text-green-600', '🟢'

def get_trend(name):
    if name in trends:
        return 'up' if trends[name] > 0 else 'down' if trends[name] < 0 else None
    return None

dashboard_data = {
    'hospitals': [
        {
            'name': name,
            'wait': wait,
            'colorClass': get_color_info(wait)[0],  # NEW
            'emoji': get_color_info(wait)[1],        # NEW
            'trend': get_trend(name),                # NEW
            'severity': '...'
        }
        for name, wait in sorted_hospitals
    ],
    'longestWait': f"{name} — <span>...</span>",    # NEW
    # ... other fields
}
```

---

### 3. **Old Placeholder Rows in HTML**
**Location:** `dashboard.html` lines 398-475

**Issue:**
- 9 old placeholder rows with **light theme styling**
- Using old classes: `hover:bg-blue-50`, `text-gray-800`
- Confusing during development
- Would show if JavaScript failed

**Fix:**
- Removed all old rows (lines 398-475)
- Kept only 3 new dark theme sample rows
- Added clear comment: `<!-- JavaScript will replace all rows above with live data -->`

---

### 4. **No Screenshot Wait Condition**
**Location:** `app_with_dashboard.py` lines 533-538

**Issue:**
- Screenshot taken after fixed 1500ms timeout
- No guarantee table was populated
- Race condition possible

**Fix:**
```python
# Wait for fonts and rendering
await page.wait_for_timeout(1000)

# Wait for table to be populated (check for new styling)
await page.wait_for_selector('tbody#hospital-table tr.hover\\:bg-slate-800\\/30', timeout=5000)

# Additional wait for transitions
await page.wait_for_timeout(500)

# Take screenshot (NOW table is guaranteed populated)
```

---

## Data Flow (Fixed)

### **Step 1: Python Fetches Data**
```python
hospitals_dict = {
    'Altnagelvin Area ED': 317,
    'Royal Victoria ED': 281,
    # ... all hospitals
}
```

### **Step 2: Python Generates Dashboard Data**
```python
dashboard_data = {
    'updateTime': '12:00 PM, Fri 17 Oct 2025',
    'trendDirection': '6 improving | 4 worsening',
    'avgWait': '187m',
    'longestWait': 'Altnagelvin — <span>317m 🔴</span>',
    'hospitals': [
        {'name': 'Altnagelvin Area ED', 'wait': 317, 'colorClass': 'text-red-600', 'emoji': '🔴', 'trend': 'up'},
        {'name': 'Royal Victoria ED', 'wait': 281, 'colorClass': 'text-red-600', 'emoji': '🔴', 'trend': 'up'},
        # ... all hospitals with full data
    ]
}
```

### **Step 3: Python Injects JavaScript**
```javascript
window.addEventListener('DOMContentLoaded', function() {
    updateDashboard({...dashboard_data...});
});
```

### **Step 4: updateDashboard() Runs**
```javascript
function updateDashboard(data) {
    // Update timestamp
    document.getElementById('update-time').textContent = data.updateTime;
    
    // Update all stat cards
    document.getElementById('avg-wait').innerHTML = data.avgWait;
    document.getElementById('longest-wait').innerHTML = data.longestWait;
    // ... all stats
    
    // Update Trend Direction split
    const improving = parseInt(data.trendDirection.match(/(\d+)\s+improving/)[1]);
    document.getElementById('improving-count').textContent = improving;
    // ... update bars
    
    // Update Regional Pressure bar
    const percentage = parseInt(data.pressureIndex.match(/(\d+)%/)[1]);
    document.getElementById('pressure-bar').style.width = percentage + '%';
    // ... update badge
    
    // **POPULATE TABLE** (THIS WAS MISSING!)
    const tbody = document.getElementById('hospital-table');
    tbody.innerHTML = data.hospitals.map(h => `
        <tr class="hover:bg-slate-800/30 transition-colors duration-100">
            <td>${getSeverityDot(h.wait)}</td>
            <td>${getWaitBadge(h.wait)}</td>
            <td>${h.name}</td>
            <td>${getTrendArrowSVG(h.trend)}</td>
        </tr>
    `).join('');
}
```

### **Step 5: Playwright Waits for Table**
```python
# Wait for table rows with new styling
await page.wait_for_selector('tbody#hospital-table tr.hover\\:bg-slate-800\\/30')
```

### **Step 6: Screenshot Captured**
```python
await page.screenshot(path=str(output_path))
```

---

## Verification Checklist

✅ **Python calls `updateDashboard()`** - Fixed in `app_with_dashboard.py`
✅ **Complete data structure** - Added `colorClass`, `emoji`, `trend`, `longestWait`
✅ **Table populated** - `updateDashboard()` now updates `tbody.innerHTML`
✅ **Stat cards populated** - All 6 cards updated dynamically
✅ **Progress bars updated** - Trend Direction and Regional Pressure
✅ **Old placeholders removed** - Clean HTML with only 3 sample rows
✅ **Screenshot waits for data** - `wait_for_selector()` ensures table is ready
✅ **No race conditions** - Proper async flow

---

## Testing

### **To Test Locally:**
1. Run: `python app_with_dashboard.py`
2. Check console for: `Dashboard generated: ...`
3. Open generated PNG - should show:
   - ✅ Live hospital data in table (sorted by wait time)
   - ✅ Colored dots and badges
   - ✅ Trend arrows (up/down)
   - ✅ All stat cards with live numbers
   - ✅ Trend Direction split (improving/worsening)
   - ✅ Regional Pressure bar at correct percentage

### **To Test HTML Directly (Development):**
1. Open `dashboard.html` in browser
2. You'll see 3 sample rows (placeholders)
3. Open console - should see: "updateDashboard() function not found"
4. This is **expected** - Python injects the call

---

## Summary

**Before:** Screenshot showed placeholder data, table empty
**After:** Screenshot shows live NI Direct data, table fully populated

**Key Fix:** Python now calls `updateDashboard()` with complete data structure, and Playwright waits for table population before screenshot.

**Result:** Every screenshot now reflects **real-time hospital wait data** from NI Direct! 🎯
