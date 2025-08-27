from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    elevenlabs_api_key: str
    
    # Model configurations
    openai_model: str = "gpt-4o-mini"  # Default OpenAI model
    
    # Legacy settings (kept for compatibility)
    baseten_api_key: str = ""
    ollama_model: str = "llama3"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()