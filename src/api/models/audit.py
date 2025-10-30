# -*- coding: utf-8 -*-
"""
Sistema de Audit Trail para transparencia y compliance gubernamental.

Este módulo implementa Task 7: Audit Trail completo
- Trazabilidad de todas las acciones de usuario
- Registro de cambios en datos críticos  
- Logs de acceso y autenticación
- Reports de compliance para auditorías gubernamentales
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ENUM, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, CustomJsonB

if TYPE_CHECKING:
    from .usuario import Usuario


class AuditEventType(str, Enum):
    """Tipos de eventos de auditoría."""
    
    # Autenticación y autorización
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PERMISSION_DENIED = "permission_denied"
    TOKEN_REFRESH = "token_refresh"
    
    # Operaciones CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    
    # Operaciones específicas de negocio
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_STATUS_CHANGED = "task_status_changed"
    EMERGENCY_CREATED = "emergency_created"
    
    # Operaciones administrativas
    USER_CREATED = "user_created"
    USER_DISABLED = "user_disabled"
    ROLE_CHANGED = "role_changed"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    
    # Operaciones de sistema
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    BACKUP_CREATED = "backup_created"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"


class AuditSeverity(str, Enum):
    """Niveles de severidad para eventos de auditoría."""
    
    LOW = "low"          # Operaciones rutinarias
    MEDIUM = "medium"    # Cambios de datos importantes
    HIGH = "high"        # Operaciones administrativas críticas
    CRITICAL = "critical"  # Eventos de seguridad, fallos de autenticación


class AuditLog(Base):
    """
    Modelo principal de audit trail para compliance gubernamental.
    
    Registra todas las acciones del sistema para:
    - Transparencia gubernamental
    - Compliance con regulaciones
    - Investigación de incidentes
    - Auditorías externas
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Identificación del evento
    event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)  # UUID
    event_type: Mapped[AuditEventType] = mapped_column(
        ENUM(AuditEventType, name="audit_event_type"), nullable=False
    )
    severity: Mapped[AuditSeverity] = mapped_column(
        ENUM(AuditSeverity, name="audit_severity"), nullable=False, default=AuditSeverity.LOW
    )
    
    # Información temporal
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    
    # Usuario y contexto
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id")
    )
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Información de la request/acción
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    http_method: Mapped[Optional[str]] = mapped_column(String(10))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    referer: Mapped[Optional[str]] = mapped_column(Text)
    
    # Detalles del evento
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))  # "task", "user", "system"
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))    # ID del recurso afectado
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Datos de la operación
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(CustomJsonB)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(CustomJsonB)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(CustomJsonB, default={})
    
    # Resultado de la operación
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    response_status: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Compliance y regulación
    compliance_tags: Mapped[Optional[str]] = mapped_column(String(500))  # Tags separados por comas
    retention_until: Mapped[Optional[datetime]] = mapped_column()  # Para políticas de retención
    
    # Relaciones
    user: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event_type={self.event_type}, "
            f"user_id={self.user_id}, timestamp={self.timestamp})>"
        )
    
    @property
    def is_security_event(self) -> bool:
        """Determina si es un evento de seguridad crítico."""
        security_events = {
            AuditEventType.LOGIN_FAILED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.USER_DISABLED,
            AuditEventType.ROLE_CHANGED,
            AuditEventType.SYSTEM_CONFIG_CHANGED
        }
        return self.event_type in security_events or self.severity == AuditSeverity.CRITICAL
    
    @property
    def compliance_summary(self) -> Dict[str, Any]:
        """Genera resumen para reports de compliance."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "action": self.action_description,
            "success": self.success,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "resource": f"{self.resource_type}:{self.resource_id}" if self.resource_type else None
        }


class AuditSession(Base):
    """
    Modelo para tracking de sesiones de usuario.
    
    Complementa AuditLog con información de sesión persistente
    para análisis de patrones de uso y compliance.
    """
    
    __tablename__ = "audit_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id")
    )
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Información de la sesión
    started_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    last_activity: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column()
    
    # Contexto de la sesión
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    platform: Mapped[Optional[str]] = mapped_column(String(50))  # "web", "telegram", "api"
    
    # Métricas de actividad
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    
    # Estado de la sesión
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    termination_reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relaciones
    user: Mapped[Optional["Usuario"]] = relationship("Usuario")
    
    @property
    def duration(self) -> Optional[int]:
        """Duración de la sesión en segundos."""
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return int((datetime.utcnow() - self.started_at).total_seconds())
    
    @property
    def is_suspicious(self) -> bool:
        """Determina si la sesión tiene patrones sospechosos."""
        # Sesión muy larga (>8 horas)
        if self.duration and self.duration > 28800:
            return True
        
        # Muchas requests fallidas
        if self.total_requests > 0 and (self.failed_requests / self.total_requests) > 0.3:
            return True
            
        return False