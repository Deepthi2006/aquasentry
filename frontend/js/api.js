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

async function getTanks() {
    return fetchAPI('/tanks');
}

async function getTank(tankId) {
    return fetchAPI(`/tanks/${tankId}`);
}

async function getTankHistory(tankId) {
    return fetchAPI(`/tanks/${tankId}/history`);
}

async function getAlerts() {
    return fetchAPI('/alerts');
}

async function getMapData() {
    return fetchAPI('/map');
}

async function getAnalytics() {
    return fetchAPI('/analytics');
}

async function getRecommendations() {
    return fetchAPI('/recommendations', { method: 'POST' });
}

export {
    getTanks,
    getTank,
    getTankHistory,
    getAlerts,
    getMapData,
    getAnalytics,
    getRecommendations
};
