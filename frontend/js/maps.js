let map = null;
let markers = [];

function initMap(containerId, center = { lat: 40.7128, lng: -74.006 }, zoom = 12) {
    if (map) {
        map.remove();
    }
    
    map = L.map(containerId).setView([center.lat, center.lng], zoom);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);
    
    return map;
}

function getMarkerIcon(status) {
    const colors = {
        normal: '#22c55e',
        warning: '#eab308',
        critical: '#ef4444'
    };
    
    const color = colors[status] || colors.normal;
    
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                width: 24px;
                height: 24px;
                background: ${color};
                border: 3px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            "></div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
}

function createPopupContent(data) {
    const statusClass = `status-${data.status}`;
    
    return `
        <div style="min-width: 200px; font-family: 'Inter', sans-serif;">
            <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${data.name}</h3>
            <span class="status-badge ${statusClass}" style="
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                margin-bottom: 8px;
            ">${data.status}</span>
            <div style="font-size: 12px; color: #666;">
                <div style="margin: 4px 0;"><strong>Level:</strong> ${data.level}%</div>
                <div style="margin: 4px 0;"><strong>pH:</strong> ${data.ph}</div>
                <div style="margin: 4px 0;"><strong>Turbidity:</strong> ${data.turbidity} NTU</div>
                <div style="margin: 4px 0;"><strong>Temp:</strong> ${data.temperature}°C</div>
                <div style="margin: 4px 0;"><strong>Last Cleaned:</strong> ${data.days_since_cleaned} days ago</div>
            </div>
            <button onclick="window.viewTankDetails('${data.id}')" style="
                margin-top: 10px;
                padding: 6px 12px;
                background: #0ea5e9;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                width: 100%;
            ">View Details</button>
        </div>
    `;
}

function addMarkers(mapData, onMarkerClick = null) {
    clearMarkers();
    
    mapData.forEach(data => {
        const marker = L.marker([data.lat, data.lng], {
            icon: getMarkerIcon(data.status)
        }).addTo(map);
        
        const popupData = {
            id: data.id,
            name: data.name,
            status: data.status,
            level: data.popup_content.level,
            ph: data.popup_content.ph,
            turbidity: data.popup_content.turbidity,
            temperature: data.popup_content.temperature,
            days_since_cleaned: data.popup_content.days_since_cleaned
        };
        
        marker.bindPopup(createPopupContent(popupData));
        
        if (onMarkerClick) {
            marker.on('click', () => onMarkerClick(data));
        }
        
        markers.push(marker);
    });
}

function clearMarkers() {
    markers.forEach(marker => marker.remove());
    markers = [];
}

function fitBounds(bounds) {
    if (map && bounds) {
        map.fitBounds([
            [bounds.south, bounds.west],
            [bounds.north, bounds.east]
        ], { padding: [50, 50] });
    }
}

function getMap() {
    return map;
}

export { initMap, addMarkers, clearMarkers, fitBounds, getMap };
