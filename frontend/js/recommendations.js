import { getRecommendations } from './api.js';

let isLoading = false;

async function loadRecommendations() {
    const container = document.getElementById('recommendations-content');
    if (!container || isLoading) return;
    
    isLoading = true;
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;
    
    try {
        const result = await getRecommendations();
        
        if (result.success && result.recommendations) {
            renderRecommendations(container, result.recommendations);
        } else if (result.fallback_recommendations) {
            renderRecommendations(container, result.fallback_recommendations);
        } else {
            container.innerHTML = `
                <div class="recommendation-item">
                    <p style="color: var(--text-secondary);">Unable to load AI recommendations. Please check API configuration.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        container.innerHTML = `
            <div class="recommendation-item">
                <p style="color: var(--danger-red);">Error loading recommendations. Please try again.</p>
            </div>
        `;
    } finally {
        isLoading = false;
    }
}

function renderRecommendations(container, data) {
    let html = '';
    
    if (data.overall_health_score !== undefined) {
        const score = data.overall_health_score;
        const scoreClass = score >= 70 ? 'score-good' : score >= 40 ? 'score-warning' : 'score-critical';
        html += `
            <div class="health-score">
                <div class="score-circle ${scoreClass}" style="--score: ${score}%">
                    <span>${score}</span>
                </div>
                <div>
                    <div style="font-weight: 600; font-size: 1.125rem;">System Health Score</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">Based on all tank readings</div>
                </div>
            </div>
        `;
    }
    
    if (data.immediate_actions && data.immediate_actions.length > 0) {
        html += `
            <div class="recommendation-item" style="border-left: 3px solid var(--danger-red);">
                <div class="recommendation-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--danger-red);">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <strong>Immediate Actions Required</strong>
                </div>
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--text-secondary);">
                    ${data.immediate_actions.map(action => `<li style="margin: 0.5rem 0;">${action}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (data.risk_assessment && data.risk_assessment.length > 0) {
        html += `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--warning-yellow);">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <strong>Risk Assessment</strong>
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;">
                    ${data.risk_assessment.map(risk => `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: var(--bg-light); border-radius: 0.25rem;">
                            <span>${risk.tank_name}</span>
                            <span class="status-badge status-${risk.risk_level}">${risk.risk_level}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (data.water_quality_advice && data.water_quality_advice.length > 0) {
        html += `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--primary-blue);">
                        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
                    </svg>
                    <strong>Water Quality Advice</strong>
                </div>
                <div style="margin-top: 0.5rem; color: var(--text-secondary);">
                    ${data.water_quality_advice.map(advice => `
                        <div style="margin: 0.5rem 0;">
                            <strong style="color: var(--text-primary);">${advice.tank_name}:</strong> ${advice.advice}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (data.trend_forecast) {
        html += `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--success-green);">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                    </svg>
                    <strong>Trend Forecast</strong>
                </div>
                <p style="margin: 0.5rem 0 0; color: var(--text-secondary);">${data.trend_forecast}</p>
            </div>
        `;
    }
    
    if (!html) {
        html = `
            <div class="recommendation-item">
                <p style="color: var(--success-green);">All systems operating normally. No immediate actions required.</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

export { loadRecommendations };
