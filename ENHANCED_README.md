# 🏥 NI Emergency Department Dashboard - Enhanced Edition

A **stunning, feature-rich** real-time web dashboard for Northern Ireland Emergency Department wait times with advanced analytics, interactive charts, alerts, and export capabilities.

![Version](https://img.shields.io/badge/Version-2.0-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Flask](https://img.shields.io/badge/Flask-3.0.0-red) ![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

---

## ✨ **NEW FEATURES**

### 📊 **Advanced Analytics**
- **Interactive Charts** powered by Chart.js
  - Real-time wait time trends (6-hour history)
  - Severity distribution pie chart
  - Average vs Maximum wait time comparison
- **Historical Data Tracking** - Stores last 24 hours of data
- **Trend Analysis** - Compare current vs 1 hour ago

### 🔔 **Smart Alert System**
- **Configurable Thresholds**
  - Critical hospital count alerts
  - Average wait time alerts
  - Individual hospital alerts
- **Visual Alert Banners** - Slide-in notifications
- **Alert Badge** - Shows active alert count
- **Alert History** - View all active alerts in modal

### 📥 **Data Export**
- **CSV Export** - Spreadsheet-ready format
- **JSON Export** - Developer-friendly format
- **Timestamped Files** - Automatic filename generation
- **One-Click Download** - Export current snapshot instantly

### 🎨 **Enhanced Design**
- **Custom Branding** - Brand colors (primary, secondary, accent)
- **Glass-morphism Effects** - Modern frosted glass UI
- **Smooth Animations** - Pulse, glow, slide-in effects
- **Responsive Charts** - Perfect on all screen sizes
- **Theme Toggle** - (Coming soon)

### 🔧 **Advanced Features**
- **Multi-level Filtering** - By severity (Critical/High/Moderate/Low)
- **Flexible Sorting** - By wait time or hospital name (ascending/descending)
- **Auto-refresh** - Configurable 60-second intervals
- **Countdown Timer** - Visual feedback for next update
- **Error Handling** - Graceful fallbacks with retry
- **Loading States** - Smooth transitions

---

## 🚀 **Quick Start**

### **Installation**

```bash
cd "c:\Users\m0luc\OneDrive\Documents\Desktop\hospital wait"
pip install -r requirements.txt
```

### **Run Enhanced Dashboard**

```bash
python enhanced_app.py
```

Open browser: **http://localhost:5001**

---

## 📁 **Project Structure**

```
hospital wait/
├── enhanced_app.py                 # Enhanced Flask backend with analytics
├── web_app.py                      # Basic Flask backend
├── app.py                          # Original Telegram bot
├── templates/
│   ├── enhanced_dashboard.html     # Advanced dashboard (NEW)
│   └── index.html                  # Basic dashboard
├── static/
│   └── dashboard.js                # Enhanced JavaScript (NEW)
├── requirements.txt                # Python dependencies
├── ENHANCED_README.md             # This file
└── WEB_README.md                  # Basic dashboard docs
```

---

## 🔌 **API Endpoints**

### **Core Endpoints**

#### `GET /`
Returns enhanced dashboard HTML

#### `GET /api/wait-times`
Returns current wait times with statistics and alerts

**Response:**
```json
{
  "success": true,
  "data": [...],
  "last_updated": "2024-12-19 00:00:00 GMT",
  "stats": {
    "total_hospitals": 10,
    "critical": 2,
    "high": 3,
    "moderate": 3,
    "low": 2,
    "average_wait": 145,
    "max_wait": 300,
    "min_wait": 45
  },
  "alerts": [
    {
      "type": "critical_count",
      "severity": "high",
      "message": "3 hospitals have critical wait times",
      "timestamp": "2024-12-19T00:00:00"
    }
  ]
}
```

### **Analytics Endpoints**

#### `GET /api/historical?hours=6`
Returns historical data for charts (max 24 hours)

#### `GET /api/trends`
Returns trend analysis (current vs 1 hour ago)

#### `GET /api/hospital/<hospital_name>`
Returns detailed info for specific hospital with history

### **Export Endpoints**

#### `GET /api/export/csv`
Downloads current data as CSV file

#### `GET /api/export/json`
Downloads current data as JSON file

### **Alert Configuration**

#### `GET /api/alerts/settings`
Returns current alert thresholds

#### `POST /api/alerts/settings`
Updates alert thresholds

**Request Body:**
```json
{
  "critical_count": 3,
  "average_wait": 180,
  "individual_wait": 300
}
```

---

## 🎯 **Feature Breakdown**

### **Statistics Dashboard**
- **Total Hospitals** - Active EDs reporting
- **Critical/High/Moderate/Low Counts** - Color-coded severity
- **Average Wait** - Mean across all hospitals
- **Real-time Updates** - Refreshes every 60 seconds

### **Interactive Charts**

#### **Trends Chart (Line)**
- Shows last 6 hours of data
- Dual lines: Average & Maximum wait times
- Hover for exact values
- Responsive design

#### **Severity Distribution (Doughnut)**
- Visual breakdown by severity level
- Color-coded segments
- Percentage display
- Interactive legend

### **Hospital Cards**
Each card displays:
- Hospital name (full)
- **Large wait time** (prominent display)
- **Severity badge** (color-coded)
- **Status indicator** (Open/Closed)
- **Progress bar** (visual wait time)
- **Description** (Excellent/Good/Busy/Very Busy)
- **Hover effects** (scale + shadow)

### **Alert System**

**Default Thresholds:**
- Critical Count: ≥3 hospitals
- Average Wait: ≥180 minutes
- Individual Wait: ≥300 minutes

**Alert Types:**
- 🔴 **High Severity** - Critical conditions
- 🟠 **Medium Severity** - Warning conditions

**Alert Display:**
- Slide-in banners (top-right)
- Badge counter (header)
- Full list in modal
- Dismissible notifications

### **Export Functionality**

**CSV Format:**
```
Hospital,Status,Wait Time (minutes),Display Wait,Severity,Last Updated
Royal Victoria Hospital ED,Open,180,3 hours,high,2024-12-19 00:00:00 GMT
```

**JSON Format:**
```json
{
  "exported_at": "2024-12-19T00:00:00",
  "last_updated": "2024-12-19 00:00:00 GMT",
  "stats": {...},
  "hospitals": [...]
}
```

---

## 🎨 **Customization Guide**

### **Change Brand Colors**

Edit `enhanced_app.py` or `enhanced_dashboard.html`:

```javascript
colors: {
    'brand-primary': '#0066cc',    // Main blue
    'brand-secondary': '#00cc66',  // Green accent
    'brand-accent': '#cc0066',     // Pink/red accent
}
```

### **Adjust Alert Thresholds**

Edit `enhanced_app.py`:

```python
alert_thresholds = {
    "critical_count": 3,      # Number of critical hospitals
    "average_wait": 180,      # Average wait in minutes
    "individual_wait": 300    # Individual hospital wait
}
```

### **Change Auto-Refresh Interval**

Edit `static/dashboard.js`:

```javascript
autoRefreshInterval = setInterval(() => {
    refreshData();
}, 60000); // Change to desired milliseconds
```

### **Modify Chart Time Range**

Edit `static/dashboard.js`:

```javascript
const response = await fetch('/api/historical?hours=6'); // Change hours
```

---

## 📊 **Data Flow**

1. **Frontend** requests data from `/api/wait-times`
2. **Backend** scrapes NI Direct website
3. **Data Processing**:
   - Parse wait times
   - Calculate statistics
   - Check alert conditions
   - Store historical data
4. **Response** sent to frontend with:
   - Hospital data
   - Statistics
   - Active alerts
5. **Frontend Updates**:
   - Statistics cards
   - Hospital grid
   - Charts
   - Alert banners

---

## 🛠️ **Advanced Configuration**

### **Historical Data Retention**

Data is automatically cleaned to keep only last 24 hours. To change:

Edit `enhanced_app.py`:

```python
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)  # Change hours
```

### **Chart Colors**

Edit `static/dashboard.js`:

```javascript
// Trends Chart
borderColor: '#0066cc',  // Line color
backgroundColor: 'rgba(0, 102, 204, 0.1)',  // Fill color

// Severity Chart
backgroundColor: ['#dc2626', '#f97316', '#eab308', '#10b981']
```

### **Hospital Card Animations**

Edit `static/dashboard.js`:

```javascript
style="animation-delay: ${index * 0.05}s"  // Stagger delay
```

---

## 🔒 **Production Deployment**

### **1. Disable Debug Mode**

```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

### **2. Use Production Server**

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 enhanced_app:app
```

### **3. Enable HTTPS**

Use Nginx reverse proxy with SSL:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **4. Environment Variables**

Create `.env` file:

```
FLASK_ENV=production
PORT=5001
AUTO_REFRESH_SECONDS=60
```

---

## 🐛 **Troubleshooting**

### **Charts Not Displaying**

- Check browser console for errors
- Verify Chart.js CDN is loading
- Ensure canvas elements exist

### **Alerts Not Showing**

- Check `/api/wait-times` response includes alerts
- Verify alert thresholds are configured
- Check browser console for JavaScript errors

### **Export Not Working**

- Verify Flask send_file is working
- Check file permissions
- Test API endpoint directly: `/api/export/csv`

### **Historical Data Missing**

- Data builds over time (need multiple refreshes)
- Check `/api/historical` endpoint
- Verify data is being stored in memory

---

## 📈 **Performance Optimization**

- **Caching**: Historical data stored in memory
- **Lazy Loading**: Charts only update when data changes
- **Debouncing**: Prevents excessive API calls
- **Efficient Rendering**: Only re-renders changed elements

---

## 🎯 **Roadmap**

- [ ] **Theme Customization** - Light/Dark mode toggle
- [ ] **Email Alerts** - Send notifications via email
- [ ] **SMS Alerts** - Text message notifications
- [ ] **Comparison View** - Compare multiple hospitals
- [ ] **Geolocation** - Find nearest hospital
- [ ] **Historical Reports** - Weekly/monthly summaries
- [ ] **API Authentication** - Secure API endpoints
- [ ] **Database Storage** - Persistent historical data
- [ ] **Mobile App** - Native iOS/Android apps

---

## 📝 **License**

This project is for educational and informational purposes. Data sourced from NI Direct.

---

## 🤝 **Contributing**

Suggestions welcome! This dashboard can be extended with:
- Additional chart types (bar, area, scatter)
- Predictive analytics (ML-based wait time forecasting)
- Integration with other health services
- Multi-language support
- Accessibility improvements (WCAG AAA)

---

## 📧 **Support**

For issues:
1. Check this README
2. Review browser console (F12)
3. Check Flask server logs
4. Test API endpoints directly

---

**Built with ❤️ for Northern Ireland's healthcare community**

*Real-time analytics • Advanced features • Beautiful design • Production ready*

---

## 🔗 **Quick Links**

- **Basic Dashboard**: http://localhost:5000 (run `web_app.py`)
- **Enhanced Dashboard**: http://localhost:5001 (run `enhanced_app.py`)
- **Data Source**: https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times
- **Emergency Services**: 999

---

**Version 2.0** | December 2024 | Enhanced Edition
