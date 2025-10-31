# -*- coding: utf-8 -*-
"""
Middleware avanzado de logging para la API de GRUPO_GAD.

Proporciona logging detallado de requests, responses, errores y métricas
de performance con información estructurada para debugging y monitoreo.
"""

import time
import uuid
from typing import Callable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger

# Logger específico para middleware
middleware_logger = get_logger("api.middleware")


class SecurityLoggingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """
    Middleware para logging de seguridad y compliance.
    
    Registra:
    - Intentos de acceso no autorizados
    - IPs sospechosas
    - Patrones de requests inusuales
    - Headers de seguridad
    """

    def __init__(self, app, sensitive_paths: list[str] | None = None):
        super().__init__(app)
        self.sensitive_paths = sensitive_paths or [
            "/api/v1/auth/login",
            "/api/v1/users",
            "/dashboard",
            "/admin"
        ]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Generar ID único para la request
        request_id = str(uuid.uuid4())[:8]
        
        # Información del cliente
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        referer = request.headers.get("referer", "direct")
        
        # Detectar rutas sensibles
        is_sensitive = any(path in str(request.url.path) for path in self.sensitive_paths)
        
        # Log inicial de request
        middleware_logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent,
            referer=referer,
            is_sensitive=is_sensitive,
            headers_count=len(request.headers)
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log de response exitosa
            middleware_logger.info(
                f"Response {request_id}: {response.status_code}",
                request_id=request_id,
                status_code=response.status_code,
                duration_seconds=round(process_time, 3),
                path=request.url.path,
                success=200 <= response.status_code < 400
            )
            
            # Log especial para requests sensibles
            if is_sensitive:
                middleware_logger.warning(
                    f"Sensitive path accessed: {request.url.path}",
                    request_id=request_id,
                    client_ip=client_ip,
                    status_code=response.status_code,
                    path=request.url.path,
                    user_agent=user_agent[:100]  # Truncar user agent
                )
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            # Log de error detallado
            middleware_logger.error(
                f"Request {request_id} failed",
                error=exc,
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                duration_seconds=round(process_time, 3),
                user_agent=user_agent[:100]
            )
            
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """
    Middleware para logging de performance y métricas.
    
    Registra:
    - Tiempos de respuesta
    - Requests lentas
    - Memoria y CPU (opcional)
    - Patrones de uso
    """

    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # segundos

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log requests lentas
            if process_time > self.slow_request_threshold:
                middleware_logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    method=request.method,
                    path=request.url.path,
                    duration_seconds=round(process_time, 3),
                    threshold_seconds=self.slow_request_threshold,
                    client_ip=request.client.host if request.client else "unknown"
                )
            
            # Métricas generales cada cierto número de requests
            if hasattr(request.app.state, 'request_count'):
                request.app.state.request_count += 1
            else:
                request.app.state.request_count = 1
            
            # Log métricas cada 100 requests
            if request.app.state.request_count % 100 == 0:
                middleware_logger.info(
                    f"Performance metrics - {request.app.state.request_count} requests processed",
                    total_requests=request.app.state.request_count,
                    current_duration=round(process_time, 3),
                    path=request.url.path
                )
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            middleware_logger.error(
                "Performance middleware error",
                error=exc,
                method=request.method,
                path=request.url.path,
                duration_seconds=round(process_time, 3)
            )
            
            raise


class DatabaseLoggingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """
    Middleware para logging de operaciones de base de datos.
    
    Útil para detectar:
    - N+1 queries
    - Queries lentas
    - Errores de conexión
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Marcar inicio de request para tracking de DB
        if hasattr(request.app.state, 'db_queries'):
            request.app.state.db_queries = []
        
        try:
            response = await call_next(request)
            
            # Log si hay muchas queries (potencial N+1)
            if hasattr(request.app.state, 'db_queries'):
                query_count = len(request.app.state.db_queries)
                if query_count > 10:  # Threshold configurable
                    middleware_logger.warning(
                        "High database query count detected",
                        path=request.url.path,
                        method=request.method,
                        query_count=query_count,
                        queries=request.app.state.db_queries[:5]  # Solo primeras 5
                    )
            
            return response
            
        except Exception as exc:
            middleware_logger.error(
                "Database middleware error",
                error=exc,
                path=request.url.path,
                method=request.method
            )
            raise