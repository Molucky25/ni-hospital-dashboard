"""
Generate a Facebook post image from NI Emergency Department wait times data.
Uses Playwright to render the HTML dashboard and capture a screenshot.
"""

import asyncio
import json
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright


# Logo path
LOGO_PATH = r"C:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait\NIERV Logo.jpg"


def logo_to_base64(logo_path: str) -> str:
    """Convert logo image to base64 data URL for embedding in HTML."""
    try:
        with open(logo_path, "rb") as f:
            logo_data = f.read()
            logo_b64 = base64.b64encode(logo_data).decode('utf-8')
            # Detect image format
            ext = Path(logo_path).suffix.lower()
            mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
            return f"data:{mime_type};base64,{logo_b64}"
    except Exception as e:
        print(f"Warning: Could not load logo: {e}")
        return ""

# Historical data file for trend tracking
TREND_DATA_FILE = "hospital_wait_trends.jsonl"


def get_severity_emoji(minutes: Optional[int]) -> str:
    """Return severity emoji based on wait time."""
    if minutes is None:
        return "⚪"
    if minutes >= 240:
        return "🔴"
    if minutes >= 120:
        return "🟠"
    if minutes >= 60:
        return "🟡"
    return "🟢"


def get_severity_color_class(minutes: Optional[int]) -> str:
    """Return Tailwind CSS color class based on wait time."""
    if minutes is None:
        return "text-gray-400"
    if minutes >= 240:
        return "text-red-600"
    if minutes >= 120:
        return "text-orange-500"
    if minutes >= 60:
        return "text-yellow-500"
    return "text-green-500"


def abbreviate_hospital_name(name: str) -> str:
    """Abbreviate hospital names for display."""
    replacements = [
        ("Hospital and Primary Care Complex", "Hospital & PCC"),
        ("Emergency Department", "ED"),
        ("Minor Injuries Unit", "MIU"),
        ("Minor Injury Unit", "MIU"),
        ("Urgent care and treatment Centre", "UCTC"),
        ("Urgent Care and Treatment Centre", "UCTC"),
        (" Hospital", ""),
    ]
    for old, new in replacements:
        name = name.replace(old, new)
    name = " ".join(name.split())
    return name.strip() if name.strip() else "Unknown"


