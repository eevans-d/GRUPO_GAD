# -*- coding: utf-8 -*-
"""
Métricas Prometheus para subsistema WebSocket de GRUPO_GAD.

Este módulo implementa la instrumentación Prometheus para el subsistema WebSocket
según el diseño especificado en PROMETHEUS_METRICAS_DISENO.md.

Las métricas se exponen a través del endpoint /metrics en el API principal.
"""

from typing import Dict, Optional, Any, List
import time
import threading
from collections import defaultdict, deque
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry

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

# --- MÉTRICAS ESPECÍFICAS WEBSOCKET (Fase 1) ---

# Métricas básicas de conexiones
ws_connections_active = Gauge(
    f"{METRIC_PREFIX}ws_connections_active",
    "Número actual de conexiones WebSocket activas",
    [ENV_LABEL, "channel_type", "user_role"]
)

ws_connections_total = Counter(
    f"{METRIC_PREFIX}ws_connections_total",
    "Total histórico de conexiones WebSocket",
    [ENV_LABEL, "channel_type", "user_role", "connection_outcome"]
)

ws_messages_sent = Counter(
    f"{METRIC_PREFIX}ws_messages_sent_total",
    "Total de mensajes WebSocket enviados",
    [ENV_LABEL, "message_type", "channel_type"]
)

ws_messages_received = Counter(
    f"{METRIC_PREFIX}ws_messages_received_total",
    "Total de mensajes WebSocket recibidos",
    [ENV_LABEL, "message_type", "channel_type"]
)

ws_message_duration = Histogram(
    f"{METRIC_PREFIX}ws_message_duration_seconds",
    "Duración de procesamiento de mensajes WebSocket",
    [ENV_LABEL, "message_type", "channel_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

ws_connection_duration = Histogram(
    f"{METRIC_PREFIX}ws_connection_duration_seconds",
    "Duración de conexiones WebSocket",
    [ENV_LABEL, "channel_type", "user_role"],
    buckets=(10, 60, 300, 600, 1800, 3600, 7200, 14400)
)

ws_errors_total = Counter(
    f"{METRIC_PREFIX}ws_errors_total",
    "Total de errores WebSocket por tipo",
    [ENV_LABEL, "error_type", "channel_type", "severity"]
)

# --- MÉTRICAS DE CANALES ---

ws_channel_messages = Counter(
    f"{METRIC_PREFIX}ws_channel_messages_total",
    "Total de mensajes por canal",
    [ENV_LABEL, "channel_name", "channel_type", "message_direction"]
)

ws_channel_subscribers = Gauge(
    f"{METRIC_PREFIX}ws_channel_subscribers",
    "Número de suscriptores por canal",
    [ENV_LABEL, "channel_name", "channel_type"]
)

ws_channel_utilization = Gauge(
    f"{METRIC_PREFIX}ws_channel_utilization_percent",
    "Porcentaje de utilización del canal",
    [ENV_LABEL, "channel_name", "channel_type"]
)

# --- MÉTRICAS DE RENDIMIENTO ---

ws_throughput_per_second = Gauge(
    f"{METRIC_PREFIX}ws_throughput_per_second",
    "Throughput de mensajes WebSocket por segundo",
    [ENV_LABEL, "channel_type"]
)

ws_latency_p50 = Gauge(
    f"{METRIC_PREFIX}ws_latency_p50_seconds",
    "Latencia P50 de mensajes WebSocket",
    [ENV_LABEL, "channel_type"]
)

ws_latency_p95 = Gauge(
    f"{METRIC_PREFIX}ws_latency_p95_seconds",
    "Latencia P95 de mensajes WebSocket",
    [ENV_LABEL, "channel_type"]
)

ws_latency_p99 = Gauge(
    f"{METRIC_PREFIX}ws_latency_p99_seconds",
    "Latencia P99 de mensajes WebSocket",
    [ENV_LABEL, "channel_type"]
)

# --- MÉTRICAS DE CIRCUIT BREAKER ---

ws_circuit_breaker_state = Gauge(
    f"{METRIC_PREFIX}ws_circuit_breaker_state",
    "Estado del circuit breaker (0=closed, 1=open, 2=half-open)",
    [ENV_LABEL, "channel_name", "breaker_type"]
)

ws_circuit_breaker_failures = Counter(
    f"{METRIC_PREFIX}ws_circuit_breaker_failures_total",
    "Total de fallos del circuit breaker",
    [ENV_LABEL, "channel_name", "breaker_type", "failure_type"]
)

# --- MÉTRICAS AGREGADAS Y LEGACY (compatibilidad) ---

# Para alertas existentes - mantener compatibilidad
websocket_connections_active = ws_connections_active
websocket_broadcast_errors_total = ws_errors_total

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

# --- GESTIÓN DE MÉTRICAS AVANZADAS ---

class WebSocketMetricsCollector:
    """Recolector avanzado de métricas WebSocket con cálculos en tiempo real."""
    
    def __init__(self):
        self.latency_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.throughput_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))  # 1 minuto
        self._lock = threading.Lock()
        
    def record_latency(self, channel_type: str, latency_seconds: float):
        """Registra latencia para cálculos posteriores."""
        with self._lock:
            self.latency_data[channel_type].append(latency_seconds)
            
    def record_throughput(self, channel_type: str, message_count: int):
        """Registra throughput para cálculos posteriores."""
        with self._lock:
            self.throughput_data[channel_type].append(message_count)
            
    def calculate_percentiles(self, channel_type: str) -> Dict[str, float]:
        """Calcula percentiles de latencia."""
        with self._lock:
            data = sorted(self.latency_data[channel_type])
            if not data:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
                
            n = len(data)
            return {
                "p50": data[int(n * 0.50)],
                "p95": data[int(n * 0.95)],
                "p99": data[int(n * 0.99)]
            }
            
    def calculate_throughput(self, channel_type: str) -> float:
        """Calcula throughput promedio por segundo."""
        with self._lock:
            data = list(self.throughput_data[channel_type])
            if len(data) < 2:
                return 0.0
            return sum(data) / len(data)

