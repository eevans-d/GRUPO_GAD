from __future__ import annotations
# -*- coding: utf-8 -*-
"""
Modelo de Tarea para el sistema GRUPO_GAD.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as sa_UUID, ENUM
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from .base import Base, CustomJsonB, CustomArray
from src.shared.constants import TaskStatus, TaskPriority, TaskType
from .associations import tarea_efectivos  # Add this line


class Tarea(Base):
    """Modelo de Tarea del sistema."""

    __tablename__ = "tareas"

    __table_args__ = (
        CheckConstraint(
            "fin_programado IS NULL OR fin_programado > inicio_programado",
            name="chk_tareas_fechas",
        ),
        CheckConstraint(
            "(inicio_real IS NULL AND fin_real IS NULL) OR "
            "(inicio_real IS NOT NULL AND fin_real IS NULL) OR "
            "(inicio_real IS NOT NULL AND fin_real IS NOT NULL AND fin_real >= inicio_real)",
            name="chk_tareas_fechas_reales",
        ),
        {"schema": "gad"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid = mapped_column(
        sa_UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    # Información básica
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    # Clasificación
    tipo: Mapped[TaskType] = mapped_column(
        ENUM(TaskType, name="tipo_tarea", schema="gad"), nullable=False
    )
    prioridad: Mapped[TaskPriority] = mapped_column(
        ENUM(TaskPriority, name="prioridad_tarea", schema="gad"),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )

    # Fechas y tiempos
    inicio_programado: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fin_programado: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    inicio_real: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fin_real: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tiempo_pausado: Mapped[Optional[timedelta]] = mapped_column()
    pausado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Estados
    estado: Mapped[TaskStatus] = mapped_column(
        ENUM(TaskStatus, name="estado_tarea", schema="gad"),
        default=TaskStatus.PROGRAMMED,
        nullable=False,
    )

    # Relaciones
    delegado_usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gad.usuarios.id"), nullable=False
    )
    creado_por_usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gad.usuarios.id"), nullable=False
    )

    # Ubicación geográfica
    ubicacion_lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 8))
    ubicacion_lon: Mapped[Optional[float]] = mapped_column(Numeric(11, 8))
    ubicacion_descripcion: Mapped[Optional[str]] = mapped_column(Text)

    # Efectivos asignados
    efectivos_asignados: Mapped[List[int]] = mapped_column(CustomArray, default=[])

    # Métricas calculadas (STORED)
    duracion_real_horas: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)

    # Metadata y notas
    notas: Mapped[dict] = mapped_column(CustomJsonB, default={})
    extra_data: Mapped[dict] = mapped_column(CustomJsonB, default={})

    # Relaciones ORM
    delegado_usuario: Mapped["Usuario"] = relationship(
        "Usuario", foreign_keys=[delegado_usuario_id], back_populates="tareas_delegadas"
    )

    creado_por_usuario: Mapped["Usuario"] = relationship(
        "Usuario", foreign_keys=[creado_por_usuario_id], back_populates="tareas_creadas"
    )

    efectivos: Mapped[List["Efectivo"]] = relationship(
        "Efectivo", secondary=tarea_efectivos, back_populates="tareas_asignadas"
    )

    historial_estados: Mapped[List["HistorialEstado"]] = relationship(
        "HistorialEstado", back_populates="tarea"
    )

    # Propiedades híbridas para cálculos
    @hybrid_property
    def duracion_estimada_horas(self) -> float:
        """Estima la duración de la tarea en horas basado en programación."""
        if self.inicio_programado and self.fin_programado:
            return (
                self.fin_programado - self.inicio_programado
            ).total_seconds() / 3600.0
        # Estimación por defecto basada en prioridad
        return 2.0 + (5 - self.prioridad.value) * 0.5

    @hybrid_property
    def esta_activa(self) -> bool:
        """Verifica si la tarea está activa."""
        return self.estado in [
            TaskStatus.PROGRAMMED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.PAUSED,
        ]

    @hybrid_property
    def esta_completada(self) -> bool:
        """Verifica si la tarea está completada."""
        return self.estado == TaskStatus.COMPLETED

    @hybrid_property
    def esta_retrasada(self) -> bool:
        """Verifica si la tarea está retrasada respecto a su programación."""
        if not self.inicio_real or not self.inicio_programado:
            return False
        return self.inicio_real > self.inicio_programado
