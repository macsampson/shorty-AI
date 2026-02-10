from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Dict, Any

class ScriptGenerator(ABC):
    @abstractmethod
    async def generate_script(self, topic: str) -> Dict[str, Any]:
        """Generate a script for a given topic."""
        pass

    @abstractmethod
    async def generate_scenes_and_prompts(self, topic: str, num_scenes: int) -> Dict[str, Any]:
        """Generate scenes and image prompts for a given topic."""
        pass

class ImageGenerator(ABC):
    @abstractmethod
    async def generate_image(self, prompt: str, output_dir: str) -> str:
        """Generate an image from a prompt and save it to output_dir. Returns the file path."""
        pass

class VoiceGenerator(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice: str, output_dir: str) -> str:
        """Generate speech from text and save it to output_dir. Returns the file path."""
        pass
