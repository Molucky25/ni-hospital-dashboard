"""
NI Emergency Department Wait Times Monitor with Dashboard Image Generation
Integrates the existing monitoring with automatic Facebook post image generation.
"""

import requests
import time
import hashlib
import json
import html
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import re
from bs4 import BeautifulSoup
from pathlib import Path

# Import the dashboard generator
from generate_dashboard_image import generate_dashboard_image, generate_square_dashboard_image

# === Configuration ===
NI_DIRECT_URL = "https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times"

# Telegram credentials
TELEGRAM_BOT_TOKEN = "8331970465:AAGSDG6PkCN1RQ27kcj0Zk0zIlfkRuNbE4Y"
TELEGRAM_CHAT_ID = "-1002987638683"

# Polling interval (seconds)
POLL_SECONDS = 300

# Testing: force send every cycle
FORCE_SEND = False

# Local state file
STATE_FILE = "state.json"

# Image output paths
IMAGE_OUTPUT_16_9 = "hospital_wait_dashboard_16_9.png"
IMAGE_OUTPUT_1_1 = "hospital_wait_dashboard_1_1.png"

# Send images to Telegram (in addition to text message)
SEND_IMAGES = True

# Severity thresholds (minutes)
THRESHOLDS = {
    "red": 240,
    "orange": 120,
    "yellow": 60,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_wait_to_minutes(text: str) -> Optional[int]:
    """Parse wait time text to minutes."""
    if not text:
        return None
    s = text.strip().lower()
    s = s.replace("mins", "minutes").replace("min", "minutes")
    s = s.replace("hrs", "hours").replace("hr", "hours")
    if any(x in s for x in ["n/a", "not available", "no data", "closed"]):
        return None
    m = re.search(r"(over|more than)\s+(\d+)\s+hours?", s)
    if m:
        return int(m.group(2)) * 60
    m = re.search(r"up to\s+(\d+)\s+minutes?", s)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+hours?\s*(\d+)?\s*minutes?", s)
    if m:
        hours = int(m.group(1))
        minutes = int(m.group(2)) if m.group(2) else 0
        return hours * 60 + minutes
    m = re.search(r"(\d+)\s+hours?", s)
    if m:
        return int(m.group(1)) * 60
    m = re.search(r"(\d+)\s+minutes?", s)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d+)\b", s)
    if m:
        return int(m.group(1))
    return None


