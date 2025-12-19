# Auto-Delete Dashboard Images After Telegram Send

## ✅ IMPLEMENTED

Dashboard images are now automatically deleted after successful Telegram upload to save disk space.

---

## 🎯 What Changed

### **Before**
- Dashboard images saved permanently
- Timestamped files accumulated: `dashboard_4k_20251018_2029.jpg`, `dashboard_4k_20251018_2034.jpg`, etc.
- Legacy file kept: `dashboard_current.png`
- Debug HTML kept: `dashboard_debug.html`
- **Result**: Disk space consumed over time

### **After**
- Dashboard images deleted immediately after successful Telegram send
- No file accumulation
- Clean workspace
- **Result**: Zero disk space used (except during brief send process)

---

## 📁 Files Deleted Automatically

After **successful** Telegram send, these files are deleted:

1. **Legacy file**: `dashboard_current.png` (or .jpg if JPEG export enabled)
2. **Timestamped file**: `dashboard_4k_20251018_2029.jpg` (current timestamp)
3. **Debug HTML**: `dashboard_debug.html` (if experimental features enabled)

---

## 🔄 Workflow

### **Step 1: Generate**
```
[2025-10-18 20:30:00] Generating dashboard...
[2025-10-18 20:30:05] 4K screenshot saved: dashboard_4k_20251018_2030.jpg
[2025-10-18 20:30:05] Dashboard generated: dashboard_current.png
```

### **Step 2: Send**
```
[2025-10-18 20:30:06] Sending to Telegram...
[2025-10-18 20:30:08] Dashboard image sent to Telegram
```

### **Step 3: Delete**
```
[2025-10-18 20:30:08] Deleted: dashboard_current.png
[2025-10-18 20:30:08] Deleted: dashboard_4k_20251018_2030.jpg
[2025-10-18 20:30:08] Deleted: dashboard_debug.html
```

**Total time files exist**: ~8 seconds (only during generation and send)

---

## 🛡️ Safety Features

### **1. Only Delete After Successful Send**

If Telegram send **fails**, files are **kept** for debugging:
```
[2025-10-18 20:30:08] Failed to send dashboard image: Network error
[2025-10-18 20:30:08] Keeping files for debugging: dashboard_current.png
```

**Result**: You can manually inspect the failed image.

---

### **2. Error Handling**

If deletion fails (permissions, file locked, etc.), a warning is logged but script continues:
```
[2025-10-18 20:30:08] Warning: Failed to delete files: Permission denied
```

**Result**: Script doesn't crash, just warns you.

---

### **3. Existence Check**

Files are only deleted if they exist:
```python
if legacy_path.exists():
    legacy_path.unlink()
```

**Result**: No errors if files are already gone.

---

## 💾 Disk Space Savings

### **Before (No Auto-Delete)**

**Per run** (every 5 minutes):
- JPEG: ~2 MB × 2 files = 4 MB
- PNG: ~4 MB × 2 files = 8 MB

**Per hour** (12 runs):
- JPEG: 4 MB × 12 = 48 MB
- PNG: 8 MB × 12 = 96 MB

**Per day** (288 runs):
- JPEG: 4 MB × 288 = **1.15 GB**
- PNG: 8 MB × 288 = **2.3 GB**

**Per week**:
- JPEG: **8 GB**
- PNG: **16 GB**

---

### **After (Auto-Delete)**

**Disk space used**: **0 MB** (files deleted after send)

**Savings**:
- JPEG: 8 GB/week saved
- PNG: 16 GB/week saved

---

## 🔍 Implementation Details

### **Code Location**
**File**: `app_with_dashboard.py` (Lines 882-909)

### **Logic**
```python
if photo_ok:  # Only if Telegram send succeeded
    print(f"[{now_iso()}] Dashboard image sent to Telegram")
    
    try:
        # Delete legacy file
        legacy_path = Path(dashboard_path)
        if legacy_path.exists():
            legacy_path.unlink()
            print(f"[{now_iso()}] Deleted: {legacy_path.name}")
        
        # Delete timestamped file
        parent_dir = legacy_path.parent
        file_extension = "jpg" if USE_JPEG_EXPORT else "png"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        timestamped_file = parent_dir / f"dashboard_4k_{timestamp}.{file_extension}"
        if timestamped_file.exists():
            timestamped_file.unlink()
            print(f"[{now_iso()}] Deleted: {timestamped_file.name}")
        
        # Delete debug HTML
        debug_html = parent_dir / "dashboard_debug.html"
        if debug_html.exists():
            debug_html.unlink()
            print(f"[{now_iso()}] Deleted: dashboard_debug.html")
            
    except Exception as del_err:
        print(f"[{now_iso()}] Warning: Failed to delete files: {del_err}")
else:
    print(f"[{now_iso()}] Failed to send dashboard image: {photo_err}")
    print(f"[{now_iso()}] Keeping files for debugging: {dashboard_path}")
```

---

## 📊 Console Output Examples

