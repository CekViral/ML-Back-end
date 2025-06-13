# cekviral_project/app/schemas.py
from pydantic import BaseModel, Field

# File ini akan berisi semua model data (skema) Pydantic.
# Ini membantu menghindari circular imports.

class ContentInput(BaseModel):
    content: str = Field(..., description="Konten yang akan diverifikasi, bisa berupa teks murni atau URL.")

class PredictionProbabilities(BaseModel):
    HOAKS: float = Field(..., description="Probabilitas konten sebagai HOAKS.")
    FAKTA: float = Field(..., description="Probabilitas konten sebagai FAKTA.")

class MLPredictionOutput(BaseModel):
    status: str
    message: str
    probabilities: PredictionProbabilities
    predicted_label_model: str
    highest_confidence: float
    final_label_thresholded: str
    inference_time_ms: float

class VerificationResult(BaseModel):
    original_input: str
    input_type: str
    processed_text: str | None
    prediction: MLPredictionOutput
    processing_message: str | None
    history_id: str