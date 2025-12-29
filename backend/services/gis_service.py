import json
from typing import Dict, Any, List
from backend.services.tank_service import get_all_tanks_with_status


def get_ward_geojson() -> Dict[str, Any]:
    tanks = get_all_tanks_with_status()
    
    features = []
    
    ward_data = {}
    for tank in tanks:
        location = tank.get('location', {})
        lat = location.get('lat', 0)
        lng = location.get('lng', 0)
        
        ward_id = f"ward_{int(lat * 10) % 10}_{int(lng * 10) % 10}"
        
        if ward_id not in ward_data:
            ward_data[ward_id] = {
                "tanks": [],
                "center_lat": lat,
                "center_lng": lng,
                "total_capacity": 0,
                "avg_ph": 0,
                "avg_turbidity": 0,
                "critical_count": 0,
                "warning_count": 0,
                "normal_count": 0
            }
        
        ward_data[ward_id]["tanks"].append(tank)
        ward_data[ward_id]["total_capacity"] += tank.get('capacity_liters', 0)
        
        readings = tank.get('current_readings', {})
        ward_data[ward_id]["avg_ph"] += readings.get('ph', 7.0)
        ward_data[ward_id]["avg_turbidity"] += readings.get('turbidity', 0)
        
        status = tank.get('status', 'normal')
        if status == 'critical':
            ward_data[ward_id]["critical_count"] += 1
        elif status == 'warning':
            ward_data[ward_id]["warning_count"] += 1
        else:
            ward_data[ward_id]["normal_count"] += 1
    
    for ward_id, data in ward_data.items():
        num_tanks = len(data["tanks"])
        if num_tanks > 0:
            data["avg_ph"] = round(data["avg_ph"] / num_tanks, 2)
            data["avg_turbidity"] = round(data["avg_turbidity"] / num_tanks, 2)
        
        if data["critical_count"] > 0:
            health_score = 30
            status = "critical"
        elif data["warning_count"] > 0:
            health_score = 60
            status = "warning"
        else:
            health_score = 90
            status = "normal"
        
        lat = data["center_lat"]
        lng = data["center_lng"]
        offset = 0.02
        
        polygon = [
            [lng - offset, lat - offset],
            [lng + offset, lat - offset],
            [lng + offset, lat + offset],
            [lng - offset, lat + offset],
            [lng - offset, lat - offset]
        ]
        
        feature = {
            "type": "Feature",
            "properties": {
                "ward_id": ward_id,
                "ward_name": f"Ward {ward_id.replace('ward_', '').replace('_', '-')}",
                "tank_count": num_tanks,
                "total_capacity_liters": data["total_capacity"],
                "avg_ph": data["avg_ph"],
                "avg_turbidity": data["avg_turbidity"],
                "health_score": health_score,
                "status": status,
                "critical_tanks": data["critical_count"],
                "warning_tanks": data["warning_count"],
                "normal_tanks": data["normal_count"],
                "tanks": [{"id": t["id"], "name": t["name"], "status": t["status"]} for t in data["tanks"]]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon]
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


def get_heatmap_data(metric: str = "health_score") -> Dict[str, Any]:
    tanks = get_all_tanks_with_status()
    
    points = []
    
    for tank in tanks:
        location = tank.get('location', {})
        readings = tank.get('current_readings', {})
        
        if metric == "health_score":
            status = tank.get('status', 'normal')
            value = 30 if status == 'critical' else 60 if status == 'warning' else 90
        elif metric == "ph":
            value = readings.get('ph', 7.0)
        elif metric == "turbidity":
            value = readings.get('turbidity', 0)
        elif metric == "temperature":
            value = readings.get('temperature', 20)
        elif metric == "water_level":
            value = tank.get('current_level_percent', 50)
        else:
            value = 50
        
        points.append({
            "lat": location.get('lat', 0),
            "lng": location.get('lng', 0),
            "value": value,
            "tank_id": tank.get('id'),
            "tank_name": tank.get('name'),
            "status": tank.get('status', 'normal')
        })
    
    return {
        "metric": metric,
        "points": points,
        "legend": get_legend_for_metric(metric),
        "bounds": calculate_bounds(points)
    }


def get_legend_for_metric(metric: str) -> Dict[str, Any]:
    legends = {
        "health_score": {
            "title": "Ward Health Score",
            "ranges": [
                {"min": 0, "max": 40, "color": "#ef4444", "label": "Critical"},
                {"min": 40, "max": 70, "color": "#f59e0b", "label": "Warning"},
                {"min": 70, "max": 100, "color": "#10b981", "label": "Normal"}
            ]
        },
        "ph": {
            "title": "pH Level",
            "ranges": [
                {"min": 0, "max": 6.5, "color": "#ef4444", "label": "Acidic"},
                {"min": 6.5, "max": 8.5, "color": "#10b981", "label": "Normal"},
                {"min": 8.5, "max": 14, "color": "#ef4444", "label": "Alkaline"}
            ]
        },
        "turbidity": {
            "title": "Turbidity (NTU)",
            "ranges": [
                {"min": 0, "max": 1, "color": "#10b981", "label": "Excellent"},
                {"min": 1, "max": 5, "color": "#f59e0b", "label": "Acceptable"},
                {"min": 5, "max": 100, "color": "#ef4444", "label": "Poor"}
            ]
        },
        "temperature": {
            "title": "Temperature (°C)",
            "ranges": [
                {"min": 0, "max": 15, "color": "#3b82f6", "label": "Cold"},
                {"min": 15, "max": 25, "color": "#10b981", "label": "Normal"},
                {"min": 25, "max": 50, "color": "#ef4444", "label": "Warm"}
            ]
        },
        "water_level": {
            "title": "Water Level (%)",
            "ranges": [
                {"min": 0, "max": 30, "color": "#ef4444", "label": "Low"},
                {"min": 30, "max": 70, "color": "#f59e0b", "label": "Medium"},
                {"min": 70, "max": 100, "color": "#10b981", "label": "High"}
            ]
        }
    }
    return legends.get(metric, legends["health_score"])


def calculate_bounds(points: List[dict]) -> Dict[str, Any]:
    if not points:
        return {
            "center": {"lat": 40.7128, "lng": -74.006},
            "zoom": 12
        }
    
    lats = [p["lat"] for p in points]
    lngs = [p["lng"] for p in points]
    
    return {
        "center": {
            "lat": sum(lats) / len(lats),
            "lng": sum(lngs) / len(lngs)
        },
        "bounds": {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        },
        "zoom": 11
    }


def get_ward_details(ward_id: str) -> Dict[str, Any]:
    geojson = get_ward_geojson()
    
    for feature in geojson.get("features", []):
        if feature.get("properties", {}).get("ward_id") == ward_id:
            return {
                "success": True,
                "ward": feature
            }
    
    return {
        "success": False,
        "error": "Ward not found"
    }
