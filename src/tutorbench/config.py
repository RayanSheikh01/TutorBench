# src/tutorbench/config.py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ollama_host: str = "http://localhost:11434"
    ollama_gen_model: str = "qwen2.5:7b-instruct"
    ollama_grade_model: str = "qwen2.5:7b-instruct"


@lru_cache
def get_settings() -> Settings:
    """Cached app settings, loaded from env / .env."""
    return Settings()