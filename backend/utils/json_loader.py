import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

# Path to backend/data/data.json
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.json')

# In-memory cache so we don't read the file on every request
_cached_data: Dict[str, Any] = {}


def load_data() -> Dict[str, Any]:
    """
    Load the entire data.json into memory (with simple caching).
    """
    global _cached_data
    if not _cached_data:
        with open(DATA_FILE_PATH, 'r') as f:
            _cached_data = json.load(f)
    return _cached_data


def get_tanks() -> list:
    """
    Return the list of tanks from data.json.
    """
    data = load_data()
    return data.get('tanks', [])


def get_tank_by_id(tank_id: str) -> dict | None:
    """
    Find a single tank by its id.
    """
    tanks = get_tanks()
    for tank in tanks:
        if tank['id'] == tank_id:
            return tank
    return None


def get_alerts() -> list:
    """
    Return the list of alerts from data.json.
    """
    data = load_data()
    return data.get('alerts', [])


def get_maintenance_schedule() -> list:
    """
    Return the maintenance_schedule array from data.json.
    """
    data = load_data()
    return data.get('maintenance_schedule', [])


def reload_data() -> Dict[str, Any]:
    """
    Clear the cache and force reload from disk.
    """
    global _cached_data
    _cached_data = {}
    return load_data()


def update_maintenance(tank_id: str, cleaned_date: str, notes: str = None) -> Dict[str, Any]:
    """
    Update maintenance info for a given tank in data.json.

    What this does:
    - Updates tanks[].last_cleaned to cleaned_date
    - Recomputes next_maintenance using maintenance_schedule[].cleaning_interval_days
      and stores it in tanks[].next_maintenance
    - Updates the corresponding entry in maintenance_schedule[]:
        - last_cleaned = cleaned_date
        - next_scheduled = cleaned_date + cleaning_interval_days
    - Stores notes under tanks[].maintenance.notes (and last_cleaned there too)
    - Saves everything back to data.json and updates the in-memory cache.
    """
    global _cached_data

    data = load_data()

    tanks = data.get('tanks', [])
    schedule_list = data.get('maintenance_schedule', [])

    # 1) Find the tank object
    tank_obj = None
    for tank in tanks:
        if tank['id'] == tank_id:
            tank_obj = tank
            break

    if tank_obj is None:
        return {"success": False, "error": f"Tank '{tank_id}' not found"}

    # 2) Find the maintenance_schedule entry for this tank
    sched_obj = None
    for entry in schedule_list:
        if entry.get('tank_id') == tank_id:
            sched_obj = entry
            break

    if sched_obj is None:
        # We can either treat this as an error or just update the tank only.
        # Here we return an error so you know the schedule config is missing.
        return {"success": False, "error": f"Maintenance schedule for '{tank_id}' not found"}

    # 3) Parse the cleaned_date and compute next_scheduled
    # Expect input like "2025-12-09"
    try:
        cleaned_dt = datetime.strptime(cleaned_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid date format for cleaned_date: '{cleaned_date}'. Expected 'YYYY-MM-DD'."
        }

    interval_days = sched_obj.get('cleaning_interval_days', 30)
    next_scheduled_dt = cleaned_dt + timedelta(days=interval_days)
    next_scheduled_str = next_scheduled_dt.strftime("%Y-%m-%d")

    # 4) Update maintenance_schedule[] entry
    sched_obj['last_cleaned'] = cleaned_date
    sched_obj['next_scheduled'] = next_scheduled_str

    # 5) Update the tank object itself
    tank_obj['last_cleaned'] = cleaned_date
    tank_obj['next_maintenance'] = next_scheduled_str

    # Ensure "maintenance" dict exists on the tank and update it
    maintenance_info = tank_obj.get('maintenance', {})
    maintenance_info['last_cleaned'] = cleaned_date
    if notes:
        maintenance_info['notes'] = notes
    tank_obj['maintenance'] = maintenance_info

    # 6) Save the updated data back to data.json
    with open(DATA_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=2)

    # 7) Update the in-memory cache
    _cached_data = data

    return {
        "success": True,
        "message": f"Maintenance updated for {tank_id}",
        "tank": tank_obj
    }
