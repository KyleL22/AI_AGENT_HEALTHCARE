from pydantic import BaseModel
from typing import Optional, List

class IngestTextRequest(BaseModel):
    user_id: str
    diet_text: str  # 하루 식단 텍스트

class QueryRequest(BaseModel):
    user_id: str
    question: str

class ReportResponse(BaseModel):
    path: str
    created_at: str

class GenericResponse(BaseModel):
    ok: bool
    msg: Optional[str] = None

class ExerciseCSVMeta(BaseModel):
    user_id: str
    source: str  # 'strava' | 'google_fit' | 'other'
