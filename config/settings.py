# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema GRUPO_GAD.
Utiliza Pydantic Settings para validación automática de variables de entorno.
"""

from typing import List, Optional
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
    DB_URL: str

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

    # === SEGURIDAD ===
    USERS_OPEN_REGISTRATION: bool = Field(False)
    ALLOWED_HOSTS: List[str] = Field(["*"])

    # === LOGGING ===
    LOG_LEVEL: str = Field("INFO")
    LOG_FILE: Optional[str] = Field(None)

    # === MONITOREO ===
    PROMETHEUS_ENABLED: bool = Field(True)

    model_config = SettingsConfigDict(
        case_sensitive=False, env_file=".env", env_file_encoding="utf-8"
    )


# Instancia única de configuración
settings = Settings()