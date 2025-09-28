# -*- coding: utf-8 -*-
"""
Utilidades de logging para endpoints de la API.

Decoradores y funciones helper para logging consistente
en todos los endpoints de la aplicación.
"""

import functools
import inspect
import time
from typing import Any, Callable, Dict

from fastapi import Request
from src.core.logging import get_logger

# Logger para endpoints
endpoint_logger = get_logger("api.endpoints")


def log_endpoint_call(operation: str = ""):
    """
    Decorador para logging automático de llamadas a endpoints.
    
    Args:
        operation: Descripción de la operación (ej: "create_user", "login")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            # Extraer request si está disponible
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Info inicial
            endpoint_logger.info(
                f"Endpoint call: {operation or func.__name__}",
                operation=operation or func.__name__,
                function=func.__name__,
                module=func.__module__,
                client_ip=request.client.host if request and request.client else "unknown"
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log exitoso
                endpoint_logger.info(
                    f"Endpoint success: {operation or func.__name__}",
                    operation=operation or func.__name__,
                    duration_seconds=round(duration, 3),
                    success=True
                )
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                # Log error
                endpoint_logger.error(
                    f"Endpoint error: {operation or func.__name__}",
                    error=exc,
                    operation=operation or func.__name__,
                    duration_seconds=round(duration, 3),
                    success=False
                )
                
                raise
        
        # Preservar firma original para compatibilidad con FastAPI (dependencias)
        wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
        return wrapper
    return decorator


def log_database_operation(operation: str, table: str = ""):
    """
    Decorador para logging de operaciones de base de datos.
    
    Args:
        operation: Tipo de operación (CREATE, READ, UPDATE, DELETE)
        table: Nombre de la tabla/entidad
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            db_logger = get_logger("api.database")
            
            db_logger.info(
                f"DB operation start: {operation}",
                operation=operation,
                table=table,
                function=func.__name__
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                db_logger.info(
                    f"DB operation success: {operation}",
                    operation=operation,
                    table=table,
                    duration_seconds=round(duration, 3),
                    success=True
                )
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                db_logger.error(
                    f"DB operation failed: {operation}",
                    error=exc,
                    operation=operation,
                    table=table,
                    duration_seconds=round(duration, 3),
                    success=False
                )
                
                raise
        
        # Preservar firma original
        wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
        return wrapper
    return decorator


def log_authentication_event(event_type: str, user_id: str | None = None, details: Dict[str, Any] | None = None):
    """
    Log eventos de autenticación y seguridad.
    
    Args:
        event_type: Tipo de evento (login, logout, failed_login, etc.)
        user_id: ID del usuario involucrado
        details: Información adicional del evento
    """
    auth_logger = get_logger("api.auth")
    
    auth_logger.info(
        f"Auth event: {event_type}",
        event_type=event_type,
        user_id=user_id,
        **(details or {})
    )


def log_security_event(event_type: str, severity: str = "INFO", details: Dict[str, Any] | None = None):
    """
    Log eventos de seguridad.
    
    Args:
        event_type: Tipo de evento (unauthorized_access, suspicious_activity, etc.)
        severity: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
        details: Información adicional del evento
    """
    security_logger = get_logger("api.security")
    
    log_method = {
        "DEBUG": security_logger.debug,
        "INFO": security_logger.info,
        "WARNING": security_logger.warning,
        "ERROR": security_logger.error,
        "CRITICAL": security_logger.critical
    }.get(severity.upper(), security_logger.info)
    
    log_method(
        f"Security event: {event_type}",
        event_type=event_type,
        severity=severity,
        **(details or {})
    )


def log_business_event(
    event_type: str, 
    entity_type: str = "", 
    entity_id: str = "", 
    details: Dict[str, Any] | None = None
):
    """
    Log eventos de negocio importantes.
    
    Args:
        event_type: Tipo de evento (task_created, user_registered, etc.)
        entity_type: Tipo de entidad (user, task, etc.)
        entity_id: ID de la entidad
        details: Información adicional
    """
    business_logger = get_logger("api.business")
    
    business_logger.info(
        f"Business event: {event_type}",
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        **(details or {})
    )