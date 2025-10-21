"""
Telegram-specific Pydantic schemas for API validation.

These models are optimized for Telegram bot integration:
- TelegramTaskCreate: Creating tasks from bot wizard
- TelegramTaskFinalize: Finalizing tasks by code
- TelegramAuthResponse: Authentication responses
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class TelegramTaskCreate(BaseModel):
    """
    Schema for creating a task from Telegram bot.
    
    Matches the wizard flow from bot:
    1. Tipo de tarea
    2. Código
    3. Título
    4. Descripción
    5. Prioridad
    6. Ubicación
    """
    telegram_id: int = Field(..., description="Telegram user ID creating the task")
    tipo: str = Field(..., description="Task type: 'operativa', 'administrativa', etc.")
    codigo: str = Field(..., min_length=3, max_length=20, description="Unique task code")
    titulo: str = Field(..., min_length=5, max_length=200, description="Task title")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Task description")
    prioridad: str = Field(default="media", description="Priority: 'baja', 'media', 'alta', 'urgente'")
    ubicacion: Optional[str] = Field(None, max_length=200, description="Task location")
    asignado_a: Optional[List[int]] = Field(default=None, description="List of telegram_ids to assign")

    @validator('tipo')
    def validate_tipo(cls, v):
        valid_types = ['operativa', 'administrativa', 'inspeccion', 'patrullaje', 'emergencia']
        if v.lower() not in valid_types:
            raise ValueError(f"Tipo must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator('prioridad')
    def validate_prioridad(cls, v):
        valid_priorities = ['baja', 'media', 'alta', 'urgente']
        if v.lower() not in valid_priorities:
            raise ValueError(f"Prioridad must be one of: {', '.join(valid_priorities)}")
        return v.lower()

    @validator('codigo')
    def validate_codigo_format(cls, v):
        """Ensure codigo follows format: letters + numbers."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Código must be alphanumeric (letters, numbers, -, _)")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "tipo": "operativa",
                "codigo": "OP-2024-001",
                "titulo": "Reparar alumbrado público calle principal",
                "descripcion": "Reemplazar 5 lámparas en calle principal sector norte",
                "prioridad": "alta",
                "ubicacion": "Calle Principal, Sector Norte",
                "asignado_a": [987654321]
            }
        }


class TelegramTaskFinalizeRequest(BaseModel):
    """
    Schema for finalizing a task from Telegram bot.
    
    User provides only the task code, system validates permissions.
    """
    codigo: str = Field(..., min_length=3, max_length=20, description="Task code to finalize")
    telegram_id: int = Field(..., description="Telegram ID of user finalizing")
    observaciones: Optional[str] = Field(None, max_length=500, description="Final observations")

    @validator('codigo')
    def uppercase_codigo(cls, v):
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "OP-2024-001",
                "telegram_id": 123456789,
                "observaciones": "Tarea completada exitosamente"
            }
        }


class TelegramTaskFinalizeResponse(BaseModel):
    """Response after finalizing a task."""
    success: bool
    message: str
    task_id: Optional[int] = None
    codigo: str
    finalized_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Tarea OP-2024-001 finalizada exitosamente",
                "task_id": 42,
                "codigo": "OP-2024-001",
                "finalized_at": "2025-10-21T14:30:00"
            }
        }


class TelegramAuthRequest(BaseModel):
    """Request to authenticate Telegram user."""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")

    class Config:
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class TelegramAuthResponse(BaseModel):
    """Response after authenticating Telegram user."""
    authenticated: bool
    user_id: Optional[int] = None
    telegram_id: int
    role: Optional[str] = None
    token: Optional[str] = Field(None, description="JWT token if authenticated")
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "authenticated": True,
                "user_id": 5,
                "telegram_id": 123456789,
                "role": "member",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "message": "Usuario autenticado correctamente"
            }
        }


class TelegramUserTasksResponse(BaseModel):
    """Response with user's tasks from Telegram."""
    telegram_id: int
    total_tasks: int
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    tasks: List[dict] = Field(default_factory=list, description="List of task summaries")

    class Config:
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "total_tasks": 15,
                "active_tasks": 3,
                "pending_tasks": 2,
                "completed_tasks": 10,
                "tasks": [
                    {
                        "id": 42,
                        "codigo": "OP-2024-001",
                        "titulo": "Reparar alumbrado",
                        "estado": "activa",
                        "prioridad": "alta"
                    }
                ]
            }
        }


class TelegramTaskCreateResponse(BaseModel):
    """Response after creating task from Telegram."""
    success: bool
    message: str
    task_id: Optional[int] = None
    codigo: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Tarea creada exitosamente",
                "task_id": 42,
                "codigo": "OP-2024-001",
                "created_at": "2025-10-21T14:30:00"
            }
        }
