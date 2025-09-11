"""
Modelo de Usuario para el sistema GRUPO_GAD.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as sa_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.constants import UserLevel

from .base import Base, CustomJsonB

if TYPE_CHECKING:
    from .efectivo import Efectivo
    from .historial_estado import HistorialEstado
    from .tarea import Tarea


class Usuario(Base):
    """Modelo de Usuario del sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid = mapped_column(
        sa_UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    # Información personal
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)

    # Nivel de autorización
    nivel: Mapped[UserLevel] = mapped_column(
    ENUM(UserLevel, name="nivel_usuario"),
        default=UserLevel.LEVEL_1,
        nullable=False,
    )

    # Campos de seguridad
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    verificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    extra_data: Mapped[dict[str, Any]] = mapped_column(CustomJsonB, default={})

    # Relaciones
    efectivo: Mapped["Efectivo"] = relationship(
        "Efectivo",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )

    tareas_delegadas: Mapped[List["Tarea"]] = relationship(
        "Tarea",
        foreign_keys="Tarea.delegado_usuario_id",
        back_populates="delegado_usuario",
    )

    tareas_creadas: Mapped[List["Tarea"]] = relationship(
        "Tarea",
        foreign_keys="Tarea.creado_por_usuario_id",
        back_populates="creado_por_usuario",
    )

    historial_estados: Mapped[List["HistorialEstado"]] = relationship(
        "HistorialEstado", back_populates="usuario"
    )

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"

    @property
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return not self.deleted_at and self.verificado

    @property
    def is_blocked(self) -> bool:
        """Verifica si el usuario está bloqueado temporalmente."""
        if not self.bloqueado_hasta:
            return False
        return self.bloqueado_hasta > datetime.now(timezone.utc)

    @property
    def is_superuser(self) -> bool:
        """Verifica si el usuario tiene nivel de superusuario (nivel 3)."""
        return self.nivel == UserLevel.LEVEL_3

    def can_access_level(self, required_level: UserLevel) -> bool:
        """Verifica si el usuario puede acceder a un nivel requerido."""
        return self.nivel.value >= required_level.value

    def reset_failed_attempts(self) -> None:
        """Reinicia los intentos fallidos."""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None

    def increment_failed_attempts(self) -> None:
        """Incrementa los intentos fallidos."""
        self.intentos_fallidos += 1

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.email})"
