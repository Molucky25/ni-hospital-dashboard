from flask import Flask, render_template, jsonify
from flask_cors import CORS
import requests
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

NI_DIRECT_URL = "https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times"

THRESHOLDS = {
    "red": 240,
    "orange": 120,
    "yellow": 60,
}

def parse_wait_to_minutes(text: str) -> Optional[int]:
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
        rows.append(
            {
                "hospital": name,
                "status": "Open",
                "wait_mins": wait_mins,
                "display_wait": wait_txt or (f"{wait_mins} mins" if wait_mins is not None else "N/A"),
                "last_updated": None,
            }
        )

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

def get_severity_level(minutes: Optional[int]) -> str:
    if minutes is None:
        return "unknown"
    if minutes >= THRESHOLDS["red"]:
        return "critical"
    if minutes >= THRESHOLDS["orange"]:
        return "high"
    if minutes >= THRESHOLDS["yellow"]:
        return "moderate"
    return "low"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wait-times')
def get_wait_times():
    try:
        rows, last_updated = fetch_ni_direct_rows()
        
        for row in rows:
            row['severity'] = get_severity_level(row['wait_mins'])
        
        stats = {
            'total_hospitals': len(rows),
            'critical': sum(1 for r in rows if r['severity'] == 'critical'),
            'high': sum(1 for r in rows if r['severity'] == 'high'),
            'moderate': sum(1 for r in rows if r['severity'] == 'moderate'),
            'low': sum(1 for r in rows if r['severity'] == 'low'),
            'average_wait': round(sum(r['wait_mins'] for r in rows if r['wait_mins'] is not None) / len([r for r in rows if r['wait_mins'] is not None])) if any(r['wait_mins'] is not None for r in rows) else 0
        }
        
        return jsonify({
            'success': True,
            'data': rows,
            'last_updated': last_updated or datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
