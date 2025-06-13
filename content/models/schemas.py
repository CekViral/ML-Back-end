from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    id: str
    name: str
    email: str


class RagRequest(BaseModel):
    processed_text: str = Field(..., description="Preprocessed text to query RAG")
    final_label_threshold: str = Field(..., description="Threshold label from inference result")


