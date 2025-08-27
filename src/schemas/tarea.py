# -*- coding: utf-8 -*-
"""
Esquemas para el modelo de Tarea.
"""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from src.shared.constants import TaskStatus, TaskPriority, TaskType


# Propiedades compartidas
class TareaBase(BaseModel):
    codigo: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[TaskType] = None
    prioridad: Optional[TaskPriority] = TaskPriority.MEDIUM
    inicio_programado: Optional[datetime] = None
    fin_programado: Optional[datetime] = None
    delegado_usuario_id: Optional[int] = None
    creado_por_usuario_id: Optional[int] = None
    efectivos_asignados: Optional[List[int]] = []


# Propiedades para la creación
class TareaCreate(TareaBase):
    codigo: str
    titulo: str
    tipo: TaskType
    inicio_programado: datetime
    delegado_usuario_id: int
    creado_por_usuario_id: int


# Propiedades para la actualización
class TareaUpdate(TareaBase):
    pass


# Propiedades compartidas por los modelos en la BD
class TareaInDBBase(TareaBase):
    id: int
    uuid: str
    estado: TaskStatus

    class Config:
        orm_mode = True


# Propiedades para retornar al cliente
class Tarea(TareaInDBBase):
    pass


# Propiedades adicionales almacenadas en la BD
class TareaInDB(TareaInDBBase):
    pass
