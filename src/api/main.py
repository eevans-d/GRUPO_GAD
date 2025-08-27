# -*- coding: utf-8 -*-
"""
Punto de entrada principal para la API de GRUPO_GAD.
"""

from fastapi import FastAPI

from src.api.routers import api_router
from config.settings import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_STR)