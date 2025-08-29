# -*- coding: utf-8 -*-
"""
Modelo de MetricaTarea para el sistema GRUPO_GAD.
"""

from typing import Optional
from sqlalchemy import Integer, REAL, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime, timezone

from .base import Base
from src.shared.constants import TaskType, TaskPriority


class MetricaTarea(Base):
    """Modelo de Métricas de Tareas."""

    __tablename__ = "metricas_tareas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tipo_tarea: Mapped[TaskType] = mapped_column(
        ENUM(TaskType, name="tipo_tarea", schema="gad"), nullable=False
    )
    prioridad: Mapped[TaskPriority] = mapped_column(
        ENUM(TaskPriority, name="prioridad_tarea", schema="gad"), nullable=False
    )

    # Métricas acumuladas
    total_tareas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_horas: Mapped[float] = mapped_column(REAL, default=0.0, nullable=False)
    tiempo_promedio_horas: Mapped[Optional[float]] = mapped_column(REAL)
    tasa_exito: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))

    # Métricas de rendimiento
    duracion_p25: Mapped[Optional[float]] = mapped_column(REAL)
    duracion_p50: Mapped[Optional[float]] = mapped_column(REAL)
    duracion_p75: Mapped[Optional[float]] = mapped_column(REAL)
    duracion_min: Mapped[Optional[float]] = mapped_column(REAL)
    duracion_max: Mapped[Optional[float]] = mapped_column(REAL)

    # Fecha de última actualización
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __str__(self) -> str:
        return f"Métricas para Tarea {self.tipo_tarea} con prioridad {self.prioridad}"
