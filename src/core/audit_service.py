# -*- coding: utf-8 -*-
"""
Servicio centralizado de Audit Trail para GRUPO_GAD.

Este módulo proporciona la funcionalidad principal para:
- Registro automático de eventos de auditoría
- Generación de reports de compliance
- Análisis de patrones sospechosos
- Gestión de retención de datos
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from src.api.models import AuditLog, AuditSession, AuditEventType, AuditSeverity, Usuario
from src.core.logging import get_logger

audit_logger = get_logger("audit")


class AuditService:
    """
    Servicio centralizado para gestión de audit trail.
    
    Proporciona métodos para:
    - Registro automático de eventos
    - Queries de compliance
    - Análisis de seguridad
    - Reports gubernamentales
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_event(
        self,
        event_type: AuditEventType,
        action_description: str,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        session_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        # Request context
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        # Resource context
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        # Operation result
        success: bool = True,
        error_message: Optional[str] = None,
        response_status: Optional[int] = None,
        # Compliance
        compliance_tags: Optional[List[str]] = None,
        retention_days: Optional[int] = None
    ) -> AuditLog:
        """
        Registra un evento de auditoría en el sistema.
        
        Args:
            event_type: Tipo de evento (de AuditEventType)
            action_description: Descripción clara de la acción realizada
            user_id: ID del usuario (si aplica)
            telegram_id: ID de Telegram (si aplica)
            session_id: ID de sesión
            severity: Nivel de severidad del evento
            ... (otros parámetros opcionales para contexto)
            
        Returns:
            AuditLog: El registro de auditoría creado
        """
        
        # Generar ID único para el evento
        event_id = str(uuid.uuid4())
        
        # Calcular fecha de retención si se especifica
        retention_until = None
        if retention_days:
            retention_until = datetime.utcnow() + timedelta(days=retention_days)
        else:
            # Política de retención por defecto según severidad
            default_retention = {
                AuditSeverity.LOW: 365,      # 1 año
                AuditSeverity.MEDIUM: 2190,  # 6 años
                AuditSeverity.HIGH: 3650,    # 10 años
                AuditSeverity.CRITICAL: 7300 # 20 años
            }
            retention_until = datetime.utcnow() + timedelta(days=default_retention[severity])
        
        # Crear registro de auditoría
        audit_log = AuditLog(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            telegram_id=telegram_id,
            session_id=session_id,
            endpoint=endpoint,
            http_method=http_method,
            user_agent=user_agent,
            ip_address=ip_address,
            referer=referer,
            resource_type=resource_type,
            resource_id=resource_id,
            action_description=action_description,
            old_values=old_values or {},
            new_values=new_values or {},
            event_metadata=event_metadata or {},
            success=success,
            error_message=error_message,
            response_status=response_status,
            compliance_tags=",".join(compliance_tags) if compliance_tags else None,
            retention_until=retention_until
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        
        # Log estructurado para sistema de logging
        audit_logger.bind(
            event_id=event_id,
            event_type=event_type.value,
            user_id=user_id,
            resource=f"{resource_type}:{resource_id}" if resource_type else None,
            success=success,
            severity=severity.value
        ).info(f"Audit event: {action_description}")
        
        return audit_log
    
    async def log_authentication_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Método especializado para eventos de autenticación.
        """
        severity = AuditSeverity.MEDIUM if success else AuditSeverity.HIGH
        
        metadata = {
            "auth_method": "telegram" if telegram_id else "web",
            **(additional_metadata or {})
        }
        
        action_desc = {
            AuditEventType.LOGIN: "Usuario inició sesión exitosamente",
            AuditEventType.LOGOUT: "Usuario cerró sesión",
            AuditEventType.LOGIN_FAILED: f"Intento fallido de login: {error_message}",
            AuditEventType.TOKEN_REFRESH: "Token de autenticación renovado"
        }.get(event_type, f"Evento de autenticación: {event_type.value}")
        
        return await self.log_event(
            event_type=event_type,
            action_description=action_desc,
            user_id=user_id,
            telegram_id=telegram_id,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="authentication",
            event_metadata=metadata,
            success=success,
            error_message=error_message,
            compliance_tags=["auth", "security"]
        )
    
    async def log_data_change(
        self,
        event_type: AuditEventType,
        resource_type: str,
        resource_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: Optional[int] = None,
        action_description: Optional[str] = None
    ) -> AuditLog:
        """
        Método especializado para cambios en datos.
        """
        if not action_description:
            action_description = f"{event_type.value.title()} en {resource_type} ID: {resource_id}"
        
        # Detectar campos sensibles para compliance
        sensitive_fields = {"password", "token", "key", "secret", "credential"}
        has_sensitive = any(
            field in str(key).lower() 
            for changes in [old_values, new_values] 
            for key in changes.keys()
        )
        
        tags = ["data_change"]
        if has_sensitive:
            tags.append("sensitive_data")
        
        return await self.log_event(
            event_type=event_type,
            action_description=action_description,
            user_id=user_id,
            severity=AuditSeverity.MEDIUM,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            compliance_tags=tags
        )
    
    async def get_user_activity_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Obtiene resumen de actividad de un usuario para compliance.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query para estadísticas de actividad
        stmt = select(
            func.count(AuditLog.id).label("total_events"),
            func.count(AuditLog.id).filter(AuditLog.success == False).label("failed_events"),
            func.count(AuditLog.id).filter(AuditLog.severity == AuditSeverity.HIGH).label("high_severity"),
            func.count(AuditLog.id).filter(AuditLog.severity == AuditSeverity.CRITICAL).label("critical_events")
        ).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        )
        
        result = await self.db.execute(stmt)
        stats = result.first()
        
        # Eventos por tipo
        event_types_stmt = select(
            AuditLog.event_type,
            func.count(AuditLog.id).label("count")
        ).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        ).group_by(AuditLog.event_type)
        
        event_types_result = await self.db.execute(event_types_stmt)
        event_types = {row.event_type.value: row.count for row in event_types_result}
        
        return {
            "user_id": user_id,
            "period_days": days,
            "summary": {
                "total_events": stats.total_events,
                "failed_events": stats.failed_events,
                "high_severity_events": stats.high_severity,
                "critical_events": stats.critical_events,
                "success_rate": (stats.total_events - stats.failed_events) / max(stats.total_events, 1)
            },
            "event_types": event_types,
            "compliance_status": "suspicious" if stats.failed_events > 10 else "normal"
        }
    
    async def get_security_incidents(
        self,
        days: int = 7,
        min_severity: AuditSeverity = AuditSeverity.HIGH
    ) -> List[Dict[str, Any]]:
        """
        Obtiene incidentes de seguridad recientes para investigación.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Mapeo de severidad a valor numérico para comparación
        severity_order = {
            AuditSeverity.LOW: 1,
            AuditSeverity.MEDIUM: 2,
            AuditSeverity.HIGH: 3,
            AuditSeverity.CRITICAL: 4
        }
        
        stmt = select(AuditLog).options(
            selectinload(AuditLog.user)
        ).where(
            and_(
                AuditLog.timestamp >= start_date,
                or_(
                    AuditLog.severity == AuditSeverity.HIGH,
                    AuditLog.severity == AuditSeverity.CRITICAL,
                    AuditLog.success == False
                )
            )
        ).order_by(AuditLog.timestamp.desc())
        
        result = await self.db.execute(stmt)
        incidents = result.scalars().all()
        
        return [
            {
                "event_id": incident.event_id,
                "timestamp": incident.timestamp.isoformat(),
                "event_type": incident.event_type.value,
                "severity": incident.severity.value,
                "user": incident.user.nombre_completo if incident.user else "Sistema",
                "action": incident.action_description,
                "success": incident.success,
                "ip_address": str(incident.ip_address) if incident.ip_address else None,
                "resource": f"{incident.resource_type}:{incident.resource_id}" if incident.resource_type else None,
                "error": incident.error_message
            }
            for incident in incidents
        ]
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_user_activity: bool = True
    ) -> Dict[str, Any]:
        """
        Genera reporte completo de compliance para auditorías gubernamentales.
        """
        
        # Estadísticas generales del período
        total_events_stmt = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            )
        )
        
        total_events = await self.db.scalar(total_events_stmt)
        
        # Eventos por severidad
        severity_stats_stmt = select(
            AuditLog.severity,
            func.count(AuditLog.id).label("count")
        ).where(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            )
        ).group_by(AuditLog.severity)
        
        severity_result = await self.db.execute(severity_stats_stmt)
        severity_stats = {row.severity.value: row.count for row in severity_result}
        
        # Eventos de seguridad críticos
        security_incidents = await self.get_security_incidents(
            days=(end_date - start_date).days
        )
        
        report = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": (end_date - start_date).days
            },
            "summary": {
                "total_events": total_events,
                "events_by_severity": severity_stats,
                "security_incidents_count": len(security_incidents)
            },
            "security_incidents": security_incidents[:50],  # Limitar a 50 más recientes
            "compliance_status": "compliant" if len(security_incidents) == 0 else "requires_review",
            "generated_at": datetime.utcnow().isoformat(),
            "report_id": str(uuid.uuid4())
        }
        
        if include_user_activity:
            # Top users por actividad (para compliance gubernamental)
            top_users_stmt = select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("event_count")
            ).where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    AuditLog.user_id.isnot(None)
                )
            ).group_by(AuditLog.user_id).order_by(
                func.count(AuditLog.id).desc()
            ).limit(20)
            
            top_users_result = await self.db.execute(top_users_stmt)
            report["top_active_users"] = [
                {"user_id": row.user_id, "event_count": row.event_count}
                for row in top_users_result
            ]
        
        return report


    # Métodos de conveniencia para operaciones CRUD comunes
    
    async def log_create(
        self,
        resource_type: str,
        resource_id: str,
        new_values: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Método de conveniencia para operaciones CREATE."""
        context = request_context or {}
        
        return await self.log_event(
            event_type=AuditEventType.CREATE,
            action_description=f"Creado {resource_type} con ID: {resource_id}",
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.MEDIUM,
            endpoint=context.get("endpoint"),
            http_method=context.get("method"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=new_values,
            compliance_tags=["create", "data_change"]
        )
    
    async def log_update(
        self,
        resource_type: str,
        resource_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Método de conveniencia para operaciones UPDATE."""
        context = request_context or {}
        
        return await self.log_event(
            event_type=AuditEventType.UPDATE,
            action_description=f"Actualizado {resource_type} con ID: {resource_id}",
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.MEDIUM,
            endpoint=context.get("endpoint"),
            http_method=context.get("method"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            compliance_tags=["update", "data_change"]
        )
    
    async def log_delete(
        self,
        resource_type: str,
        resource_id: str,
        old_values: Dict[str, Any],
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Método de conveniencia para operaciones DELETE."""
        context = request_context or {}
        
        return await self.log_event(
            event_type=AuditEventType.DELETE,
            action_description=f"Eliminado {resource_type} con ID: {resource_id}",
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.HIGH,
            endpoint=context.get("endpoint"),
            http_method=context.get("method"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            compliance_tags=["delete", "data_change", "sensitive"]
        )
    
    async def log_read(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None,
        is_sensitive: bool = False
    ) -> AuditLog:
        """Método de conveniencia para operaciones READ (especialmente datos sensibles)."""
        context = request_context or {}
        
        action_desc = f"Consultado {resource_type}"
        if resource_id:
            action_desc += f" con ID: {resource_id}"
        
        tags = ["read"]
        if is_sensitive:
            tags.append("sensitive_data")
        
        return await self.log_event(
            event_type=AuditEventType.READ,
            action_description=action_desc,
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.LOW if not is_sensitive else AuditSeverity.MEDIUM,
            endpoint=context.get("endpoint"),
            http_method=context.get("method"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            compliance_tags=tags
        )
    
    async def log_login_attempt(
        self,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Método de conveniencia para intentos de login."""
        event_type = AuditEventType.LOGIN if success else AuditEventType.LOGIN_FAILED
        
        return await self.log_authentication_event(
            event_type=event_type,
            user_id=user_id,
            telegram_id=telegram_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )


# Instancia global del servicio (se inicializa con la sesión de DB)
async def get_audit_service(db: AsyncSession) -> AuditService:
    """Factory function para obtener instancia del servicio de auditoría."""
    return AuditService(db)