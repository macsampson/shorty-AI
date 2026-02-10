from api.config import settings
from api.generators.base import ScriptGenerator, ImageGenerator, VoiceGenerator

# Script Generators
from api.generators.script.openai_generator import OpenAIScriptGenerator
from api.generators.script.ollama_generator import OllamaScriptGenerator

# Image Generators
from api.generators.image.openai_generator import OpenAIImageGenerator
from api.generators.image.flux_generator import FluxImageGenerator

# Voice Generators
from api.generators.voice.elevenlabs_generator import ElevenLabsVoiceGenerator
from api.generators.voice.local_generator import LocalVoiceGenerator

class GeneratorFactory:
    @staticmethod
    def get_script_generator() -> ScriptGenerator:
        provider = settings.ai_provider_script.lower()
        if provider == "openai":
            return OpenAIScriptGenerator()
        elif provider == "ollama":
            return OllamaScriptGenerator()
        else:
            raise ValueError(f"Unknown script provider: {provider}")

    @staticmethod
    def get_image_generator() -> ImageGenerator:
        provider = settings.ai_provider_image.lower()
        if provider == "openai":
            return OpenAIImageGenerator()
        elif provider == "flux":
            return FluxImageGenerator()
        else:
            raise ValueError(f"Unknown image provider: {provider}")

    @staticmethod
    def get_voice_generator() -> VoiceGenerator:
        provider = settings.ai_provider_voice.lower()
        if provider == "elevenlabs":
            return ElevenLabsVoiceGenerator()
        elif provider == "local_tts":
            return LocalVoiceGenerator()
        else:
            raise ValueError(f"Unknown voice provider: {provider}")
