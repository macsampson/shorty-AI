from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    elevenlabs_api_key: str
    
    # Model configurations
    openai_model: str = "gpt-4o-mini"
    
    # Provider Selection (openai, ollama, elevenlabs, local_tts, flux, etc.)
    ai_provider_script: str = "openai"
    ai_provider_image: str = "openai"
    ai_provider_voice: str = "elevenlabs"

    # Local/Alternative Provider Settings
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"
    
    flux_api_url: str = "http://flux:8000"
    
    local_tts_url: str = "http://tts:5002"
    
    # Resource management
    single_gpu_mode: bool = False

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()