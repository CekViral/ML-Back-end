from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class User(BaseModel):
    id: str
    name: str
    email: str


class HistoryItem(BaseModel):
    history_id: str
    original_input: str
    processed_text: str
    predicted_label: str
    prob_hoax: float
    prob_fakta: float
    final_label_threshold: str
    inference_time_ms: float
    created_at: datetime


class Response(BaseModel):
    detail: str