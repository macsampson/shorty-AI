from api.generators.base import PromptExpansionGenerator, VideoGenerator, CaptionGenerator

# VidiGen Generators
from api.generators.prompt.ollama_expander import OllamaPromptExpander
from api.generators.video.comfyui_generator import ComfyUIVideoGenerator
from api.generators.caption.whisper_generator import WhisperCaptionGenerator

class GeneratorFactory:
    @staticmethod
    def get_prompt_expander() -> PromptExpansionGenerator:
        """Get prompt expansion generator (currently only Ollama)"""
        return OllamaPromptExpander()

    @staticmethod
    def get_video_generator() -> VideoGenerator:
        """Get video generator (currently only ComfyUI/LTX-2)"""
        return ComfyUIVideoGenerator()

    @staticmethod
    def get_caption_generator() -> CaptionGenerator:
        """Get caption generator (currently only Whisper)"""
        return WhisperCaptionGenerator()
