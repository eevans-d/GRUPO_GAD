from pydantic import BaseModel
from typing import List, Optional
import datetime
from .models import NivelAutenticacion, EstadoDisponibilidad, EstadoTarea

# --- Base Schemas ---

class EfectivoBase(BaseModel):
    nombre: str
    especialidad: Optional[str] = None

class UsuarioBase(BaseModel):
    telegram_id: int
    nombre: str
    nivel: NivelAutenticacion

class TareaBase(BaseModel):
    codigo: str
    titulo: str
    tipo: str

# --- Schemas for Reading Data (Responses) ---

class Efectivo(EfectivoBase):
    id: int
    dni: str
    estado_disponibilidad: EstadoDisponibilidad

    class Config:
        orm_mode = True

class Usuario(UsuarioBase):
    id: int

    class Config:
        orm_mode = True

class Tarea(TareaBase):
    id: int
    inicio_programado: datetime.datetime
    estado: EstadoTarea
    delegado: Usuario
    asignados: List[Efectivo] = []

    class Config:
        orm_mode = True

# --- Schemas for Creating Data (Requests) ---

class TareaCreate(TareaBase):
    delegado_usuario_id: int
    asignados_ids: List[int]

class EfectivoCreate(EfectivoBase):
    dni: str
    usuario_id: Optional[int] = None # An officer can optionally be linked to a user

# --- Schemas for Specific Endpoints ---

class AuthDetails(BaseModel):
    nivel: NivelAutenticacion

class TareaFinalizarRequest(BaseModel):
    telegram_id: int

class TareaCreateRequest(TareaCreate):
    nivel_solicitante: str
