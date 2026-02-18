from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"

    # ComfyUI Configuration
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_output_dir: str = "O:/dev/ComfyUI/output"

    # Whisper Configuration
    whisper_model_size: str = "medium"  # base, small, medium, large
    whisper_min_confidence: float = 0.4  # Drop words below this probability (0.0-1.0)
    whisper_no_speech_threshold: float = 0.3  # Segments with no_speech_prob above this are silenced

    # VidiGen Video Settings
    # Frame count must be divisible by 8 + 1 (e.g. 97, 121, 161, 241, 481)
    # Width/height must be divisible by 32 + 1 (e.g. 321, 641, 961) — set in workflow JSON
    vidigen_frame_count: int = 121  # 121 frames ~= 5s at 24fps

    # Resource management
    single_gpu_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
