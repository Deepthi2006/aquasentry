const API_BASE = '/api';

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error for ${endpoint}:`, error);
        throw error;
    }
}

async function getPrediction(tankId) {
    return fetchAPI(`/ai/predict/${tankId}`);
}

async function getLeakageDetection(tankId) {
    return fetchAPI(`/ai/leakage/${tankId}`);
}

async function getMaintenancePrediction(tankId) {
    return fetchAPI(`/ai/maintenance/${tankId}`);
}

async function getDemandForecast() {
    return fetchAPI('/ai/demand-forecast');
}

async function getRainwaterHarvesting() {
    return fetchAPI('/ai/rainwater');
}

async function getExplainableAlert(alertId) {
    return fetchAPI(`/ai/explain-alert/${alertId}`);
}

async function getWardGeoJSON() {
    return fetchAPI('/gis/wards');
}

async function getHeatmapData(metric = 'health_score') {
    return fetchAPI(`/gis/heatmap?metric=${metric}`);
}

async function chatWithCopilot(query, context = '') {
    return fetchAPI('/ai/copilot', {
        method: 'POST',
        body: JSON.stringify({ query, context })
    });
}

export {
    getPrediction,
    getLeakageDetection,
    getMaintenancePrediction,
    getDemandForecast,
    getRainwaterHarvesting,
    getExplainableAlert,
    getWardGeoJSON,
    getHeatmapData,
    chatWithCopilot
};
