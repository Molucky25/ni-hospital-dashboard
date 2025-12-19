// Enhanced Dashboard JavaScript
let allHospitals = [];
let currentFilter = 'all';
let currentSort = 'wait-desc';
let trendsChart = null;
let severityChart = null;
let countdownInterval;
let autoRefreshInterval;
let secondsRemaining = 60;

document.addEventListener('DOMContentLoaded', function() {
    loadData();
    startAutoRefresh();
    startCountdown();
});

async function loadData() {
    try {
        const response = await fetch('/api/wait-times');
        const result = await response.json();
        
        if (result.success) {
            allHospitals = result.data;
            updateUI(result);
            updateCharts();
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('error-state').classList.add('hidden');
            document.getElementById('hospitals-grid').classList.remove('hidden');
        } else {
            showError();
        }
    } catch (error) {
        console.error('Error loading data:', error);
        showError();
    }
}

function updateUI(result) {
    updateLastUpdated(result.last_updated);
    updateStats(result.stats);
    updateAlerts(result.alerts || []);
    renderHospitals();
}

function updateLastUpdated(timestamp) {
    document.getElementById('last-updated').textContent = timestamp;
}

function updateStats(stats) {
    const container = document.getElementById('stats-container');
    container.innerHTML = `
        <div class="glass-card rounded-xl p-4 border border-white/10 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-hospital text-blue-400 text-xl"></i>
                <span class="text-3xl font-bold text-white">${stats.total_hospitals}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">Total Hospitals</p>
        </div>
        <div class="glass-card rounded-xl p-4 border border-red-500/30 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-exclamation-triangle text-red-500 text-xl"></i>
                <span class="text-3xl font-bold text-red-500">${stats.critical}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">Critical</p>
        </div>
        <div class="glass-card rounded-xl p-4 border border-orange-500/30 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-exclamation-circle text-orange-500 text-xl"></i>
                <span class="text-3xl font-bold text-orange-500">${stats.high}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">High</p>
        </div>
        <div class="glass-card rounded-xl p-4 border border-yellow-500/30 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-clock text-yellow-500 text-xl"></i>
                <span class="text-3xl font-bold text-yellow-500">${stats.moderate}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">Moderate</p>
        </div>
        <div class="glass-card rounded-xl p-4 border border-green-500/30 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-check-circle text-green-500 text-xl"></i>
                <span class="text-3xl font-bold text-green-500">${stats.low}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">Low</p>
        </div>
        <div class="glass-card rounded-xl p-4 border border-purple-500/30 hover:scale-105 transition-transform">
            <div class="flex items-center justify-between mb-2">
                <i class="fas fa-chart-line text-purple-400 text-xl"></i>
                <span class="text-3xl font-bold text-purple-400">${stats.average_wait}</span>
            </div>
            <p class="text-xs text-gray-400 font-medium">Avg (mins)</p>
        </div>
    `;
}

function updateAlerts(alerts) {
    const badge = document.getElementById('alert-badge');
    if (alerts.length > 0) {
        badge.textContent = alerts.length;
        badge.classList.remove('hidden');
        showAlertBanners(alerts);
    } else {
        badge.classList.add('hidden');
    }
}

