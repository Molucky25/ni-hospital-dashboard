# Fixes Applied to app_with_dashboard.py

## ✅ Changes Made

### **1. Removed ArcGIS URLs**
**Removed:**
- `FEATURE_LAYER_QUERY_URL` - ArcGIS Feature Layer URL
- `FALLBACK_STATS_URL` - ArcGIS Fallback stats URL

**Why:** You only use NI Direct as the data source, so these were unnecessary.

---

### **2. Forced Dark Mode**
**Changed:**
```python
def get_auto_theme() -> str:
    """Force dark mode for dashboard generation"""
    return 'dark'
```

**Updated startup message:**
```
Theme: DARK (forced)
```

**Why:** You wanted dark mode all the time instead of auto-detection.

---

## ⚠️ NI Direct Scraping Issue

### **Error:**
```
[2025-10-17 11:13:11] NI Direct fetch failed: NI Direct: Could not locate Emergency Departments table
```

### **Possible Causes:**

1. **Website structure changed** - NI Direct may have updated their HTML
2. **Network/timeout issue** - Temporary connection problem
3. **Page requires JavaScript** - Data might be loaded dynamically

### **Troubleshooting Steps:**

#### **Step 1: Test the scraper**
Run the test script to see what's on the page:
```bash
python test_ni_direct.py
```

This will show:
- All headings containing "emergency" or "department"
- All tables found on the page
- Where hospital data might be located

#### **Step 2: Check if it's a temporary issue**
Try running the main script again:
```bash
python app_with_dashboard.py
```

Sometimes it's just a network hiccup.

#### **Step 3: Manual check**
Visit the URL in your browser:
```
https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times
```

Check if:
- The page loads correctly
- There's a table with hospital wait times
- The heading says "Emergency Departments"

---

## 🔧 If Scraping Still Fails

### **Option A: Update the scraper**
If the website structure changed, we may need to update the scraping logic in `fetch_ni_direct_rows()`.

### **Option B: Use test data**
For testing the dashboard, you can temporarily use sample data:

```python
# In run_once_async(), replace the fetch with:
rows = [
    {"hospital": "Altnagelvin Area ED", "wait_mins": 317, "status": "Open", "display_wait": "317 mins", "last_updated": None},
    {"hospital": "Royal Victoria ED", "wait_mins": 281, "status": "Open", "display_wait": "281 mins", "last_updated": None},
    {"hospital": "Ulster ED", "wait_mins": 238, "status": "Open", "display_wait": "238 mins", "last_updated": None},
    {"hospital": "Mater ED", "wait_mins": 220, "status": "Open", "display_wait": "220 mins", "last_updated": None},
    {"hospital": "Antrim Area ED", "wait_mins": 162, "status": "Open", "display_wait": "162 mins", "last_updated": None},
    {"hospital": "Craigavon Area ED", "wait_mins": 157, "status": "Open", "display_wait": "157 mins", "last_updated": None},
    {"hospital": "Causeway ED", "wait_mins": 152, "status": "Open", "display_wait": "152 mins", "last_updated": None},
    {"hospital": "South West Acute ED", "wait_mins": 131, "status": "Open", "display_wait": "131 mins", "last_updated": None},
    {"hospital": "Royal Children's ED", "wait_mins": 119, "status": "Open", "display_wait": "119 mins", "last_updated": None},
    {"hospital": "Daisy Hill ED", "wait_mins": 86, "status": "Open", "display_wait": "86 mins", "last_updated": None},
]
last_updated_hint = "Test data"
```

This will let you test the dashboard generation while we fix the scraper.

---

## 📋 Current Configuration

```python
POLL_SECONDS = 300          # Poll every 5 minutes
FORCE_SEND = False          # Only send on changes
GENERATE_DASHBOARD = True   # Dashboard enabled
Theme = 'dark'              # Always dark mode
```

---

## 🚀 Next Steps

1. **Run test script:** `python test_ni_direct.py`
2. **Check output** to see what's on the NI Direct page
3. **Share results** so we can update the scraper if needed
4. **Or use test data** to verify dashboard generation works

---

## 📝 Files Modified

- ✅ `app_with_dashboard.py` - Removed ArcGIS URLs, forced dark mode
- ✅ `test_ni_direct.py` - Created diagnostic script

---

## ✨ Summary

**Fixed:**
- ✅ Removed unwanted ArcGIS URLs
- ✅ Dark mode now forced (not auto-detect)
- ✅ Startup message updated

**To Investigate:**
- ⚠️ NI Direct scraping failure (run test script to diagnose)
