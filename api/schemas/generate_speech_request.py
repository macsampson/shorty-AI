from pydantic import BaseModel


class GenerateSpeechRequest(BaseModel):
    text: str
    voice: str
    preset: str = "ultra_fast"
    candidates: int = 1
    cvvp_amount: float = 0.0
