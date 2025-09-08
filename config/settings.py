# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema GRUPO_GAD.
Utiliza Pydantic Settings para validación automática de variables de entorno.
"""

import os
import pathlib
from typing import List, Optional, ClassVar
from pydantic import Field
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
    # La SECRET_KEY debe ser proporcionada a través de una variable de entorno.
    # Es crucial para la seguridad de la aplicación (ej. JWT).
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)

    # === BASE DE DATOS ===
    # Valor por defecto 'db' para evitar fallo si la variable no está
    # presente en entornos docker
    POSTGRES_SERVER: str = Field("db")
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = Field(5432)
    DATABASE_URL: Optional[str] = None

    from pydantic import field_validator

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        # Priority: explicit DATABASE_URL -> legacy DB_URL env var -> assemble from parts
        if isinstance(v, str) and v:
            return v

        # Allow legacy DB_URL environment variable as a fallback for compatibility
        legacy = os.getenv("DB_URL")
        if isinstance(legacy, str) and legacy:
            return legacy

        # Fallback: build from individual POSTGRES_* components
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )

    # === REDIS (CACHÉ) ===
    REDIS_HOST: str = Field("redis")
    REDIS_PORT: int = Field(6379)
    REDIS_DB: int = Field(0)
    REDIS_PASSWORD: Optional[str] = Field(None)

    # === TELEGRAM BOT ===
    TELEGRAM_TOKEN: str
    ADMIN_CHAT_ID: str
    WHITELIST_IDS: List[int]
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None)
    TELEGRAM_WEBHOOK_PATH: str = Field("/webhook/telegram")
    TELEGRAM_WEBHOOK_PORT: int = Field(8000)

    # === TIMEZONE ===
    TZ: str = Field("UTC")

    # Environment metadata (may be provided by deploy systems)
    ENVIRONMENT: Optional[str] = Field(None)

    # === SEGURIDAD ===
    USERS_OPEN_REGISTRATION: bool = Field(False)
    ALLOWED_HOSTS: List[str] = Field(["*"])

    # === LOGGING ===
    LOG_LEVEL: str = Field("INFO")
    LOG_FILE: Optional[str] = Field(None)

    # === MONITOREO ===
    PROMETHEUS_ENABLED: bool = Field(True)

    # Preferir .env.production si existe; caer a .env como fallback
    env_files: ClassVar[List[str]] = []
    if pathlib.Path('.env.production').exists():
        env_files.append('.env.production')
    env_files.append('.env')

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=env_files,
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instancia única de configuración
settings = Settings()