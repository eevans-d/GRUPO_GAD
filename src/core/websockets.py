# -*- coding: utf-8 -*-
"""
Sistema de WebSockets para GRUPO_GAD.

Proporciona comunicación en tiempo real para:
- Actualizaciones del dashboard
- Notificaciones de sistema
- Estados de tareas en tiempo real
- Alertas y eventos críticos
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

from fastapi import WebSocket
from pydantic import BaseModel, Field

from src.core.logging import get_logger

# Logger para WebSockets
ws_logger = get_logger("websockets")


class EventType(str, Enum):
    """Tipos de eventos WebSocket."""
    # Sistema
    SYSTEM_STATUS = "system_status"
    USER_ACTIVITY = "user_activity"
    
    # Dashboard
    DASHBOARD_UPDATE = "dashboard_update"
    METRICS_UPDATE = "metrics_update"
    
    # Tareas
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNED = "task_assigned"
    
    # Efectivos
    EFECTIVO_STATUS_CHANGED = "efectivo_status_changed"
    EFECTIVO_LOCATION_UPDATE = "efectivo_location_update"
    
    # Notificaciones
    NOTIFICATION = "notification"
    ALERT = "alert"
    WARNING = "warning"
    ERROR = "error"
    
    # Conexión
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"


class WSMessage(BaseModel):
    """Modelo para mensajes WebSocket."""
    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_user_id: Optional[int] = None
    target_role: Optional[str] = None


class ConnectionInfo(BaseModel):
    """Información de conexión WebSocket."""
    websocket: WebSocket
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connected_at: datetime = Field(default_factory=datetime.now)
    last_ping: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "arbitrary_types_allowed": True
    }


class WebSocketManager:
    """
    Manager para conexiones WebSocket del sistema GRUPO_GAD.
    
    Maneja:
    - Conexiones activas por usuario y rol
    - Distribución de mensajes
    - Heartbeat/keepalive
    - Autorización y seguridad
    """
    
    def __init__(self):
        # Conexiones activas: connection_id -> ConnectionInfo
        self.active_connections: Dict[str, ConnectionInfo] = {}
        
        # Mapeos para búsqueda rápida
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.role_connections: Dict[str, Set[str]] = {}  # role -> connection_ids
        
        # Task para heartbeat
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval: int = 30  # segundos
        # Métricas básicas (reinician por proceso)
        self.total_messages_sent = 0
        self.total_broadcasts = 0
        self.total_send_errors = 0
        self.last_broadcast_at: Optional[datetime] = None
        
    ws_logger.info("WebSocketManager inicializado")
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None, 
                     user_role: Optional[str] = None) -> str:
        """
        Establece una nueva conexión WebSocket.
        
        Args:
            websocket: Conexión WebSocket
            user_id: ID del usuario conectado
            user_role: Rol del usuario
            
        Returns:
            connection_id: ID único de la conexión
        """
        await websocket.accept()
        
        connection_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            user_role=user_role
        )
        
        connection_id = connection_info.connection_id
        self.active_connections[connection_id] = connection_info
        
        # Mapear por usuario
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Mapear por rol
        if user_role:
            if user_role not in self.role_connections:
                self.role_connections[user_role] = set()
            self.role_connections[user_role].add(connection_id)
        
        ws_logger.info(
            "Nueva conexión WebSocket establecida",
            connection_id=connection_id,
            user_id=user_id,
            user_role=user_role,
            total_connections=len(self.active_connections)
        )
        
        # Enviar ACK de conexión
        await self.send_to_connection(
            connection_id,
            WSMessage(
                event_type=EventType.CONNECTION_ACK,
                data={
                    "connection_id": connection_id,
                    "connected_at": connection_info.connected_at.isoformat(),
                    "server_time": datetime.now().isoformat()
                }
            )
        )
        
        # Iniciar heartbeat si es la primera conexión (después de enviar ACK)
        if len(self.active_connections) == 1 and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Desconecta y limpia una conexión WebSocket.
        
        Args:
            connection_id: ID de la conexión a desconectar
        """
        if connection_id not in self.active_connections:
            return
        
        connection_info = self.active_connections[connection_id]
        
        # Limpiar mapeos
        if connection_info.user_id:
            if connection_info.user_id in self.user_connections:
                self.user_connections[connection_info.user_id].discard(connection_id)
                if not self.user_connections[connection_info.user_id]:
                    del self.user_connections[connection_info.user_id]
        
        if connection_info.user_role:
            if connection_info.user_role in self.role_connections:
                self.role_connections[connection_info.user_role].discard(connection_id)
                if not self.role_connections[connection_info.user_role]:
                    del self.role_connections[connection_info.user_role]
        
        # Remover conexión
        del self.active_connections[connection_id]
        
        # Detener heartbeat si no hay conexiones
        if not self.active_connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        ws_logger.info(
            "Conexión WebSocket desconectada",
            connection_id=connection_id,
            user_id=connection_info.user_id,
            total_connections=len(self.active_connections)
        )
    
    async def send_to_connection(self, connection_id: str, message: WSMessage) -> bool:
        """
        Envía un mensaje a una conexión específica.
        
        Args:
            connection_id: ID de la conexión
            message: Mensaje a enviar
            
        Returns:
            bool: True si se envió exitosamente
        """
        if connection_id not in self.active_connections:
            ws_logger.warning(f"Conexión no encontrada: {connection_id}")
            return False
        
        connection_info = self.active_connections[connection_id]
        
        try:
            message_dict = message.model_dump(mode='json')
            # Convertir datetime a string para JSON
            message_dict['timestamp'] = message.timestamp.isoformat()
            
            await connection_info.websocket.send_text(json.dumps(message_dict))
            
            ws_logger.debug(
                f"Mensaje enviado a conexión {connection_id}",
                event_type=message.event_type,
                message_id=message.message_id
            )

            # Métricas: ignorar ACK y PING para total_messages_sent
            if message.event_type not in (EventType.CONNECTION_ACK, EventType.PING):
                self.total_messages_sent += 1
            
            return True
            
        except Exception as e:
            ws_logger.error(
                f"Error enviando mensaje a conexión {connection_id}: {str(e)}"
            )
            # Desconectar conexión problemática
            await self.disconnect(connection_id)
            self.total_send_errors += 1
            return False
    
    async def send_to_user(self, user_id: int, message: WSMessage) -> int:
        """
        Envía un mensaje a todas las conexiones de un usuario.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
            
        Returns:
            int: Número de conexiones a las que se envió
        """
        if user_id not in self.user_connections:
            return 0
        
        connection_ids = self.user_connections[user_id].copy()
        sent_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
        return sent_count
    
    async def send_to_role(self, role: str, message: WSMessage) -> int:
        """
        Envía un mensaje a todas las conexiones de un rol.
        
        Args:
            role: Rol objetivo
            message: Mensaje a enviar
            
        Returns:
            int: Número de conexiones a las que se envió
        """
        if role not in self.role_connections:
            return 0
        
        connection_ids = self.role_connections[role].copy()
        sent_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: WSMessage, 
                       exclude_connections: Optional[Set[str]] = None) -> int:
        """
        Envía un mensaje a todas las conexiones activas.
        
        Args:
            message: Mensaje a enviar
            exclude_connections: Conexiones a excluir
            
        Returns:
            int: Número de conexiones a las que se envió
        """
        exclude_connections = exclude_connections or set()
        connection_ids = [
            cid for cid in self.active_connections.keys() 
            if cid not in exclude_connections
        ]
        
        sent_count = 0
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        # Actualizar métricas si hubo envíos
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()

        return sent_count
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para mantener conexiones vivas."""
        while self.active_connections:
            try:
                # Espera inicial para evitar enviar PING antes del ACK inicial
                await asyncio.sleep(self._heartbeat_interval)
                current_time = datetime.now()
                ping_message = WSMessage(
                    event_type=EventType.PING,
                    data={"server_time": current_time.isoformat()}
                )
                
                # Enviar ping a todas las conexiones
                await self.broadcast(ping_message)
                
                ws_logger.debug(
                    f"Heartbeat enviado a {len(self.active_connections)} conexiones"
                )
                
                await asyncio.sleep(self._heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                ws_logger.error(f"Error en heartbeat loop: {str(e)}")
                await asyncio.sleep(5)  # Esperar antes de reintentar
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conexiones WebSocket.
        
        Returns:
            Dict con estadísticas
        """
        return {
            "total_connections": len(self.active_connections),
            "connections_by_role": {
                role: len(connections) 
                for role, connections in self.role_connections.items()
            },
            "unique_users": len(self.user_connections),
            "heartbeat_active": self._heartbeat_task is not None,
            "heartbeat_interval": self._heartbeat_interval,
            "metrics": {
                "total_messages_sent": self.total_messages_sent,
                "total_broadcasts": self.total_broadcasts,
                "total_send_errors": self.total_send_errors,
                "last_broadcast_at": self.last_broadcast_at.isoformat() if self.last_broadcast_at else None,
            }
        }


