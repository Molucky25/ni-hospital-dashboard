#!/usr/bin/env python3
"""Script to create the enhanced dashboard HTML file"""

html_content = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NI Emergency Department Dashboard - Advanced Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'brand-primary': '#0066cc',
                        'brand-secondary': '#00cc66',
                        'brand-accent': '#cc0066',
                        'dark-bg': '#0a0e27',
                        'dark-card': '#151b3d',
                        'dark-border': '#1e2749',
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #151b3d 50%, #1e2749 100%);
            min-height: 100vh;
        }
        
        .glass-card {
            background: rgba(21, 27, 61, 0.6);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chart-container {
            position: relative;
            height: 300px;
        }
        
        @media (max-width: 768px) {
            .chart-container {
                height: 250px;
            }
        }
    </style>
</head>
<body class="antialiased">
    
    <header class="glass-card sticky top-0 z-50 border-b border-white/10 shadow-2xl">
        <div class="container mx-auto px-4 py-4 sm:py-6">
            <div class="flex flex-col lg:flex-row items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                    <div class="bg-gradient-to-br from-brand-primary to-brand-secondary p-4 rounded-2xl shadow-lg">
                        <i class="fas fa-heartbeat text-white text-3xl"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl sm:text-3xl font-black text-white">NI Emergency Departments</h1>
                        <p class="text-sm text-gray-400 font-medium">Advanced Analytics Dashboard</p>
                    </div>
                </div>
                <div class="flex flex-wrap items-center gap-3">
                    <button onclick="toggleTheme()" class="glass-card px-4 py-2 rounded-lg text-white hover:bg-white/10 transition-all flex items-center gap-2">
                        <i class="fas fa-palette"></i>
                        <span class="hidden sm:inline">Theme</span>
                    </button>
                    <button onclick="showExportModal()" class="glass-card px-4 py-2 rounded-lg text-white hover:bg-white/10 transition-all flex items-center gap-2">
                        <i class="fas fa-download"></i>
                        <span class="hidden sm:inline">Export</span>
                    </button>
                    <button onclick="showAlertsModal()" class="glass-card px-4 py-2 rounded-lg text-white hover:bg-white/10 transition-all flex items-center gap-2 relative">
                        <i class="fas fa-bell"></i>
                        <span class="hidden sm:inline">Alerts</span>
                        <span id="alert-badge" class="hidden absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">0</span>
                    </button>
                    <button onclick="refreshData()" class="bg-brand-primary hover:bg-blue-700 px-4 py-2 rounded-lg text-white transition-all flex items-center gap-2 shadow-lg">
                        <i class="fas fa-sync-alt" id="refresh-icon"></i>
                        <span class="hidden sm:inline">Refresh</span>
                    </button>
                    <div class="glass-card px-4 py-2 rounded-lg">
                        <div class="flex items-center gap-2">
                            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span class="text-sm text-gray-300 font-medium">Live</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <div id="alert-container" class="fixed top-20 right-4 z-40 space-y-2 max-w-md"></div>

    <main class="container mx-auto px-4 py-8">
        
        <div class="glass-card rounded-xl p-4 mb-6 border border-brand-primary/30 shadow-xl">
            <div class="flex items-center justify-between flex-wrap gap-3">
                <div class="flex items-center gap-3">
                    <i class="fas fa-clock text-brand-primary text-2xl"></i>
                    <div>
                        <p class="text-xs text-gray-400 uppercase tracking-wide">Last Updated</p>
                        <p id="last-updated" class="text-white font-bold text-lg">Loading...</p>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p class="text-xs text-gray-400">Next refresh in</p>
                        <p id="countdown" class="text-brand-secondary font-mono font-bold text-xl">60s</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="stats-container" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8"></div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="glass-card rounded-xl p-6 border border-white/10 shadow-xl">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-chart-line text-brand-primary"></i>
                    Wait Time Trends (6 Hours)
                </h3>
                <div class="chart-container">
                    <canvas id="trendsChart"></canvas>
                </div>
            </div>
            <div class="glass-card rounded-xl p-6 border border-white/10 shadow-xl">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-chart-pie text-brand-secondary"></i>
                    Severity Distribution
                </h3>
                <div class="chart-container">
                    <canvas id="severityChart"></canvas>
                </div>
            </div>
        </div>

        <div class="glass-card rounded-xl p-4 sm:p-6 mb-6 border border-white/10 shadow-xl">
            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div class="flex flex-wrap gap-2">
                    <button onclick="filterBySeverity('all')" class="filter-btn active bg-brand-primary px-4 py-2 rounded-lg text-sm font-medium transition-all text-white" data-filter="all">
                        All Hospitals
                    </button>
                    <button onclick="filterBySeverity('critical')" class="filter-btn glass-card px-4 py-2 rounded-lg text-sm font-medium transition-all text-gray-400 hover:bg-white/5" data-filter="critical">
                        <i class="fas fa-circle text-red-500 text-xs"></i> Critical
                    </button>
                    <button onclick="filterBySeverity('high')" class="filter-btn glass-card px-4 py-2 rounded-lg text-sm font-medium transition-all text-gray-400 hover:bg-white/5" data-filter="high">
                        <i class="fas fa-circle text-orange-500 text-xs"></i> High
                    </button>
                    <button onclick="filterBySeverity('moderate')" class="filter-btn glass-card px-4 py-2 rounded-lg text-sm font-medium transition-all text-gray-400 hover:bg-white/5" data-filter="moderate">
                        <i class="fas fa-circle text-yellow-500 text-xs"></i> Moderate
                    </button>
                    <button onclick="filterBySeverity('low')" class="filter-btn glass-card px-4 py-2 rounded-lg text-sm font-medium transition-all text-gray-400 hover:bg-white/5" data-filter="low">
                        <i class="fas fa-circle text-green-500 text-xs"></i> Low
                    </button>
                </div>
                <div class="flex items-center gap-3">
                    <label class="text-sm text-gray-400">Sort:</label>
                    <select id="sort-select" onchange="sortHospitals(this.value)" class="glass-card px-4 py-2 rounded-lg text-white border border-white/10 focus:border-brand-primary focus:outline-none">
                        <option value="wait-desc">Wait Time ↓</option>
                        <option value="wait-asc">Wait Time ↑</option>
                        <option value="name-asc">Name A-Z</option>
                        <option value="name-desc">Name Z-A</option>
                    </select>
                </div>
            </div>
        </div>

        <div id="loading-state" class="flex flex-col items-center justify-center py-20">
            <div class="w-16 h-16 border-4 border-brand-primary border-t-transparent rounded-full animate-spin mb-4"></div>
            <p class="text-gray-400 text-lg font-medium">Loading wait times...</p>
        </div>

        <div id="error-state" class="hidden glass-card rounded-xl p-8 text-center border border-red-500/30">
            <i class="fas fa-exclamation-triangle text-red-500 text-6xl mb-4"></i>
            <h3 class="text-2xl font-bold text-white mb-2">Unable to Load Data</h3>
            <p class="text-gray-400 mb-6">There was an error fetching the wait times. Please try again.</p>
            <button onclick="refreshData()" class="bg-brand-primary hover:bg-blue-700 px-8 py-3 rounded-lg text-white font-medium transition-all shadow-lg">
                <i class="fas fa-redo mr-2"></i>Retry
            </button>
        </div>

        <div id="hospitals-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 hidden"></div>

    </main>

    <div id="export-modal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="glass-card rounded-2xl p-8 max-w-md w-full border border-white/20 shadow-2xl">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-2xl font-bold text-white">Export Data</h3>
                <button onclick="closeExportModal()" class="text-gray-400 hover:text-white transition-colors">
                    <i class="fas fa-times text-2xl"></i>
                </button>
            </div>
            <div class="space-y-4">
                <button onclick="exportData('csv')" class="w-full glass-card hover:bg-white/10 p-4 rounded-lg text-left transition-all border border-white/10">
                    <div class="flex items-center gap-4">
                        <i class="fas fa-file-csv text-green-500 text-3xl"></i>
                        <div>
                            <p class="text-white font-bold">Export as CSV</p>
                            <p class="text-sm text-gray-400">Spreadsheet format</p>
                        </div>
                    </div>
                </button>
                <button onclick="exportData('json')" class="w-full glass-card hover:bg-white/10 p-4 rounded-lg text-left transition-all border border-white/10">
                    <div class="flex items-center gap-4">
                        <i class="fas fa-file-code text-blue-500 text-3xl"></i>
                        <div>
                            <p class="text-white font-bold">Export as JSON</p>
                            <p class="text-sm text-gray-400">Developer format</p>
                        </div>
                    </div>
                </button>
            </div>
        </div>
    </div>

    <div id="alerts-modal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="glass-card rounded-2xl p-8 max-w-2xl w-full border border-white/20 shadow-2xl max-h-[80vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-2xl font-bold text-white flex items-center gap-2">
                    <i class="fas fa-bell text-brand-accent"></i>
                    Active Alerts
                </h3>
                <button onclick="closeAlertsModal()" class="text-gray-400 hover:text-white transition-colors">
                    <i class="fas fa-times text-2xl"></i>
                </button>
            </div>
            <div id="alerts-list" class="space-y-3"></div>
        </div>
    </div>

    <footer class="glass-card border-t border-white/10 mt-12">
        <div class="container mx-auto px-4 py-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h4 class="text-white font-bold mb-3 flex items-center gap-2">
                        <i class="fas fa-info-circle text-brand-primary"></i>
                        About
                    </h4>
                    <p class="text-sm text-gray-400 leading-relaxed">
                        Real-time dashboard displaying NI Emergency Department wait times with advanced analytics and alerts.
                    </p>
                </div>
                <div>
                    <h4 class="text-white font-bold mb-3 flex items-center gap-2">
                        <i class="fas fa-link text-brand-secondary"></i>
                        Resources
                    </h4>
                    <ul class="space-y-2 text-sm">
                        <li><a href="https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times" target="_blank" class="text-gray-400 hover:text-brand-primary transition-colors"><i class="fas fa-external-link-alt mr-1"></i>Data Source</a></li>
                        <li><a href="tel:999" class="text-gray-400 hover:text-brand-primary transition-colors"><i class="fas fa-phone mr-1"></i>Emergency: 999</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="text-white font-bold mb-3 flex items-center gap-2">
                        <i class="fas fa-cog text-brand-accent"></i>
                        Settings
                    </h4>
                    <p class="text-sm text-gray-400">Auto-refresh: 60 seconds</p>
                    <p class="text-sm text-gray-400">Data updates: Hourly</p>
                </div>
            </div>
            <div class="border-t border-white/10 mt-6 pt-6 text-center text-sm text-gray-400">
                <p>© 2024 NI Emergency Department Dashboard • Built with ❤️ for Northern Ireland</p>
            </div>
        </div>
    </footer>

    <script src="/static/dashboard.js"></script>
</body>
</html>
"""

# Write the file
with open('templates/enhanced_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Enhanced dashboard HTML created successfully!")
print("📁 File: templates/enhanced_dashboard.html")
print("🚀 Run: python enhanced_app.py")
print("🌐 Open: http://localhost:5001")
