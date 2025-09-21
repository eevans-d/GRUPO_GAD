# -*- coding: utf-8 -*-
"""Modelo de Efectivo para el sistema GRUPO_GAD."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base

if TYPE_CHECKING:
    from .tarea import Tarea
    from .usuario import Usuario


class EstadoDisponibilidad(str, enum.Enum):
    """Enum para los estados de disponibilidad de un efectivo."""

    DISPONIBLE = "disponible"
    EN_TAREA = "en_tarea"
    FUERA_SERVICIO = "fuera_servicio"
    NO_DISPONIBLE = "no_disponible"


class Efectivo(Base):
    """Modelo de Efectivo del sistema."""

    __tablename__ = "efectivos"
    # __table_args__ eliminado para compatibilidad con SQLite

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uuid: Mapped[UUID] = mapped_column(
        pg_UUID(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
        default=uuid4,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), unique=True, nullable=False
    )
    codigo_interno: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    rango: Mapped[Optional[str]] = mapped_column(String(50))
    unidad: Mapped[Optional[str]] = mapped_column(String(100))
    especialidad: Mapped[Optional[str]] = mapped_column(String(100))

    estado_disponibilidad: Mapped[EstadoDisponibilidad] = mapped_column(
        pg_ENUM(
            EstadoDisponibilidad,
            name="estado_disponibilidad",
            create_type=False,
            # schema eliminado para SQLite
        ),
        nullable=False,
        default=EstadoDisponibilidad.DISPONIBLE,
        index=True,
    )

    ultima_actualizacion_estado: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    extra_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON)

    # --- Relationships ---
    usuario: Mapped["Usuario"] = relationship(back_populates="efectivo")

    tareas_asignadas: Mapped[List["Tarea"]] = relationship(
        secondary="tarea_efectivos",
        back_populates="efectivos",  # Corrected attribute name and back_populates
    )
# Definir la tabla de asociación al final del archivo, fuera de la clase
