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
from starlette.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

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

# --- Middleware de limitación de tamaño de petición (mitigación DoS multipart) ---
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MiB


@app.middleware("http")
async def max_body_size_middleware(request: Request, call_next):
    # Comprobar Content-Length si está presente
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_REQUEST_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
        except ValueError:
            # Si no es un número válido, continuar y dejar que downstream valide
            pass

    # Para transferencias chunked u otras sin Content-Length, no se puede
    # verificar sin consumir el body; confiamos en proxies frontales y límites
    # adicionales en producción para esa protección.
    return await call_next(request)

# --- Middleware CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,  # Usar la configuración de ALLOWED_HOSTS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Manejo de Errores Personalizado ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        },
    )


# --- Middleware de Logging Mejorado ---
import time
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Error: {exc}")
        raise
    process_time = (time.time() - start_time) * 1000
    logger.info(f"Response: {response.status_code} | Time: {process_time:.2f}ms")
    return response

# --- Endpoint de métricas básicas ---
from fastapi.responses import PlainTextResponse
@app.get("/metrics", response_class=PlainTextResponse, tags=["monitoring"])
async def metrics():
    uptime = int(time.time() - app.state.start_time)
    return f"# HELP app_uptime_seconds Uptime in seconds\napp_uptime_seconds {uptime}\n"

# Guardar tiempo de inicio para métricas
app.state.start_time = time.time()

# Montar archivos estáticos para el dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Incluir routers
app.include_router(dashboard_router.router)
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("API iniciada y lista para recibir peticiones.")