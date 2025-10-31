from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-not-found]
from typing import List
from functools import lru_cache

class Settings(BaseSettings):  # type: ignore[misc]
    # Defaults seguros para dev/test (NO usar en producción)
    SECRET_KEY: str = "dev-insecure-secret-key-change-me-please-0123456789"
    JWT_SECRET_KEY: str = "dev-insecure-jwt-secret-key-change-me-please-0123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GRUPO_GAD"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
