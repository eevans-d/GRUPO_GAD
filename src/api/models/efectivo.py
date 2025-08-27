# -*- coding: utf-8 -*-
"""
Modelo de Efectivo para el sistema GRUPO_GAD.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as sa_UUID, JSONB, ENUM
import uuid
from datetime import datetime

from .base import Base
from src.shared.constants import AvailabilityStatus


class Efectivo(Base):
    """Modelo de Efectivo del sistema."""
    
    __tablename__ = "efectivos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid = mapped_column(
        sa_UUID(as_uuid=True), 
        default=uuid.uuid4, 
        unique=True, 
        nullable=False
    )
    
    # Relación con usuario
    usuario_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False
    )
    
    # Información profesional
    codigo_interno: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rango: Mapped[Optional[str]] = mapped_column(String(50))
    unidad: Mapped[Optional[str]] = mapped_column(String(100))
    especialidad: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Estado de disponibilidad
    estado_disponibilidad: Mapped[AvailabilityStatus] = mapped_column(
        ENUM(AvailabilityStatus, name="estado_disponibilidad", schema="gad"),
        default=AvailabilityStatus.AVAILABLE,
        nullable=False
    )
    
    ultima_actualizacion_estado: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    extra_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Relaciones
    usuario: Mapped["Usuario"] = relationship(
        "Usuario", 
        back_populates="efectivo",
        foreign_keys=[usuario_id]
    )
    
    tareas_asignadas: Mapped[List["Tarea"]] = relationship(
        "Tarea",
        secondary="tarea_efectivos",
        back_populates="efectivos"
    )
    
    @property
    def is_available(self) -> bool:
        """Verifica si el efectivo está disponible."""
        return (
            self.estado_disponibilidad == AvailabilityStatus.AVAILABLE 
            and not self.usuario.deleted_at
        )
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del efectivo."""
        return self.usuario.nombre_completo if self.usuario else "Desconocido"
    
    def update_availability_status(self, new_status: AvailabilityStatus) -> None:
        """Actualiza el estado de disponibilidad."""
        self.estado_disponibilidad = new_status
        self.ultima_actualizacion_estado = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"{self.nombre_completo} - {self.codigo_interno}"
