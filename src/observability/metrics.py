# -*- coding: utf-8 -*-
"""
Métricas Prometheus para subsistema WebSocket de GRUPO_GAD.

Este módulo implementa la instrumentación Prometheus para el subsistema WebSocket
según el diseño especificado en PROMETHEUS_METRICAS_DISENO.md.

Las métricas se exponen a través del endpoint /metrics en el API principal.
"""

from typing import Dict, Optional, Any
import time
from prometheus_client import Counter, Gauge, Histogram

from src.core.logging import get_logger

# Logger para métricas
metrics_logger = get_logger("observability.metrics")

# Prefijo para todas las métricas
METRIC_PREFIX = "ggrt_"

# Label común para distinguir entornos
ENV_LABEL = "env"

# Obtener entorno (development, production, etc.)
try:
    from config.settings import settings
    ENVIRONMENT = getattr(settings, "ENVIRONMENT", "development")
except (ImportError, AttributeError):
    ENVIRONMENT = "development"
    metrics_logger.warning("No se pudo determinar el entorno, usando 'development' por defecto")

# --- Métricas básicas (Fase 1) ---

# Conexiones activas
active_connections = Gauge(
    f"{METRIC_PREFIX}active_connections",
    "Número actual de conexiones WebSocket activas",
    [ENV_LABEL]
)

# Total de conexiones históricas
connections_total = Counter(
    f"{METRIC_PREFIX}connections_total",
    "Total histórico de conexiones WebSocket aceptadas",
    [ENV_LABEL]
)

# Total de mensajes enviados
messages_sent_total = Counter(
    f"{METRIC_PREFIX}messages_sent_total",
    "Total de mensajes WebSocket enviados (unicast + broadcast)",
    [ENV_LABEL]
)

# Total de broadcasts realizados
broadcasts_total = Counter(
    f"{METRIC_PREFIX}broadcasts_total",
    "Total de eventos broadcast realizados",
    [ENV_LABEL]
)

# Total de errores al enviar mensajes
send_errors_total = Counter(
    f"{METRIC_PREFIX}send_errors_total",
    "Total de errores al enviar mensajes WebSocket",
    [ENV_LABEL]
)

# Timestamp del último ciclo heartbeat completado
heartbeat_last_timestamp = Gauge(
    f"{METRIC_PREFIX}heartbeat_last_timestamp",
    "Timestamp (segundos desde epoch) del último ciclo heartbeat completado",
    [ENV_LABEL]
)

# --- Métricas opcionales (Fase 2) ---

# Conexiones por rol
role_connections = Gauge(
    f"{METRIC_PREFIX}role_connections",
    "Conexiones WebSocket activas por rol",
    [ENV_LABEL, "role"]
)

# Usuarios activos totales
user_active = Gauge(
    f"{METRIC_PREFIX}user_active",
    "Cantidad de usuarios únicos con al menos una conexión activa",
    [ENV_LABEL]
)

# Histograma de latencia de mensajes (para futuro PING/PONG)
message_latency = Histogram(
    f"{METRIC_PREFIX}message_latency_seconds",
    "Latencia de mensajes WebSocket (segundos)",
    [ENV_LABEL],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# --- Funciones de instrumentación ---

def initialize_metrics() -> None:
    """
    Inicializa las métricas con valores por defecto.
    Debe llamarse al inicio de la aplicación.
    """
    # Establecer valores iniciales en 0
    active_connections.labels(ENVIRONMENT).set(0)
    user_active.labels(ENVIRONMENT).set(0)
    heartbeat_last_timestamp.labels(ENVIRONMENT).set(time.time())
    
    metrics_logger.info("Métricas Prometheus inicializadas")


def connection_established(user_id: Optional[int] = None, user_role: Optional[str] = None) -> None:
    """
    Registra una nueva conexión WebSocket establecida.
    
    Args:
        user_id: ID del usuario (opcional)
        user_role: Rol del usuario (opcional)
    """
    active_connections.labels(ENVIRONMENT).inc()
    connections_total.labels(ENVIRONMENT).inc()
    
    # Si tenemos información de rol, actualizar métricas por rol
    if user_role:
        role_connections.labels(ENVIRONMENT, user_role).inc()


def connection_closed(user_id: Optional[int] = None, user_role: Optional[str] = None) -> None:
    """
    Registra una conexión WebSocket cerrada.
    
    Args:
        user_id: ID del usuario (opcional)
        user_role: Rol del usuario (opcional)
    """
    active_connections.labels(ENVIRONMENT).dec()
    
    # Si tenemos información de rol, actualizar métricas por rol
    if user_role:
        role_connections.labels(ENVIRONMENT, user_role).dec()


def message_sent(is_broadcast: bool = False) -> None:
    """
    Registra un mensaje WebSocket enviado.
    
    Args:
        is_broadcast: Si el mensaje fue un broadcast
    """
    messages_sent_total.labels(ENVIRONMENT).inc()
    
    if is_broadcast:
        broadcasts_total.labels(ENVIRONMENT).inc()


def send_error() -> None:
    """
    Registra un error al enviar un mensaje WebSocket.
    """
    send_errors_total.labels(ENVIRONMENT).inc()


def heartbeat_completed() -> None:
    """
    Registra la finalización de un ciclo heartbeat.
    """
    heartbeat_last_timestamp.labels(ENVIRONMENT).set(time.time())


def update_user_count(active_users_count: int) -> None:
    """
    Actualiza el contador de usuarios únicos activos.
    
    Args:
        active_users_count: Número de usuarios únicos con conexiones activas
    """
    user_active.labels(ENVIRONMENT).set(active_users_count)


def record_message_latency(latency_seconds: float) -> None:
    """
    Registra la latencia de un mensaje (para futuras mediciones PING/PONG).
    
    Args:
        latency_seconds: Latencia en segundos
    """
    message_latency.labels(ENVIRONMENT).observe(latency_seconds)


def update_all_metrics_from_manager(stats: Dict[str, Any]) -> None:
    """
    Actualiza todas las métricas desde los stats del WebSocketManager.
    
    Args:
        stats: Estadísticas del WebSocketManager
    """
    # Actualizar métricas básicas desde los stats
    active_connections.labels(ENVIRONMENT).set(stats.get('active_connections', 0))
    
    # Si hay información de usuarios activos
    unique_users = stats.get('unique_users', 0)
    if unique_users > 0:
        user_active.labels(ENVIRONMENT).set(unique_users)
    
    # Actualizar timestamp de último heartbeat si está disponible
    last_heartbeat = stats.get('last_heartbeat_time')
    if last_heartbeat:
        heartbeat_last_timestamp.labels(ENVIRONMENT).set(last_heartbeat)
    
    # Actualizar métricas por rol si están disponibles
    roles_data = stats.get('roles', {})
    for role, count in roles_data.items():
        role_connections.labels(ENVIRONMENT, role).set(count)