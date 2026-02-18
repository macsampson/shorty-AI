import logging
import whisper
import torch
import os
from typing import List, Dict, Any
from api.generators.base import CaptionGenerator
from api.config import settings

logger = logging.getLogger(__name__)

class WhisperCaptionGenerator(CaptionGenerator):
    def __init__(self):
        self.model_size = settings.whisper_model_size  # "base", "small", "medium", "large"
        self.min_confidence = settings.whisper_min_confidence
        self.no_speech_threshold = settings.whisper_no_speech_threshold
        self.model = None

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            self.model = whisper.load_model(self.model_size)

    def _unload_model(self):
        """Unload model and free VRAM"""
        if self.model is not None:
            del self.model
            self.model = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

    async def generate_captions(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Extract word-level captions from video audio using Whisper

        Returns:
            [{"text": "hello", "start": 0.0, "end": 0.5}, ...]
        """
        try:
            self._load_model()

            # Transcribe with word-level timestamps
            # no_speech_threshold: segments with no_speech_prob above this are
            # treated as silence — reduces hallucinated text on silent audio
            # logprob_threshold: segments with avg log probability below this
            # are treated as failed decoding — filters out low-quality output
            result = self.model.transcribe(
                video_path,
                task="transcribe",
                language="en",
                word_timestamps=True,
                verbose=False,
                no_speech_threshold=self.no_speech_threshold,
                logprob_threshold=-0.5,
                condition_on_previous_text=False,
            )

            # Extract word-level timestamps, filtering by confidence
            word_timestamps = []
            dropped = 0

            for segment in result.get("segments", []):
                # Skip entire segment if Whisper thinks it's likely not speech
                if segment.get("no_speech_prob", 0) > self.no_speech_threshold:
                    dropped += len(segment.get("words", []))
                    logger.info(
                        f"[Whisper] Skipping segment (no_speech_prob={segment['no_speech_prob']:.2f}): "
                        f"{segment.get('text', '').strip()[:80]}"
                    )
                    continue

                for word_data in segment.get("words", []):
                    probability = word_data.get("probability", 0)
                    if probability < self.min_confidence:
                        dropped += 1
                        continue
                    word_timestamps.append({
                        "text": word_data["word"].strip(),
                        "start": word_data["start"],
                        "end": word_data["end"]
                    })

            if dropped:
                logger.info(
                    f"[Whisper] Dropped {dropped} low-confidence words "
                    f"(min_confidence={self.min_confidence})"
                )

            return word_timestamps

        finally:
            # Always unload model if in single GPU mode
            if settings.single_gpu_mode:
                self._unload_model()
