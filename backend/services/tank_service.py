from datetime import datetime, date
from typing import List, Optional
from backend.utils.json_loader import get_tanks, get_tank_by_id, get_maintenance_schedule


def calculate_days_since_cleaned(last_cleaned: str) -> int:
    cleaned_date = datetime.strptime(last_cleaned, "%Y-%m-%d").date()
    today = date.today()
    return (today - cleaned_date).days


def calculate_days_until_maintenance(next_maintenance: str) -> int:
    maintenance_date = datetime.strptime(next_maintenance, "%Y-%m-%d").date()
    today = date.today()
    return (maintenance_date - today).days


def get_tank_status(tank: dict) -> str:
    readings = tank.get('current_readings', {})
    ph = readings.get('ph', 7.0)
    turbidity = readings.get('turbidity', 0)
    days_since_cleaned = calculate_days_since_cleaned(tank.get('last_cleaned', '2024-01-01'))
    
    if turbidity > 5 or ph < 6.5 or ph > 8.5 or days_since_cleaned > 30:
        if turbidity > 7 or ph < 6.0 or ph > 9.0 or days_since_cleaned > 60:
            return 'critical'
        return 'warning'
    return 'normal'


def get_all_tanks_with_status() -> List[dict]:
    tanks = get_tanks()
    result = []
    
    for tank in tanks:
        days_since_cleaned = calculate_days_since_cleaned(tank['last_cleaned'])
        days_until_maintenance = calculate_days_until_maintenance(tank['next_maintenance'])
        status = get_tank_status(tank)
        
        result.append({
            'id': tank['id'],
            'name': tank['name'],
            'location': tank['location'],
            'capacity_liters': tank['capacity_liters'],
            'current_level_percent': tank['current_level_percent'],
            'status': status,
            'last_cleaned': tank['last_cleaned'],
            'next_maintenance': tank['next_maintenance'],
            'current_readings': tank['current_readings'],
            'days_since_cleaned': days_since_cleaned,
            'days_until_maintenance': days_until_maintenance
        })
    
    return result


def get_single_tank(tank_id: str) -> Optional[dict]:
    tank = get_tank_by_id(tank_id)
    if not tank:
        return None
    
    days_since_cleaned = calculate_days_since_cleaned(tank['last_cleaned'])
    days_until_maintenance = calculate_days_until_maintenance(tank['next_maintenance'])
    status = get_tank_status(tank)
    
    return {
        **tank,
        'status': status,
        'days_since_cleaned': days_since_cleaned,
        'days_until_maintenance': days_until_maintenance
    }


def get_tank_history(tank_id: str) -> Optional[List[dict]]:
    tank = get_tank_by_id(tank_id)
    if not tank:
        return None
    return tank.get('history', [])


def get_tanks_summary() -> dict:
    tanks = get_all_tanks_with_status()
    
    total = len(tanks)
    normal = sum(1 for t in tanks if t['status'] == 'normal')
    warning = sum(1 for t in tanks if t['status'] == 'warning')
    critical = sum(1 for t in tanks if t['status'] == 'critical')
    
    return {
        'total': total,
        'normal': normal,
        'warning': warning,
        'critical': critical,
        'avg_level': sum(t['current_level_percent'] for t in tanks) / total if total > 0 else 0
    }
