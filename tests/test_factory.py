import pytest
from unittest.mock import patch


class TestGeneratorFactory:
    def test_get_prompt_expander_returns_ollama(self):
        from api.generators.factory import GeneratorFactory
        from api.generators.prompt.ollama_expander import OllamaPromptExpander
        from api.generators.base import PromptExpansionGenerator

        expander = GeneratorFactory.get_prompt_expander()
        assert isinstance(expander, OllamaPromptExpander)
        assert isinstance(expander, PromptExpansionGenerator)

    def test_get_video_generator_returns_comfyui(self):
        from api.generators.factory import GeneratorFactory
        from api.generators.video.comfyui_generator import ComfyUIVideoGenerator
        from api.generators.base import VideoGenerator

        generator = GeneratorFactory.get_video_generator()
        assert isinstance(generator, ComfyUIVideoGenerator)
        assert isinstance(generator, VideoGenerator)

    def test_get_caption_generator_returns_whisper(self):
        from api.generators.factory import GeneratorFactory
        from api.generators.caption.whisper_generator import WhisperCaptionGenerator
        from api.generators.base import CaptionGenerator

        generator = GeneratorFactory.get_caption_generator()
        assert isinstance(generator, WhisperCaptionGenerator)
        assert isinstance(generator, CaptionGenerator)
