# -*- coding: utf-8 -*-
"""
Sistema de logging centralizado para GRUPO_GAD.

Proporciona configuración consistente de logging para todos los módulos
del proyecto con diferentes niveles, formateo estructurado y múltiples outputs.
"""

import sys
from pathlib import Path
import os
from typing import Optional
import json
from datetime import datetime

from loguru import logger

# Crear directorio de logs si no existe
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de formatos
CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

JSON_FORMAT = "{time} | {level} | {name} | {function} | {line} | {message}"


class StructuredLogger:
    """Logger con capacidades de logging estructurado."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(service=name)

    def info(self, message: str, **kwargs):
        """Log info con datos estructurados opcionales."""
        if kwargs:
            self.logger.info(f"{message} | Data: {json.dumps(kwargs, default=str)}")
        else:
            self.logger.info(message)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error con información de excepción y datos adicionales."""
        extra_data = kwargs.copy()
        if error:
            extra_data.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
            })
        
        if extra_data:
            self.logger.error(f"{message} | Error: {json.dumps(extra_data, default=str)}")
        else:
            self.logger.error(message)

    def warning(self, message: str, **kwargs):
        """Log warning con datos estructurados opcionales."""
        if kwargs:
            self.logger.warning(f"{message} | Data: {json.dumps(kwargs, default=str)}")
        else:
            self.logger.warning(message)

    def debug(self, message: str, **kwargs):
        """Log debug con datos estructurados opcionales."""
        if kwargs:
            self.logger.debug(f"{message} | Debug: {json.dumps(kwargs, default=str)}")
        else:
            self.logger.debug(message)

    def critical(self, message: str, **kwargs):
        """Log crítico con datos estructurados opcionales."""
        if kwargs:
            self.logger.critical(f"{message} | Critical: {json.dumps(kwargs, default=str)}")
        else:
            self.logger.critical(message)


def setup_logging(
    service_name: str = "grupogad",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False,
) -> StructuredLogger:
    """
    Configura el sistema de logging para un servicio específico.
    
    Args:
        service_name: Nombre del servicio (api, bot, worker, etc.)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Habilitar output a consola
        enable_file: Habilitar output a archivo
        enable_json: Habilitar logging en formato JSON para producción
        
    Returns:
        StructuredLogger: Logger configurado para el servicio
    """
    # Limpiar configuración previa
    logger.remove()
    
    # Configurar nivel de logging
    log_level = log_level.upper()
    
    # Handler para consola (desarrollo)
    if enable_console:
        logger.add(
            sys.stdout,
            colorize=True,
            format=CONSOLE_FORMAT,
            level=log_level,
            filter=lambda record: record["level"].name != "DEBUG" or log_level == "DEBUG"
        )
    
    # Handler para archivo principal del servicio
    if enable_file:
        try:
            log_file = LOGS_DIR / f"{service_name}.log"
            # Verificar permiso de escritura en el directorio
            if os.access(LOGS_DIR, os.W_OK):
                logger.add(
                    str(log_file),
                    rotation="10 MB",
                    retention="30 days",
                    compression="zip",
                    format=FILE_FORMAT,
                    level=log_level,
                    enqueue=True,
                    backtrace=True,
                    diagnose=True,
                )
            else:
                # Sin permiso de escritura, deshabilitar file logging
                enable_file = False
        except Exception:
            enable_file = False
    
    # Handler para archivo de errores
    if enable_file:
        try:
            error_log_file = LOGS_DIR / f"{service_name}_errors.log"
            if os.access(LOGS_DIR, os.W_OK):
                logger.add(
                    str(error_log_file),
                    rotation="5 MB",
                    retention="30 days",
                    compression="zip",
                    format=FILE_FORMAT,
                    level="ERROR",
                    enqueue=True,
                    backtrace=True,
                    diagnose=True,
                )
        except Exception:
            pass
    
    # Handler para JSON (producción)
    if enable_json and os.access(LOGS_DIR, os.W_OK):
        try:
            json_log_file = LOGS_DIR / f"{service_name}_structured.jsonl"
            logger.add(
                str(json_log_file),
                rotation="50 MB",
                retention="30 days",
                compression="zip",
                format=JSON_FORMAT,
                level=log_level,
                serialize=True,  # Output en formato JSON
                enqueue=True,
            )
        except Exception:
            pass
    
    # Logger inicial con información del sistema
    structured_logger = StructuredLogger(service_name)
    structured_logger.info(
        f"Logging inicializado para {service_name}",
        level=log_level,
        console=enable_console,
        file=enable_file,
        json=enable_json,
        timestamp=datetime.now().isoformat()
    )
    
    return structured_logger


def get_logger(name: str) -> StructuredLogger:
    """
    Obtiene un logger estructurado para un módulo específico.
    
    Args:
        name: Nombre del módulo/componente
        
    Returns:
        StructuredLogger: Logger configurado
    """
    return StructuredLogger(name)


# Logger por defecto para el core
core_logger = get_logger("core.logging")