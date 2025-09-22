# -*- coding: utf-8 -*-
"""
Punto de entrada principal para la API de GRUPO_GAD.
"""
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.responses import Response

from config.settings import settings
from src.api.routers import api_router
from src.api.routers import dashboard as dashboard_router
from src.api.routers import websockets as websockets_router
from src.api.middleware.websockets import websocket_event_emitter
from src.core.database import async_engine, init_db
from src.core.logging import setup_logging
from src.core.websocket_integration import (
    initialize_websocket_integrator,
    start_websocket_integration,
    stop_websocket_integration
)

# --- Configuración de Logging Mejorado ---
api_logger = setup_logging(
    service_name="api",
    log_level=settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO",
    enable_console=True,
    enable_file=True,
    enable_json=getattr(settings, 'ENVIRONMENT', 'development') == 'production'
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Gestiona los eventos de arranque y parada de la aplicación.
    """
    # Startup
    api_logger.info("Iniciando aplicación y conexión a la base de datos...")
    init_db(str(settings.DATABASE_URL))
    app.state.start_time = time.time()
    api_logger.info("Conexión a la base de datos establecida.")
    
    # Iniciar sistema de WebSockets
    api_logger.info("Iniciando sistema de WebSockets...")
    await websocket_event_emitter.start()
    
    # Inicializar integrador de WebSocket con modelos
    api_logger.info("Inicializando integración WebSocket-Modelos...")
    initialize_websocket_integrator(websocket_event_emitter)
    await start_websocket_integration()
    
    api_logger.info("Sistema de WebSockets iniciado correctamente.")
    
    yield
    
    # Shutdown
    api_logger.info("Deteniendo integración WebSocket-Modelos...")
    await stop_websocket_integration()
    
    api_logger.info("Deteniendo sistema de WebSockets...")
    await websocket_event_emitter.stop()
    api_logger.info("Sistema de WebSockets detenido.")
    
    api_logger.info("Cerrando conexión a la base de datos...")
    if async_engine:
        await async_engine.dispose()
    api_logger.info("Conexión a la base de datos cerrada.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Reconocer X-Forwarded-* cuando corremos detrás de un reverse proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])  # type: ignore

# --- Middleware de limitación de tamaño de petición (mitigación DoS multipart) ---
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MiB


@app.middleware("http")
async def max_body_size_middleware(
    request: Request, 
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
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
    response = await call_next(request)
    # Ocultar cabecera 'server' por seguridad básica
    if "server" in response.headers:
        del response.headers["server"]
    return response

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
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    api_logger.error(
        f"Validation error for request {request.url}",
        validation_errors=exc.errors(),
        method=request.method,
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        },
    )


# --- Middleware de Logging Mejorado ---


@app.middleware("http")
async def log_requests(
    request: Request, 
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = time.time()
    
    # Log de request con información estructurada
    api_logger.info(
        f"Request: {request.method} {request.url}",
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        response = await call_next(request)
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        api_logger.error(
            f"Request failed: {request.method} {request.url}",
            error=exc,
            method=request.method,
            url=str(request.url),
            duration_ms=round(process_time, 2)
        )
        raise
    
    process_time = (time.time() - start_time) * 1000
    api_logger.info(
        f"Response: {response.status_code} | Time: {process_time:.2f}ms",
        status_code=response.status_code,
        duration_ms=round(process_time, 2),
        method=request.method,
        path=request.url.path
    )
    return response

# --- Endpoint de métricas básicas ---


@app.get("/metrics", response_class=PlainTextResponse, tags=["monitoring"])
async def metrics() -> PlainTextResponse:
    # Fallback si el lifespan aún no setea start_time (p.ej. pruebas con ASGITransport)
    if not hasattr(app.state, "start_time"):
        app.state.start_time = time.time()
    uptime = int(time.time() - app.state.start_time)
    return PlainTextResponse(
        f"# HELP app_uptime_seconds Uptime in seconds\napp_uptime_seconds {uptime}\n"
    )



# Montar archivos estáticos para el dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Incluir routers
app.include_router(dashboard_router.router)
app.include_router(websockets_router.router)
app.include_router(api_router, prefix=settings.API_V1_STR)

api_logger.info(
    "API iniciada y lista para recibir peticiones.",
    project_name=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    environment=getattr(settings, 'ENVIRONMENT', 'development')
)