# app/schemas/generate_text_request.py
from pydantic import BaseModel


class GenerateTextRequest(BaseModel):
    prompt: str
    max_length: int = 200
    num_return_sequences: int = 1