def load_historical_data(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Load historical data from JSONL file.
    Returns list of historical snapshots within the specified hours.
    """
    historical = []
    try:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        if Path(TREND_DATA_FILE).exists():
            with open(TREND_DATA_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                        if entry_time >= cutoff:
                            historical.append(entry)
                    except Exception:
                        continue
    except Exception as e:
        print(f"Warning: Could not load historical data: {e}")
    
    return historical


def save_historical_snapshot(rows: List[Dict[str, Any]]) -> None:
    """
    Append current data snapshot to historical trend file.
    Keeps only last 7 days of data to prevent file from growing indefinitely.
    """
    try:
        from datetime import timedelta
        
        # Calculate average wait time
        valid_waits = [r["wait_mins"] for r in rows if r["wait_mins"] is not None]
        avg_wait = sum(valid_waits) // len(valid_waits) if valid_waits else 0
        
        # Create hospital snapshot
        hospital_data = {}
        for row in rows:
            if row["wait_mins"] is not None:
                hospital_data[row["hospital"]] = row["wait_mins"]
        
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "avg_wait": avg_wait,
            "hospitals": hospital_data
        }
        
        # Append to file
        with open(TREND_DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        
        # Clean up old data (keep last 7 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        temp_file = TREND_DATA_FILE + ".tmp"
        
        with open(TREND_DATA_FILE, "r", encoding="utf-8") as f_in:
            with open(temp_file, "w", encoding="utf-8") as f_out:
                for line in f_in:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                        if entry_time >= cutoff:
                            f_out.write(line)
                    except Exception:
                        continue
        
        # Replace original file
        Path(temp_file).replace(TREND_DATA_FILE)
        
    except Exception as e:
        print(f"Warning: Could not save historical snapshot: {e}")


def calculate_hospital_trends(rows: List[Dict[str, Any]], historical: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Calculate trend direction for each hospital based on recent history.
    Returns dict mapping hospital name to trend ('up', 'down', or None).
    """
    trends = {}
    
    if len(historical) < 2:
        return trends
    
    # Get average from 4-8 hours ago as baseline
    baseline_entries = [h for h in historical if len(historical) - historical.index(h) > len(historical) // 2]
    
    if not baseline_entries:
        return trends
    
    for row in rows:
        hospital = row["hospital"]
        current_wait = row["wait_mins"]
        
        if current_wait is None:
            continue
        
        # Calculate baseline average for this hospital
        baseline_waits = []
        for entry in baseline_entries:
            if hospital in entry.get("hospitals", {}):
                baseline_waits.append(entry["hospitals"][hospital])
        
        if baseline_waits:
            baseline_avg = sum(baseline_waits) / len(baseline_waits)
            diff = current_wait - baseline_avg
            
            # Only mark as trend if change is significant (>15 minutes)
            if diff > 15:
                trends[hospital] = "up"
            elif diff < -15:
                trends[hospital] = "down"
    
    return trends


def calculate_24h_trend_data(historical: List[Dict[str, Any]]) -> List[int]:
    """
    Calculate hourly average wait times for sparkline.
    Returns list of average wait times, one per hour for last 24 hours.
    """
    if len(historical) < 2:
        return []
    
    from datetime import timedelta
    
    # Group by hour
    hourly_data = {}
    for entry in historical:
        try:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
            
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            
            hourly_data[hour_key].append(entry["avg_wait"])
        except Exception:
            continue
    
    # Calculate average for each hour and sort by time
    hourly_averages = []
    for hour in sorted(hourly_data.keys()):
        avg = sum(hourly_data[hour]) // len(hourly_data[hour])
        hourly_averages.append(avg)
    
    # Return last 24 data points (or all if less than 24)
    return hourly_averages[-24:] if len(hourly_averages) > 24 else hourly_averages


def prepare_dashboard_data(rows: List[Dict[str, Any]], last_updated: str, logo_path: str = LOGO_PATH) -> Dict[str, Any]:
    """
    Prepare data structure for the dashboard.
    
    Args:
        rows: List of hospital data dicts with 'hospital', 'wait_mins', 'status' keys
        last_updated: Timestamp string for last update
    
    Returns:
        Dictionary with formatted data for the dashboard
    """
    # Sort by wait time descending
    sorted_rows = sorted(rows, key=lambda r: (r["wait_mins"] is None, -(r["wait_mins"] or 0)))
    
    # Calculate statistics
    valid_waits = [r["wait_mins"] for r in rows if r["wait_mins"] is not None]
    avg_wait = sum(valid_waits) // len(valid_waits) if valid_waits else 0
    
    # Find longest wait
    longest = sorted_rows[0] if sorted_rows else None
    longest_name = abbreviate_hospital_name(longest["hospital"]) if longest else "N/A"
    longest_wait = longest["wait_mins"] if longest else 0
    longest_emoji = get_severity_emoji(longest_wait)
    
    # Format longest wait display
    longest_wait_html = (
        f'{longest_name} — <span class="{get_severity_color_class(longest_wait)}">'
        f'{longest_wait}m {longest_emoji}</span>'
    )
    
    # Format average wait display
    avg_emoji = get_severity_emoji(avg_wait)
    avg_wait_html = (
        f'<span class="{get_severity_color_class(avg_wait)}">'
        f'{avg_wait}m {avg_emoji}</span>'
    )
    
    # Load historical data for trends
    historical = load_historical_data(24)
    trends = calculate_hospital_trends(rows, historical)
    trend_data = calculate_24h_trend_data(historical)
    
    # Save current snapshot for future trend calculation
    save_historical_snapshot(rows)
    
    # Prepare hospital rows for table
    hospitals = []
    for row in sorted_rows:
        wait = row["wait_mins"]
        hospital_name = row["hospital"]
        trend = trends.get(hospital_name)
        
        hospitals.append({
            "emoji": get_severity_emoji(wait),
            "wait": wait if wait is not None else "N/A",
            "name": abbreviate_hospital_name(hospital_name),
            "colorClass": get_severity_color_class(wait),
            "trend": trend
        })
    
    # Convert logo to base64 for embedding
    logo_data_url = logo_to_base64(logo_path) if Path(logo_path).exists() else ""
    
    return {
        "updateTime": last_updated,
        "longestWait": longest_wait_html,
        "avgWait": avg_wait_html,
        "hospitalCount": len(rows),
        "hospitals": hospitals,
        "trendData": trend_data,
        "logoPath": logo_data_url
    }


async def generate_dashboard_image(
    rows: List[Dict[str, Any]],
    last_updated: str,
    output_path: str = "hospital_wait_dashboard.png",
    width: int = 1920,
    height: int = 1080
):
    """
    Generate a dashboard image using Playwright.
    
    Args:
        rows: List of hospital data dicts
        last_updated: Timestamp string
        output_path: Where to save the PNG
        width: Image width in pixels (default 1920 for 16:9 at 1080p)
        height: Image height in pixels (default 1080)
    """
    # Prepare data
    data = prepare_dashboard_data(rows, last_updated)
    
    # Read the HTML template
    html_path = Path(__file__).parent / "dashboard.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject data into HTML
    data_json = json.dumps(data, ensure_ascii=False)
    inject_script = f"""
    <script>
        const dashboardData = {data_json};
        updateDashboard(dashboardData);
    </script>
    """
    html_content = html_content.replace("</body>", f"{inject_script}</body>")
    
    # Launch Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2  # Higher quality rendering
        )
        
        # Set content and wait for rendering
        await page.set_content(html_content, wait_until="networkidle")
        
        # Wait a bit for fonts and rendering
        await asyncio.sleep(1)
        
        # Take screenshot
        await page.screenshot(path=output_path, full_page=False)
        
        await browser.close()
    
    print(f"Dashboard image saved to: {output_path}")


async def generate_square_dashboard_image(
    rows: List[Dict[str, Any]],
    last_updated: str,
    output_path: str = "hospital_wait_dashboard_square.png"
):
    """Generate a 1:1 aspect ratio version for Instagram/Facebook square posts."""
    await generate_dashboard_image(rows, last_updated, output_path, width=1080, height=1080)


# Example usage
async def main():
    """Example of how to use the dashboard generator."""
    # Sample data - in production, this would come from your app.py
    sample_rows = [
        {"hospital": "Altnagelvin Area Hospital Emergency Department", "wait_mins": 317, "status": "Open"},
        {"hospital": "Royal Victoria Hospital Emergency Department", "wait_mins": 281, "status": "Open"},
        {"hospital": "Ulster Hospital Emergency Department", "wait_mins": 238, "status": "Open"},
        {"hospital": "Mater Hospital Emergency Department", "wait_mins": 220, "status": "Open"},
        {"hospital": "Antrim Area Hospital Emergency Department", "wait_mins": 162, "status": "Open"},
        {"hospital": "Craigavon Area Hospital Emergency Department", "wait_mins": 157, "status": "Open"},
        {"hospital": "Causeway Hospital Emergency Department", "wait_mins": 152, "status": "Open"},
        {"hospital": "South West Acute Hospital Emergency Department", "wait_mins": 131, "status": "Open"},
        {"hospital": "Royal Children's Hospital Emergency Department", "wait_mins": 119, "status": "Open"},
        {"hospital": "Daisy Hill Hospital Emergency Department", "wait_mins": 86, "status": "Open"},
    ]
    
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%I:%M %p, %a %d %b %Y")
    
    # Generate 16:9 image (for Facebook landscape posts)
    await generate_dashboard_image(sample_rows, timestamp)
    
    # Generate 1:1 image (for Instagram/Facebook square posts)
    await generate_square_dashboard_image(sample_rows, timestamp)


if __name__ == "__main__":
    asyncio.run(main())
