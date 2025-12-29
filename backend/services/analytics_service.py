from typing import List, Dict, Any
from backend.utils.json_loader import get_tanks, get_alerts


def analyze_water_quality(tank: dict) -> Dict[str, Any]:
    readings = tank.get('current_readings', {})
    ph = readings.get('ph', 7.0)
    turbidity = readings.get('turbidity', 0)
    temperature = readings.get('temperature', 20)
    
    issues = []
    recommendations = []
    
    if ph < 6.5:
        issues.append(f"pH too low ({ph})")
        recommendations.append("Add pH increaser (sodium carbonate)")
    elif ph > 8.5:
        issues.append(f"pH too high ({ph})")
        recommendations.append("Add pH decreaser (sodium bisulfate)")
    
    if turbidity > 5:
        issues.append(f"High turbidity ({turbidity} NTU)")
        recommendations.append("Schedule immediate tank cleaning")
        recommendations.append("Check filtration system")
    elif turbidity > 3:
        issues.append(f"Elevated turbidity ({turbidity} NTU)")
        recommendations.append("Monitor turbidity levels closely")
    
    if temperature > 25:
        issues.append(f"Temperature elevated ({temperature}°C)")
        recommendations.append("Check cooling systems")
    
    return {
        'tank_id': tank['id'],
        'tank_name': tank['name'],
        'issues': issues,
        'recommendations': recommendations,
        'risk_level': 'critical' if len(issues) >= 2 else 'warning' if len(issues) == 1 else 'normal'
    }


def get_system_analytics() -> Dict[str, Any]:
    tanks = get_tanks()
    alerts = get_alerts()
    
    total_capacity = sum(t['capacity_liters'] for t in tanks)
    avg_level = sum(t['current_level_percent'] for t in tanks) / len(tanks) if tanks else 0
    
    ph_values = [t['current_readings']['ph'] for t in tanks]
    turbidity_values = [t['current_readings']['turbidity'] for t in tanks]
    temp_values = [t['current_readings']['temperature'] for t in tanks]
    
    critical_tanks = [t for t in tanks if analyze_water_quality(t)['risk_level'] == 'critical']
    warning_tanks = [t for t in tanks if analyze_water_quality(t)['risk_level'] == 'warning']
    
    unacknowledged_alerts = [a for a in alerts if not a.get('acknowledged', False)]
    
    return {
        'total_tanks': len(tanks),
        'total_capacity_liters': total_capacity,
        'average_level_percent': round(avg_level, 1),
        'average_ph': round(sum(ph_values) / len(ph_values), 2) if ph_values else 0,
        'average_turbidity': round(sum(turbidity_values) / len(turbidity_values), 2) if turbidity_values else 0,
        'average_temperature': round(sum(temp_values) / len(temp_values), 1) if temp_values else 0,
        'critical_count': len(critical_tanks),
        'warning_count': len(warning_tanks),
        'normal_count': len(tanks) - len(critical_tanks) - len(warning_tanks),
        'active_alerts': len(unacknowledged_alerts),
        'critical_tanks': [{'id': t['id'], 'name': t['name']} for t in critical_tanks],
        'warning_tanks': [{'id': t['id'], 'name': t['name']} for t in warning_tanks]
    }


def get_trend_analysis(tank_id: str) -> Dict[str, Any]:
    from backend.utils.json_loader import get_tank_by_id
    
    tank = get_tank_by_id(tank_id)
    if not tank:
        return {'error': 'Tank not found'}
    
    history = tank.get('history', [])
    if len(history) < 2:
        return {'trend': 'insufficient_data'}
    
    recent = history[-1]
    older = history[0]
    
    ph_trend = 'stable'
    if recent['ph'] - older['ph'] > 0.3:
        ph_trend = 'increasing'
    elif older['ph'] - recent['ph'] > 0.3:
        ph_trend = 'decreasing'
    
    turbidity_trend = 'stable'
    if recent['turbidity'] - older['turbidity'] > 1:
        turbidity_trend = 'increasing'
    elif older['turbidity'] - recent['turbidity'] > 1:
        turbidity_trend = 'decreasing'
    
    temp_trend = 'stable'
    if recent['temperature'] - older['temperature'] > 1:
        temp_trend = 'increasing'
    elif older['temperature'] - recent['temperature'] > 1:
        temp_trend = 'decreasing'
    
    return {
        'tank_id': tank_id,
        'ph_trend': ph_trend,
        'turbidity_trend': turbidity_trend,
        'temperature_trend': temp_trend,
        'data_points': len(history)
    }
