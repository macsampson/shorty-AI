from pydantic import BaseModel


class GenerateImageRequest(BaseModel):
    prompt: str
    num_inference_steps: int = 4
    guidance_scale: float = 0.0
    max_sequence_length: int = 256
