from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    baseten_api_key: str
    ollama_model: str = "llama3"  # Default value

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()