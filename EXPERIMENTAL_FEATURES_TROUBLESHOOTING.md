# Experimental Features - Troubleshooting Guide

## Issue: No Visible Changes on Telegram

You've enabled both experimental features but aren't seeing changes on Telegram. Let's diagnose the problem.

---

## ✅ Step 1: Verify Features Are Enabled

Check `app_with_dashboard.py` lines 56 and 59:

```python
USE_PORTRAIT_MODE = True   # ✅ Should be True
USE_TEXT_SCALING = True    # ✅ Should be True
TEXT_SCALE_FACTOR = 1.25   # ✅ Should be 1.25 or 1.30
```

---

## ✅ Step 2: Check Console Output

When you run the script, you should see:

```
[EXPERIMENTAL] Portrait mode enabled: 2160x3840
[EXPERIMENTAL] Text scaling enabled: 1.25x
[EXPERIMENTAL] Text scaling wrapper applied: scale(1.25)
[DEBUG] Modified HTML saved to: dashboard_debug.html
```

**If you DON'T see these messages**, the features aren't being applied.

---

## ✅ Step 3: Verify Screenshot Dimensions

Check the generated file properties:

**Right-click** `dashboard_4k_20251018_XXXX.png` → **Properties** → **Details**

**Expected with Portrait Mode**:
- Width: **2160 pixels** (not 3840)
- Height: **3840 pixels** (not 2160)

**If dimensions are still 3840×2160**, portrait mode didn't apply.

---

## ✅ Step 4: Check Debug HTML File

A file called `dashboard_debug.html` should be created in your folder.

**Open it in a browser** and look for:

1. **Text Scaling**: Everything should look 25% bigger
2. **HTML Source**: Search for `transform: scale(1.25)`

**Example of what you should find**:
```html
<div style="transform: scale(1.25); transform-origin: top left;">
    <div class="max-w-6xl mx-auto bg-white rounded-2xl...">
```

**If you DON'T see the transform wrapper**, the text scaling isn't being applied.

---

## 🔍 Common Issues & Fixes

### **Issue 1: Features Enabled But Console Shows Nothing**

**Cause**: Script might be using cached code

**Fix**:
1. Close all Python processes
2. Save the file again (Ctrl+S)
3. Run the script fresh: `python app_with_dashboard.py`

---

### **Issue 2: Portrait Mode Not Working**

**Symptoms**: Image is still 3840×2160

**Possible Causes**:
- Configuration not saved
- Script using old code

**Fix**:
```python
# Verify this code is at line 63-64:
if USE_PORTRAIT_MODE:
    SCREENSHOT_4K_WIDTH, SCREENSHOT_4K_HEIGHT = 2160, 3840  # Flip to portrait
```

**Test**: Add a print statement:
```python
if USE_PORTRAIT_MODE:
    SCREENSHOT_4K_WIDTH, SCREENSHOT_4K_HEIGHT = 2160, 3840
    print(f"[DEBUG] Dimensions flipped: {SCREENSHOT_4K_WIDTH}x{SCREENSHOT_4K_HEIGHT}")
```

---

### **Issue 3: Text Scaling Not Working**

**Symptoms**: Text looks the same size in debug HTML

**Possible Causes**:
- HTML replacement not matching
- Transform not being applied

**Fix**: Check if the HTML structure matches

**Run this test**:
```python
# Add after line 700 (after the replacement):
if USE_TEXT_SCALING:
    if 'transform: scale(' in html_content:
        print("[DEBUG] ✅ Text scaling wrapper found in HTML")
    else:
        print("[DEBUG] ❌ Text scaling wrapper NOT found in HTML")
```

---

### **Issue 4: Changes Not Visible on Telegram**

**Symptoms**: 
- Console shows features are enabled
- Debug HTML shows scaling
- Image dimensions are correct (2160×3840)
- But Telegram image looks the same

**Possible Causes**:
1. **Telegram cached the old image** (same filename)
2. **Visual difference is subtle** at Telegram's compression level
3. **Need to compare side-by-side** with old version

**Fix**:

**A) Force Telegram to refresh**:
- Delete old messages with dashboard
- Send new one (Telegram will fetch fresh)

**B) Compare side-by-side**:
1. Disable features: `USE_PORTRAIT_MODE = False`, `USE_TEXT_SCALING = False`
2. Run script → Save as `dashboard_old.png`
3. Enable features: `USE_PORTRAIT_MODE = True`, `USE_TEXT_SCALING = True`
4. Run script → Save as `dashboard_new.png`
5. Open both in image viewer and compare

**C) Check file sizes**:
```
dashboard_old.png: ~3.5 MB (3840×2160)
dashboard_new.png: ~4.5 MB (2160×3840, scaled text)
```

If file sizes are identical, features aren't working.

---

## 🧪 Diagnostic Test Script

Add this to the end of `generate_dashboard_image()` function (before returning):

