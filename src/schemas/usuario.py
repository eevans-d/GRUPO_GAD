# -*- coding: utf-8 -*-
"""
Esquemas para el modelo de Usuario.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from src.shared.constants import UserLevel


# Propiedades compartidas
class UsuarioBase(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    telegram_id: Optional[int] = None
    nivel: Optional[UserLevel] = UserLevel.LEVEL_1
    verificado: Optional[bool] = False


# Propiedades para la creación
class UsuarioCreate(UsuarioBase):
    email: EmailStr
    password: str
    nombre: str
    apellido: str
    dni: str


# Propiedades para la actualización
class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    telegram_id: Optional[int] = None
    nivel: Optional[UserLevel] = None
    verificado: Optional[bool] = None
    password: Optional[str] = None


# Propiedades compartidas por los modelos en la BD
class UsuarioInDBBase(UsuarioBase):
    id: int
    uuid: UUID

    @field_serializer('uuid')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    model_config = ConfigDict(from_attributes=True)


# Propiedades para retornar al cliente
class Usuario(UsuarioInDBBase):
    pass


# Propiedades adicionales almacenadas en la BD
class UsuarioInDB(UsuarioInDBBase):
    hashed_password: str
