from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Location(BaseModel):
    lat: float
    lng: float
    address: str


class Reading(BaseModel):
    ph: float
    turbidity: float
    temperature: float
    dissolved_oxygen: Optional[float] = None
    chlorine: Optional[float] = None
    timestamp: Optional[str] = None


class HistoryEntry(BaseModel):
    date: str
    ph: float
    turbidity: float
    temperature: float


class Tank(BaseModel):
    id: str
    name: str
    location: Location
    capacity_liters: int
    current_level_percent: int
    status: str
    last_cleaned: str
    next_maintenance: str
    current_readings: Reading
    history: List[HistoryEntry]


class TankSummary(BaseModel):
    id: str
    name: str
    status: str
    current_level_percent: int
    ph: float
    turbidity: float
    temperature: float
    days_since_cleaned: int
    days_until_maintenance: int
