# -*- coding: utf-8 -*-
"""
Modelos ORM para el sistema GRUPO_GAD.
Implementación con SQLAlchemy 2.0 async/await.
"""

from .base import Base
from .usuario import Usuario
from .efectivo import Efectivo
from .tarea import Tarea
from .historial_estado import HistorialEstado
from .metrica_tarea import MetricaTarea
from .metrica_tarea import MetricaTarea
from .associations import tarea_efectivos  # Add this line

__all__ = [
    "Base",
    "Usuario",
    "Efectivo",
    "Tarea",
    "HistorialEstado",
    "MetricaTarea",
    "tarea_efectivos",  # Add this to __all__
]


__all__ = [
    "Base",
    "Usuario",
    "Efectivo",
    "Tarea",
    "HistorialEstado",
    "MetricaTarea",
    "tarea_efectivos",  # Add this to __all__
]
