const CACHE_NAME = 'aquasentry-v2';
const OFFLINE_URL = '/offline';

const STATIC_ASSETS = [
    '/',
    '/dashboard',
    '/login',
    '/alerts',
    '/map',
    '/maintenance',
    '/copilot',
    '/vision',
    '/static/css/styles.css',
    '/static/js/api.js',
    '/static/js/auth.js',
    '/static/js/dashboard.js',
    '/static/js/charts.js',
    '/static/js/maps.js',
    '/static/js/recommendations.js',
    '/static/js/ai-features.js'
];

const API_CACHE_DURATION = 5 * 60 * 1000;

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('AquaSentry: Caching static assets for offline use');
            return cache.addAll(STATIC_ASSETS.filter(url => !url.startsWith('/api')));
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstWithCache(request));
    } else {
        event.respondWith(cacheFirstWithNetwork(request));
    }
});

async function networkFirstWithCache(request) {
    const cache = await caches.open(CACHE_NAME);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok && request.method === 'GET') {
            const responseClone = networkResponse.clone();
            cache.put(request, responseClone);
        }
        
        return networkResponse;
    } catch (error) {
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            console.log('AquaSentry: Serving cached API response (offline)');
            return cachedResponse;
        }
        
        return new Response(JSON.stringify({
            success: false,
            offline: true,
            error: 'You are offline. Please check your internet connection.',
            cached_at: null
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function cacheFirstWithNetwork(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        fetchAndCache(request, cache);
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        if (request.mode === 'navigate') {
            const offlinePage = await cache.match(OFFLINE_URL);
            if (offlinePage) return offlinePage;
        }
        
        return new Response('Offline', { status: 503 });
    }
}

async function fetchAndCache(request, cache) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
    } catch (error) {
    }
}

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-data') {
        event.waitUntil(syncOfflineData());
    }
});

async function syncOfflineData() {
    console.log('AquaSentry: Syncing offline data...');
}

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_OFFLINE_DATA') {
        cacheOfflineData();
    }
});

async function cacheOfflineData() {
    try {
        const cache = await caches.open(CACHE_NAME);
        
        const endpoints = [
            '/api/tanks',
            '/api/alerts',
            '/api/map',
            '/api/analytics',
            '/api/offline-data'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    await cache.put(endpoint, response);
                    console.log(`AquaSentry: Cached ${endpoint} for offline use`);
                }
            } catch (e) {
                console.log(`AquaSentry: Could not cache ${endpoint}`);
            }
        }
    } catch (error) {
        console.error('AquaSentry: Error caching offline data', error);
    }
}
