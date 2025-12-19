from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import requests
import re
import json
import csv
import io
import logging
import traceback
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

NI_DIRECT_URL = "https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times"

THRESHOLDS = {
    "red": 240,
    "orange": 120,
    "yellow": 60,
}

# In-memory storage for historical data
historical_data = []
alert_thresholds = {
    "critical_count": 3,
    "average_wait": 180,
    "individual_wait": 300
}
active_alerts = []

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    r = requests.get(NI_DIRECT_URL, headers=headers, timeout=30)
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

def store_historical_data(rows: List[Dict[str, Any]], timestamp: str):
    """Store current data for historical tracking"""
    global historical_data
    
    # Store with ISO format timestamp for easier parsing
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    
    data_point = {
        "timestamp": iso_timestamp,
        "display_timestamp": timestamp,  # Keep human-readable for display
        "data": rows,
        "stats": calculate_stats(rows)
    }
    
    historical_data.append(data_point)
    
    # Keep only last 24 hours of data
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    historical_data = [d for d in historical_data if datetime.fromisoformat(d["timestamp"]) > cutoff]

def calculate_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics from hospital data"""
    stats = {
        'total_hospitals': len(rows),
        'critical': sum(1 for r in rows if get_severity_level(r['wait_mins']) == 'critical'),
        'high': sum(1 for r in rows if get_severity_level(r['wait_mins']) == 'high'),
        'moderate': sum(1 for r in rows if get_severity_level(r['wait_mins']) == 'moderate'),
        'low': sum(1 for r in rows if get_severity_level(r['wait_mins']) == 'low'),
        'unknown': sum(1 for r in rows if r['wait_mins'] is None),
    }
    
    valid_waits = [r['wait_mins'] for r in rows if r['wait_mins'] is not None]
    if valid_waits:
        stats['average_wait'] = round(sum(valid_waits) / len(valid_waits))
        stats['max_wait'] = max(valid_waits)
        stats['min_wait'] = min(valid_waits)
    else:
        stats['average_wait'] = 0
        stats['max_wait'] = 0
        stats['min_wait'] = 0
    
    return stats

def check_alerts(rows: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Check if any alert conditions are met"""
    global active_alerts
    active_alerts = []
    
    # Check critical count threshold
    if stats['critical'] >= alert_thresholds['critical_count']:
        active_alerts.append({
            'type': 'critical_count',
            'severity': 'high',
            'message': f"{stats['critical']} hospitals have critical wait times (≥240 minutes)",
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    # Check average wait threshold
    if stats['average_wait'] >= alert_thresholds['average_wait']:
        active_alerts.append({
            'type': 'average_wait',
            'severity': 'medium',
            'message': f"Average wait time is {stats['average_wait']} minutes",
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    # Check individual hospital thresholds
    for row in rows:
        if row['wait_mins'] and row['wait_mins'] >= alert_thresholds['individual_wait']:
            active_alerts.append({
                'type': 'individual_wait',
                'severity': 'high',
                'message': f"{row['hospital']} has {row['wait_mins']} minute wait time",
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'hospital': row['hospital']
            })

@app.route('/')
def index():
    return render_template('enhanced_dashboard.html')

@app.route('/api/wait-times')
def get_wait_times():
    try:
        logger.info("Fetching wait times from NI Direct...")
        rows, last_updated = fetch_ni_direct_rows()
        logger.info(f"Successfully fetched {len(rows)} hospitals")
        
        for row in rows:
            row['severity'] = get_severity_level(row['wait_mins'])
        
        stats = calculate_stats(rows)
        
        # Store for historical tracking
        timestamp = last_updated or datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        store_historical_data(rows, timestamp)
        
        # Check for alerts
        check_alerts(rows, stats)
        
        return jsonify({
            'success': True,
            'data': rows,
            'last_updated': timestamp,
            'stats': stats,
            'alerts': active_alerts
        })
    except Exception as e:
        logger.error(f"Error in get_wait_times: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/historical')
def get_historical():
    """Get historical data for charts"""
    hours = request.args.get('hours', default=6, type=int)
    hours = min(hours, 24)  # Max 24 hours
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    filtered_data = [
        d for d in historical_data 
        if datetime.fromisoformat(d["timestamp"]) > cutoff
    ]
    
    return jsonify({
        'success': True,
        'data': filtered_data,
        'hours': hours
    })

@app.route('/api/trends')
def get_trends():
    """Calculate trends from historical data"""
    if len(historical_data) < 2:
        return jsonify({
            'success': True,
            'trends': {},
            'message': 'Insufficient data for trends'
        })
    
    # Compare current vs 1 hour ago
    current = historical_data[-1]
    one_hour_ago = None
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    for d in reversed(historical_data[:-1]):
        if datetime.fromisoformat(d["timestamp"]) <= cutoff:
            one_hour_ago = d
            break
    
    if not one_hour_ago:
        one_hour_ago = historical_data[0]
    
    trends = {
        'average_wait': {
            'current': current['stats']['average_wait'],
            'previous': one_hour_ago['stats']['average_wait'],
            'change': current['stats']['average_wait'] - one_hour_ago['stats']['average_wait'],
            'direction': 'up' if current['stats']['average_wait'] > one_hour_ago['stats']['average_wait'] else 'down'
        },
        'critical_count': {
            'current': current['stats']['critical'],
            'previous': one_hour_ago['stats']['critical'],
            'change': current['stats']['critical'] - one_hour_ago['stats']['critical'],
            'direction': 'up' if current['stats']['critical'] > one_hour_ago['stats']['critical'] else 'down'
        }
    }
    
    return jsonify({
        'success': True,
        'trends': trends
    })

@app.route('/api/export/csv')
def export_csv():
    """Export current data as CSV"""
    try:
        rows, last_updated = fetch_ni_direct_rows()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Hospital', 'Status', 'Wait Time (minutes)', 'Display Wait', 'Severity', 'Last Updated'])
        
        # Data
        for row in rows:
            writer.writerow([
                row['hospital'],
                row['status'],
                row['wait_mins'] if row['wait_mins'] is not None else 'N/A',
                row['display_wait'],
                get_severity_level(row['wait_mins']),
                last_updated or 'N/A'
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ni_ed_wait_times_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/json')
def export_json():
    """Export current data as JSON"""
    try:
        rows, last_updated = fetch_ni_direct_rows()
        
        for row in rows:
            row['severity'] = get_severity_level(row['wait_mins'])
        
        stats = calculate_stats(rows)
        
        export_data = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'last_updated': last_updated,
            'stats': stats,
            'hospitals': rows
        }
        
        return send_file(
            io.BytesIO(json.dumps(export_data, indent=2).encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'ni_ed_wait_times_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/settings', methods=['GET', 'POST'])
def alert_settings():
    """Get or update alert threshold settings"""
    global alert_thresholds
    
    if request.method == 'POST':
        data = request.json
        if 'critical_count' in data:
            alert_thresholds['critical_count'] = int(data['critical_count'])
        if 'average_wait' in data:
            alert_thresholds['average_wait'] = int(data['average_wait'])
        if 'individual_wait' in data:
            alert_thresholds['individual_wait'] = int(data['individual_wait'])
        
        return jsonify({
            'success': True,
            'settings': alert_thresholds
        })
    
    return jsonify({
        'success': True,
        'settings': alert_thresholds
    })

@app.route('/api/hospital/<hospital_name>')
def get_hospital_detail(hospital_name):
    """Get detailed information for a specific hospital"""
    try:
        rows, last_updated = fetch_ni_direct_rows()
        
        # Find the hospital
        hospital = None
        for row in rows:
            if row['hospital'].lower() == hospital_name.lower():
                hospital = row
                break
        
        if not hospital:
            return jsonify({
                'success': False,
                'error': 'Hospital not found'
            }), 404
        
        hospital['severity'] = get_severity_level(hospital['wait_mins'])
        
        # Get historical data for this hospital
        hospital_history = []
        for data_point in historical_data:
            for h in data_point['data']:
                if h['hospital'].lower() == hospital_name.lower():
                    hospital_history.append({
                        'timestamp': data_point['timestamp'],
                        'wait_mins': h['wait_mins']
                    })
                    break
        
        return jsonify({
            'success': True,
            'hospital': hospital,
            'history': hospital_history[-20:]  # Last 20 data points
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