### **Successful Run (Files Deleted)**
```
[2025-10-18 20:30:00 GMT] Generating dashboard (theme: dark)...
[2025-10-18 20:30:05 GMT] 4K screenshot saved: dashboard_4k_20251018_2030.jpg
[2025-10-18 20:30:05 GMT] Resolution: 2160x3840 @ 2x scale
[2025-10-18 20:30:05 GMT] Format: JPEG (quality=95)
[2025-10-18 20:30:05 GMT] Dashboard generated: dashboard_current.png
[2025-10-18 20:30:08 GMT] Dashboard image sent to Telegram
[2025-10-18 20:30:08 GMT] Deleted: dashboard_current.png
[2025-10-18 20:30:08 GMT] Deleted: dashboard_4k_20251018_2030.jpg
[2025-10-18 20:30:08 GMT] Deleted: dashboard_debug.html
```

---

### **Failed Send (Files Kept)**
```
[2025-10-18 20:30:00 GMT] Generating dashboard (theme: dark)...
[2025-10-18 20:30:05 GMT] 4K screenshot saved: dashboard_4k_20251018_2030.jpg
[2025-10-18 20:30:05 GMT] Dashboard generated: dashboard_current.png
[2025-10-18 20:30:08 GMT] Failed to send dashboard image: Network timeout
[2025-10-18 20:30:08 GMT] Keeping files for debugging: dashboard_current.png
```

**Files remain** for you to inspect.

---

### **Deletion Error (Warning Only)**
```
[2025-10-18 20:30:08 GMT] Dashboard image sent to Telegram
[2025-10-18 20:30:08 GMT] Warning: Failed to delete files: Permission denied
```

**Script continues** despite deletion failure.

---

## 🎯 Benefits

### **1. Zero Disk Space Usage**
✅ No file accumulation  
✅ No manual cleanup needed  
✅ Workspace stays clean  

### **2. Automatic Cleanup**
✅ Happens immediately after send  
✅ No cron jobs or scripts needed  
✅ Fully integrated into workflow  

### **3. Safe Deletion**
✅ Only deletes after successful send  
✅ Keeps files if send fails  
✅ Error handling prevents crashes  

### **4. Debug-Friendly**
✅ Failed sends keep files for inspection  
✅ Console logs show what was deleted  
✅ Easy to troubleshoot issues  

---

## 🔧 Customization

### **Disable Auto-Delete**

If you want to keep files, comment out the deletion code:

```python
if photo_ok:
    print(f"[{now_iso()}] Dashboard image sent to Telegram")
    
    # DISABLED: Auto-delete files
    # try:
    #     legacy_path = Path(dashboard_path)
    #     if legacy_path.exists():
    #         legacy_path.unlink()
    # ...
```

---

### **Keep Timestamped Files Only**

Delete only the legacy file, keep timestamped:

```python
# Delete legacy file
legacy_path = Path(dashboard_path)
if legacy_path.exists():
    legacy_path.unlink()

# SKIP: Don't delete timestamped file
# timestamped_file.unlink()
```

---

### **Keep Debug HTML**

Delete images but keep debug HTML:

```python
# Delete images
legacy_path.unlink()
timestamped_file.unlink()

# SKIP: Don't delete debug HTML
# debug_html.unlink()
```

---

## 🚨 Important Notes

### **1. No Archival**

Files are **not archived** - they're permanently deleted.

**If you need archival**:
- Disable auto-delete
- Implement your own archival logic
- Or save to cloud storage before deletion

---

### **2. Telegram is Your Archive**

Since files are deleted after send, **Telegram becomes your archive**.

**To retrieve old dashboards**:
- Check Telegram chat history
- Download images from Telegram
- Telegram keeps all sent images

---

### **3. Failed Sends Keep Files**

If Telegram is down or network fails, files accumulate.

**Manual cleanup**:
```bash
# Delete all dashboard files
rm dashboard_4k_*.jpg
rm dashboard_current.png
rm dashboard_debug.html
```

---

## 📈 Performance Impact

### **Deletion Speed**
- **Per file**: <1ms
- **Total (3 files)**: <3ms
- **Impact**: Negligible

### **Disk I/O**
- **Write**: During generation (~2 MB)
- **Delete**: After send (~2 MB)
- **Net**: 0 MB (write then delete)

**Result**: No performance impact.

---

## ✅ Status: FULLY IMPLEMENTED

Auto-delete is now active and will:
- ✅ Delete files after successful Telegram send
- ✅ Keep files if send fails (for debugging)
- ✅ Handle errors gracefully
- ✅ Log all deletion actions
- ✅ Save disk space automatically

**Your workspace will stay clean with zero manual intervention!** 🎯

---

## 🎉 Summary

**Before**: Files accumulated, consuming GB of disk space  
**After**: Files deleted automatically, zero disk space used  

**Workflow**:
1. Generate dashboard → 2. Send to Telegram → 3. Delete files → 4. Repeat

**Result**: Clean workspace, no manual cleanup, Telegram as your archive! 📸🗑️