def fetch_ni_direct_rows() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch hospital data from NI Direct website."""
    r = requests.get(NI_DIRECT_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    heading = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if "emergency departments" in tag.get_text(strip=True).lower():
            heading = tag
            break
    
    table = None
    if heading is not None:
        nxt = heading
        for _ in range(20):
            nxt = nxt.find_next_sibling()
            if nxt is None:
                break
            if nxt.name == "table":
                table = nxt
                break
            inner_table = nxt.find("table") if hasattr(nxt, "find") else None
            if inner_table is not None:
                table = inner_table
                break
    
    if table is None:
        table = soup.find("table")
    if table is None:
        raise RuntimeError("NI Direct: Could not locate Emergency Departments table")

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    
    def find_col(candidates: List[str]) -> Optional[int]:
        for i, h in enumerate(headers):
            hl = h.lower()
            for cand in candidates:
                if cand in hl:
                    return i
        return None

    idx_name = find_col(["hospital", "trust", "site", "department", "ed"])
    idx_wait = find_col(["average", "waiting", "wait"])
    
    if idx_name is None or idx_wait is None:
        first_row = table.find("tr")
        if first_row:
            cells = [c.get_text(strip=True) for c in first_row.find_all(["td", "th"])]
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
        tds = tr.find_all(["td", "th"])
        if len(tds) < max(idx_name, idx_wait) + 1:
            continue
        if all(td.name == "th" for td in tds):
            continue
        name = tds[idx_name].get_text(strip=True)
        if "average waiting time" in name.lower():
            continue
        wait_txt = tds[idx_wait].get_text(" ", strip=True)
        wait_mins = parse_wait_to_minutes(wait_txt)
        rows.append({
            "hospital": name,
            "status": "Open",
            "wait_mins": wait_mins,
            "display_wait": wait_txt or (f"{wait_mins} mins" if wait_mins is not None else "N/A"),
            "last_updated": None,
        })

    last_updated_any: Optional[str] = None
    context = heading.parent if heading else soup
    text_blob = context.get_text("\n", strip=True)
    m = re.search(r"last\s*updated\s*[:\-]?\s*(.+)", text_blob, re.I)
    if m:
        last_updated_any = m.group(1).split("\n")[0][:80]
    else:
        m2 = re.search(r"last\s*updated\s*[:\-]?\s*(.+)", soup.get_text("\n", strip=True), re.I)
        if m2:
            last_updated_any = m2.group(1).split("\n")[0][:80]

    if last_updated_any:
        for rrow in rows:
            rrow["last_updated"] = last_updated_any

    seen = set()
    uniq: List[Dict[str, Any]] = []
    for rrow in rows:
        key = rrow["hospital"].lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(rrow)

    uniq.sort(key=lambda x: (x["wait_mins"] is None, -(x["wait_mins"] or 0)))
    return uniq, last_updated_any


def compute_digest(rows: List[Dict[str, Any]]) -> str:
    """Compute hash digest of current data."""
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


def telegram_send_photo(photo_path: str, caption: str = "") -> Tuple[bool, Optional[str]]:
    """Send a photo to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    try:
        with open(photo_path, "rb") as photo:
            files = {"photo": photo}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }
            r = requests.post(url, data=data, files=files, timeout=30)
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


def telegram_send_message(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """Send a text message to Telegram."""
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


async def run_once_async() -> None:
    """Main monitoring loop with image generation."""
    rows: List[Dict[str, Any]] = []
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
 
    # Format timestamp for display
    if not last_updated_hint:
        last_updated_hint = now_iso()
    
    # Generate dashboard images
    if SEND_IMAGES:
        try:
            print(f"[{now_iso()}] Generating dashboard images...")
            await generate_dashboard_image(rows, last_updated_hint, IMAGE_OUTPUT_16_9)
            await generate_square_dashboard_image(rows, last_updated_hint, IMAGE_OUTPUT_1_1)
            print(f"[{now_iso()}] Dashboard images generated successfully")
        except Exception as e:
            print(f"[{now_iso()}] Image generation failed: {e}")
            SEND_IMAGES = False  # Disable for this cycle
    
    # Send image to Telegram (16:9 version for Facebook)
    if SEND_IMAGES and Path(IMAGE_OUTPUT_16_9).exists():
        caption = f"🚑 <b>NI Emergency Department Wait Times</b>\n\n🕛 Updated: {last_updated_hint}"
        ok, err = telegram_send_photo(IMAGE_OUTPUT_16_9, caption)
        if ok:
            print(f"[{now_iso()}] Dashboard image sent to Telegram")
        else:
            print(f"[{now_iso()}] Failed to send image: {err}")
    
    # Update state
    state["digest"] = digest
    state["last_sent"] = now_iso()
    state["previous_waits"] = {row["hospital"]: row["wait_mins"] for row in rows if row["wait_mins"] is not None}
    save_state(state)
    print(f"[{now_iso()}] Update complete. Rows: {len(rows)}")


def run_once() -> None:
    """Wrapper to run async function."""
    asyncio.run(run_once_async())


if __name__ == "__main__":
    print(f"[{now_iso()}] Starting NI ED wait monitor with image generation.")
    print(f"Poll every {POLL_SECONDS}s | FORCE_SEND={'ON' if FORCE_SEND else 'OFF'} | SEND_IMAGES={'ON' if SEND_IMAGES else 'OFF'}")
    
    while True:
        run_once()
        try:
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("Exiting...")
            break
