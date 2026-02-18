from api.schemas.generate_text_request import GenerateTextRequest
from pydantic import BaseModel
from typing import Optional


class VideoGenerationStatus(BaseModel):
    job_id: str
    status: str  # "started", "processing", "complete", "error"
    progress: float = 0.0
    stage: str = ""
    message: str = ""
    video_url: Optional[str] = None
