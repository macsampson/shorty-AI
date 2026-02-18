from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable


class PromptExpansionGenerator(ABC):
    """Expands simple prompts into detailed cinematic descriptions"""

    @abstractmethod
    async def expand_prompt(self, simple_prompt: str) -> str:
        """
        Expand a simple prompt into a detailed cinematic description

        Args:
            simple_prompt: User's simple video idea (e.g., "cat on street")

        Returns:
            Expanded 80-word cinematic prompt with camera angles, lighting, textures
        """
        pass

class VideoGenerator(ABC):
    """Generates video from detailed prompts"""

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        output_dir: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        frame_count: Optional[int] = None
    ) -> str:
        """
        Generate video from prompt

        Args:
            prompt: Detailed cinematic prompt
            output_dir: Directory to save video
            progress_callback: Async function to report progress (0-100)

        Returns:
            Path to generated video file (MP4 with audio)
        """
        pass

class CaptionGenerator(ABC):
    """Generates word-level captions from video audio"""

    @abstractmethod
    async def generate_captions(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Extract word-level timestamps from video audio

        Args:
            video_path: Path to video file with audio

        Returns:
            List of word dictionaries: [{"text": "word", "start": 0.5, "end": 0.8}, ...]
        """
        pass
