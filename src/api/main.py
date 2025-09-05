# -*- coding: utf-8 -*-
"""
Punto de entrada principal para la API de GRUPO_GAD.
"""
import sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.api.routers import api_router
from src.api.routers import dashboard as dashboard_router
from config.settings import settings

# --- Configuración de Loguru ---
# Eliminar el handler por defecto para evitar duplicados en la consola
logger.remove()
# Añadir un handler para la consola con un formato simple
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)
# Añadir un handler para escribir logs a un archivo, con rotación y retención
logger.add(
    "logs/api.log",
    rotation="10 MB",  # Rotar cuando el archivo alcance 10 MB
    retention="7 days",  # Mantener logs por 7 días
    enqueue=True,  # Hacerlo seguro para multiprocesamiento
    backtrace=True,
    diagnose=True,
    format="{time} {level} {message}"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# --- Middleware de Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Montar archivos estáticos para el dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Incluir routers
app.include_router(dashboard_router.router)
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("API iniciada y lista para recibir peticiones.")