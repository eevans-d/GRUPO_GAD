# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema GRUPO_GAD.
Utiliza Pydantic Settings para validación automática de variables de entorno.
"""

from typing import List, Optional
from pydantic import AnyHttpUrl, Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración principal del sistema.
    Todas las variables pueden ser sobreescritas con variables de entorno.
    """
    
    # === PROYECTO ===
    PROJECT_NAME: str = Field("GRUPO_GAD", env="PROJECT_NAME")
    PROJECT_VERSION: str = Field("1.0.0", env="PROJECT_VERSION")
    PROJECT_DESCRIPTION: str = Field(
        "Sistema de Gestión de Tareas para Personal Policial",
        env="PROJECT_DESCRIPTION"
    )
    DEBUG: bool = Field(False, env="DEBUG")
    
    # === API ===
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # === BASE DE DATOS ===
    POSTGRES_SERVER: str = Field("localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field("gad_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("gad_db", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Construye la URL de conexión a la base de datos."""
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB') or ''}"
        )
    
    # === REDIS (CACHÉ) ===
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # === TELEGRAM BOT ===
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    TELEGRAM_WEBHOOK_PATH: str = Field("/webhook/telegram", env="TELEGRAM_WEBHOOK_PATH")
    TELEGRAM_WEBHOOK_PORT: int = Field(8000, env="TELEGRAM_WEBHOOK_PORT")
    
    # === SEGURIDAD ===
    USERS_OPEN_REGISTRATION: bool = Field(False, env="USERS_OPEN_REGISTRATION")
    ALLOWED_HOSTS: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    
    # === LOGGING ===
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(None, env="LOG_FILE")
    
    # === MONITOREO ===
    PROMETHEUS_ENABLED: bool = Field(True, env="PROMETHEUS_ENABLED")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instancia única de configuración
settings = Settings()