# Instancia global del recolector
metrics_collector = WebSocketMetricsCollector()

# --- Funciones de instrumentación ---

def initialize_metrics(registry: Optional[CollectorRegistry] = None) -> None:
    """
    Inicializa las métricas con valores por defecto.
    Debe llamarse al inicio de la aplicación.
    
    Args:
        registry: Registry opcional de Prometheus
    """
    # Establecer valores iniciales en 0
    ws_connections_active.labels(ENVIRONMENT, "unknown", "unknown").set(0)
    user_active.labels(ENVIRONMENT).set(0)
    heartbeat_last_timestamp.labels(ENVIRONMENT).set(time.time())
    
    # Inicializar métricas de canales
    for channel_type in ["general", "admin", "users", "priority"]:
        ws_throughput_per_second.labels(ENVIRONMENT, channel_type).set(0.0)
        ws_latency_p50.labels(ENVIRONMENT, channel_type).set(0.0)
        ws_latency_p95.labels(ENVIRONMENT, channel_type).set(0.0)
        ws_latency_p99.labels(ENVIRONMENT, channel_type).set(0.0)
    
    metrics_logger.info("Métricas WebSocket Prometheus inicializadas")
    
    if registry:
        metrics_logger.info(f"Métricas registradas en registry: {registry}")


def connection_established(user_id: Optional[int] = None, user_role: Optional[str] = None, 
                         channel_type: str = "general", channel_name: str = "default") -> str:
    """
    Registra una nueva conexión WebSocket establecida.
    
    Args:
        user_id: ID del usuario (opcional)
        user_role: Rol del usuario (opcional)
        channel_type: Tipo de canal asignado
        channel_name: Nombre del canal específico
        
    Returns:
        str: ID de conexión generado para tracking
    """
    import uuid
    connection_id = str(uuid.uuid4())
    
    # Métricas básicas
    ws_connections_active.labels(ENVIRONMENT, channel_type, user_role or "unknown").inc()
    ws_connections_total.labels(ENVIRONMENT, channel_type, user_role or "unknown", "established").inc()
    
    # Métricas de canal
    ws_channel_subscribers.labels(ENVIRONMENT, channel_name, channel_type).inc()
    
    # Métricas legacy para compatibilidad
    active_connections.labels(ENVIRONMENT).inc()
    connections_total.labels(ENVIRONMENT).inc()
    
    # Si tenemos información de rol, actualizar métricas por rol
    if user_role:
        role_connections.labels(ENVIRONMENT, user_role).inc()
        
    return connection_id


