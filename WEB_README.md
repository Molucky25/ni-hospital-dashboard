# 🏥 NI Emergency Department Wait Times - Live Dashboard

A stunning, real-time web dashboard displaying live wait times for Northern Ireland Emergency Departments. Built with Flask and Tailwind CSS for a beautiful, responsive experience across all devices.

![Dashboard Preview](https://img.shields.io/badge/Status-Live-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)

## ✨ Features

### 🎨 Visual Design
- **Stunning Dark Theme** with gradient backgrounds and glass-morphism effects
- **Responsive Layout** - Perfect on desktop, tablet, and mobile devices
- **Smooth Animations** - Fade-ins, slide-ups, and hover effects
- **Color-Coded Severity** - Instant visual indication of wait times
  - 🟢 **Low** (< 60 minutes)
  - 🟡 **Moderate** (60-119 minutes)
  - 🟠 **High** (120-239 minutes)
  - 🔴 **Critical** (≥ 240 minutes)

### 📊 Real-Time Data
- **Live Updates** - Auto-refresh every 60 seconds
- **Countdown Timer** - Shows time until next refresh
- **Statistics Dashboard** - Overview of all hospitals by severity
- **Average Wait Time** - Calculated across all departments

### 🔧 Interactive Features
- **Filter by Severity** - View only Critical, High, Moderate, or Low wait times
- **Multiple Sort Options**:
  - Wait Time (High to Low / Low to High)
  - Hospital Name (A-Z / Z-A)
- **Manual Refresh** - Update data on demand
- **Error Handling** - Graceful fallback with retry option

### 📱 Mobile Optimized
- Touch-friendly interface
- Optimized card layouts for small screens
- Readable typography at all sizes
- Fast loading and smooth scrolling

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**
```bash
cd "hospital wait"
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the web application**
```bash
python web_app.py
```

4. **Open your browser**
Navigate to: `http://localhost:5000`

The dashboard will automatically start fetching live data from NI Direct!

## 📁 Project Structure

```
hospital wait/
├── web_app.py              # Flask backend with API endpoints
├── templates/
│   └── index.html          # Tailwind CSS dashboard frontend
├── app.py                  # Original Telegram bot script
├── requirements.txt        # Python dependencies
├── WEB_README.md          # This file
└── README.md              # Original project README
```

## 🔌 API Endpoints

### `GET /`
Returns the main dashboard HTML page

### `GET /api/wait-times`
Returns JSON data with current wait times

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "hospital": "Royal Victoria Hospital Emergency Department",
      "status": "Open",
      "wait_mins": 180,
      "display_wait": "3 hours",
      "severity": "high",
      "last_updated": "2024-12-19 12:00:00 GMT"
    }
  ],
  "last_updated": "2024-12-19 12:00:00 GMT",
  "stats": {
    "total_hospitals": 10,
    "critical": 2,
    "high": 3,
    "moderate": 3,
    "low": 2,
    "average_wait": 145
  }
}
```

## 🎯 Features Breakdown

### Statistics Cards
- **Total Hospitals** - Number of EDs reporting
- **Critical Count** - Hospitals with ≥240 min waits
- **High Count** - Hospitals with 120-239 min waits
- **Moderate Count** - Hospitals with 60-119 min waits
- **Low Count** - Hospitals with <60 min waits
- **Average Wait** - Mean wait time across all hospitals

### Hospital Cards
Each card displays:
- Hospital name
- Current wait time (large, prominent)
- Severity badge (color-coded)
- Status indicator (Open/Closed)
- Wait time progress bar
- Descriptive wait time label (Excellent/Good/Busy/Very Busy)

### Filter & Sort Controls
- **Filter Buttons** - Click to show only specific severity levels
- **Sort Dropdown** - Choose how to order hospitals
- **Active State** - Visual feedback on current filter/sort

## 🛠️ Customization

### Changing Auto-Refresh Interval
Edit `index.html` line ~603:
```javascript
autoRefreshInterval = setInterval(() => {
    refreshData();
}, 60000); // Change 60000 to desired milliseconds
```

### Modifying Severity Thresholds
Edit `web_app.py` lines 12-16:
```python
THRESHOLDS = {
    "red": 240,      # Critical threshold (minutes)
    "orange": 120,   # High threshold
    "yellow": 60,    # Moderate threshold
}
```

### Customizing Colors
The dashboard uses Tailwind CSS. Modify the `tailwind.config` in `index.html` (lines 9-35) to change:
- Primary colors
- Animations
- Gradient effects

## 📊 Data Source

Data is scraped in real-time from:
**NI Direct - Emergency Department Average Waiting Times**
https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times

Wait times represent averages over the past 4 hours and are updated hourly by the hospitals.

## ⚠️ Important Notes

- **Triage Priority** - A&E departments use triage to prioritize the most urgent cases
- **Emergency Services** - For life-threatening emergencies, always call 999
- **Alternative Care** - Consider Minor Injury Units for non-urgent issues
- **Data Accuracy** - Times are estimates and may vary based on patient volume and complexity

## 🔒 Production Deployment

For production use:

1. **Disable Debug Mode**
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use Production Server** (e.g., Gunicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
   ```

3. **Add HTTPS** - Use a reverse proxy like Nginx with SSL certificates

4. **Environment Variables** - Store sensitive config in `.env` files

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Data Not Loading
- Check internet connection
- Verify NI Direct website is accessible
- Check browser console for errors (F12)
- Ensure Flask server is running

### Styling Issues
- Clear browser cache (Ctrl+Shift+R)
- Verify Tailwind CDN is loading
- Check browser console for CSS errors

## 📝 License

This project is for educational and informational purposes. Data is sourced from publicly available NI Direct resources.

## 🤝 Contributing

Suggestions and improvements welcome! This dashboard can be extended with:
- Historical trend charts
- Email/SMS alerts for high wait times
- Comparison with previous weeks
- Geolocation-based nearest hospital finder
- Export data to CSV/PDF

## 📧 Support

For issues or questions, please check:
1. This README
2. Browser console errors (F12)
3. Flask server logs in terminal

---

**Built with ❤️ for Northern Ireland's healthcare community**

*Data updates every 60 seconds | Optimized for all devices | Accessible design*