function showAlertBanners(alerts) {
    const container = document.getElementById('alert-container');
    container.innerHTML = alerts.slice(0, 3).map(alert => `
        <div class="alert-banner glass-card rounded-lg p-4 border ${alert.severity === 'high' ? 'border-red-500/50 bg-red-500/10' : 'border-orange-500/50 bg-orange-500/10'} shadow-xl">
            <div class="flex items-start gap-3">
                <i class="fas fa-exclamation-triangle ${alert.severity === 'high' ? 'text-red-500' : 'text-orange-500'} text-xl"></i>
                <div class="flex-1">
                    <p class="text-white font-medium text-sm">${alert.message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-white">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderHospitals() {
    let filtered = [...allHospitals];
    
    if (currentFilter !== 'all') {
        filtered = filtered.filter(h => h.severity === currentFilter);
    }
    
    filtered.sort((a, b) => {
        switch(currentSort) {
            case 'wait-desc':
                return (b.wait_mins || 0) - (a.wait_mins || 0);
            case 'wait-asc':
                return (a.wait_mins || 0) - (b.wait_mins || 0);
            case 'name-asc':
                return a.hospital.localeCompare(b.hospital);
            case 'name-desc':
                return b.hospital.localeCompare(a.hospital);
        }
    });
    
    const container = document.getElementById('hospitals-grid');
    container.innerHTML = filtered.map((hospital, index) => {
        const severityColors = {
            'critical': 'from-red-600 to-red-800',
            'high': 'from-orange-600 to-orange-800',
            'moderate': 'from-yellow-600 to-yellow-800',
            'low': 'from-green-600 to-green-800',
            'unknown': 'from-gray-600 to-gray-800'
        };
        
        return `
            <div class="glass-card rounded-xl overflow-hidden border border-white/10 hover:scale-105 hover:shadow-2xl transition-all duration-300" style="animation-delay: ${index * 0.05}s">
                <div class="bg-gradient-to-r ${severityColors[hospital.severity]} p-1">
                    <div class="bg-dark-card p-5">
                        <div class="flex items-start justify-between mb-4">
                            <div class="flex-1">
                                <h3 class="text-lg font-bold text-white mb-2 leading-tight">${hospital.hospital}</h3>
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span class="px-2 py-1 rounded text-xs font-bold ${getSeverityBadgeClass(hospital.severity)}">
                                        ${hospital.severity.toUpperCase()}
                                    </span>
                                    <span class="px-2 py-1 rounded text-xs font-medium bg-white/10 text-gray-300">
                                        <i class="fas fa-door-open mr-1"></i>${hospital.status}
                                    </span>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-5xl font-black text-white mb-1">
                                    ${hospital.wait_mins !== null ? hospital.wait_mins : '—'}
                                </div>
                                <div class="text-xs text-gray-400 font-medium">minutes</div>
                            </div>
                        </div>
                        
                        <div class="border-t border-white/10 pt-4 mt-4">
                            <div class="flex items-center justify-between text-sm mb-3">
                                <span class="text-gray-400">
                                    <i class="fas fa-info-circle mr-1"></i>Average wait
                                </span>
                                <span class="text-white font-medium">${hospital.display_wait}</span>
                            </div>
                            
                            ${hospital.wait_mins !== null ? `
                            <div>
                                <div class="flex items-center justify-between text-xs text-gray-400 mb-1">
                                    <span>Wait Time Indicator</span>
                                    <span class="font-medium">${getWaitTimeDescription(hospital.wait_mins)}</span>
                                </div>
                                <div class="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                    <div class="bg-gradient-to-r ${severityColors[hospital.severity]} h-full rounded-full transition-all duration-500" style="width: ${Math.min((hospital.wait_mins / 300) * 100, 100)}%"></div>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getSeverityBadgeClass(severity) {
    const classes = {
        'critical': 'bg-red-500/20 text-red-400 border border-red-500/30',
        'high': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
        'moderate': 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
        'low': 'bg-green-500/20 text-green-400 border border-green-500/30',
        'unknown': 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
    };
    return classes[severity] || classes.unknown;
}

function getWaitTimeDescription(minutes) {
    if (minutes < 60) return 'Excellent';
    if (minutes < 120) return 'Good';
    if (minutes < 240) return 'Busy';
    return 'Very Busy';
}

async function updateCharts() {
    try {
        const response = await fetch('/api/historical?hours=6');
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            updateTrendsChart(result.data);
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
    
    updateSeverityChart();
}

function updateTrendsChart(historicalData) {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;
    
    const labels = historicalData.map(d => {
        const date = new Date(d.timestamp.replace(' GMT', '+00:00'));
        return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    });
    
    const avgData = historicalData.map(d => d.stats.average_wait);
    const maxData = historicalData.map(d => d.stats.max_wait);
    
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Wait',
                data: avgData,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Maximum Wait',
                data: maxData,
                borderColor: '#dc2626',
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#fff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

function updateSeverityChart() {
    const ctx = document.getElementById('severityChart');
    if (!ctx) return;
    
    const stats = {
        critical: allHospitals.filter(h => h.severity === 'critical').length,
        high: allHospitals.filter(h => h.severity === 'high').length,
        moderate: allHospitals.filter(h => h.severity === 'moderate').length,
        low: allHospitals.filter(h => h.severity === 'low').length
    };
    
    if (severityChart) {
        severityChart.destroy();
    }
    
    severityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'High', 'Moderate', 'Low'],
            datasets: [{
                data: [stats.critical, stats.high, stats.moderate, stats.low],
                backgroundColor: ['#dc2626', '#f97316', '#eab308', '#10b981'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#fff', padding: 15 }
                }
            }
        }
    });
}

function filterBySeverity(severity) {
    currentFilter = severity;
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-brand-primary', 'text-white');
        btn.classList.add('glass-card', 'text-gray-400', 'hover:bg-white/5');
    });
    
    const activeBtn = document.querySelector(`[data-filter="${severity}"]`);
    activeBtn.classList.add('active', 'bg-brand-primary', 'text-white');
    activeBtn.classList.remove('glass-card', 'text-gray-400', 'hover:bg-white/5');
    
    renderHospitals();
}

function sortHospitals(sortType) {
    currentSort = sortType;
    renderHospitals();
}

async function refreshData() {
    const icon = document.getElementById('refresh-icon');
    icon.classList.add('fa-spin');
    
    await loadData();
    resetCountdown();
    
    setTimeout(() => {
        icon.classList.remove('fa-spin');
    }, 1000);
}

function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        refreshData();
    }, 60000);
}

function startCountdown() {
    countdownInterval = setInterval(() => {
        secondsRemaining--;
        document.getElementById('countdown').textContent = secondsRemaining + 's';
        
        if (secondsRemaining <= 0) {
            resetCountdown();
        }
    }, 1000);
}

function resetCountdown() {
    secondsRemaining = 60;
    document.getElementById('countdown').textContent = '60s';
}

function showError() {
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('hospitals-grid').classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');
}

function showExportModal() {
    document.getElementById('export-modal').classList.remove('hidden');
}

function closeExportModal() {
    document.getElementById('export-modal').classList.add('hidden');
}

function showAlertsModal() {
    document.getElementById('alerts-modal').classList.remove('hidden');
    loadAlertsList();
}

function closeAlertsModal() {
    document.getElementById('alerts-modal').classList.add('hidden');
}

async function loadAlertsList() {
    try {
        const response = await fetch('/api/wait-times');
        const result = await response.json();
        
        const alertsList = document.getElementById('alerts-list');
        if (result.alerts && result.alerts.length > 0) {
            alertsList.innerHTML = result.alerts.map(alert => `
                <div class="glass-card p-4 rounded-lg border ${alert.severity === 'high' ? 'border-red-500/30' : 'border-orange-500/30'}">
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle ${alert.severity === 'high' ? 'text-red-500' : 'text-orange-500'} text-xl"></i>
                        <div class="flex-1">
                            <p class="text-white font-medium">${alert.message}</p>
                            <p class="text-xs text-gray-400 mt-1">${new Date(alert.timestamp).toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            alertsList.innerHTML = '<p class="text-gray-400 text-center py-8">No active alerts</p>';
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function exportData(format) {
    window.location.href = `/api/export/${format}`;
    closeExportModal();
}

function toggleTheme() {
    alert('Theme customization coming soon!');
}

window.addEventListener('beforeunload', () => {
    clearInterval(countdownInterval);
    clearInterval(autoRefreshInterval);
});
