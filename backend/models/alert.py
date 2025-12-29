from pydantic import BaseModel
from typing import Optional


class Alert(BaseModel):
    id: str
    tank_id: str
    type: str
    message: str
    created_at: str
    acknowledged: bool = False


class AlertCreate(BaseModel):
    tank_id: str
    type: str
    message: str
