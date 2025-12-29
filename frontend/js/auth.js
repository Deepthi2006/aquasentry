async function checkAuth() {
    const token = localStorage.getItem('aquasentry_token');
    if (!token && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
        return;
    }
    
    if (token) {
        try {
            const response = await fetch(`/api/auth/validate?token=${encodeURIComponent(token)}`);
            const data = await response.json();
            if (!data.valid) {
                localStorage.removeItem('aquasentry_token');
                localStorage.removeItem('aquasentry_user');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Auth validation error:', error);
        }
    }
}

async function logout() {
    const token = localStorage.getItem('aquasentry_token');
    if (token) {
        try {
            await fetch(`/api/auth/logout?token=${encodeURIComponent(token)}`, { method: 'POST' });
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
    localStorage.removeItem('aquasentry_token');
    localStorage.removeItem('aquasentry_user');
    window.location.href = '/login';
}

function getUser() {
    const userStr = localStorage.getItem('aquasentry_user');
    return userStr ? JSON.parse(userStr) : null;
}

function getToken() {
    return localStorage.getItem('aquasentry_token');
}

export { checkAuth, logout, getUser, getToken };
