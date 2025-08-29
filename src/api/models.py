import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    ForeignKey,
    DateTime,
    Enum,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# Define ENUM types for use in models
class NivelAutenticacion(str, enum.Enum):
    uno = "1"
    dos = "2"
    tres = "3"


class EstadoDisponibilidad(str, enum.Enum):
    activo = "activo"
    en_tarea = "en_tarea"
    en_licencia = "en_licencia"


class EstadoTarea(str, enum.Enum):
    programada = "programada"
    en_curso = "en_curso"
    finalizada = "finalizada"


# Association Table for Tareas <-> Efectivos (many-to-many)
tarea_asignaciones = Table(
    "tarea_asignaciones",
    Base.metadata,
    Column(
        "tarea_id",
        Integer,
        ForeignKey("gad.tareas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "efectivo_id",
        Integer,
        ForeignKey("gad.efectivos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema="gad",
)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "gad"}

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    nivel = Column(
        Enum(NivelAutenticacion), nullable=False, default=NivelAutenticacion.uno
    )

    efectivo = relationship("Efectivo", back_populates="usuario", uselist=False)
    tareas_delegadas = relationship("Tarea", back_populates="delegado")


class Efectivo(Base):
    __tablename__ = "efectivos"
    __table_args__ = {"schema": "gad"}

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(50))
    estado_disponibilidad = Column(
        Enum(EstadoDisponibilidad), nullable=False, default=EstadoDisponibilidad.activo
    )

    usuario_id = Column(Integer, ForeignKey("gad.usuarios.id"))
    usuario = relationship("Usuario", back_populates="efectivo")

    tareas = relationship(
        "Tarea", secondary=tarea_asignaciones, back_populates="asignados"
    )


class Tarea(Base):
    __tablename__ = "tareas"
    __table_args__ = {"schema": "gad"}

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False)
    titulo = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False)
    inicio_programado = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    inicio_real = Column(DateTime(timezone=True))
    fin_real = Column(DateTime(timezone=True))
    estado = Column(Enum(EstadoTarea), nullable=False, default=EstadoTarea.programada)

    delegado_usuario_id = Column(Integer, ForeignKey("gad.usuarios.id"), nullable=False)
    delegado = relationship("Usuario", back_populates="tareas_delegadas")

    asignados = relationship(
        "Efectivo", secondary=tarea_asignaciones, back_populates="tareas"
    )


# Note: Turnos and Licencias are not modeled here to keep the refactoring focused.
# They can be added later following the same pattern.
