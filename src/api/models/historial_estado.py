# -*- coding: utf-8 -*-
"""
Modelo de HistorialEstado para el sistema GRUPO_GAD.
"""

from typing import Optional
from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from datetime import datetime

from .base import Base
from src.shared.constants import TaskStatus


class HistorialEstado(Base):
    """Modelo de Historial de Estados de Tareas."""
    
    __tablename__ = "historial_estados"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    tarea_id: Mapped[int] = mapped_column(Integer, ForeignKey("gad.tareas.id"), nullable=False)
    
    estado_anterior: Mapped[Optional[TaskStatus]] = mapped_column(
        ENUM(TaskStatus, name="estado_tarea", schema="gad")
    )
    estado_nuevo: Mapped[TaskStatus] = mapped_column(
        ENUM(TaskStatus, name="estado_tarea", schema="gad"),
        nullable=False
    )
    
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gad.usuarios.id"))
    
    motivo: Mapped[Optional[str]] = mapped_column(Text)
    
    extra_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Relaciones
    tarea: Mapped["Tarea"] = relationship(
        "Tarea",
        back_populates="historial_estados"
    )
    
    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        back_populates="historial_estados"
    )

    def __str__(self) -> str:
        return f"Historial {self.id} para Tarea {self.tarea_id}"
