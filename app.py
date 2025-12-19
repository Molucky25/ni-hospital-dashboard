import requests
import time
import hashlib
import json
import html
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import re
from bs4 import BeautifulSoup

# === Configuration ===
# ArcGIS Feature Layer base query URL (raw features, no stats aggregation)
FEATURE_LAYER_QUERY_URL = (
    "https://services2.arcgis.com/D09jZplR1biTVYOE/arcgis/rest/services/NI_Hospital_Waiting_Times/FeatureServer/0/query"
)

# Fallback stats (averages) URL if raw field WaitTimeInt isn't present (rare)
FALLBACK_STATS_URL = (
    "https://services2.arcgis.com/D09jZplR1biTVYOE/arcgis/rest/services/NI_Hospital_Waiting_Times/FeatureServer/0/query"
)

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


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


# === NI Direct scraper ===
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


def fetch_raw_features() -> List[Dict[str, Any]]:
    params = {
        "where": "Status <> 'Closed'",
        "outFields": "Hospital,Status,WaitTimeInt,WaitTime,OpeningHours,Last_Updated,EditDate,OBJECTID",
        "returnGeometry": "false",
        "orderByFields": "WaitTimeInt DESC",
        "f": "json",
    }
    r = requests.get(FEATURE_LAYER_QUERY_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error']}")
    features = data.get("features", [])
    return features


def fetch_fallback_averages() -> List[Dict[str, Any]]:
    # Use grouped statistics as a fallback to compute average wait per hospital
    params = {
        "f": "json",
        "cacheHint": "true",
        "groupByFieldsForStatistics": "Hospital",
        "maxRecordCountFactor": "5",
        "resultRecordCount": "10001",
        "where": "Status <> 'Closed'",
        "orderByFields": "AVG_WAITTIMEINT DESC",
        "outFields": "*",
        "outStatistics": (
            "[{\"onStatisticField\":\"WaitTimeInt\",\"outStatisticFieldName\":\"AVG_WAITTIMEINT\",\"statisticType\":\"avg\"}]"
        ),
        "returnGeometry": "false",
        "spatialRel": "esriSpatialRelIntersects",
    }
    r = requests.get(FALLBACK_STATS_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"ArcGIS error (fallback): {data['error']}")
    return data.get("features", [])


def normalize_rows(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for f in features:
        attrs = f.get("attributes", {})
        name = attrs.get("Hospital") or attrs.get("hospital") or "Unknown"
        status = attrs.get("Status") or attrs.get("status") or "Unknown"
        wait = attrs.get("WaitTimeInt")
        # Some fields may present as strings
        try:
            wait = int(round(float(wait))) if wait is not None else None
        except Exception:
            wait = None
        display_wait = attrs.get("WaitTime")
        last_updated = attrs.get("Last_Updated") or attrs.get("EditDate")
        # ArcGIS timestamps are often in epoch ms
        if isinstance(last_updated, (int, float)) and last_updated > 10_000_000_000:
            try:
                dt = datetime.fromtimestamp(last_updated / 1000, tz=timezone.utc).astimezone()
                last_updated_str = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception:
                last_updated_str = None
        else:
            last_updated_str = last_updated if isinstance(last_updated, str) else None

        rows.append(
            {
                "hospital": name.strip(),
                "status": status.strip(),
                "wait_mins": wait,
                "display_wait": display_wait,
                "last_updated": last_updated_str,
            }
        )
    # Deduplicate by hospital, prefer the first (already ordered by wait desc)
    seen = set()
    unique_rows = []
    for r in rows:
        key = r["hospital"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(r)
    return unique_rows


def normalize_rows_from_averages(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for f in features:
        attrs = f.get("attributes", {})
        name = attrs.get("Hospital") or "Unknown"
        avg_wait = attrs.get("AVG_WAITTIMEINT")
        try:
            avg_wait = int(round(float(avg_wait))) if avg_wait is not None else None
        except Exception:
            avg_wait = None
        rows.append(
            {
                "hospital": name.strip(),
                "status": "Open",  # stats query omits status; assume open
                "wait_mins": avg_wait,
                "display_wait": f"{avg_wait} mins" if avg_wait is not None else "N/A",
                "last_updated": None,
            }
        )
    # Sort desc by wait
    rows.sort(key=lambda x: (x["wait_mins"] is None, -(x["wait_mins"] or 0)))
    return rows


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
        
        # Abbreviate hospital name - use same logic as main format
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
    # Sort by wait desc, Nones at bottom
    rows_sorted = sorted(rows, key=lambda r: (r["wait_mins"] is None, -(r["wait_mins"] or 0)))

    def abbr(name: str) -> str:
        # Abbreviate common long terms for mobile readability
        # Order matters - do specific replacements before general ones
        replacements = [
            ("Hospital and Primary Care Complex", "Hospital & PCC"),
            ("Emergency Department", "ED"),
            ("Minor Injuries Unit", "MIU"),
            ("Minor Injury Unit", "MIU"),
            ("Urgent care and treatment Centre", "UCTC"),
            ("Urgent Care and Treatment Centre", "UCTC"),
            (" Hospital", ""),  # Remove " Hospital" (with leading space)
        ]
        for old, new in replacements:
            name = name.replace(old, new)
        # Clean up extra spaces and ensure not empty
        name = " ".join(name.split())
        return name.strip() if name.strip() else "Unknown"

    def wrap_text(text: str, width: int) -> List[str]:
        words = (text or "").split()
        if not words:
            return [""]
        lines: List[str] = []
        cur = words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= width:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    header_time = last_updated_any or now_iso()
    header_time_esc = html.escape(header_time)

    if MOBILE_COMPACT:
        # Compact format: one item per line, keep wait first; avoid <pre> to prevent mobile horizontal scroll
        lines_html = []
        for r in rows_sorted:
            emoji = severity_emoji(r["wait_mins"])
            wait = r["wait_mins"]
            wait_str = f"{wait} m" if isinstance(wait, int) else (r["display_wait"] or "N/A")
            name = abbr(r["hospital"]) 
            name_esc = html.escape(name)
            # Single line per hospital to avoid awkward mobile line breaks
            line = f"{emoji} {wait_str} — {name_esc}"
            lines_html.append(line)
        body = "\n".join(lines_html)
        
        # Add changes section if provided
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

    # Desktop-style aligned table (monospaced)
    # Determine name column width with an upper bound for neatness
    longest = max((len(r["hospital"]) for r in rows_sorted), default=20)
    name_width = min(max(24, longest), 46)  # clamp between 24 and 46

    def wrap_name(name: str, width: int) -> List[str]:
        return wrap_text(name, width)

    lines = []
    # Header inside the monospaced block
    header_line = f"{'Hospital'.ljust(name_width)}  {'Wait (m)'.rjust(8)}"
    sep_line = f"{'-' * name_width}  {'-' * 8}"
    lines.append(header_line)
    lines.append(sep_line)

    for r in rows_sorted:
        name_lines = wrap_name(abbr(r["hospital"]), name_width)
        wait = r["wait_mins"]
        disp = f"{wait:>3} mins" if isinstance(wait, int) else (r["display_wait"] or "N/A").rjust(8)
        emoji = severity_emoji(wait)
        # First line with emoji and wait
        first = name_lines[0]
        line1 = f"{emoji} {first.ljust(name_width)}  {disp.rjust(8)}"
        lines.append(line1)
        # Continuation lines aligned under the name column, blank wait
        for cont in name_lines[1:]:
            lines.append(f"  {cont.ljust(name_width)}  {'':>8}")

    body_raw = "\n".join(lines)
    body = html.escape(body_raw)
    # Add changes section if provided
    changes_section = ""
    if changes:
        changes_section = format_changes_section(changes)
    
    header = (
        f"<b>NI Emergency Department Waits</b>\n\n"
        f"Last updated: <i>{header_time_esc}</i>\n\n"
        f"{changes_section}"
        f"<code>Times shown in minutes (m) unless stated</code>\n\n"
    )

    footer = (
        f"\n\n<code>Severity: 🟢 &lt;60m | 🟡 60–119m | 🟠 120–239m | 🔴 ≥240m</code>\n\n"
        f"<code>Abbrev: ED=Emergency Dept | MIU=Minor Injuries Unit | UCTC=Urgent Care &amp; Treatment Centre</code>\n\n"
        f"<i>Note: The times depicted here are updated hourly and are calculated as an average taken over the past 4 hours. A&amp;E triage ensures that those in the greatest need are prioritised for treatment.</i>"
    )

    # Use <pre> for monospaced alignment
    return header + "<pre>" + body + "</pre>" + footer


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


def telegram_edit_message(message_id: int, text: str) -> Tuple[bool, Optional[str]]:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
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
            return False, str(err)
        return True, None
    except Exception as e:
        return False, str(e)


def get_last_updated_hint(rows: List[Dict[str, Any]]) -> Optional[str]:
    # Pick the most common or latest non-null last_updated
    candidates = [r["last_updated"] for r in rows if r.get("last_updated")]
    return candidates[0] if candidates else None


def run_once() -> None:
    # Use only NI Direct page (no ArcGIS fallback)
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
 
    digest = compute_digest(rows)
    state = load_state()
    if not FORCE_SEND and state.get("digest") == digest:
        print(f"[{now_iso()}] No change detected. Skipping send.")
        return
 
    # Detect changes from previous run
    previous_waits = state.get("previous_waits", {})
    changes = detect_changes(rows, previous_waits) if previous_waits else []
    
    last_updated_hint = last_updated_hint or get_last_updated_hint(rows)
    message = format_message(rows, source_label, last_updated_hint, changes)

    # Debug: save message to file to inspect
    try:
        with open("debug_message.html", "w", encoding="utf-8") as f:
            f.write(message)
        print(f"[{now_iso()}] Debug: Message saved to debug_message.html")
    except Exception as e:
        print(f"[{now_iso()}] Debug save failed: {e}")

    # Send a new message for every change
    ok, err, message_id = telegram_send_message(message)
    if ok:
        state["digest"] = digest
        state["last_sent"] = now_iso()
        if message_id is not None:
            state["last_message_id"] = message_id
        # Store current wait times for next comparison
        state["previous_waits"] = {row["hospital"]: row["wait_mins"] for row in rows if row["wait_mins"] is not None}
        save_state(state)
        print(f"[{now_iso()}] Update sent to Telegram. Rows: {len(rows)} | Changes: {len(changes)} | message_id={message_id}")
    else:
        print(f"[{now_iso()}] Failed to send Telegram message: {err}")


if __name__ == "__main__":
    print(f"[{now_iso()}] Starting NI ED wait monitor. Poll every {POLL_SECONDS}s | FORCE_SEND={'ON' if FORCE_SEND else 'OFF'}")
    while True:
        run_once()
        try:
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("Exiting...")
            break
