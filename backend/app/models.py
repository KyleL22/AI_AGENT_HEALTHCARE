from pydantic import BaseModel
from typing import Optional, List

class DietIn(BaseModel):
    text: Optional[str] = None
    note: Optional[str] = None

class ExerciseIn(BaseModel):
    source: str  # 'strava' | 'google_fit' | 'manual'
    csv_text: str

class ReportRequest(BaseModel):
    day: Optional[str] = None  # YYYY-MM-DD; default: today
    email: Optional[str] = None

class ChatIn(BaseModel):
    message: str
    history: Optional[List[dict]] = None  # [{role, content}...]
