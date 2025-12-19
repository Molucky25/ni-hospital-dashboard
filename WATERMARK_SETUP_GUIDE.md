# Watermark Setup Guide 🎨

## The Issue

The watermark wasn't showing because it needs to be set via JavaScript. The CSS just defines how it looks, but the actual image needs to be loaded.

---

## Quick Test (Now Fixed!)

I've added auto-loading code to `dashboard.html`. Now when you open it in a browser, it will automatically try to load `logo.jpg` as the watermark.

### **To Test:**
1. Open `dashboard.html` in your browser
2. Watermark should now be visible!

### **If Still Not Visible:**
The logo file might have a different name. Try changing line 379 in `dashboard.html`:

```javascript
const logoPath = 'logo.jpg';  // Change to one of these:
// 'NIERV Logo.jpg'
// 'logo.png'
// 'logo-dark.png'
```

---

## How It Works

### **1. CSS (Defines Appearance):**
```css
.watermark {
    opacity: 0.35;           /* Visibility */
    width: 95%;              /* Size */
    background-image: ???    /* ← Needs to be set! */
}
```

### **2. JavaScript (Sets the Image):**
```javascript
document.getElementById('logo-watermark')
    .style.backgroundImage = `url('logo.jpg')`;
```

**Without JavaScript setting the image, CSS has nothing to display!**

---

## For Python Integration

When your Python script generates the dashboard, it should call:

```python
# In your generate_dashboard_image.py

dashboard_data = {
    'logoPath': 'logo.jpg',  # or full path
    'hospitals': [...],
    # ... other data
}

# The JavaScript will use this:
# setLogo(data.logoPath);
```

---

## Logo File Options

You have these logo files available:
1. `logo.jpg`
2. `NIERV Logo.jpg`
3. `logo.png`
4. `logo-dark.png`

**Choose the one that looks best as a watermark!**

---

## Current Auto-Load Code

Added to `dashboard.html` (line 377-381):

```javascript
window.addEventListener('DOMContentLoaded', function() {
    const logoPath = 'logo.jpg';
    document.getElementById('logo-watermark')
        .style.backgroundImage = `url('${logoPath}')`;
});
```

**This runs automatically when page loads!**

---

## Watermark Settings (Already Perfect!)

```css
.watermark {
    opacity: 0.35;              /* 35% visible */
    width: 95%;                 /* Large coverage */
    height: 95%;                /* Large coverage */
    filter: grayscale(0%)       /* Full color */
            brightness(1.15)    /* 15% brighter */
            contrast(1.1);      /* 10% sharper */
}
```

---

## Troubleshooting

### **Still Can't See Watermark?**

#### **Check 1: Logo File Name**
Make sure the filename in line 379 matches your actual file:
```javascript
const logoPath = 'logo.jpg';  // ← Check this matches your file
```

#### **Check 2: File Location**
Logo file must be in the same folder as `dashboard.html`

#### **Check 3: Browser Console**
1. Open browser DevTools (F12)
2. Check Console for errors
3. Look for "Failed to load resource" messages

#### **Check 4: File Path**
If logo is in a subfolder:
```javascript
const logoPath = 'images/logo.jpg';  // Adjust path
```

---

## For Production (Python Script)

### **Option 1: Pass Logo Path**
```python
def generate_dashboard_image(data, logo_path='logo.jpg'):
    dashboard_data = {
        'logoPath': logo_path,
        'hospitals': data,
        # ...
    }
    # Render with Playwright/Puppeteer
```

### **Option 2: Embed Logo as Base64**
```python
import base64

def get_logo_base64(logo_path):
    with open(logo_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

logo_data = f"data:image/jpeg;base64,{get_logo_base64('logo.jpg')}"

dashboard_data = {
    'logoPath': logo_data,  # Embedded!
    # ...
}
```

**Base64 embedding is better for image generation - no file path issues!**

---

## Expected Result

When working correctly, you should see:
- ✅ Large, semi-transparent logo in center background
- ✅ 35% opacity (clearly visible but not distracting)
- ✅ Full color (no grayscale)
- ✅ Covers 95% of container
- ✅ Behind all content (z-index: 0)

---

## Summary

### **The Problem:**
- CSS defined watermark style
- But no image was set via JavaScript
- Result: Invisible watermark

### **The Solution:**
- Added auto-load code in JavaScript
- Sets `logo.jpg` as watermark on page load
- Now visible immediately!

### **Next Steps:**
1. Open `dashboard.html` in browser
2. Check if watermark appears
3. If not, adjust logo filename in line 379
4. For Python: Pass logo path or embed as base64

---

**Your watermark should now be visible!** 🎉

**If you still can't see it, let me know which logo file you want to use and I'll update the path!**
