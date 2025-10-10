# -*- coding: utf-8 -*-
"""
Esquemas para el modelo de Tarea.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from src.shared.constants import TaskPriority, TaskStatus, TaskType


# Propiedades compartidas
class TareaBase(BaseModel):
    codigo: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[TaskStatus] = None
    tipo: Optional[TaskType] = None
    prioridad: Optional[TaskPriority] = TaskPriority.MEDIUM
    inicio_programado: Optional[datetime] = None
    fin_programado: Optional[datetime] = None
    delegado_usuario_id: Optional[int] = None
    creado_por_usuario_id: Optional[int] = None
    efectivos_asignados: Optional[List[int]] = []


# Propiedades para la creación
class TareaCreate(BaseModel):
    # Campos obligatorios
    codigo: str
    titulo: str
    tipo: TaskType
    inicio_programado: datetime
    delegado_usuario_id: int
    creado_por_usuario_id: int
    
    # Campos opcionales
    descripcion: Optional[str] = None
    prioridad: Optional[TaskPriority] = TaskPriority.MEDIUM
    fin_programado: Optional[datetime] = None
    efectivos_asignados: Optional[List[int]] = []


# Propiedades para la actualización (todos opcionales)
class TareaUpdate(BaseModel):
    codigo: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[TaskStatus] = None
    tipo: Optional[TaskType] = None
    prioridad: Optional[TaskPriority] = None
    inicio_programado: Optional[datetime] = None
    fin_programado: Optional[datetime] = None
    delegado_usuario_id: Optional[int] = None
    efectivos_asignados: Optional[List[int]] = None


# Propiedades compartidas por los modelos en la BD
class TareaInDBBase(BaseModel):
    # Campos requeridos en BD
    id: int
    uuid: UUID
    codigo: str
    titulo: str
    estado: TaskStatus
    tipo: TaskType
    prioridad: TaskPriority
    delegado_usuario_id: int
    creado_por_usuario_id: int
    inicio_programado: datetime
    
    # Campos opcionales
    descripcion: Optional[str] = None
    fin_programado: Optional[datetime] = None

    @field_serializer('uuid')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    model_config = ConfigDict(from_attributes=True)


# Propiedades para retornar al cliente
class Tarea(TareaInDBBase):
    pass


# Propiedades adicionales almacenadas en la BD
class TareaInDB(TareaInDBBase):
    pass
