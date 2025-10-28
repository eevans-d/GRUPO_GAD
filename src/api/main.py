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

from config.settings import get_settings, settings
from src.api.routers import api_router
from src.api.routers import dashboard as dashboard_router
from src.api.routers import websockets as websockets_router
from src.api.middleware.websockets import websocket_event_emitter
from src.api.middleware.government_rate_limiting import setup_government_rate_limiting
from src.core import database as db
from src.core.logging import setup_logging
from src.core.websocket_integration import (
    initialize_websocket_integrator,
    start_websocket_integration,
    stop_websocket_integration
)
from src.core.websockets import websocket_manager
from src.core.ws_pubsub import RedisWebSocketPubSub  # opcional si hay Redis
from src.core.cache import init_cache_service, shutdown_cache_service

# Importar métricas Prometheus si están disponibles
try:
    from src.observability.metrics import initialize_metrics
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

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
    # Obtener una instancia validada de Settings para evitar atributos faltantes del proxy
    _settings = get_settings()
    db_url = _settings.assemble_db_url() if hasattr(_settings, "assemble_db_url") else None
    if not db_url:
        # Fallback a variable de entorno directa si existe
        import os
        db_url = os.getenv("DATABASE_URL")
        # Normalizar a driver async si viene en formato postgres:// o postgresql://
        if db_url and "+asyncpg" not in db_url:
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if not db_url:
        # En desarrollo/testing, permitir iniciar sin DB si ALLOW_NO_DB=1
        import os
        if os.getenv("ALLOW_NO_DB") != "1":
            api_logger.error("DATABASE_URL no configurada y no se pudo ensamblar desde POSTGRES_*.")
            raise RuntimeError("DATABASE_URL no configurada")
        else:
            api_logger.warning("⚠️  Iniciando SIN base de datos (ALLOW_NO_DB=1). Solo endpoints sin DB funcionarán.")
            db_url = None
    if db_url:
        db.init_db(db_url)
    app.state.start_time = time.time()
    api_logger.info("Conexión a la base de datos establecida.")
    
    # Iniciar sistema de WebSockets
    api_logger.info("Iniciando sistema de WebSockets...")
    await websocket_event_emitter.start()
    
    # Inicializar integrador de WebSocket con modelos
    api_logger.info("Inicializando integración WebSocket-Modelos...")
    initialize_websocket_integrator(websocket_event_emitter)
    await start_websocket_integration()
    
    # Inicializar métricas Prometheus si están disponibles
    if METRICS_ENABLED:
        api_logger.info("Inicializando métricas Prometheus...")
        initialize_metrics()
        api_logger.info("Métricas Prometheus inicializadas")
    
    api_logger.info("Sistema de WebSockets iniciado correctamente.")

    # Iniciar pub/sub Redis para broadcast cross-worker si está configurado
    app.state.ws_pubsub = None
    try:
        # Preferir REDIS_URL completa si está definida (permite rediss:// con TLS)
        import os
        from urllib.parse import urlparse

        def _sanitize_redis_url(url: str) -> str:
            try:
                parsed = urlparse(url)
                # Construir forma segura sin credenciales
                netloc = parsed.hostname or "localhost"
                if parsed.port:
                    netloc = f"{netloc}:{parsed.port}"
                path = parsed.path or "/0"
                return f"{parsed.scheme}://{netloc}{path}"
            except Exception:
                return "<invalid>"

        # Priorizar URL TLS de Upstash si existe
        raw_upstash_tls = os.getenv("UPSTASH_REDIS_TLS_URL")
        raw_redis_url = os.getenv("REDIS_URL")
        raw_upstash_url = os.getenv("UPSTASH_REDIS_URL")
        redis_url = raw_upstash_tls.strip() if isinstance(raw_upstash_tls, str) else None
        if not redis_url:
            redis_url = raw_redis_url.strip() if isinstance(raw_redis_url, str) else None
        if not redis_url:
            # Compatibilidad con proveedores que exponen UPSTASH_REDIS_URL
            redis_url = raw_upstash_url.strip() if isinstance(raw_upstash_url, str) else None

        # Backwards-compat: construir desde componentes si no se definió REDIS_URL
        if not redis_url:
            redis_host = getattr(_settings, 'REDIS_HOST', None) or None
            redis_port = getattr(_settings, 'REDIS_PORT', 6379)
            redis_db = getattr(_settings, 'REDIS_DB', 0)
            redis_password = getattr(_settings, 'REDIS_PASSWORD', None)
            if redis_host:
                # Permitir forzar TLS con REDIS_SCHEME=rediss si el proveedor lo exige (Upstash)
                scheme = os.getenv("REDIS_SCHEME", "redis").strip() or "redis"
                auth = f":{redis_password}@" if redis_password else ""
                redis_url = f"{scheme}://{auth}{redis_host}:{redis_port}/{redis_db}"

        if redis_url:
            # Ajuste Upstash TLS: si es rediss://*.upstash.io y no usa 6380, cambiar a 6380
            try:
                parsed0 = urlparse(redis_url.strip())
                host = (parsed0.hostname or "").lower()
                if parsed0.scheme == "rediss" and host.endswith(".upstash.io"):
                    tls_port = 6380
                    # Reconstruir URL manteniendo userinfo si existe
                    userinfo = ""
                    if parsed0.username or parsed0.password:
                        u = parsed0.username or ""
                        p = parsed0.password or ""
                        userinfo = f"{u}:{p}@" if (u or p) else ""
                    path = parsed0.path or "/0"
                    if parsed0.port != tls_port:
                        redis_url = f"rediss://{userinfo}{host}:{tls_port}{path}"
                        api_logger.info(
                            "Ajuste Upstash TLS: redirigido a 6380",
                            redis_url_sanitized=_sanitize_redis_url(redis_url)
                        )
            except Exception as ex:
                api_logger.warning("No se pudo aplicar ajuste Upstash TLS", error=str(ex))
            api_logger.info(
                "Detectada configuración Redis",
                redis_url_sanitized=_sanitize_redis_url(redis_url),
                source=(
                    "UPSTASH_REDIS_TLS_URL" if raw_upstash_tls else
                    ("REDIS_URL/UPSTASH_REDIS_URL" if (raw_redis_url or raw_upstash_url) else "settings+REDIS_*")
                ),
            )
            pubsub = RedisWebSocketPubSub(redis_url)
            websocket_manager.set_pubsub(pubsub)
            await pubsub.start(websocket_manager)
            app.state.ws_pubsub = pubsub
            api_logger.info("Pub/Sub Redis para WebSockets habilitado", redis=redis_url)
            
            # Inicializar CacheService con la misma URL de Redis
            api_logger.info("Inicializando CacheService...")
            cache_service = init_cache_service(redis_url=redis_url, prefix="gad:")
            await cache_service.connect()
            app.state.cache_service = cache_service
            api_logger.info("CacheService iniciado correctamente")
        else:
            # Log extendido para ayudar a diagnosticar casos donde la variable existe pero está vacía o con espacios
            env_present = "REDIS_URL" in os.environ or "UPSTASH_REDIS_URL" in os.environ
            api_logger.warning(
                "Redis no configurado - CacheService no disponible",
                env_present=env_present,
                REDIS_URL_len=len(os.environ.get("REDIS_URL", "")),
                UPSTASH_REDIS_URL_len=len(os.environ.get("UPSTASH_REDIS_URL", "")),
            )
    except Exception as e:
        api_logger.error(f"No se pudo iniciar pub/sub Redis o CacheService: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    api_logger.info("Deteniendo integración WebSocket-Modelos...")
    await stop_websocket_integration()
    
    api_logger.info("Deteniendo sistema de WebSockets...")
    await websocket_event_emitter.stop()
    api_logger.info("Sistema de WebSockets detenido.")

    # Detener CacheService si está habilitado
    try:
        cache_service = getattr(app.state, 'cache_service', None)
        if cache_service is not None:
            await shutdown_cache_service()
            api_logger.info("CacheService detenido")
    except Exception as e:
        api_logger.error(f"Error deteniendo CacheService: {e}")

    # Detener pub/sub si estaba habilitado
    try:
        _pubsub = getattr(app.state, 'ws_pubsub', None)
        if _pubsub is not None:
            await _pubsub.stop()
    except Exception:
        pass
    
    api_logger.info("Cerrando conexión a la base de datos...")
    if db.async_engine:
        await db.async_engine.dispose()
    api_logger.info("Conexión a la base de datos cerrada.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Reconocer X-Forwarded-* cuando corremos detrás de un reverse proxy
# Confiar solo en proxies explícitos (configurable por entorno)
trusted_hosts = getattr(settings, 'trusted_proxy_hosts_list', ["localhost", "127.0.0.1"])  # type: ignore
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=trusted_hosts)  # type: ignore

# --- Middleware de limitación de tamaño de petición (mitigación DoS multipart) ---
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MiB


@app.middleware("http")
async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy for API
    if request.url.path.startswith("/api/"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"

    # Lightweight CORS headers for simple requests (complementa CORSMiddleware)
    # Nota: CORSMiddleware solo añade cabeceras cuando la petición incluye 'Origin'.
    # Para facilitar UAT y clientes simples, exponemos 'Access-Control-Allow-Origin'
    # cuando la configuración permite '*'.
    try:
        from config.settings import get_settings as _get_settings  # local import to avoid import-time effects
        _s = _get_settings()
        allowed = getattr(_s, 'cors_origins_list', [])
        if (not allowed) and hasattr(_s, 'ALLOWED_HOSTS'):
            allowed = getattr(_s, 'ALLOWED_HOSTS') or []
        # Si '*' está habilitado explícitamente, añade cabecera universal
        if isinstance(allowed, list) and any(o == "*" for o in allowed):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            response.headers.setdefault("Access-Control-Allow-Headers", "*")
    except Exception:
        # Mantener silencioso si no hay settings válidos en tiempo de import
        pass
    
    # Remove server header for security
    if "server" in response.headers:
        del response.headers["server"]
    
    return response


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
    return response

# --- Middleware CORS ---
cors_origins = getattr(settings, 'cors_origins_list', []) or getattr(settings, 'ALLOWED_HOSTS', [])
cors_credentials = bool(getattr(settings, 'CORS_ALLOW_CREDENTIALS', False))
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware de Rate Limiting Gubernamental ---
# Protección DoS para servicios ciudadanos

# Verificar si rate limiting está habilitado (por defecto: sí, salvo config explícita)
rate_limiting_enabled = getattr(settings, 'RATE_LIMITING_ENABLED', True)
if rate_limiting_enabled:
    setup_government_rate_limiting(app)
    api_logger.info("Rate limiting gubernamental activado para protección ciudadana")
else:
    api_logger.warning("Rate limiting deshabilitado - solo usar en desarrollo")

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
    # Sanitizar logs: evitar imprimir query completa y headers sensibles
    redacted_query = "<redacted>" if request.url.query else ""
    api_logger.info(
        f"Request: {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        query=redacted_query,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    
    try:
        response = await call_next(request)
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        api_logger.error(
            f"Request failed: {request.method} {request.url.path}",
            error=exc,
            method=request.method,
            path=request.url.path,
            duration_ms=round(process_time, 2),
        )
        raise
    
    process_time = (time.time() - start_time) * 1000
    
    # Record performance metrics
    from src.core.performance import performance_middleware
    performance_middleware.record_request(
        method=request.method,
        path=request.url.path,
        duration=process_time / 1000,  # Convert to seconds
        status_code=response.status_code
    )
    
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
    
    # Versión simple para compatibilidad hacia atrás
    # Las métricas detalladas están disponibles en /api/v1/metrics/prometheus
    metrics_text = f"# HELP app_uptime_seconds Uptime in seconds\napp_uptime_seconds {uptime}\n"
    
    # Añadir métricas básicas de WebSockets
    stats = websocket_manager.get_stats()
    # Contar conexiones reales, no roles
    connections_count = len(websocket_manager.active_connections)
    metrics_text += "\n# HELP ws_connections_active Active WebSocket connections\n"
    metrics_text += f"ws_connections_active {connections_count}\n"
    
    messages_sent = stats.get('metrics', {}).get('total_messages_sent', 0)
    metrics_text += "\n# HELP ws_messages_sent Total WebSocket messages sent\n"
    metrics_text += f"ws_messages_sent {messages_sent}\n"
    
    broadcasts_total = stats.get('metrics', {}).get('total_broadcasts', 0)
    metrics_text += "\n# HELP ws_broadcasts_total Total WebSocket broadcasts\n"
    metrics_text += f"ws_broadcasts_total {broadcasts_total}\n"
    
    return PlainTextResponse(metrics_text)


# --- Health Check Endpoints para Railway ---

@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check simple para Railway.
    Railway llama a este endpoint cada 30 segundos.
    """
    return {
        "status": "ok",
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "timestamp": time.time()
    }


@app.get("/health/ready", tags=["monitoring"])
async def health_ready():
    """
    Health check detallado para monitoreo externo.
    Verifica estado de todas las dependencias críticas.
    """
    from sqlalchemy import text
    
    checks = {}
    
    # Check Database
    try:
        # Auto-reparación si el motor no fue inicializado por alguna razón
        if db.async_engine is None:
            try:
                _s = get_settings()
                _db_url = _s.assemble_db_url() if hasattr(_s, "assemble_db_url") else None
                if not _db_url:
                    import os as _os
                    _db_url = _os.getenv("DATABASE_URL")
                    if _db_url and "+asyncpg" not in _db_url:
                        if _db_url.startswith("postgresql://"):
                            _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                        elif _db_url.startswith("postgres://"):
                            _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
                if _db_url:
                    db.init_db(_db_url)
                    api_logger.warning("DB engine no estaba inicializado; inicializado durante health_ready")
            except Exception as _e:
                api_logger.error("Auto-inicialización de DB en health_ready falló", error=_e, exc_info=True)

        async with db.async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        api_logger.error("Health check DB failed", error=e)

    # Check Redis (si está habilitado)
    try:
        if hasattr(app.state, 'cache_service') and app.state.cache_service:
            stats = await app.state.cache_service.get_stats()
            checks["redis"] = "ok" if stats.get("connected") else f"error: {stats.get('error', 'unknown')}"
        else:
            checks["redis"] = "not_configured"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        api_logger.error("Health check Redis failed", error=e)
    
    # Check WebSocket Manager
    try:
        checks["websocket_manager"] = "ok"
        checks["active_ws_connections"] = len(websocket_manager.active_connections)
        checks["unique_users"] = len(websocket_manager.user_connections)
    except Exception as e:
        checks["websocket_manager"] = f"error: {str(e)}"
    
    # Check WebSocket Pub/Sub
    try:
        if hasattr(app.state, 'ws_pubsub') and app.state.ws_pubsub:
            checks["ws_pubsub"] = "ok"
        else:
            checks["ws_pubsub"] = "not_configured"
    except Exception as e:
        checks["ws_pubsub"] = f"error: {str(e)}"
    
    # Determinar estado general
    all_ok = all(
        v in ["ok", "not_configured"] or isinstance(v, int) 
        for v in checks.values()
    )
    
    status_code = 200 if all_ok else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ok else "degraded",
            "checks": checks,
            "timestamp": time.time()
        }
    )


# Montar archivos estáticos para el dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Incluir routers
app.include_router(dashboard_router.router)
app.include_router(websockets_router.router)

# Telegram-specific routers
from src.api.routers import telegram_auth, telegram_tasks, usuarios
app.include_router(telegram_auth.router, prefix=settings.API_V1_STR)
app.include_router(telegram_tasks.router, prefix=settings.API_V1_STR)
app.include_router(usuarios.router, prefix=settings.API_V1_STR)

app.include_router(api_router, prefix=settings.API_V1_STR)

api_logger.info(
    "API iniciada y lista para recibir peticiones.",
    project_name=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    environment=getattr(settings, 'ENVIRONMENT', 'development')
)