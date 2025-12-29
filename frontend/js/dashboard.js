import { getTanks, getTank, getTankHistory, getAlerts, getMapData, getAnalytics } from './api.js';
import { initCharts, createOverviewChart, destroyCharts } from './charts.js';
import { initMap, addMarkers, fitBounds } from './maps.js';
import { loadRecommendations } from './recommendations.js';

let selectedTankId = null;

async function initDashboard() {
    showLoading();
    
    try {
        await Promise.all([
            loadTanks(),
            loadAlerts(),
            loadMap(),
            loadAnalytics()
        ]);
        
        loadRecommendations();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

function showLoading() {
    const tanksGrid = document.getElementById('tanks-grid');
    if (tanksGrid) {
        tanksGrid.innerHTML = `
            <div class="loading" style="grid-column: 1 / -1;">
                <div class="spinner"></div>
            </div>
        `;
    }
}

function showError(message) {
    const tanksGrid = document.getElementById('tanks-grid');
    if (tanksGrid) {
        tanksGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--danger-red);">
                ${message}
            </div>
        `;
    }
}

async function loadTanks() {
    const data = await getTanks();
    const tanks = data.tanks;
    const summary = data.summary;
    
    updateSummaryCards(summary);
    renderTankCards(tanks);
    createOverviewChart(tanks);
    
    if (tanks.length > 0 && !selectedTankId) {
        selectTank(tanks[0].id);
    }
}

function updateSummaryCards(summary) {
    const elements = {
        'total-tanks': summary.total,
        'normal-count': summary.normal,
        'warning-count': summary.warning,
        'critical-count': summary.critical
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}

function renderTankCards(tanks) {
    const container = document.getElementById('tanks-grid');
    if (!container) return;
    
    container.innerHTML = tanks.map(tank => {
        const readings = tank.current_readings;
        const maintenanceClass = tank.days_since_cleaned > 30 ? 'maintenance-overdue' : 
                                  tank.days_until_maintenance <= 7 ? 'maintenance-soon' : 'maintenance-ok';
        const maintenanceText = tank.days_since_cleaned > 30 ? 
                                `Overdue: ${tank.days_since_cleaned} days` :
                                `Next: ${tank.days_until_maintenance} days`;
        
        return `
            <div class="tank-card" onclick="window.selectTank('${tank.id}')">
                <div class="tank-header">
                    <div>
                        <div class="tank-name">${tank.name}</div>
                        <div class="tank-location">${tank.location.address}</div>
                    </div>
                    <span class="status-badge status-${tank.status}">${tank.status}</span>
                </div>
                
                <div class="level-bar">
                    <div class="level-fill" style="width: ${tank.current_level_percent}%"></div>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
                    Water Level: ${tank.current_level_percent}%
                </div>
                
                <div class="tank-metrics">
                    <div class="metric">
                        <div class="metric-value">${readings.ph}</div>
                        <div class="metric-label">pH</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${readings.turbidity}</div>
                        <div class="metric-label">NTU</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${readings.temperature}°</div>
                        <div class="metric-label">Temp</div>
                    </div>
                </div>
                
                <div class="maintenance-badge ${maintenanceClass}">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    ${maintenanceText}
                </div>
            </div>
        `;
    }).join('');
}

async function selectTank(tankId) {
    selectedTankId = tankId;
    
    try {
        const [tankData, historyData] = await Promise.all([
            getTank(tankId),
            getTankHistory(tankId)
        ]);
        
        updateTankDetails(tankData);
        initCharts(historyData.history);
        
        document.querySelectorAll('.tank-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const selectedCard = document.querySelector(`.tank-card[onclick*="${tankId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
    } catch (error) {
        console.error('Error selecting tank:', error);
    }
}

function updateTankDetails(data) {
    const tank = data.tank;
    const analysis = data.analysis;
    const trend = data.trend;
    
    const detailsContainer = document.getElementById('tank-details');
    if (!detailsContainer) return;
    
    const readings = tank.current_readings;
    
    detailsContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1.5rem;">
            <div>
                <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.25rem;">${tank.name}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">${tank.location.address}</p>
            </div>
            <span class="status-badge status-${tank.status}">${tank.status}</span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
            <div class="metric" style="padding: 1rem;">
                <div class="metric-value" style="color: ${readings.ph < 6.5 || readings.ph > 8.5 ? 'var(--danger-red)' : 'var(--success-green)'}">
                    ${readings.ph}
                </div>
                <div class="metric-label">pH Level</div>
            </div>
            <div class="metric" style="padding: 1rem;">
                <div class="metric-value" style="color: ${readings.turbidity > 5 ? 'var(--danger-red)' : readings.turbidity > 3 ? 'var(--warning-yellow)' : 'var(--success-green)'}">
                    ${readings.turbidity}
                </div>
                <div class="metric-label">Turbidity (NTU)</div>
            </div>
            <div class="metric" style="padding: 1rem;">
                <div class="metric-value">${readings.temperature}°C</div>
                <div class="metric-label">Temperature</div>
            </div>
            <div class="metric" style="padding: 1rem;">
                <div class="metric-value">${tank.current_level_percent}%</div>
                <div class="metric-label">Water Level</div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
            <div style="padding: 0.75rem; background: var(--bg-light); border-radius: 0.5rem;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Dissolved Oxygen</div>
                <div style="font-weight: 600;">${readings.dissolved_oxygen || 'N/A'} mg/L</div>
            </div>
            <div style="padding: 0.75rem; background: var(--bg-light); border-radius: 0.5rem;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Chlorine</div>
                <div style="font-weight: 600;">${readings.chlorine || 'N/A'} ppm</div>
            </div>
        </div>
        
        ${analysis.recommendations && analysis.recommendations.length > 0 ? `
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 0.5rem; border-left: 3px solid var(--danger-red);">
                <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--danger-red);">Recommendations</div>
                <ul style="margin: 0; padding-left: 1.25rem; color: var(--text-secondary); font-size: 0.875rem;">
                    ${analysis.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${trend ? `
            <div style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <span style="padding: 0.25rem 0.5rem; background: var(--bg-light); border-radius: 0.25rem; font-size: 0.75rem;">
                    pH: ${trend.ph_trend}
                </span>
                <span style="padding: 0.25rem 0.5rem; background: var(--bg-light); border-radius: 0.25rem; font-size: 0.75rem;">
                    Turbidity: ${trend.turbidity_trend}
                </span>
                <span style="padding: 0.25rem 0.5rem; background: var(--bg-light); border-radius: 0.25rem; font-size: 0.75rem;">
                    Temp: ${trend.temperature_trend}
                </span>
            </div>
        ` : ''}
    `;
}

async function loadAlerts() {
    const data = await getAlerts();
    const alerts = data.alerts;
    
    const container = document.getElementById('alerts-list');
    if (!container) return;
    
    const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged).slice(0, 5);
    
    if (unacknowledgedAlerts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                No active alerts
            </div>
        `;
        return;
    }
    
    container.innerHTML = unacknowledgedAlerts.map(alert => {
        const icon = alert.type === 'critical' ? 
            `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--danger-red);">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>` :
            `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--warning-yellow);">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>`;
        
        const time = new Date(alert.created_at).toLocaleTimeString();
        
        return `
            <div class="alert-item ${alert.type}">
                <div class="alert-icon">${icon}</div>
                <div class="alert-content">
                    <div class="alert-title">${alert.tank_id}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${time}</div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadMap() {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;
    
    const data = await getMapData();
    
    initMap('map', data.bounds.center, data.bounds.zoom);
    addMarkers(data.markers);
    
    if (data.bounds.bounds) {
        fitBounds(data.bounds.bounds);
    }
}

async function loadAnalytics() {
    const analytics = await getAnalytics();
    
    const avgPh = document.getElementById('avg-ph');
    const avgTurbidity = document.getElementById('avg-turbidity');
    const avgTemp = document.getElementById('avg-temp');
    
    if (avgPh) avgPh.textContent = analytics.average_ph;
    if (avgTurbidity) avgTurbidity.textContent = analytics.average_turbidity;
    if (avgTemp) avgTemp.textContent = analytics.average_temperature + '°C';
}

window.selectTank = selectTank;
window.viewTankDetails = selectTank;
window.refreshDashboard = initDashboard;

document.addEventListener('DOMContentLoaded', initDashboard);

export { initDashboard };
