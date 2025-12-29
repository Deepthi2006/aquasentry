from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorReading(BaseModel):
    ph: float
    turbidity: float
    temperature: float
    dissolved_oxygen: Optional[float] = None
    chlorine: Optional[float] = None
    timestamp: str


class HistoricalReading(BaseModel):
    date: str
    ph: float
    turbidity: float
    temperature: float


class ReadingAnalysis(BaseModel):
    status: str
    ph_status: str
    turbidity_status: str
    temperature_status: str
    recommendations: list[str]