def connection_closed(user_id: Optional[int] = None, user_role: Optional[str] = None,
                       connection_duration: Optional[float] = None,
                       channel_type: str = "general", 
                       channel_name: str = "default") -> None:
    """
    Registra una conexión WebSocket cerrada.
    
    Args:
        user_id: ID del usuario (opcional)
        user_role: Rol del usuario (opcional)
        connection_duration: Duración de la conexión en segundos
        channel_type: Tipo de canal
        channel_name: Nombre del canal específico
    """
    # Métricas básicas
    ws_connections_active.labels(ENVIRONMENT, channel_type, user_role or "unknown").dec()
    ws_connections_total.labels(ENVIRONMENT, channel_type, user_role or "unknown", "closed").inc()
    
    # Métricas de duración
    if connection_duration:
        ws_connection_duration.labels(ENVIRONMENT, channel_type, user_role or "unknown").observe(connection_duration)
    
    # Métricas de canal
    ws_channel_subscribers.labels(ENVIRONMENT, channel_name, channel_type).dec()
    
    # Métricas legacy
    active_connections.labels(ENVIRONMENT).dec()
    
    # Si tenemos información de rol, actualizar métricas por rol
    if user_role:
        role_connections.labels(ENVIRONMENT, user_role).dec()


def message_sent(is_broadcast: bool = False, message_type: str = "unknown",
                  channel_type: str = "general", channel_name: str = "default",
                  duration: Optional[float] = None) -> None:
    """
    Registra un mensaje WebSocket enviado.
    
    Args:
        is_broadcast: Si el mensaje fue un broadcast
        message_type: Tipo de mensaje (task_update, notification, etc.)
        channel_type: Tipo de canal
        channel_name: Nombre del canal específico
        duration: Duración de procesamiento del mensaje
    """
    # Métricas específicas WebSocket
    ws_messages_sent.labels(ENVIRONMENT, message_type, channel_type).inc()
    ws_channel_messages.labels(ENVIRONMENT, channel_name, channel_type, "sent").inc()
    
    # Métricas de rendimiento
    if duration:
        ws_message_duration.labels(ENVIRONMENT, message_type, channel_type).observe(duration)
        metrics_collector.record_latency(channel_type, duration)
    
    # Actualizar throughput
    metrics_collector.record_throughput(channel_type, 1)
    current_throughput = metrics_collector.calculate_throughput(channel_type)
    ws_throughput_per_second.labels(ENVIRONMENT, channel_type).set(current_throughput)
    
    # Métricas legacy
    messages_sent_total.labels(ENVIRONMENT).inc()
    
    if is_broadcast:
        broadcasts_total.labels(ENVIRONMENT).inc()


def send_error(error_type: str = "send_failure", channel_type: str = "general",
                 channel_name: str = "default", severity: str = "warning") -> None:
    """
    Registra un error al enviar un mensaje WebSocket.
    
    Args:
        error_type: Tipo de error (send_failure, timeout, connection_lost, etc.)
        channel_type: Tipo de canal donde ocurrió el error
        channel_name: Nombre del canal específico
        severity: Severidad del error (warning, error, critical)
    """
    # Métricas específicas WebSocket
    ws_errors_total.labels(ENVIRONMENT, error_type, channel_type, severity).inc()
    
    # Métricas de circuit breaker si es error crítico
    if severity in ["error", "critical"]:
        ws_circuit_breaker_failures.labels(ENVIRONMENT, channel_name, "message_breaker", error_type).inc()
    
    # Métricas legacy
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