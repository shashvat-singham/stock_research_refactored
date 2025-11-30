"""
Configuration settings for the Stock Research Chatbot.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    gemini_api_key: Optional[str] = None
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "default_secret_key"
    
    # Agent Configuration
    max_iterations: int = 3
    request_timeout: int = 30
    rate_limit_requests_per_minute: int = 60
    
    # Vector Database Configuration
    chroma_persist_directory: str = "./data/chroma_db"
    
    # API Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', case_sensitive=False, extra='ignore')



# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings."""
    return settings
