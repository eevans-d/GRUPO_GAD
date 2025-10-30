# Exponer símbolos principales para tests y uso externo
# -*- coding: utf-8 -*-
"""
Modelos ORM para el sistema GRUPO_GAD.
Implementación con SQLAlchemy 2.0 async/await.
"""

from .associations import tarea_efectivos
from .audit import AuditLog, AuditSession, AuditEventType, AuditSeverity
from .base import Base
from .efectivo import Efectivo
from .historial_estado import HistorialEstado
from .metrica_tarea import MetricaTarea
from .tarea import Tarea
from .usuario import Usuario

__all__ = [
    "Base",
    "Usuario",
    "Efectivo", 
    "Tarea",
    "HistorialEstado",
    "MetricaTarea",
    "AuditLog",
    "AuditSession",
    "AuditEventType",
    "AuditSeverity",
    "tarea_efectivos",
]