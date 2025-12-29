from typing import List, Dict, Any
from backend.services.tank_service import get_all_tanks_with_status


def get_map_markers() -> List[Dict[str, Any]]:
    tanks = get_all_tanks_with_status()
    markers = []
    
    for tank in tanks:
        location = tank.get('location', {})
        readings = tank.get('current_readings', {})
        
        color = 'green'
        if tank['status'] == 'warning':
            color = 'yellow'
        elif tank['status'] == 'critical':
            color = 'red'
        
        markers.append({
            'id': tank['id'],
            'name': tank['name'],
            'lat': location.get('lat', 0),
            'lng': location.get('lng', 0),
            'address': location.get('address', ''),
            'status': tank['status'],
            'color': color,
            'popup_content': {
                'name': tank['name'],
                'status': tank['status'],
                'level': tank['current_level_percent'],
                'ph': readings.get('ph', 0),
                'turbidity': readings.get('turbidity', 0),
                'temperature': readings.get('temperature', 0),
                'days_since_cleaned': tank['days_since_cleaned'],
                'days_until_maintenance': tank['days_until_maintenance']
            }
        })
    
    return markers


def get_map_bounds() -> Dict[str, Any]:
    tanks = get_all_tanks_with_status()
    
    if not tanks:
        return {
            'center': {'lat': 40.7128, 'lng': -74.006},
            'zoom': 12
        }
    
    lats = [t['location']['lat'] for t in tanks]
    lngs = [t['location']['lng'] for t in tanks]
    
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    
    return {
        'center': {'lat': center_lat, 'lng': center_lng},
        'zoom': 12,
        'bounds': {
            'north': max(lats),
            'south': min(lats),
            'east': max(lngs),
            'west': min(lngs)
        }
    }


def get_map_data() -> Dict[str, Any]:
    return {
        'markers': get_map_markers(),
        'bounds': get_map_bounds()
    }
