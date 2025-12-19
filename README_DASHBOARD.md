# NI Emergency Department Wait Times Dashboard

A modern, professional dashboard system for monitoring and sharing NI Emergency Department wait times on social media.

## Features

- **Clean, Modern Design**: Tailwind CSS-based dashboard with NHS-style clarity
- **Automatic Image Generation**: Uses Playwright to render dashboard as PNG images
- **Multiple Aspect Ratios**: Generates both 16:9 (Facebook landscape) and 1:1 (Instagram/Facebook square) images
- **Real-time Data**: Fetches live data from NI Direct
- **Telegram Integration**: Automatically posts updates with dashboard images
- **Professional Branding**: Includes logo placement and watermark options

## Files Overview

- `dashboard.html` - Tailwind CSS dashboard template
- `generate_dashboard_image.py` - Python script to generate dashboard images using Playwright
- `app_with_images.py` - Integrated monitoring + image generation script
- `app.py` - Original text-only monitoring script (still works independently)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

After installing the Python package, you need to install the browser binaries:

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright uses to render the dashboard.

## Usage

### Option 1: Generate Images Only (Testing)

To test the dashboard image generation with sample data:

```bash
python generate_dashboard_image.py
```

This will create:
- `hospital_wait_dashboard.png` (16:9 aspect ratio - 1920x1080)
- `hospital_wait_dashboard_square.png` (1:1 aspect ratio - 1080x1080)

### Option 2: Full Monitoring with Images

To run the full monitoring system that sends both text updates and dashboard images to Telegram:

```bash
python app_with_images.py
```

This will:
1. Monitor NI Direct for wait time updates every 5 minutes
2. Generate dashboard images when changes are detected
3. Send dashboard image to Telegram with caption
4. Track changes and maintain state

### Option 3: Text-Only Monitoring (Original)

If you prefer text-only updates without images:

```bash
python app.py
```

## Customization

### Logo

Replace the placeholder logo in `dashboard.html` (line 42):

```html
<img src="your-logo.png" alt="Logo" class="w-20 h-20">
```

Or keep the styled text placeholder and customize it.

### Colors and Styling

The dashboard uses Tailwind CSS. Edit `dashboard.html` to customize:
- Colors: Change `bg-gray-50`, `text-red-600`, etc.
- Spacing: Modify `p-4`, `mb-6`, etc.
- Borders: Adjust `rounded-2xl`, `shadow-lg`, etc.

### Image Dimensions

Edit `generate_dashboard_image.py` to change output sizes:

```python
# For 16:9 images
await generate_dashboard_image(rows, timestamp, width=1920, height=1080)

# For 1:1 images  
await generate_dashboard_image(rows, timestamp, width=1080, height=1080)

# For 4:5 (Instagram portrait)
await generate_dashboard_image(rows, timestamp, width=1080, height=1350)
```

### Watermark

The dashboard includes a subtle "NIERV" watermark. Edit in `dashboard.html`:

```html
<div class="watermark">NIERV</div>
```

Change the text or remove entirely by deleting this div.

## Configuration

### Telegram Settings

Edit in `app_with_images.py`:

```python
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID = "your-chat-id"
```

### Monitoring Settings

```python
POLL_SECONDS = 300  # Check every 5 minutes
FORCE_SEND = False  # Set True to send every cycle regardless of changes
SEND_IMAGES = True  # Set False to disable image generation
```

## How It Works

1. **Data Collection**: Scrapes NI Direct website for emergency department wait times
2. **Change Detection**: Compares with previous data using SHA256 hash
3. **Data Processing**: 
   - Calculates statistics (longest wait, average, count)
   - Formats hospital names with abbreviations
   - Assigns severity emojis and colors
4. **Image Generation**:
   - Injects data into HTML template
   - Launches headless Chromium browser
   - Renders page at specified resolution
   - Captures screenshot as PNG
5. **Telegram Posting**: Sends image with caption to configured chat

## Dashboard Layout

The dashboard includes:

### Header
- Title with ambulance emoji
- Last updated timestamp
- Logo/branding area

### Summary Stats
- Longest wait time
- Average wait time across all hospitals
- Total hospitals reporting

### Main Table
- Severity indicator (emoji)
- Wait time (color-coded)
- Hospital name (abbreviated)

### Footer
- Data source attribution
- Severity key legend
- Telegram channel link
- Triage information note

## Troubleshooting

### Playwright Installation Issues

If `playwright install` fails:
```bash
# Try with specific browser
playwright install chromium

# Or with sudo/admin if permissions issue
```

### Font Rendering Issues

The dashboard uses system fonts. If fonts look wrong:
- Ensure you have good system fonts installed
- Edit `dashboard.html` to specify different fonts
- Playwright uses the system font stack

### Image Generation Timeout

If images take too long to generate:
```python
# Reduce wait time in generate_dashboard_image.py
await asyncio.sleep(0.5)  # Instead of 1 second
```

### Memory Issues

If running on low-memory system:
```python
# Use lower device_scale_factor
device_scale_factor=1  # Instead of 2 (less quality but smaller memory)
```

## Examples

### Integrating with Existing Scripts

```python
from generate_dashboard_image import generate_dashboard_image
import asyncio

# Your existing data fetching
rows = fetch_hospital_data()
timestamp = get_timestamp()

# Generate image
asyncio.run(generate_dashboard_image(rows, timestamp, "output.png"))
```

### Custom Data Format

The dashboard expects data in this format:

```python
rows = [
    {
        "hospital": "Hospital Name",
        "wait_mins": 120,  # or None
        "status": "Open"
    },
    # ... more hospitals
]
```

## License

This is part of the NI Emergency Response Videos monitoring suite.

## Support

For issues or questions, contact via Telegram: t.me/NIIncidentAlerts
