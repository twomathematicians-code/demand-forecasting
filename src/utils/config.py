from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    environment: str = "development"
    log_level: str = "INFO"
    mlflow_tracking_uri: str = "http://localhost:5000"

@lru_cache
def get_settings() -> Settings:
    return Settings()
