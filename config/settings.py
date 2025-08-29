# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema GRUPO_GAD.
Utiliza Pydantic Settings para validación automática de variables de entorno.
"""

from typing import List, Optional
from pydantic import Field, PostgresDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración principal del sistema.
    Todas las variables pueden ser sobreescritas con variables de entorno.
    """

    # === PROYECTO ===
    PROJECT_NAME: str = Field("GRUPO_GAD")
    PROJECT_VERSION: str = Field("1.0.0")
    PROJECT_DESCRIPTION: str = Field(
        "Sistema de Gestión de Tareas para Personal Policial"
    )
    DEBUG: bool = Field(False)

    # === API ===
    API_V1_STR: str = Field("/api/v1")
    SECRET_KEY: str = Field(...)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)

    # === BASE DE DATOS ===
    POSTGRES_SERVER: str = Field("localhost")
    POSTGRES_USER: str = Field("gad_user")
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field("gad_db")
    POSTGRES_PORT: int = Field(5432)
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Construye la URL de conexión a la base de datos."""
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{info.data.get('POSTGRES_USER')}:"
            f"{info.data.get('POSTGRES_PASSWORD')}@"
            f"{info.data.get('POSTGRES_SERVER')}:"
            f"{info.data.get('POSTGRES_PORT')}/"
            f"{info.data.get('POSTGRES_DB') or ''}"
        )

    # === REDIS (CACHÉ) ===
    REDIS_HOST: str = Field("localhost")
    REDIS_PORT: int = Field(6379)
    REDIS_DB: int = Field(0)
    REDIS_PASSWORD: Optional[str] = Field(None)

    # === TELEGRAM BOT ===
    TELEGRAM_BOT_TOKEN: str = Field(...)
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None)
    TELEGRAM_WEBHOOK_PATH: str = Field("/webhook/telegram")
    TELEGRAM_WEBHOOK_PORT: int = Field(8000)

    # === SEGURIDAD ===
    USERS_OPEN_REGISTRATION: bool = Field(False)
    ALLOWED_HOSTS: List[str] = Field(["*"])

    # === LOGGING ===
    LOG_LEVEL: str = Field("INFO")
    LOG_FILE: Optional[str] = Field(None)

    # === MONITOREO ===
    PROMETHEUS_ENABLED: bool = Field(True)

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8"
    )


# Instancia única de configuración
settings = Settings()
