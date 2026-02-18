# app/schemas/generate_text_request.py
from pydantic import BaseModel, Field


class GenerateTextRequest(BaseModel):
    prompt: str
    max_length: int = 200
    num_return_sequences: int = 1
    duration_seconds: int = Field(default=5, ge=5, le=30)
