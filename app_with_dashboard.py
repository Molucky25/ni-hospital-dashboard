import requests
import time
import hashlib
import json
import html
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import re
from bs4 import BeautifulSoup
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

# Import trend cache system
from trend_cache_system import HospitalTrendCache

# Import daily stats system
from daily_stats_system import daily_stats_tracker

# === Configuration ===
# Primary NI Direct source (Emergency Departments)
NI_DIRECT_URL = "https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times"

# Telegram credentials (user provided)
TELEGRAM_BOT_TOKEN = "8331970465:AAGSDG6PkCN1RQ27kcj0Zk0zIlfkRuNbE4Y"
TELEGRAM_CHAT_ID = "-1002987638683"

# Polling interval (seconds)
POLL_SECONDS = 300

# Testing: force send every cycle (bypass no-change detection)
FORCE_SEND = False  # set to False to re-enable change detection

# Mobile-friendly output (compact, no table header, better for phones)
MOBILE_COMPACT = True

# Local state file for change detection
STATE_FILE = "state.json"

# Severity thresholds (minutes)
THRESHOLDS = {
    "red": 240,
    "orange": 120,
    "yellow": 60,
}

# Dashboard configuration
GENERATE_DASHBOARD = True  # Set to False to disable dashboard generation
DASHBOARD_FILE = "dashboard_current.png"  # Legacy filename for compatibility
DASHBOARD_HTML_TEMPLATE = "dashboard.html"

# 4K Screenshot configuration
SCREENSHOT_4K_WIDTH = 3840
SCREENSHOT_4K_HEIGHT = 2160
SCREENSHOT_DEVICE_SCALE = 2  # Retina-level clarity

# === EXPERIMENTAL FEATURES (Easy to toggle) ===
# Feature 1: Portrait mode for better Telegram compression
USE_PORTRAIT_MODE = True  # Set to True to flip to 2160x3840 (preserves text detail)

# Feature 2: Global text scaling for better readability after compression
USE_TEXT_SCALING = True  # Set to True to scale all text by 25%
TEXT_SCALE_FACTOR = 1.50  # 1.25 = 25% larger, 1.30 = 30% larger

# Feature 3: JPEG export for better Telegram compression
USE_JPEG_EXPORT = True  # Set to True to export as JPEG instead of PNG
JPEG_QUALITY = 95  # 95 = high quality, avoids Telegram's aggressive re-encode

# Apply experimental settings
if USE_PORTRAIT_MODE:
    SCREENSHOT_4K_WIDTH, SCREENSHOT_4K_HEIGHT = 2160, 3840  # Flip to portrait

