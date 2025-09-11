# -*- coding: utf-8 -*-
"""
Modelo de HistorialEstado para el sistema GRUPO_GAD.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from typing import Any

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.constants import TaskStatus

from .base import Base, CustomJsonB

if TYPE_CHECKING:
    from .tarea import Tarea
    from .usuario import Usuario


class HistorialEstado(Base):
    """Modelo de Historial de Estados de Tareas."""

    __tablename__ = "historial_estados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tarea_id: Mapped[int] = mapped_column(
    Integer, ForeignKey("tareas.id"), nullable=False
    )

    estado_anterior: Mapped[Optional[TaskStatus]] = mapped_column(
    ENUM(TaskStatus, name="estado_tarea")
    )
    estado_nuevo: Mapped[TaskStatus] = mapped_column(
    ENUM(TaskStatus, name="estado_tarea"), nullable=False
    )

    usuario_id: Mapped[Optional[int]] = mapped_column(
    Integer, ForeignKey("usuarios.id")
    )

    motivo: Mapped[Optional[str]] = mapped_column(Text)

    extra_data: Mapped[dict[str, Any]] = mapped_column(CustomJsonB, default={})

    # Relaciones
    tarea: Mapped["Tarea"] = relationship("Tarea", back_populates="historial_estados")

    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", back_populates="historial_estados"
    )

    def __str__(self) -> str:
        return f"Historial {self.id} para Tarea {self.tarea_id}"