# Instancia global del manager
websocket_manager = WebSocketManager()


# Funciones helper para eventos específicos
async def notify_task_update(task_id: int, task_data: Dict[str, Any], 
                            user_id: Optional[int] = None):
    """Notifica actualización de tarea."""
    message = WSMessage(
        event_type=EventType.TASK_UPDATED,
        data={
            "task_id": task_id,
            "task_data": task_data
        },
        target_user_id=user_id
    )
    
    if user_id:
        await websocket_manager.send_to_user(user_id, message)
    else:
        await websocket_manager.broadcast(message)


async def notify_dashboard_update(dashboard_data: Dict[str, Any]):
    """Notifica actualización del dashboard."""
    message = WSMessage(
        event_type=EventType.DASHBOARD_UPDATE,
        data=dashboard_data
    )
    
    await websocket_manager.broadcast(message)


async def send_notification(user_id: int, title: str, content: str, 
                           level: str = "info"):
    """Envía notificación a usuario específico."""
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={
            "title": title,
            "content": content,
            "level": level
        },
        target_user_id=user_id
    )
    
    await websocket_manager.send_to_user(user_id, message)


async def send_system_alert(title: str, content: str, level: str = "warning"):
    """Envía alerta del sistema a todos los usuarios."""
    event_type = {
        "info": EventType.NOTIFICATION,
        "warning": EventType.WARNING,
        "error": EventType.ERROR,
        "alert": EventType.ALERT
    }.get(level, EventType.NOTIFICATION)
    
    message = WSMessage(
        event_type=event_type,
        data={
            "title": title,
            "content": content,
            "level": level
        }
    )
    
    await websocket_manager.broadcast(message)