# Initialize trend cache
trend_cache = HospitalTrendCache(
    cache_file="hospital_wait_cache.json",
    history_file="hospital_wait_history.json"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def get_auto_theme() -> str:
    """Force dark mode for dashboard generation"""
    return 'dark'


# === NI Direct scraper === (Keep all your existing functions)
def abbreviate_hospital_name(name: str) -> str:
    """
    Abbreviate hospital names for cleaner display.
    Replaces long phrases with shorter versions.
    """
    replacements = [
        ("Hospital and Primary Care Complex", "Hospital & PCC"),
        ("Emergency Department", "ED"),
        ("Minor Injuries Unit", "MIU"),
        ("Minor Injury Unit", "MIU"),
        ("Urgent care and treatment Centre", "UCTC"),
        ("Urgent Care and Treatment Centre", "UCTC"),
        ("Area Hospital", "Area"),
        ("Hospital", ""),  # Remove standalone "Hospital" if not already replaced
    ]
    
    result = name
    for old, new in replacements:
        result = result.replace(old, new)
    
    # Clean up extra spaces
    result = " ".join(result.split())
    
    return result


def parse_wait_to_minutes(text: str) -> Optional[int]:
    if not text:
        return None
    s = text.strip().lower()
    # Normalizations
    s = s.replace("mins", "minutes").replace("min", "minutes")
    s = s.replace("hrs", "hours").replace("hr", "hours")
    # Direct N/A
    if any(x in s for x in ["n/a", "not available", "no data", "closed"]):
        return None
    # "Over X hours" or "More than X hours"
    m = re.search(r"(over|more than)\s+(\d+)\s+hours?", s)
    if m:
        return int(m.group(2)) * 60
    # "Up to X minutes"
    m = re.search(r"up to\s+(\d+)\s+minutes?", s)
    if m:
        return int(m.group(1))
    # "X hours Y minutes"
    m = re.search(r"(\d+)\s+hours?\s*(\d+)?\s*minutes?", s)
    if m:
        hours = int(m.group(1))
        minutes = int(m.group(2)) if m.group(2) else 0
        return hours * 60 + minutes
    # "X hours"
    m = re.search(r"(\d+)\s+hours?", s)
    if m:
        return int(m.group(1)) * 60
    # "X minutes"
    m = re.search(r"(\d+)\s+minutes?", s)
    if m:
        return int(m.group(1))
    # Bare number (assume minutes)
    m = re.search(r"\b(\d+)\b", s)
    if m:
        return int(m.group(1))
    return None


def fetch_ni_direct_rows() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    r = requests.get(NI_DIRECT_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the heading for "Emergency Departments" and the first table after it
    heading = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if "emergency departments" in tag.get_text(strip=True).lower():
            heading = tag
            break
    table = None
    if heading is not None:
        # Search next siblings for a table
        nxt = heading
        for _ in range(20):  # look ahead a few siblings
            nxt = nxt.find_next_sibling()
            if nxt is None:
                break
            if nxt.name == "table":
                table = nxt
                break
            # Sometimes tables are nested in a div/container
            inner_table = nxt.find("table") if hasattr(nxt, "find") else None
            if inner_table is not None:
                table = inner_table
                break
    if table is None:
        # Fallback: first table on page
        table = soup.find("table")
    if table is None:
        raise RuntimeError("NI Direct: Could not locate Emergency Departments table")

    # Map column indices from header
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    # Try to identify relevant columns
    def find_col(candidates: List[str]) -> Optional[int]:
        for i, h in enumerate(headers):
            hl = h.lower()
            for cand in candidates:
                if cand in hl:
                    return i
        return None

    idx_name = find_col(["hospital", "trust", "site", "department", "ed"])
    idx_wait = find_col(["average", "waiting", "wait"])
    # If no thead, compute from first row
    if idx_name is None or idx_wait is None:
        first_row = table.find("tr")
        if first_row:
            cells = [c.get_text(strip=True) for c in first_row.find_all(["td", "th"])]
            # Heuristic: name is first, wait is a cell containing 'min' or 'hour'
            if idx_name is None:
                idx_name = 0 if cells else 0
            if idx_wait is None:
                for i, c in enumerate(cells):
                    if re.search(r"(min|hour)", c.lower()):
                        idx_wait = i
                        break
    if idx_name is None:
        idx_name = 0
    if idx_wait is None:
        idx_wait = 1

    rows: List[Dict[str, Any]] = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        tds = tr.find_all(["td", "th"])  # some tables use th for row headers
        if len(tds) < max(idx_name, idx_wait) + 1:
            continue
        # Skip header-like rows (all-th) or known header text
        if all(td.name == "th" for td in tds):
            continue
        name = tds[idx_name].get_text(strip=True)
        if "average waiting time" in name.lower():
            continue
        # Abbreviate hospital name for cleaner display
        name = abbreviate_hospital_name(name)
        wait_txt = tds[idx_wait].get_text(" ", strip=True)
        wait_mins = parse_wait_to_minutes(wait_txt)
        rows.append(
            {
                "hospital": name,
                "status": "Open",
                "wait_mins": wait_mins,
                "display_wait": wait_txt or (f"{wait_mins} mins" if wait_mins is not None else "N/A"),
                "last_updated": None,  # filled from page footer below
            }
        )

    # Last updated hint from page text
    last_updated_any: Optional[str] = None
    # Search near heading first
    context = heading.parent if heading else soup
    text_blob = context.get_text("\n", strip=True)
    m = re.search(r"last\s*updated\s*[:\-]?\s*(.+)", text_blob, re.I)
    if m:
        last_updated_any = m.group(1).split("\n")[0][:80]
    else:
        # Global search
        m2 = re.search(r"last\s*updated\s*[:\-]?\s*(.+)", soup.get_text("\n", strip=True), re.I)
        if m2:
            last_updated_any = m2.group(1).split("\n")[0][:80]

    # Attach the same last_updated to all rows for consistency
    if last_updated_any:
        for rrow in rows:
            rrow["last_updated"] = last_updated_any

    # Deduplicate by hospital
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for rrow in rows:
        key = rrow["hospital"].lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(rrow)

    # Sort by wait desc
    uniq.sort(key=lambda x: (x["wait_mins"] is None, -(x["wait_mins"] or 0)))
    return uniq, last_updated_any


def compute_digest(rows: List[Dict[str, Any]]) -> str:
    # Stable digest based on hospital|status|wait
    parts = []
    for r in sorted(rows, key=lambda x: x["hospital"].lower()):
        parts.append(f"{r['hospital']}|{r['status']}|{r['wait_mins']}")
    blob = "\n".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def severity_emoji(minutes: Optional[int]) -> str:
    if minutes is None:
        return "⚪"
    if minutes >= THRESHOLDS["red"]:
        return "🔴"
    if minutes >= THRESHOLDS["orange"]:
        return "🟠"
    if minutes >= THRESHOLDS["yellow"]:
        return "🟡"
    return "🟢"


def detect_changes(current_rows: List[Dict[str, Any]], previous_data: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Compare current rows with previous wait times and return a list of changes.
    Returns list of dicts with: hospital, old_wait, new_wait, change_mins
    """
    changes = []
    for row in current_rows:
        hospital = row["hospital"]
        new_wait = row["wait_mins"]
        old_wait = previous_data.get(hospital)
        
        # Only track changes where both old and new are valid numbers
        if old_wait is not None and new_wait is not None and old_wait != new_wait:
            changes.append({
                "hospital": hospital,
                "old_wait": old_wait,
                "new_wait": new_wait,
                "change_mins": new_wait - old_wait
            })
    
    return changes


def format_changes_section(changes: List[Dict[str, Any]]) -> str:
    """
    Format the changes section with emojis and clear display of increases/decreases.
    """
    if not changes:
        return ""
    
    # Sort by absolute change magnitude (largest changes first)
    changes_sorted = sorted(changes, key=lambda x: abs(x["change_mins"]), reverse=True)
    
    lines = ["<b>📊 What's Changed</b>\n"]
    
    for change in changes_sorted:
        hospital = change["hospital"]
        old = change["old_wait"]
        new = change["new_wait"]
        diff = change["change_mins"]
        
        # Choose emoji based on direction
        if diff > 0:
            emoji = "📈"  # Increase (worse)
            direction = "increased"
        else:
            emoji = "📉"  # Decrease (better)
            direction = "decreased"
            diff = abs(diff)  # Make positive for display
        
        # Abbreviate hospital name
        name_abbr = hospital
        replacements = [
            ("Hospital and Primary Care Complex", "Hospital & PCC"),
            ("Emergency Department", "ED"),
            ("Minor Injuries Unit", "MIU"),
            ("Minor Injury Unit", "MIU"),
            ("Urgent care and treatment Centre", "UCTC"),
            ("Urgent Care and Treatment Centre", "UCTC"),
            (" Hospital", ""),  # Remove " Hospital" (with leading space)
        ]
        for old_text, new_text in replacements:
            name_abbr = name_abbr.replace(old_text, new_text)
        name_abbr = " ".join(name_abbr.split()).strip()
        if not name_abbr:
            name_abbr = "Unknown"
        
        name_esc = html.escape(name_abbr)
        line = f"{emoji} <b>{name_esc}</b>: {old} m → {new} m ({direction} by {diff} m)"
        lines.append(line)
    
    return "\n".join(lines) + "\n\n"


def format_message(rows: List[Dict[str, Any]], source_label: str, last_updated_any: Optional[str], changes: Optional[List[Dict[str, Any]]] = None) -> str:
    # (Keep all your existing format_message logic - not repeating for brevity)
    # Just return your existing formatted message
    rows_sorted = sorted(rows, key=lambda r: (r["wait_mins"] is None, -(r["wait_mins"] or 0)))

    def abbr(name: str) -> str:
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

    header_time = last_updated_any or now_iso()
    header_time_esc = html.escape(header_time)

    if MOBILE_COMPACT:
        lines_html = []
        for r in rows_sorted:
            emoji = severity_emoji(r["wait_mins"])
            wait = r["wait_mins"]
            wait_str = f"{wait} m" if isinstance(wait, int) else (r["display_wait"] or "N/A")
            name = abbr(r["hospital"]) 
            name_esc = html.escape(name)
            line = f"{emoji} {wait_str} — {name_esc}"
            lines_html.append(line)
        body = "\n".join(lines_html)
        
        changes_section = ""
        if changes:
            changes_section = format_changes_section(changes) + "\n"
        
        header = (
            f"<b>🚑 NI Emergency Department Wait Times — Live Update</b>\n\n"
            f"<i>🕛 Updated: {header_time_esc}</i>\n\n"
            f"{changes_section}"
            f"<b>📊 Average over past 4 hours</b>\n\n"
            f"<b>Hospitals:</b>\n"
        )
        footer = (
            "\n\n"
            "🩺 <b>Severity Key:</b>\n\n"
            "🟢 &lt; 60 m | 🟡 60–119 m | 🟠 120–239 m | 🔴 ≥ 240 m\n\n"
            "<i>ℹ️ A&amp;E triage ensures the most urgent cases are treated first.</i>"
        )
        return header + body + footer

    return "Desktop format message..."  # Your existing desktop logic


def telegram_send_message(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        ok = r.status_code == 200 and data.get("ok", False)
        if not ok:
            err = data or {"status": r.status_code, "text": r.text[:200]}
            return False, str(err), None
        message_id = (data.get("result") or {}).get("message_id")
        return True, None, message_id
    except Exception as e:
        return False, str(e), None


def telegram_send_photo(image_path: str, caption: str = "") -> Tuple[bool, Optional[str]]:
    """Send image to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            r = requests.post(url, files=files, data=data, timeout=30)
        
        response_data = {}
        try:
            response_data = r.json()
        except Exception:
            pass
        
        ok = r.status_code == 200 and response_data.get("ok", False)
        if not ok:
            err = response_data or {"status": r.status_code, "text": r.text[:200]}
            return False, str(err)
        
        return True, None
    except Exception as e:
        return False, str(e)


async def generate_dashboard_image(hospitals_dict: Dict[str, int], theme: str = 'light', source_updated: str = None) -> Tuple[str, str]:
    """
    Generate dashboard image using Playwright
    
    Args:
        hospitals_dict: Dict of {hospital_name: wait_minutes}
        theme: 'light' or 'dark'
        source_updated: When NI Direct last updated (from their webpage)
    
    Returns:
        Tuple of (image_path, headline_text)
    """
    # Calculate all stats using trend cache
    trends = trend_cache.calculate_trends(hospitals_dict)
    biggest_change_24h = trend_cache.calculate_biggest_24h_change(hospitals_dict)
    pressure = trend_cache.calculate_pressure_index(hospitals_dict)
    
    # Helper function to get color class and emoji
    def get_color_info(wait):
        if wait >= 240:
            return 'text-red-600', '🔴'
        elif wait >= 120:
            return 'text-orange-500', '🟠'
        elif wait >= 60:
            return 'text-yellow-500', '🟡'
        else:
            return 'text-green-600', '🟢'
    
    # Helper function to get trend
    def get_trend(name):
        # Look for hospital in the changes list
        if 'changes' in trends:
            for change in trends['changes']:
                if change['hospital'] == name:
                    diff = change['diff']
                    if diff > 0:
                        return 'up'  # Wait time increased (worsening)
                    elif diff < 0:
                        return 'down'  # Wait time decreased (improving)
                    # If diff == 0, check last known trend
                    elif 'last_trends' in trends and name in trends['last_trends']:
                        trend = trends['last_trends'][name]
                        print(f"[TREND DEBUG] {name}: diff=0, using persisted trend '{trend}'")
                        return trend
        
        # Fallback to last known trend if hospital not in changes
        if 'last_trends' in trends and name in trends['last_trends']:
            trend = trends['last_trends'][name]
            print(f"[TREND DEBUG] {name}: not in changes, using persisted trend '{trend}'")
            return trend
        
        print(f"[TREND DEBUG] {name}: no trend data available")
        return None  # No change or no data
    
    # Sort hospitals by wait time (descending)
    sorted_hospitals = sorted(hospitals_dict.items(), key=lambda x: -x[1])
    
    # Extract fastest improvement details for before/after visualization
    fastest_improvement_detail = None
    if trends.get('fastest_improvement'):
        fastest = trends['fastest_improvement']
        print(f"[DEBUG] Fastest improvement raw: {fastest}")
        # Find the change data for this hospital
        for change in trends.get('changes', []):
            if change['hospital'] == fastest['hospital']:
                fastest_improvement_detail = {
                    'name': fastest['hospital'],
                    'before': change['previous'],
                    'after': change['current'],
                    'diff': change['diff']
                }
                print(f"[DEBUG] Fastest improvement detail: {fastest_improvement_detail}")
                break
    else:
        # No improvement yet - use first hospital as placeholder with no change
        print(f"[DEBUG] No fastest_improvement (value is None). Using placeholder.")
        if trends.get('changes') and len(trends['changes']) > 0:
            first_change = trends['changes'][0]
            fastest_improvement_detail = {
                'name': first_change['hospital'],
                'before': first_change['previous'],
                'after': first_change['current'],
                'diff': first_change['diff']
            }
            print(f"[DEBUG] Using placeholder: {fastest_improvement_detail}")
    
    # Calculate hourly trend (average wait time change)
    hourly_trend = None
    if trends.get('changes') and len(trends['changes']) > 0:
        # Calculate current and previous average
        current_avg = sum(hospitals_dict.values()) / len(hospitals_dict)
        previous_values = [c['previous'] for c in trends['changes']]
        if previous_values:
            previous_avg = sum(previous_values) / len(previous_values)
            change_minutes = current_avg - previous_avg
            percentage_change = (change_minutes / previous_avg) * 100 if previous_avg > 0 else 0
            
            # Format the hourly trend string (using inline SVG for better rendering)
            if percentage_change < 0:
                # Down arrow (improving)
                hourly_trend = f'<span class="inline-flex items-center gap-1 text-emerald-400"><svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg><span>{abs(percentage_change):.0f}% vs 1h ago</span></span>'
            elif percentage_change > 0:
                # Up arrow (worsening)
                hourly_trend = f'<span class="inline-flex items-center gap-1 text-rose-400"><svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg><span>{percentage_change:.0f}% vs 1h ago</span></span>'
            else:
                # Right arrow (stable)
                hourly_trend = '<span class="inline-flex items-center gap-1 text-slate-400"><svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"/></svg><span>0% vs 1h ago</span></span>'
            
            print(f"[DEBUG] Hourly trend: current_avg={current_avg:.1f}, previous_avg={previous_avg:.1f}, change={percentage_change:.1f}%")
    
    # Generate headline story
    headline = None
    if trends.get('changes') and len(trends['changes']) > 0:
        avg_wait = int(current_avg)
        avg_change = int(change_minutes) if 'change_minutes' in locals() else 0
        improving = trends.get('improving_count', 0)
        worsening = trends.get('worsening_count', 0)
        pressure_pct = pressure.get('percentage', 0)
        
        # Extract names for headlines
        fastest_improvement_name = trends['fastest_improvement']['hospital'].split()[0] if trends.get('fastest_improvement') else None
        fastest_improvement_drop = trends['fastest_improvement']['diff'] if trends.get('fastest_improvement') else 0
        longest_wait_name = sorted_hospitals[0][0].split()[0] if sorted_hospitals else None
        longest_wait_value = sorted_hospitals[0][1] if sorted_hospitals else 0
        
        # Extract biggest change info for headlines
        biggest_increase_name = None
        biggest_increase_change = 0
        if biggest_change_24h and biggest_change_24h.get('biggest_increase'):
            biggest_increase_name = biggest_change_24h['biggest_increase']['hospital'].split()[0]
            biggest_increase_change = biggest_change_24h['biggest_increase']['change']
        
        # Headline logic (priority order) - avoid duplicating hourly trend %
        if pressure_pct >= 70:
            # Severe pressure
            headline = f"High strain — {pressure_pct}% of hospitals over 2h."
        elif longest_wait_value >= 240:
            # Highlight critical longest wait
            headline = f"{longest_wait_name} under pressure — {longest_wait_value}m wait tops NI."
        elif avg_change < -5 and improving > worsening and fastest_improvement_name:
            # Improving situation - focus on specific hospital
            headline = f"{fastest_improvement_name} leads recovery — down {abs(int(fastest_improvement_drop))}m."
        elif avg_change > 5 and worsening > improving:
            # Worsening situation - focus on hospital count
            headline = f"Pressure building — {worsening} hospitals report longer waits."
        elif improving > 0 and worsening > 0:
            # Mixed picture
            headline = f"Mixed picture — {improving} improving, {worsening} worsening."
        elif biggest_increase_name and biggest_increase_change > 50:
            # Highlight significant 24h increase
            headline = f"{biggest_increase_name} surge — up {biggest_increase_change}m vs yesterday."
        elif improving > worsening and improving > 0:
            # General improvement without specific hospital
            headline = f"{improving} hospitals improving — waits trending down."
        else:
            # Default fallback - current average
            headline = f"Regional average wait time at {avg_wait}m."
        
        print(f"[DEBUG] Generated headline: {headline}")
    
    # Prepare JavaScript data injection
    # Use source timestamp if available, otherwise fall back to current time
    display_time = source_updated if source_updated else datetime.now().strftime('%I:%M %p, %a %d %b %Y')
    dashboard_data = {
        'theme': theme,
        'updateTime': display_time,
        'trendDirection': trend_cache.format_trend_direction(trends),
        'hourlyTrend': hourly_trend,
        'headline': headline,
        'improvingCount': trends.get('improving_count', 0),
        'worseningCount': trends.get('worsening_count', 0),
        'avgWait': f"{sum(hospitals_dict.values()) // len(hospitals_dict)}m" if hospitals_dict else "N/A",
        'longestWait': f"{sorted_hospitals[0][0]} — <span class=\"{get_color_info(sorted_hospitals[0][1])[0]}\">{sorted_hospitals[0][1]}m {get_color_info(sorted_hospitals[0][1])[1]}</span>" if sorted_hospitals else "N/A",
        'fastestImprovement': trend_cache.format_fastest_improvement(trends),
        'fastestImprovementDetail': fastest_improvement_detail,
        'biggestChange24h': trend_cache.format_biggest_24h_change(biggest_change_24h),
        'pressureIndex': trend_cache.format_pressure_index(pressure),
        'hospitals': [
            {
                'name': name,
                'wait': wait,
                'colorClass': get_color_info(wait)[0],
                'emoji': get_color_info(wait)[1],
                'trend': get_trend(name),
                'severity': 'critical' if wait >= 240 else 'high' if wait >= 120 else 'moderate' if wait >= 60 else 'low'
            }
            for name, wait in sorted_hospitals
        ]
    }
    
    # Debug: Print hospital count and trends
    print(f"[DEBUG] Generating dashboard with {len(dashboard_data['hospitals'])} hospitals")
    print(f"[DEBUG] Trends data: {trends}")
    for i, h in enumerate(dashboard_data['hospitals'][:3]):
        print(f"  [{i+1}] {h['name']}: {h['wait']}m, trend: {h['trend']}")
    
    # Load HTML template
    html_path = Path(__file__).parent / DASHBOARD_HTML_TEMPLATE
    if not html_path.exists():
        raise FileNotFoundError(f"Dashboard template not found: {html_path}")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Add theme attribute to body
    html_content = html_content.replace(
        '<body class="bg-white p-8">',
        f'<body class="bg-white p-8" data-theme="{theme}">'
    )
    
    # EXPERIMENTAL: Apply text scaling wrapper if enabled
    if USE_TEXT_SCALING:
        # Wrap the main dashboard container with scaling transform
        # Use inline style for better compatibility (Tailwind CDN may not support arbitrary scale values)
        html_content = html_content.replace(
            '<div class="max-w-6xl mx-auto bg-white rounded-2xl shadow-lg overflow-visible relative"',
            f'<div style="transform: scale({TEXT_SCALE_FACTOR}); transform-origin: top left;"><div class="max-w-6xl mx-auto bg-white rounded-2xl shadow-lg overflow-visible relative"'
        )
        # Close the wrapper before the closing body tag
        html_content = html_content.replace(
            '</div>\n</body>',
            '</div></div>\n</body>'
        )
        print(f"[EXPERIMENTAL] Text scaling enabled: {TEXT_SCALE_FACTOR}x")
    
    # Inject data via JavaScript - call updateDashboard() function
    data_script = f"""
    <script>
        // Inject dashboard data and call updateDashboard() on load
        window.addEventListener('DOMContentLoaded', function() {{
            if (typeof updateDashboard === 'function') {{
                updateDashboard({json.dumps(dashboard_data)});
            }} else {{
                console.error('updateDashboard() function not found');
            }}
        }});
    </script>
    </head>
    """
    html_content = html_content.replace('</head>', data_script)
    
    # DEBUG: Save modified HTML for verification (only when experimental features are enabled)
    if USE_TEXT_SCALING or USE_PORTRAIT_MODE:
        debug_html_path = Path(__file__).parent / "dashboard_debug.html"
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[DEBUG] Modified HTML saved to: {debug_html_path}")
    
    # Generate image with Playwright in true 4K resolution
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Log experimental features status
        if USE_PORTRAIT_MODE:
            print(f"[EXPERIMENTAL] Portrait mode enabled: {SCREENSHOT_4K_WIDTH}x{SCREENSHOT_4K_HEIGHT}")
        if USE_TEXT_SCALING:
            print(f"[EXPERIMENTAL] Text scaling wrapper applied: scale({TEXT_SCALE_FACTOR})")
        
        # Create page with 4K viewport (3840x2160 or 2160x3840 if portrait) and 2x device scale for retina clarity
        page = await browser.new_page(
            viewport={'width': SCREENSHOT_4K_WIDTH, 'height': SCREENSHOT_4K_HEIGHT},
            device_scale_factor=SCREENSHOT_DEVICE_SCALE
        )
        
        # Enable console logging
        page.on('console', lambda msg: print(f'[BROWSER] {msg.type}: {msg.text}'))
        page.on('pageerror', lambda err: print(f'[BROWSER ERROR] {err}'))
        
        # Set content
        await page.set_content(html_content, wait_until='networkidle')
        
        # Wait for fonts and rendering
        await page.wait_for_timeout(1000)
        
        # Wait for table to be populated (check for at least one row)
        await page.wait_for_selector('tbody#hospital-table tr', timeout=5000)
        
        # Wait 3 seconds for dashboard animations/data load before capture
        await page.wait_for_timeout(3000)
        
        # Generate timestamped filename for 4K capture
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Determine file extension and type based on JPEG export setting
        file_extension = "jpg" if USE_JPEG_EXPORT else "png"
        screenshot_type = "jpeg" if USE_JPEG_EXPORT else "png"
        
        output_filename_4k = f"dashboard_4k_{timestamp}.{file_extension}"
        output_path_4k = Path(__file__).parent / output_filename_4k
        
        # Also save to legacy filename for compatibility (keep as PNG for backward compatibility)
        output_path_legacy = Path(__file__).parent / DASHBOARD_FILE
        
        # Take screenshot of only the dashboard container (not the entire page)
        # This eliminates empty space and provides a tight, zoomed-in view
        dashboard_element = await page.query_selector('.max-w-6xl')
        if dashboard_element:
            # Save 4K timestamped version (JPEG or PNG based on setting)
            if USE_JPEG_EXPORT:
                await dashboard_element.screenshot(path=str(output_path_4k), type='jpeg', quality=JPEG_QUALITY)
                print(f"[EXPERIMENTAL] JPEG export enabled: quality={JPEG_QUALITY}")
            else:
                await dashboard_element.screenshot(path=str(output_path_4k), type='png')
            
            # Save legacy version for Telegram (always use current format)
            if USE_JPEG_EXPORT:
                await dashboard_element.screenshot(path=str(output_path_legacy), type='jpeg', quality=JPEG_QUALITY)
            else:
                await dashboard_element.screenshot(path=str(output_path_legacy), type='png')
            
            print(f"[{now_iso()}] 4K screenshot saved: {output_path_4k}")
            print(f"[{now_iso()}] Resolution: {SCREENSHOT_4K_WIDTH}x{SCREENSHOT_4K_HEIGHT} @ {SCREENSHOT_DEVICE_SCALE}x scale")
            print(f"[{now_iso()}] Format: {screenshot_type.upper()}" + (f" (quality={JPEG_QUALITY})" if USE_JPEG_EXPORT else ""))
        else:
            # Fallback to full page if selector not found
            if USE_JPEG_EXPORT:
                await page.screenshot(path=str(output_path_4k), full_page=False, type='jpeg', quality=JPEG_QUALITY)
                await page.screenshot(path=str(output_path_legacy), full_page=False, type='jpeg', quality=JPEG_QUALITY)
            else:
                await page.screenshot(path=str(output_path_4k), full_page=False, type='png')
                await page.screenshot(path=str(output_path_legacy), full_page=False, type='png')
        
        await browser.close()
    
    print(f"[{now_iso()}] Dashboard generated: {output_path_legacy}")
    # Return both image path and headline for Telegram caption (use legacy path for Telegram)
    return str(output_path_legacy), headline if headline else "NI A&E Wait Times Update"


async def run_once_async() -> None:
    """Main polling function with async dashboard generation"""
    # Fetch hospital data
    rows: List[Dict[str, Any]] = []
    source_label = "NI Direct — Emergency Departments"
    last_updated_hint: Optional[str] = None
    
    try:
        rows, last_updated_hint = fetch_ni_direct_rows()
        if not rows:
            print(f"[{now_iso()}] NI Direct returned no rows. Skipping send.")
            return
    except Exception as e:
        print(f"[{now_iso()}] NI Direct fetch failed: {e}")
        return
 
    # Check for changes
    digest = compute_digest(rows)
    state = load_state()
    if not FORCE_SEND and state.get("digest") == digest:
        print(f"[{now_iso()}] No change detected. Skipping send.")
        return
 
    # Detect changes from previous run
    previous_waits = state.get("previous_waits", {})
    changes = detect_changes(rows, previous_waits) if previous_waits else []
    
    # Format and send text message
    last_updated_hint = last_updated_hint or None
    message = format_message(rows, source_label, last_updated_hint, changes)

    # Send text update
    ok, err, message_id = telegram_send_message(message)
    if not ok:
        print(f"[{now_iso()}] Failed to send Telegram message: {err}")
        return
    
    print(f"[{now_iso()}] Text update sent to Telegram. Rows: {len(rows)} | Changes: {len(changes)}")
    
    # Generate and send dashboard image
    if GENERATE_DASHBOARD:
        try:
            # Convert rows to dict for trend cache
            hospitals_dict = {
                row["hospital"]: row["wait_mins"]
                for row in rows
                if row["wait_mins"] is not None
            }
            
            # Auto-detect theme
            theme = get_auto_theme()
            print(f"[{now_iso()}] Generating dashboard (theme: {theme})...")
            
            # Generate dashboard (returns path and headline)
            # NOTE: Dashboard generation uses current cache for trend comparison
            dashboard_path, headline_text = await generate_dashboard_image(
                hospitals_dict, 
                theme, 
                source_updated=last_updated_hint
            )
            
            # Send to Telegram with headline as caption
            photo_ok, photo_err = telegram_send_photo(
                dashboard_path,
                caption=headline_text
            )
            
            if photo_ok:
                print(f"[{now_iso()}] Dashboard image sent to Telegram")
                
                # Delete the dashboard images after successful send
                try:
                    # Delete the legacy file (used for Telegram)
                    legacy_path = Path(dashboard_path)
                    if legacy_path.exists():
                        legacy_path.unlink()
                        print(f"[{now_iso()}] Deleted: {legacy_path.name}")
                    
                    # Delete the timestamped 4K file
                    parent_dir = legacy_path.parent
                    file_extension = "jpg" if USE_JPEG_EXPORT else "png"
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    timestamped_file = parent_dir / f"dashboard_4k_{timestamp}.{file_extension}"
                    if timestamped_file.exists():
                        timestamped_file.unlink()
                        print(f"[{now_iso()}] Deleted: {timestamped_file.name}")
                    
                    # Also delete debug HTML if it exists
                    debug_html = parent_dir / "dashboard_debug.html"
                    if debug_html.exists():
                        debug_html.unlink()
                        print(f"[{now_iso()}] Deleted: dashboard_debug.html")
                        
                except Exception as del_err:
                    print(f"[{now_iso()}] Warning: Failed to delete files: {del_err}")
            else:
                print(f"[{now_iso()}] Failed to send dashboard image: {photo_err}")
                print(f"[{now_iso()}] Keeping files for debugging: {dashboard_path}")
            
            # Update cache for next trend comparison
            trend_cache.update_cache(hospitals_dict, source_updated=last_updated_hint)
            
            # Record reading for daily statistics
            daily_stats_tracker.record_reading(hospitals_dict, source_updated=last_updated_hint)
            
            # Check if it's time to send daily update
            if daily_stats_tracker.should_send_update():
                print(f"[{now_iso()}] Sending daily statistics update...")
                try:
                    daily_stats = daily_stats_tracker.calculate_daily_stats(hospitals_dict)
                    if daily_stats:
                        daily_message = daily_stats_tracker.format_daily_update(daily_stats)
                        daily_ok, daily_err, _ = telegram_send_message(daily_message)
                        if daily_ok:
                            print(f"[{now_iso()}] Daily statistics update sent to Telegram")
                        else:
                            print(f"[{now_iso()}] Failed to send daily update: {daily_err}")
                except Exception as daily_e:
                    print(f"[{now_iso()}] Daily stats error: {daily_e}")
                    import traceback
                    traceback.print_exc()
            
        except Exception as e:
            print(f"[{now_iso()}] Dashboard generation failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Update state
    state["digest"] = digest
    state["last_sent"] = now_iso()
    if message_id is not None:
        state["last_message_id"] = message_id
    state["previous_waits"] = {row["hospital"]: row["wait_mins"] for row in rows if row["wait_mins"] is not None}
    save_state(state)


def run_once() -> None:
    """Synchronous wrapper for async run_once"""
    asyncio.run(run_once_async())


if __name__ == "__main__":
    print(f"[{now_iso()}] Starting NI ED wait monitor with dashboard generation")
    print(f"  Poll interval: {POLL_SECONDS}s")
    print(f"  FORCE_SEND: {'ON' if FORCE_SEND else 'OFF'}")
    print(f"  Dashboard: {'ENABLED' if GENERATE_DASHBOARD else 'DISABLED'}")
    print(f"  Theme: DARK (forced)")
    
    while True:
        run_once()
        try:
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("Exiting...")
            break
