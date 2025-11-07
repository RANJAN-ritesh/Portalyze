"""
Configuration management for Portalyze 2.0
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AI Providers
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Server
    api_base_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    allow_origin_regex: Optional[str] = None
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./cache.db"

    # Performance & Limits
    max_concurrent_analyses: int = 5
    analysis_timeout_seconds: int = 90
    page_load_timeout: int = 30
    ai_request_timeout: int = 20

    # Cache
    cache_ttl_days: int = 7
    enable_caching: bool = True

    # Rate Limiting
    rate_limit_per_hour: int = 10
    rate_limit_per_day: int = 100

    # Features
    enable_face_detection: bool = True
    enable_ai_analysis: bool = True
    enable_screenshot_capture: bool = False
    enable_shareable_links: bool = True

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/portalyze.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def origins_list(self) -> List[str]:
        """Parse allowed origins into list"""
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins

    @property
    def cors_origin_regex(self) -> Optional[str]:
        """Return regex for allowed origins when configured"""
        if self.allow_origin_regex:
            return self.allow_origin_regex
        if not self.is_production:
            return r"http://(localhost|127\.0\.0\.1):\d+"
        return None

    @property
    def is_production(self) -> bool:
        """Determine if app is running in production mode"""
        return self.environment.lower() == "production"

    def validate_required_keys(self) -> None:
        """Validate that at least one AI provider key is available"""
        if not self.gemini_api_key and not self.groq_api_key:
            raise ValueError(
                "At least one AI provider API key is required. "
                "Please set GEMINI_API_KEY or GROQ_API_KEY in your .env file."
            )

    def get_available_ai_providers(self) -> List[str]:
        """Return list of available AI providers"""
        providers = []
        if self.gemini_api_key:
            providers.append("gemini")
        if self.groq_api_key:
            providers.append("groq")
        return providers


# Create global settings instance
settings = Settings()

# Ensure logs directory exists
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
