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
import hashlib
import math
from typing import Dict, Set, Optional, Any, List, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
from dataclasses import dataclass, field
import weakref

from fastapi import WebSocket
from pydantic import BaseModel, Field

from src.core.logging import get_logger

# Intentar importar métricas si están disponibles
try:
    from src.observability.metrics import (
        connection_established, 
        connection_closed,
        message_sent, 
        send_error, 
        heartbeat_completed,
        update_user_count
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

# Logger para WebSockets
ws_logger = get_logger("websockets")


# --- SISTEMA DE SHARDING DE CANALES --- #

class ChannelType(str, Enum):
    """Tipos de canales especializados para sharding."""
    GENERAL = "general"
    ADMIN = "admin"
    USERS = "users"
    PRIORITY = "priority"


@dataclass
class ChannelInfo:
    """Información de un canal de comunicación."""
    name: str
    channel_type: ChannelType
    user_capacity: int
    current_load: int = 0
    priority_level: int = 1  # 1-10, 10 siendo máxima prioridad
    active_connections: Set[str] = field(default_factory=set)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def utilization(self) -> float:
        """Porcentaje de utilización del canal."""
        return (self.current_load / self.user_capacity) * 100 if self.user_capacity > 0 else 0
    
    @property
    def is_overloaded(self) -> bool:
        """Indica si el canal está sobrecargado."""
        return self.utilization > 80.0
    
    @property
    def is_underutilized(self) -> bool:
        """Indica si el canal está subutilizado."""
        return self.utilization < 30.0


class ConsistentHashRing:
    """Sistema de hashing consistente para distribución de canales."""
    
    def __init__(self, nodes: List[str] = None, replicas: int = 150):
        """
        Inicializa el anillo de hash consistente.
        
        Args:
            nodes: Lista de nodos/canales
            replicas: Número de réplicas virtuales por nodo (más = mejor distribución)
        """
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key: str) -> int:
        """Genera hash MD5 para la clave."""
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    
    def add_node(self, node: str):
        """Añade un nodo al anillo de hash."""
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
            self.sorted_keys.append(key)
        
        self.sorted_keys.sort()
    
    def remove_node(self, node: str):
        """Remueve un nodo del anillo de hash."""
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            if key in self.ring:
                del self.ring[key]
                self.sorted_keys.remove(key)
    
    def get_node(self, key: str) -> Optional[str]:
        """Obtiene el nodo para una clave dada usando hashing consistente."""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Encontrar el primer nodo en sentido horario desde el hash
        for ring_key in self.sorted_keys:
            if hash_value <= ring_key:
                return self.ring[ring_key]
        
        # Si no se encuentra, retornar el primer nodo (comportamiento circular)
        return self.ring[self.sorted_keys[0]]
    
    def get_nodes(self, key: str, count: int = 2) -> List[str]:
        """Obtiene múltiples nodos para una clave (para redundancia)."""
        if not self.ring or count <= 0:
            return []
        
        nodes = []
        hash_value = self._hash(key)
        idx = 0
        
        # Encontrar índice inicial
        for i, ring_key in enumerate(self.sorted_keys):
            if hash_value <= ring_key:
                idx = i
                break
        
        # Recopilar nodos únicos
        while len(nodes) < count and len(nodes) < len(self.ring):
            node = self.ring[self.sorted_keys[idx % len(self.sorted_keys)]]
            if node not in nodes:
                nodes.append(node)
            idx += 1
        
        return nodes


