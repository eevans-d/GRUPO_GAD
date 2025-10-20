# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema GRUPO_GAD.
Utiliza Pydantic Settings para validación automática de variables de entorno.
"""

import os
from typing import Any, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración principal del sistema.
    Todas las variables pueden ser sobreescritas con variables de entorno.
    """

    # === PROYECTO ===
    PROJECT_NAME: str = "GRUPO_GAD"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Sistema de Gestión de Tareas para Personal Policial"
    DEBUG: bool = False

    # === API ===
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === BASE DE DATOS ===
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    
    # Configuración avanzada de pool de conexiones para producción
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Reciclar conexiones cada hora
    
    # La URL de la base de datos se construye dinámicamente si no se provee.
    # Prioridad: 1. DATABASE_URL, 2. DB_URL (legado), 3. Componentes POSTGRES_*.
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str | None:
        # Keep behaviour for direct DATABASE_URL or legacy DB_URL env
        if isinstance(v, str) and v:
            return v

        legacy_db_url = os.getenv("DB_URL")
        if legacy_db_url:
            return legacy_db_url

        # Fall back to components
        data = getattr(info, "data", {})
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB")

        if all([user, password, server, port, db]):
            return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

        # Return None if we can't assemble; caller may handle the absence.
        return None

    def assemble_db_url(self) -> Optional[str]:
        """Return a usable DB URL compatible with asyncpg (Railway-compatible).

        This helper is explicit and safe to call at runtime without relying on
        a global settings instantiation at import time.
        
        Transforms postgresql:// to postgresql+asyncpg:// for Railway compatibility.
        """
        # Prefer explicit DATABASE_URL set during initialization
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Railway inyecta postgresql://, transformar para asyncpg
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        # Fallback to legacy env var
        legacy_db_url = os.getenv("DB_URL")
        if legacy_db_url:
            # Aplicar misma transformación
            if legacy_db_url.startswith("postgresql://") and "+asyncpg" not in legacy_db_url:
                legacy_db_url = legacy_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return legacy_db_url

        # Use components if available (be tolerant if attributes are missing when constructed without validation)
        user = getattr(self, "POSTGRES_USER", None)
        password = getattr(self, "POSTGRES_PASSWORD", None)
        db = getattr(self, "POSTGRES_DB", None)
        server = getattr(self, "POSTGRES_SERVER", "db")
        port = getattr(self, "POSTGRES_PORT", 5432)
        if user and password and db:
            return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

        return None

    # === REDIS (CACHÉ) ===
    REDIS_HOST: Optional[str] = None  # None = disabled; set to hostname to enable
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # === TELEGRAM BOT ===
    TELEGRAM_TOKEN: str
    ADMIN_CHAT_ID: str
    WHITELIST_IDS: List[int]
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_PATH: str = "/webhook/telegram"
    TELEGRAM_WEBHOOK_PORT: int = 8000

    # === TIMEZONE ===
    TZ: str = "UTC"

    # Environment metadata
    ENVIRONMENT: Optional[str] = None

    # === SEGURIDAD ===
    USERS_OPEN_REGISTRATION: bool = False
    ALLOWED_HOSTS: List[str] = ["*"]
    # CORS y proxies (producción debe fijar orígenes explícitos)
    # Notas: mantener como strings para permitir carga desde .env con formato "a,b,c"
    CORS_ALLOWED_ORIGINS: str = ""
    CORS_ALLOW_CREDENTIALS: bool = False
    TRUSTED_PROXY_HOSTS: str = "localhost,127.0.0.1"

    # === LOGGING ===
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # === MONITOREO ===
    PROMETHEUS_ENABLED: bool = True

    model_config = SettingsConfigDict(
            case_sensitive=False,
            env_file=(".env.production", ".env"),
            env_file_encoding="utf-8",
            extra="ignore",
        )

    # Helpers derivados
    @property
    def cors_origins_list(self) -> List[str]:
        raw = getattr(self, "CORS_ALLOWED_ORIGINS", "") or ""
        return [s.strip() for s in raw.split(",") if s.strip()]

    @property
    def trusted_proxy_hosts_list(self) -> List[str]:
        raw = getattr(self, "TRUSTED_PROXY_HOSTS", "") or ""
        return [s.strip() for s in raw.split(",") if s.strip()] or ["localhost", "127.0.0.1"]

def get_settings() -> "Settings":
    """Return a fresh Settings instance.

    Use this helper to instantiate settings lazily (for example inside scripts
    or migration runners). Avoid importing and using a global `settings` at
    module import time in order to prevent ValidationError when env vars are missing.
    """
    return Settings(
        SECRET_KEY=os.getenv("SECRET_KEY", ""),
        POSTGRES_USER=os.getenv("POSTGRES_USER", ""),
        POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", ""),
        POSTGRES_DB=os.getenv("POSTGRES_DB", ""),
        TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN", ""),
        ADMIN_CHAT_ID=os.getenv("ADMIN_CHAT_ID", ""),
        WHITELIST_IDS=[
            int(s.strip())
            for s in os.getenv("WHITELIST_IDS", "").replace("[", "").replace("]", "").split(",")
            if s.strip().isdigit()
        ],
        # Listas separadas por coma para CORS/Proxies (p.ej. "https://app.example.com,https://admin.example.com")
        CORS_ALLOWED_ORIGINS=os.getenv("CORS_ALLOWED_ORIGINS", ""),
        CORS_ALLOW_CREDENTIALS=os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() in {"1", "true", "yes"},
        TRUSTED_PROXY_HOSTS=os.getenv("TRUSTED_PROXY_HOSTS", "localhost,127.0.0.1"),
    )


# Backwards-compatible module-level `settings` object.
# This is a lazy proxy that will attempt to instantiate a fully-validated
# Settings on first attribute access. If instantiation fails (missing envs),
# it falls back to Settings.construct() to provide a non-validating object
# so other modules that import `settings` at import time do not crash.
class _LazySettingsProxy:
    _inst = None

    def _build(self) -> Settings:
        if self._inst is None:
            try:
                self._inst = Settings(
                    SECRET_KEY=os.getenv("SECRET_KEY", ""),
                    POSTGRES_USER=os.getenv("POSTGRES_USER", ""),
                    POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", ""),
                    POSTGRES_DB=os.getenv("POSTGRES_DB", ""),
                    TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN", ""),
                    ADMIN_CHAT_ID=os.getenv("ADMIN_CHAT_ID", ""),
                    WHITELIST_IDS=[
                        int(s.strip())
                        for s in os.getenv("WHITELIST_IDS", "").replace("[", "").replace("]", "").split(",")
                        if s.strip().isdigit()
                    ],
                    CORS_ALLOWED_ORIGINS=os.getenv("CORS_ALLOWED_ORIGINS", ""),
                    CORS_ALLOW_CREDENTIALS=os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() in {"1", "true", "yes"},
                    TRUSTED_PROXY_HOSTS=os.getenv("TRUSTED_PROXY_HOSTS", "localhost,127.0.0.1"),
                )
            except Exception:
                # Last-resort: construct without validation to avoid import errors
                # Provide minimal defaults so attribute access doesn't crash in tests/tools
                # mypy: construir con kwargs desde un dict variable para evitar error de tipo
                # Crear instancia mínima sin cargar de .env para evitar errores en import-time
                # y sin requerir kwargs tipeados (mypy friendly)
                self._inst = Settings.model_validate({}, from_attributes=False)
        return self._inst

    def __getattr__(self, name: str) -> Any:
        return getattr(self._build(), name)


settings = _LazySettingsProxy()