```python
# DIAGNOSTIC OUTPUT
print("\n=== EXPERIMENTAL FEATURES DIAGNOSTIC ===")
print(f"Portrait Mode: {'ENABLED' if USE_PORTRAIT_MODE else 'DISABLED'}")
print(f"Text Scaling: {'ENABLED' if USE_TEXT_SCALING else 'DISABLED'}")
print(f"Viewport: {SCREENSHOT_4K_WIDTH}x{SCREENSHOT_4K_HEIGHT}")
print(f"Scale Factor: {TEXT_SCALE_FACTOR if USE_TEXT_SCALING else 'N/A'}")
print(f"Transform in HTML: {'YES' if 'transform: scale(' in html_content else 'NO'}")
print("========================================\n")
```

---

## 📊 Expected vs Actual Comparison

### **Expected Output (Both Features Enabled)**

**Console**:
```
[EXPERIMENTAL] Portrait mode enabled: 2160x3840
[EXPERIMENTAL] Text scaling enabled: 1.25x
[EXPERIMENTAL] Text scaling wrapper applied: scale(1.25)
[DEBUG] Modified HTML saved to: dashboard_debug.html
[2025-10-18 20:00:00 GMT] 4K screenshot saved: dashboard_4k_20251018_2000.png
[2025-10-18 20:00:00 GMT] Resolution: 2160x3840 @ 2x scale
```

**File Properties**:
- Width: 2160 pixels
- Height: 3840 pixels
- Size: ~4-5 MB

**Debug HTML**:
- Contains: `<div style="transform: scale(1.25); transform-origin: top left;">`
- Text appears 25% larger when opened in browser

---

### **Actual Output (If Not Working)**

**Console**:
```
[2025-10-18 20:00:00 GMT] 4K screenshot saved: dashboard_4k_20251018_2000.png
[2025-10-18 20:00:00 GMT] Resolution: 3840x2160 @ 2x scale
```
❌ No experimental feature messages

**File Properties**:
- Width: 3840 pixels (wrong!)
- Height: 2160 pixels (wrong!)
- Size: ~3.5 MB

**Debug HTML**:
- File doesn't exist OR
- Doesn't contain transform wrapper

---

## 🎯 Quick Verification Checklist

Run through this checklist:

- [ ] Configuration flags are set to `True` (lines 56, 59)
- [ ] File is saved (Ctrl+S)
- [ ] Script is run fresh (not cached)
- [ ] Console shows experimental feature messages
- [ ] `dashboard_debug.html` file exists
- [ ] Debug HTML contains `transform: scale(1.25)`
- [ ] Screenshot dimensions are 2160×3840 (not 3840×2160)
- [ ] File size is larger (~4-5 MB vs ~3.5 MB)
- [ ] Telegram message is deleted and re-sent (not cached)

---

## 🔧 Nuclear Option: Force Verification

If nothing works, add this at the very start of `generate_dashboard_image()`:

```python
async def generate_dashboard_image(hospitals_dict: Dict[str, int], theme: str = 'dark') -> Tuple[str, str]:
    """Generate dashboard image using Playwright"""
    
    # FORCE VERIFICATION
    print("\n" + "="*60)
    print("EXPERIMENTAL FEATURES STATUS")
    print("="*60)
    print(f"USE_PORTRAIT_MODE = {USE_PORTRAIT_MODE}")
    print(f"USE_TEXT_SCALING = {USE_TEXT_SCALING}")
    print(f"TEXT_SCALE_FACTOR = {TEXT_SCALE_FACTOR}")
    print(f"SCREENSHOT_4K_WIDTH = {SCREENSHOT_4K_WIDTH}")
    print(f"SCREENSHOT_4K_HEIGHT = {SCREENSHOT_4K_HEIGHT}")
    print("="*60 + "\n")
    
    # Rest of function...
```

This will show you **immediately** if the configuration is being read correctly.

---

## 💡 Most Likely Cause

Based on "no changes visible on Telegram", the most likely issues are:

1. **Telegram is caching the old image** (same filename)
   - **Fix**: Delete old messages, send fresh

2. **Changes are subtle at Telegram's compression**
   - **Fix**: Compare side-by-side with old version

3. **Text scaling wrapper isn't being applied** (HTML mismatch)
   - **Fix**: Check `dashboard_debug.html` for transform wrapper

4. **Portrait mode is working but you're comparing wrong images**
   - **Fix**: Check file properties to confirm 2160×3840

---

## 📞 Next Steps

1. **Run the script** with both features enabled
2. **Check console output** for experimental messages
3. **Check file dimensions** (should be 2160×3840)
4. **Open `dashboard_debug.html`** in browser (text should look bigger)
5. **Compare side-by-side** with old version
6. **Delete Telegram message** and send fresh (avoid cache)

If you've done all this and still see no difference, please share:
- Console output
- File dimensions from Properties
- Whether `dashboard_debug.html` exists
- Whether debug HTML shows transform wrapper

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ Console shows: `[EXPERIMENTAL] Portrait mode enabled: 2160x3840`
2. ✅ Console shows: `[EXPERIMENTAL] Text scaling wrapper applied: scale(1.25)`
3. ✅ File dimensions: 2160×3840 (not 3840×2160)
4. ✅ Debug HTML exists and shows transform wrapper
5. ✅ Debug HTML in browser shows visibly larger text
6. ✅ Telegram image (fresh upload) shows better readability

**If all 6 are true, the features are working!** The difference may be subtle but should be noticeable when comparing side-by-side.