class ChannelRouter:
    """Router inteligente para distribución de canales basada en tipo de usuario y prioridad."""
    
    def __init__(self):
        self.ring = ConsistentHashRing()
        self.channel_configs = {
            ChannelType.GENERAL: {
                "capacity": 1000,
                "priority": 1,
                "channels": ["ws_broadcast_general_1", "ws_broadcast_general_2", "ws_broadcast_general_3"]
            },
            ChannelType.ADMIN: {
                "capacity": 100,
                "priority": 8,
                "channels": ["ws_broadcast_admin_1", "ws_broadcast_admin_2"]
            },
            ChannelType.USERS: {
                "capacity": 800,
                "priority": 3,
                "channels": ["ws_broadcast_users_1", "ws_broadcast_users_2", "ws_broadcast_users_3", "ws_broadcast_users_4"]
            },
            ChannelType.PRIORITY: {
                "capacity": 200,
                "priority": 10,
                "channels": ["ws_broadcast_priority_1", "ws_broadcast_priority_2"]
            }
        }
        
        # Inicializar anillo con todos los canales
        self._initialize_ring()
    
    def _initialize_ring(self):
        """Inicializa el anillo de hash con todos los canales configurados."""
        for channel_type, config in self.channel_configs.items():
            for channel in config["channels"]:
                self.ring.add_node(channel)
    
    def route_user(self, user_id: Union[int, str], user_role: Optional[str] = None, 
                   priority: int = 1) -> str:
        """
        Determina el canal óptimo para un usuario basado en su perfil.
        
        Args:
            user_id: ID del usuario
            user_role: Rol del usuario
            priority: Prioridad del usuario (1-10)
            
        Returns:
            str: Nombre del canal asignado
        """
        # Determinar tipo de canal basado en rol y prioridad
        channel_type = self._determine_channel_type(user_role, priority)
        
        # Generar clave consistente para el usuario
        key = f"{user_id}:{channel_type.value}"
        
        # Usar hash consistente para distribuir carga
        selected_channel = self.ring.get_node(key)
        
        # Fallback: usar canal del tipo correspondiente si no se encuentra
        if not selected_channel:
            config = self.channel_configs.get(channel_type, {})
            channels = config.get("channels", [])
            selected_channel = channels[0] if channels else "ws_broadcast_general_1"
        
        return selected_channel
    
    def _determine_channel_type(self, user_role: Optional[str], priority: int) -> ChannelType:
        """Determina el tipo de canal basado en rol y prioridad."""
        if user_role in ["ADMIN", "SUPER_ADMIN"] or priority >= 8:
            return ChannelType.ADMIN
        elif priority >= 7:
            return ChannelType.PRIORITY
        elif user_role in ["LEVEL_2", "LEVEL_3", "MODERATOR"]:
            return ChannelType.USERS
        else:
            return ChannelType.GENERAL
    
    def get_optimal_channels(self, user_id: Union[int, str], count: int = 2) -> List[str]:
        """Obtiene canales óptimos para redundancia."""
        key = f"{user_id}"
        return self.ring.get_nodes(key, count)
    
    def add_channel(self, channel_type: ChannelType, channel_name: str, capacity: int = 1000):
        """Añade dinámicamente un nuevo canal."""
        if channel_type not in self.channel_configs:
            self.channel_configs[channel_type] = {"capacity": capacity, "priority": 1, "channels": []}
        
        config = self.channel_configs[channel_type]
        if channel_name not in config["channels"]:
            config["channels"].append(channel_name)
            self.ring.add_node(channel_name)
    
    def get_channel_stats(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene estadísticas de todos los canales."""
        stats = {}
        for channel_type, config in self.channel_configs.items():
            stats[channel_type.value] = {
                "capacity": config["capacity"],
                "priority": config["priority"],
                "channels": config["channels"],
                "channel_count": len(config["channels"])
            }
        return stats


class ChannelLoadBalancer:
    """Load balancer inteligente para distribución de carga entre canales."""
    
    def __init__(self, router: ChannelRouter):
        self.router = router
        self.channel_metrics: Dict[str, Dict[str, Any]] = {}
    
    def select_optimal_channel(self, channel_type: ChannelType, exclude_overloaded: bool = True) -> str:
        """
        Selecciona el canal óptimo para un tipo dado.
        
        Args:
            channel_type: Tipo de canal
            exclude_overloaded: Si excluir canales sobrecargados
            
        Returns:
            str: Nombre del canal óptimo
        """
        config = self.router.channel_configs.get(channel_type)
        if not config or not config.get("channels"):
            return "ws_broadcast_general_1"  # Fallback
        
        channels = config["channels"]
        
        if exclude_overloaded:
            # Filtrar canales sobrecargados
            channels = [
                ch for ch in channels 
                if self._get_channel_utilization(ch) < 80.0
            ]
        
        if not channels:
            channels = config["channels"]  # Usar todos si todos están sobrecargados
        
        # Seleccionar canal con menor carga
        optimal_channel = min(channels, key=lambda ch: self._get_channel_utilization(ch))
        return optimal_channel
    
    def _get_channel_utilization(self, channel_name: str) -> float:
        """Obtiene la utilización de un canal específico."""
        metrics = self.channel_metrics.get(channel_name, {})
        return metrics.get("utilization", 0.0)
    
    def update_channel_metrics(self, channel_name: str, connection_count: int, 
                             message_count: int = 0, error_count: int = 0):
        """Actualiza métricas de un canal."""
        if channel_name not in self.channel_metrics:
            self.channel_metrics[channel_name] = {
                "connection_count": 0,
                "message_count": 0,
                "error_count": 0,
                "utilization": 0.0,
                "last_updated": datetime.now()
            }
        
        metrics = self.channel_metrics[channel_name]
        metrics["connection_count"] = connection_count
        metrics["message_count"] += message_count
        metrics["error_count"] += error_count
        metrics["last_updated"] = datetime.now()
        
        # Calcular utilización (esto debería venir de ChannelInfo real)
        config = self._find_channel_config(channel_name)
        if config:
            capacity = config.get("capacity", 1000)
            metrics["utilization"] = (connection_count / capacity) * 100
    
    def _find_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Encuentra la configuración de un canal por nombre."""
        for config in self.router.channel_configs.values():
            if channel_name in config.get("channels", []):
                return config
        return None
    
    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del load balancing."""
        return {
            "channel_metrics": self.channel_metrics,
            "total_channels": len(self.router.channel_configs),
            "total_active_channels": len([ch for ch in self.channel_metrics.keys() 
                                        if self.channel_metrics[ch]["connection_count"] > 0])
        }


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
    """Modelo para mensajes WebSocket con soporte para sharding de canales."""
    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_user_id: Optional[int] = None
    target_role: Optional[str] = None
    # Canal/tema opcional para routing por suscripción
    topic: Optional[str] = None
    # Nuevos campos para sharding de canales
    channel_name: Optional[str] = None
    channel_type: Optional[ChannelType] = None
    priority_level: int = Field(default=1, ge=1, le=10)
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)


class ConnectionInfo(BaseModel):
    """Información de conexión WebSocket con soporte para sharding de canales."""
    websocket: WebSocket
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connected_at: datetime = Field(default_factory=datetime.now)
    last_ping: datetime = Field(default_factory=datetime.now)
    # Suscripciones a topics (MVP)
    subscriptions: Set[str] = Field(default_factory=set)
    # Información de canal asignada
    assigned_channel: Optional[str] = None
    channel_type: Optional[ChannelType] = None
    user_priority: int = Field(default=1, ge=1, le=10)
    # Métricas de la conexión
    messages_sent: int = 0
    messages_received: int = 0
    last_message_at: Optional[datetime] = None
    
    model_config = {
        "arbitrary_types_allowed": True
    }


class WebSocketManager:
    """
    Manager para conexiones WebSocket del sistema GRUPO_GAD con sharding de canales.
    
    Maneja:
    - Conexiones activas por usuario y rol
    - Distribución de mensajes
    - Heartbeat/keepalive
    - Autorización y seguridad
    - Sharding de canales con hashing consistente
    - Load balancing inteligente
    - Métricas por canal
    """
    
    def __init__(self, redis_url: Optional[str] = None, enable_aggressive_cleanup: bool = True):
        # Conexiones activas: connection_id -> ConnectionInfo
        self.active_connections: Dict[str, ConnectionInfo] = {}
        
        # Mapeos para búsqueda rápida
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.role_connections: Dict[str, Set[str]] = {}  # role -> connection_ids
        
        # Sistema de sharding de canales
        self.channel_router = ChannelRouter()
        self.load_balancer = ChannelLoadBalancer(self.channel_router)
        
        # Métricas de canales
        self.channel_stats: Dict[str, ChannelInfo] = {}
        self._initialize_channel_stats()
        
        # Task para heartbeat
        self._heartbeat_task: Optional[asyncio.Task[Any]] = None
        self._heartbeat_interval: int = 30  # segundos
        # Métricas básicas (reinician por proceso)
        self.total_messages_sent = 0
        self.total_broadcasts = 0
        self.total_send_errors = 0
        self.last_broadcast_at: Optional[datetime] = None
        # Pub/Sub (opcional): se inyecta en runtime
        self._pubsub = None
        
        # Redis URL para canales especializados
        self.redis_url = redis_url
        
        # Sistema de cleanup agresivo
        self.enable_aggressive_cleanup = enable_aggressive_cleanup
        self.cleanup_integration_active = False
        self._cleanup_buffers: Dict[str, Any] = {}  # Buffers registrados para cleanup
        
        ws_logger.info("WebSocketManager con sharding de canales inicializado")
    
    def _initialize_channel_stats(self):
        """Inicializa estadísticas para todos los canales configurados."""
        for channel_type, config in self.channel_router.channel_configs.items():
            for channel_name in config["channels"]:
                self.channel_stats[channel_name] = ChannelInfo(
                    name=channel_name,
                    channel_type=channel_type,
                    user_capacity=config["capacity"],
                    priority_level=config["priority"]
                )
    
    def assign_channel(self, user_id: Optional[int], user_role: Optional[str], 
                      user_priority: int = 1) -> Tuple[str, ChannelType]:
        """
        Asigna un canal óptimo a un usuario usando sharding inteligente.
        
        Args:
            user_id: ID del usuario
            user_role: Rol del usuario
            user_priority: Prioridad del usuario (1-10)
            
        Returns:
            Tuple[str, ChannelType]: Nombre del canal y tipo asignado
        """
        if user_id is None:
            # Asignar a canal general para usuarios anónimos
            default_channel = "ws_broadcast_general_1"
            return default_channel, ChannelType.GENERAL
        
        # Usar router inteligente para determinar canal
        channel_name = self.channel_router.route_user(user_id, user_role, user_priority)
        channel_type = self.channel_router._determine_channel_type(user_role, user_priority)
        
        return channel_name, channel_type

    # --- Gestión de Suscripciones (MVP) ---
    def subscribe(self, connection_id: str, topics: Set[str]) -> None:
        if not topics:
            return
        ci = self.active_connections.get(connection_id)
        if not ci:
            return
        ci.subscriptions.update(t.strip() for t in topics if isinstance(t, str) and t.strip())

    def unsubscribe(self, connection_id: str, topics: Set[str]) -> None:
        if not topics:
            return
        ci = self.active_connections.get(connection_id)
        if not ci:
            return
        for t in list(topics):
            if isinstance(t, str):
                ci.subscriptions.discard(t.strip())

    @staticmethod
    def _should_receive(ci: "ConnectionInfo", topic: Optional[str]) -> bool:
        # Si no hay topic en el mensaje: todos reciben
        if not topic:
            return True
        # Si hay topic, solo conexiones suscritas lo reciben
        return topic in ci.subscriptions
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None, 
                     user_role: Optional[str] = None, user_priority: int = 1) -> str:
        """
        Establece una nueva conexión WebSocket con asignación de canal inteligente.
        
        Args:
            websocket: Conexión WebSocket
            user_id: ID del usuario conectado
            user_role: Rol del usuario
            user_priority: Prioridad del usuario (1-10)
            
        Returns:
            connection_id: ID único de la conexión
        """
        await websocket.accept()
        
        # Asignar canal usando sistema de sharding
        channel_name, channel_type = self.assign_channel(user_id, user_role, user_priority)
        
        connection_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            user_role=user_role,
            assigned_channel=channel_name,
            channel_type=channel_type,
            user_priority=user_priority
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
        
        # Actualizar estadísticas del canal
        self._update_channel_stats(channel_name, 1)
        
        # Registrar métricas de conexión si están disponibles
        if METRICS_ENABLED:
            connection_established(user_id, user_role)
        
        ws_logger.info(
            "Nueva conexión WebSocket establecida con sharding",
            connection_id=connection_id,
            user_id=user_id,
            user_role=user_role,
            assigned_channel=channel_name,
            channel_type=channel_type.value,
            total_connections=len(self.active_connections)
        )
        
        # Enviar ACK de conexión con información de canal
        await self.send_to_connection(
            connection_id,
            WSMessage(
                event_type=EventType.CONNECTION_ACK,
                data={
                    "connection_id": connection_id,
                    "connected_at": connection_info.connected_at.isoformat(),
                    "server_time": datetime.now().isoformat(),
                    "assigned_channel": channel_name,
                    "channel_type": channel_type.value
                },
                channel_name=channel_name,
                channel_type=channel_type
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
        
        # Capturar info antes de eliminar para métricas
        user_id = connection_info.user_id
        user_role = connection_info.user_role
        assigned_channel = connection_info.assigned_channel
        
        # Limpiar mapeos
        if user_id:
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
        
        if user_role:
            if user_role in self.role_connections:
                self.role_connections[user_role].discard(connection_id)
                if not self.role_connections[user_role]:
                    del self.role_connections[user_role]
        
        # Actualizar estadísticas del canal
        if assigned_channel:
            self._update_channel_stats(assigned_channel, -1)
        
        # Remover conexión
        del self.active_connections[connection_id]
        
        # Registrar métricas de desconexión si están disponibles
        if METRICS_ENABLED:
            connection_closed(user_id, user_role)
            # Actualizar conteo de usuarios activos
            update_user_count(len(self.user_connections))
        
        # Detener heartbeat si no hay conexiones
        if not self.active_connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        ws_logger.info(
            "Conexión WebSocket desconectada",
            connection_id=connection_id,
            user_id=user_id,
            assigned_channel=assigned_channel,
            total_connections=len(self.active_connections)
        )
    
    def _update_channel_stats(self, channel_name: str, delta: int):
        """Actualiza las estadísticas de un canal."""
        if channel_name in self.channel_stats:
            channel_info = self.channel_stats[channel_name]
            channel_info.current_load = max(0, channel_info.current_load + delta)
            channel_info.active_connections.discard(channel_name)  # Note: this should be connection_ids
        else:
            ws_logger.warning(f"Canal no encontrado en estadísticas: {channel_name}")
    
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
                # Registrar en métricas Prometheus si están habilitadas
                if METRICS_ENABLED:
                    message_sent(is_broadcast=False)
            
            return True
            
        except Exception as e:
            ws_logger.error(
                f"Error enviando mensaje a conexión {connection_id}: {str(e)}"
            )
            # Desconectar conexión problemática
            await self.disconnect(connection_id)
            self.total_send_errors += 1
            
            # Registrar error en métricas Prometheus
            if METRICS_ENABLED:
                send_error()
                
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
            ci = self.active_connections.get(connection_id)
            if not ci:
                continue
            if self._should_receive(ci, message.topic) and await self.send_to_connection(connection_id, message):
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
            ci = self.active_connections.get(connection_id)
            if not ci:
                continue
            if self._should_receive(ci, message.topic) and await self.send_to_connection(connection_id, message):
                sent_count += 1
        # Actualizar métricas si hubo envíos
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
            if METRICS_ENABLED:
                # Consideramos envío por rol como broadcast para métricas
                message_sent(is_broadcast=True)
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
            ci = self.active_connections.get(connection_id)
            if not ci:
                continue
            if self._should_receive(ci, message.topic) and await self.send_to_connection(connection_id, message):
                sent_count += 1
        # Actualizar métricas si hubo envíos
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
            # Registrar en métricas Prometheus
            if METRICS_ENABLED:
                message_sent(is_broadcast=True)
        # Publicar en pub/sub para otros workers (si está configurado)
        try:
            if self._pubsub is not None and message.event_type != EventType.PING:
                await self._pubsub.publish(message.model_dump(mode='json'))
        except Exception:
            # No afectar envío local por errores de pub/sub
            pass

        return sent_count

    async def broadcast_local_dict(self, message_dict: Dict[str, Any]) -> int:
        """Broadcast local desde un dict (usado por pub/sub) sin republicar.

        Retorna el número de conexiones locales a las que se envió.
        """
        try:
            evt = EventType(message_dict.get("event_type"))
        except Exception:
            return 0
        if evt == EventType.PING:
            # Evitar meter PINGs desde pub/sub
            return 0
        # Normalizar timestamp iso si falta
        if "timestamp" not in message_dict:
            message_dict["timestamp"] = datetime.now().isoformat()

        exclude_connections: Set[str] = set()
        topic = message_dict.get("topic")
        sent_count = 0
        for cid, info in list(self.active_connections.items()):
            if cid in exclude_connections:
                continue
            try:
                if self._should_receive(info, topic):
                    await info.websocket.send_text(json.dumps(message_dict))
                    if evt not in (EventType.CONNECTION_ACK, EventType.PING):
                        self.total_messages_sent += 1
                    sent_count += 1
            except Exception:
                await self.disconnect(cid)
                self.total_send_errors += 1
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
        return sent_count

    def set_pubsub(self, pubsub) -> None:
        """Inyecta el bridge de pub/sub (por ejemplo, Redis)."""
        self._pubsub = pubsub
    
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
                
                # Actualizar métricas Prometheus si están habilitadas
                if METRICS_ENABLED:
                    heartbeat_completed()
                
                ws_logger.debug(
                    f"Heartbeat enviado a {len(self.active_connections)} conexiones"
                )
                
                await asyncio.sleep(self._heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                ws_logger.error(f"Error en heartbeat loop: {str(e)}")
                await asyncio.sleep(5)  # Esperar antes de reintentar
    
    async def broadcast_by_channel(self, channel_name: str, message: WSMessage) -> int:
        """
        Envía un mensaje a todas las conexiones de un canal específico.
        
        Args:
            channel_name: Nombre del canal
            message: Mensaje a enviar
            
        Returns:
            int: Número de conexiones a las que se envió
        """
        connection_ids = [
            cid for cid, info in self.active_connections.items()
            if info.assigned_channel == channel_name
        ]
        
        sent_count = 0
        for connection_id in connection_ids:
            ci = self.active_connections.get(connection_id)
            if not ci:
                continue
            if self._should_receive(ci, message.topic) and await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
            if METRICS_ENABLED:
                message_sent(is_broadcast=True)
        
        return sent_count
    
    async def broadcast_by_channel_type(self, channel_type: ChannelType, message: WSMessage) -> int:
        """
        Envía un mensaje a todas las conexiones de un tipo de canal.
        
        Args:
            channel_type: Tipo de canal
            message: Mensaje a enviar
            
        Returns:
            int: Número de conexiones a las que se envió
        """
        connection_ids = [
            cid for cid, info in self.active_connections.items()
            if info.channel_type == channel_type
        ]
        
        sent_count = 0
        for connection_id in connection_ids:
            ci = self.active_connections.get(connection_id)
            if not ci:
                continue
            if self._should_receive(ci, message.topic) and await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        if sent_count:
            self.total_broadcasts += 1
            self.last_broadcast_at = datetime.now()
            if METRICS_ENABLED:
                message_sent(is_broadcast=True)
        
        return sent_count
    
    def get_channel_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene métricas detalladas de todos los canales.
        
        Returns:
            Dict con métricas de canales
        """
        metrics = {}
        for channel_name, channel_info in self.channel_stats.items():
            # Contar conexiones activas en este canal
            active_connections = [
                cid for cid, info in self.active_connections.items()
                if info.assigned_channel == channel_name
            ]
            
            metrics[channel_name] = {
                "channel_type": channel_info.channel_type.value,
                "user_capacity": channel_info.user_capacity,
                "current_load": len(active_connections),
                "utilization_percent": channel_info.utilization,
                "is_overloaded": channel_info.is_overloaded,
                "is_underutilized": channel_info.is_underutilized,
                "priority_level": channel_info.priority_level,
                "active_connections": len(active_connections)
            }
        
        return metrics
    
    def get_sharding_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del sistema de sharding.
        
        Returns:
            Dict con estadísticas de sharding
        """
        # Contar conexiones por tipo de canal
        channel_type_counts = {}
        for channel_type in ChannelType:
            channel_type_counts[channel_type.value] = 0
        
        for info in self.active_connections.values():
            if info.channel_type:
                channel_type_counts[info.channel_type.value] += 1
        
        return {
            "total_connections": len(self.active_connections),
            "connections_by_channel_type": channel_type_counts,
            "channel_routing": self.channel_router.get_channel_stats(),
            "load_balancing": self.load_balancer.get_load_balancing_stats(),
            "channel_metrics": self.get_channel_metrics()
        }
    
    def add_dynamic_channel(self, channel_type: ChannelType, channel_name: str, 
                          capacity: int = 1000, priority: int = 1):
        """
        Añade dinámicamente un nuevo canal al sistema.
        
        Args:
            channel_type: Tipo de canal
            channel_name: Nombre del canal
            capacity: Capacidad de usuarios
            priority: Nivel de prioridad (1-10)
        """
        # Añadir al router
        self.channel_router.add_channel(channel_type, channel_name, capacity)
        
        # Añadir a estadísticas
        self.channel_stats[channel_name] = ChannelInfo(
            name=channel_name,
            channel_type=channel_type,
            user_capacity=capacity,
            priority_level=priority
        )
        
        ws_logger.info(
            "Canal dinámico añadido",
            channel_name=channel_name,
            channel_type=channel_type.value,
            capacity=capacity,
            priority=priority
        )
    
    def optimize_channels(self):
        """Optimiza la distribución de canales basada en la carga actual."""
        # Implementar lógica de optimización aquí
        # Por ejemplo, mover conexiones de canales sobrecargados a subutilizados
        pass
    
    def get_channel_utilization_matrix(self) -> Dict[str, Dict[str, float]]:
        """Obtiene matriz de utilización de canales para análisis."""
        matrix = {}
        for channel_name, channel_info in self.channel_stats.items():
            connections = [
                cid for cid, info in self.active_connections.items()
                if info.assigned_channel == channel_name
            ]
            utilization = (len(connections) / channel_info.user_capacity) * 100
            matrix[channel_name] = {
                "utilization": utilization,
                "connection_count": len(connections),
                "capacity": channel_info.user_capacity
            }
        return matrix
    
    # --- INTEGRACIÓN CON SISTEMA DE CLEANUP AGRESIVO --- #
    
    def register_cleanup_buffer(self, buffer_id: str, buffer_data: Any):
        """
        Registra un buffer para tracking automático de cleanup.
        
        Args:
            buffer_id: ID único del buffer
            buffer_data: Datos del buffer
        """
        if self.enable_aggressive_cleanup and self.cleanup_integration_active:
            try:
                from src.core.aggressive_cleanup import track_buffer
                track_buffer(buffer_id, buffer_data)
                ws_logger.debug(f"Buffer registrado para cleanup: {buffer_id}")
            except ImportError:
                # Graceful fallback si el módulo de cleanup no está disponible
                self._cleanup_buffers[buffer_id] = {
                    'data': buffer_data,
                    'registered_at': datetime.now()
                }
    
    def update_buffer_access(self, buffer_id: str):
        """
        Actualiza el tracking de un buffer existente.
        
        Args:
            buffer_id: ID del buffer
        """
        if self.enable_aggressive_cleanup and self.cleanup_integration_active:
            try:
                from src.core.aggressive_cleanup import update_buffer_tracking
                update_buffer_tracking(buffer_id)
            except ImportError:
                # Actualizar registro local si el módulo no está disponible
                if buffer_id in self._cleanup_buffers:
                    self._cleanup_buffers[buffer_id]['last_access'] = datetime.now()
    
    async def activate_cleanup_integration(self):
        """Activa la integración con el sistema de cleanup agresivo."""
        if not self.enable_aggressive_cleanup:
            ws_logger.info("Cleanup agresivo deshabilitado en configuración")
            return
        
        try:
            # Importar el sistema de cleanup
            from src.core.aggressive_cleanup import aggressive_cleanup, initialize_aggressive_cleanup
            
            # Inicializar el sistema de cleanup
            await initialize_aggressive_cleanup()
            
            # Registrar callbacks de emergencia
            aggressive_cleanup.register_emergency_callback(self._emergency_cleanup_callback)
            
            self.cleanup_integration_active = True
            
            ws_logger.info("Integración con cleanup agresivo activada")
            
        except ImportError as e:
            ws_logger.warning(f"No se pudo importar el sistema de cleanup: {e}")
            self.cleanup_integration_active = False
        except Exception as e:
            ws_logger.error(f"Error activando integración de cleanup: {e}")
            self.cleanup_integration_active = False
    
    async def deactivate_cleanup_integration(self):
        """Desactiva la integración con el sistema de cleanup agresivo."""
        if not self.cleanup_integration_active:
            return
        
        try:
            from src.core.aggressive_cleanup import shutdown_aggressive_cleanup
            await shutdown_aggressive_cleanup()
            self.cleanup_integration_active = False
            
            ws_logger.info("Integración con cleanup agresivo desactivada")
            
        except Exception as e:
            ws_logger.error(f"Error desactivando integración de cleanup: {e}")
    
    async def _emergency_cleanup_callback(self):
        """Callback ejecutado en cleanup de emergencia."""
        ws_logger.warning("Ejecutando callback de cleanup de emergencia en WebSocketManager")
        
        # Forzar limpieza de conexiones problemáticas
        disconnected_count = 0
        current_time = datetime.now()
        
        # Identificar y desconectar conexiones problemáticas
        problematic_connections = []
        for connection_id, connection_info in list(self.active_connections.items()):
            try:
                # Verificar si la conexión está realmente activa
                if hasattr(connection_info, 'websocket'):
                    # Intentar verificar estado de la conexión
                    pass  # WebSocket no tiene método directo para verificar estado
                
                # Desconectar conexiones muy antiguas sin actividad
                connected_duration = (current_time - connection_info.connected_at).total_seconds()
                if connected_duration > 3600:  # 1 hora
                    problematic_connections.append(connection_id)
                    
            except Exception:
                # Cualquier error indica problema con la conexión
                problematic_connections.append(connection_id)
        
        # Desconectar conexiones problemáticas
        for connection_id in problematic_connections:
            try:
                await self.disconnect(connection_id)
                disconnected_count += 1
            except Exception as e:
                ws_logger.error(f"Error desconectando conexión problemática {connection_id}: {e}")
        
        # Limpiar buffers registrados
        self._cleanup_buffers.clear()
        
        ws_logger.info(
            f"Cleanup de emergencia completado en WebSocketManager",
            disconnected_connections=disconnected_count,
            cleared_buffers=len(self._cleanup_buffers)
        )
    
    async def trigger_emergency_cleanup(self, reason: str = "Manual trigger"):
        """
        Dispara un cleanup de emergencia manual.
        
        Args:
            reason: Razón del cleanup de emergencia
        """
        if not self.cleanup_integration_active:
            ws_logger.warning("No se puede ejecutar cleanup: integración no activa")
            return
        
        try:
            from src.core.aggressive_cleanup import emergency_cleanup
            await emergency_cleanup(reason)
            
            ws_logger.info(f"Cleanup de emergencia activado: {reason}")
            
        except Exception as e:
            ws_logger.error(f"Error ejecutando cleanup de emergencia: {e}")
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de cleanup.
        
        Returns:
            Dict con estadísticas de cleanup
        """
        stats = {
            "cleanup_enabled": self.enable_aggressive_cleanup,
            "integration_active": self.cleanup_integration_active,
            "registered_buffers": len(self._cleanup_buffers),
        }
        
        if self.cleanup_integration_active:
            try:
                from src.core.aggressive_cleanup import aggressive_cleanup
                cleanup_stats = aggressive_cleanup.get_cleanup_stats()
                stats.update(cleanup_stats)
            except ImportError:
                stats["cleanup_error"] = "Módulo de cleanup no disponible"
        
        return stats
    
    def get_connection_health_report(self) -> Dict[str, Any]:
        """
        Genera un reporte de salud de las conexiones.
        
        Returns:
            Dict con reporte de salud
        """
        current_time = datetime.now()
        
        # Analizar conexiones
        connection_ages = []
        inactive_connections = []
        healthy_connections = 0
        
        for connection_id, connection_info in self.active_connections.items():
            connection_age = (current_time - connection_info.connected_at).total_seconds()
            connection_ages.append(connection_age)
            
            # Verificar actividad
            last_activity = getattr(connection_info, 'last_ping', connection_info.connected_at)
            inactive_time = (current_time - last_activity).total_seconds()
            
            if inactive_time > 300:  # 5 minutos
                inactive_connections.append({
                    "connection_id": connection_id,
                    "inactive_seconds": inactive_time,
                    "connected_at": connection_info.connected_at.isoformat()
                })
            else:
                healthy_connections += 1
        
        # Calcular estadísticas
        avg_connection_age = sum(connection_ages) / len(connection_ages) if connection_ages else 0
        max_connection_age = max(connection_ages) if connection_ages else 0
        
        return {
            "total_connections": len(self.active_connections),
            "healthy_connections": healthy_connections,
            "inactive_connections": len(inactive_connections),
            "inactive_connection_details": inactive_connections,
            "avg_connection_age_seconds": avg_connection_age,
            "max_connection_age_seconds": max_connection_age,
            "health_score": (healthy_connections / len(self.active_connections)) * 100 if self.active_connections else 100,
            "cleanup_integration_active": self.cleanup_integration_active,
            "recommendations": self._get_cleanup_recommendations(healthy_connections, len(inactive_connections))
        }
    
    def _get_cleanup_recommendations(self, healthy: int, inactive: int) -> List[str]:
        """Genera recomendaciones basadas en el estado de las conexiones."""
        recommendations = []
        
        total = healthy + inactive
        if total == 0:
            return recommendations
        
        inactive_ratio = inactive / total
        
        if inactive_ratio > 0.3:
            recommendations.append("Alto porcentaje de conexiones inactivas - ejecutar cleanup agresivo")
        
        if inactive > 50:
            recommendations.append("Muchas conexiones inactivas - verificar configuración de timeout")
        
        if healthy > 500:
            recommendations.append("Muchas conexiones activas - considerar escalamiento horizontal")
        
        if inactive_ratio < 0.1:
            recommendations.append("Sistema saludable - cleanup normal es suficiente")
        
        return recommendations
    
    async def get_detailed_cleanup_report(self) -> Dict[str, Any]:
        """
        Genera un reporte detallado del estado de cleanup.
        
        Returns:
            Dict con reporte completo
        """
        base_report = self.get_connection_health_report()
        cleanup_stats = self.get_cleanup_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "connection_health": base_report,
            "cleanup_system": cleanup_stats,
            "recommendations": {
                "immediate_actions": base_report.get("recommendations", []),
                "system_optimization": self._get_system_optimization_suggestions()
            }
        }
    
    def _get_system_optimization_suggestions(self) -> List[str]:
        """Genera sugerencias de optimización del sistema."""
        suggestions = []
        
        # Análisis basado en estadísticas actuales
        total_connections = len(self.active_connections)
        
        if total_connections > 800:
            suggestions.append("Considerar añadir más canales de WebSocket para distribuir carga")
        
        if total_connections < 100:
            suggestions.append("Sistema subutilizado - reducir recursos si es posible")
        
        # Análisis de canales
        overloaded_channels = [
            name for name, info in self.channel_stats.items()
            if info.is_overloaded
        ]
        
        if overloaded_channels:
            suggestions.append(f"Canales sobrecargados detectados: {', '.join(overloaded_channels)}")
        
        # Análisis de eficiencia
        if self.total_send_errors > 0:
            error_rate = (self.total_send_errors / max(self.total_messages_sent, 1)) * 100
            if error_rate > 5:
                suggestions.append(f"Alta tasa de errores ({error_rate:.2f}%) - revisar estabilidad de conexiones")
        
        return suggestions

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas de conexiones WebSocket y sharding.
        
        Returns:
            Dict con estadísticas completas
        """
        base_stats = {
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
        
        # Añadir estadísticas de sharding
        base_stats["sharding"] = self.get_sharding_stats()
        
        # Añadir estadísticas de cleanup si está habilitado
        if self.enable_aggressive_cleanup:
            try:
                base_stats["cleanup"] = self.get_cleanup_stats()
                base_stats["connection_health"] = self.get_connection_health_report()
            except Exception as e:
                base_stats["cleanup_error"] = str(e)
        
        return base_stats


# Instancia global del manager con cleanup agresivo habilitado por defecto
websocket_manager = WebSocketManager(enable_aggressive_cleanup=True)


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


# --- FUNCIONES DE NOTIFICACIÓN PARA CLEANUP --- #

async def notify_cleanup_status(status_data: Dict[str, Any]):
    """Notifica el estado del sistema de cleanup a administradores."""
    message = WSMessage(
        event_type=EventType.SYSTEM_STATUS,
        data={
            "type": "cleanup_status",
            "cleanup_data": status_data,
            "timestamp": datetime.now().isoformat()
        },
        target_role="ADMIN"
    )
    
    await websocket_manager.broadcast(message)


async def notify_emergency_cleanup(reason: str, severity: str = "critical"):
    """Notifica un cleanup de emergencia a todos los administradores."""
    message = WSMessage(
        event_type=EventType.ALERT,
        data={
            "title": "Cleanup de Emergencia Activado",
            "content": f"Se ha activado un cleanup de emergencia: {reason}",
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "action_required": True
        },
        target_role="ADMIN"
    )
    
    await websocket_manager.broadcast(message)


async def notify_cleanup_metrics(metrics_data: Dict[str, Any]):
    """Notifica métricas de cleanup a usuarios autorizados."""
    message = WSMessage(
        event_type=EventType.METRICS_UPDATE,
        data={
            "type": "cleanup_metrics",
            "metrics": metrics_data,
            "timestamp": datetime.now().isoformat()
        },
        target_role="ADMIN"
    )
    
    await websocket_manager.broadcast(message)


# --- FUNCIONES DE INICIALIZACIÓN Y CONTROL --- #

async def initialize_websocket_system_with_cleanup():
    """
    Inicializa el sistema WebSocket con cleanup agresivo integrado.
    
    Returns:
        bool: True si se inicializó correctamente
    """
    try:
        # Activar integración de cleanup
        await websocket_manager.activate_cleanup_integration()
        
        ws_logger.info("Sistema WebSocket con cleanup agresivo inicializado correctamente")
        return True
        
    except Exception as e:
        ws_logger.error(f"Error inicializando sistema WebSocket con cleanup: {str(e)}")
        return False


async def shutdown_websocket_system():
    """Detiene el sistema WebSocket y cleanup de forma segura."""
    try:
        # Desactivar integración de cleanup
        await websocket_manager.deactivate_cleanup_integration()
        
        ws_logger.info("Sistema WebSocket detenido correctamente")
        return True
        
    except Exception as e:
        ws_logger.error(f"Error deteniendo sistema WebSocket: {str(e)}")
        return False


async def force_emergency_cleanup(reason: str = "Manual trigger"):
    """
    Fuerza un cleanup de emergencia manual.
    
    Args:
        reason: Razón del cleanup de emergencia
    
    Returns:
        bool: True si se ejecutó correctamente
    """
    try:
        await websocket_manager.trigger_emergency_cleanup(reason)
        
        # Notificar a administradores
        await notify_emergency_cleanup(reason, "warning")
        
        ws_logger.info(f"Cleanup de emergencia forzado: {reason}")
        return True
        
    except Exception as e:
        ws_logger.error(f"Error ejecutando cleanup de emergencia: {str(e)}")
        return False


# --- FUNCIONES DE UTILIDAD PARA BUFFERS --- #

def register_websocket_buffer(buffer_id: str, buffer_data: Any):
    """
    Registra un buffer del sistema WebSocket para tracking de cleanup.
    
    Args:
        buffer_id: ID único del buffer
        buffer_data: Datos del buffer
    """
    websocket_manager.register_cleanup_buffer(buffer_id, buffer_data)


def update_websocket_buffer_access(buffer_id: str):
    """
    Actualiza el acceso a un buffer WebSocket registrado.
    
    Args:
        buffer_id: ID del buffer
    """
    websocket_manager.update_buffer_access(buffer_id)


# --- FUNCIONES DE REPORTE Y MÉTRICAS --- #

async def get_websocket_cleanup_report() -> Dict[str, Any]:
    """
    Obtiene un reporte completo del estado de WebSockets y cleanup.
    
    Returns:
        Dict con reporte completo
    """
    return await websocket_manager.get_detailed_cleanup_report()


def get_websocket_health_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de salud del sistema WebSocket.
    
    Returns:
        Dict con resumen de salud
    """
    health = websocket_manager.get_connection_health_report()
    cleanup_stats = websocket_manager.get_cleanup_stats()
    
    return {
        "overall_health": "healthy" if health.get("health_score", 0) > 80 else "warning",
        "health_score": health.get("health_score", 100),
        "total_connections": health.get("total_connections", 0),
        "cleanup_active": cleanup_stats.get("integration_active", False),
        "recommendations": health.get("recommendations", [])
    }