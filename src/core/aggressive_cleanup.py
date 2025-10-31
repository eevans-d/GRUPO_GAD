# -*- coding: utf-8 -*-
"""
Sistema Aggresivo de Cleanup de Conexiones Inactivas para GRUPO_GAD.

Proporciona:
- Cleanup dinámico de conexiones WebSocket inactivas
- Limpieza automática de canales Redis vacíos
- Optimización de memoria de buffers no utilizados
- Recolección de basura periódica optimizada
- Recovery automático de health checks
- Métricas detalladas de cleanup
- Triggers de emergencia para situaciones críticas
"""

import asyncio
import gc
import json
import os
import psutil
import time
import weakref
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Set, List, Optional, Any, Tuple, Callable
from threading import Lock
import tracemalloc

from src.core.logging import get_logger
from src.core.redis_cluster_integration import RedisClusterIntegration
from src.core.websockets import websocket_manager, EventType, WSMessage, ChannelType

# Logger para aggressive cleanup
cleanup_logger = get_logger("aggressive.cleanup")

# Métricas de cleanup (intentar importar, fallback a métricas básicas)
try:
    from src.observability.metrics import (
        cleanup_connections_removed,
        cleanup_memory_freed,
        cleanup_duration,
        cleanup_channels_cleaned,
        cleanup_errors,
        emergency_cleanup_triggered
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


class CleanupLevel(Enum):
    """Niveles de limpieza según carga del sistema."""
    LOW = "low"           # Cada 5 minutos
    MEDIUM = "medium"     # Cada 2 minutos  
    HIGH = "high"         # Cada 30 segundos
    EMERGENCY = "emergency"  # Continuo


class CleanupType(Enum):
    """Tipos de limpieza disponibles."""
    CONNECTIONS = "connections"
    REDIS_CHANNELS = "redis_channels"
    MEMORY_BUFFERS = "memory_buffers"
    GARBAGE_COLLECTION = "garbage_collection"
    FULL_SYSTEM = "full_system"


@dataclass
class CleanupMetrics:
    """Métricas detalladas de operaciones de cleanup."""
    connections_removed: int = 0
    redis_channels_cleaned: int = 0
    memory_freed_mb: float = 0.0
    cleanup_duration_ms: float = 0.0
    emergency_triggers: int = 0
    last_cleanup_at: Optional[datetime] = None
    total_cleanups: int = 0
    avg_cleanup_duration_ms: float = 0.0
    success_rate: float = 100.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte métricas a diccionario."""
        return {
            "connections_removed": self.connections_removed,
            "redis_channels_cleaned": self.redis_channels_cleaned,
            "memory_freed_mb": self.memory_freed_mb,
            "cleanup_duration_ms": self.cleanup_duration_ms,
            "emergency_triggers": self.emergency_triggers,
            "last_cleanup_at": self.last_cleanup_at.isoformat() if self.last_cleanup_at else None,
            "total_cleanups": self.total_cleanups,
            "avg_cleanup_duration_ms": self.avg_cleanup_duration_ms,
            "success_rate": self.success_rate,
            "errors": self.errors
        }


@dataclass
class SystemLoadMetrics:
    """Métricas de carga del sistema para determinar nivel de cleanup."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    buffer_count: int = 0
    redis_channel_count: int = 0
    load_score: float = 0.0
    
    def calculate_load_score(self) -> float:
        """Calcula un score de carga del sistema (0-100)."""
        # Pesos: conexiones 40%, memoria 30%, CPU 20%, Redis 10%
        connection_score = min((self.active_connections / 1000) * 100, 100) * 0.4
        memory_score = self.memory_usage * 0.3
        cpu_score = self.cpu_usage * 0.2
        redis_score = min((self.redis_channel_count / 100) * 100, 100) * 0.1
        
        self.load_score = min(connection_score + memory_score + cpu_score + redis_score, 100)
        return self.load_score
    
    def get_cleanup_level(self) -> CleanupLevel:
        """Determina el nivel de cleanup basado en la carga."""
        score = self.calculate_load_score()
        
        if score >= 80:
            return CleanupLevel.EMERGENCY
        elif score >= 60:
            return CleanupLevel.HIGH
        elif score >= 30:
            return CleanupLevel.MEDIUM
        else:
            return CleanupLevel.LOW


class AggressiveConnectionCleanup:
    """
    Sistema agresivo de cleanup de conexiones inactivas con intervalos dinámicos.
    
    Características:
    - Detección automática de conexiones inactivas
    - Limpieza de canales Redis vacíos
    - Optimización de memoria de buffers
    - Recolección de basura optimizada
    - Recovery automático de health checks
    - Métricas detalladas
    - Triggers de emergencia
    """
    
    def __init__(self, 
                 websocket_manager_instance=None,
                 redis_integration: Optional[RedisClusterIntegration] = None,
                 cleanup_interval_seconds: int = 30):
        """
        Inicializa el sistema de cleanup agresivo.
        
        Args:
            websocket_manager_instance: Instancia del manager de WebSockets
            redis_integration: Integración con Redis cluster
            cleanup_interval_seconds: Intervalo base de cleanup
        """
        # Referencias principales
        self.ws_manager = websocket_manager_instance or websocket_manager
        self.redis_integration = redis_integration
        
        # Configuración de cleanup
        self.base_cleanup_interval = cleanup_interval_seconds
        self.connection_timeout_seconds = 300  # 5 minutos
        self.redis_channel_timeout_seconds = 3600  # 1 hora
        self.memory_buffer_timeout_seconds = 600  # 10 minutos
        
        # Estado del sistema
        self.is_running = False
        self.current_cleanup_level = CleanupLevel.LOW
        self.emergency_mode = False
        
        # Tracking de conexiones y recursos
        self.inactive_connections: Set[str] = set()
        self.empty_redis_channels: Set[str] = set()
        self.unused_buffers: Set[str] = set()
        
        # Buffers de memoria para tracking
        self.buffer_registry: Dict[str, Any] = {}
        self.buffer_last_access: Dict[str, datetime] = {}
        
        # Métricas
        self.metrics = CleanupMetrics()
        self.system_load = SystemLoadMetrics()
        
        # Task de cleanup
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = Lock()
        
        # Callbacks de emergencia
        self.emergency_callbacks: List[Callable] = []
        
        # Health check
        self.last_health_check = datetime.now()
        self.health_check_interval = 60  # 1 minuto
        
        cleanup_logger.info(
            "AggressiveConnectionCleanup inicializado",
            cleanup_interval=cleanup_interval_seconds,
            connection_timeout=self.connection_timeout_seconds,
            redis_timeout=self.redis_channel_timeout_seconds
        )
    
    def register_emergency_callback(self, callback: Callable):
        """Registra un callback para triggers de emergencia."""
        self.emergency_callbacks.append(callback)
    
    def get_dynamic_interval(self) -> int:
        """Calcula el intervalo dinámico de cleanup basado en carga."""
        load_score = self.system_load.calculate_load_score()
        
        if load_score >= 80:
            return 30  # 30 segundos
        elif load_score >= 60:
            return 60  # 1 minuto
        elif load_score >= 30:
            return 120  # 2 minutos
        else:
            return 300  # 5 minutos
    
    async def start(self):
        """Inicia el sistema de cleanup agresivo."""
        if self.is_running:
            cleanup_logger.warning("Sistema de cleanup ya está ejecutándose")
            return
        
        self.is_running = True
        self.emergency_mode = False
        
        # Iniciar tracemalloc para tracking de memoria
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Iniciar task de cleanup
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Iniciar health check
        asyncio.create_task(self._health_check_loop())
        
        cleanup_logger.info("Sistema de cleanup agresivo iniciado")
    
    async def stop(self):
        """Detiene el sistema de cleanup agresivo."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.emergency_mode = False
        
        # Cancelar tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        cleanup_logger.info("Sistema de cleanup agresivo detenido")
    
    async def trigger_emergency_cleanup(self, reason: str = "Manual trigger"):
        """Fuerza un cleanup de emergencia."""
        cleanup_logger.warning(
            "Cleanup de emergencia activado",
            reason=reason,
            current_level=self.current_cleanup_level.value
        )
        
        self.emergency_mode = True
        self.metrics.emergency_triggers += 1
        
        # Registrar métricas de emergencia
        if METRICS_ENABLED:
            emergency_cleanup_triggered()
        
        # Ejecutar cleanup completo inmediatamente
        try:
            await self._perform_full_cleanup()
        except Exception as e:
            cleanup_logger.error(f"Error en cleanup de emergencia: {str(e)}")
            self.metrics.errors.append(f"Emergency cleanup error: {str(e)}")
        
        # Ejecutar callbacks de emergencia
        for callback in self.emergency_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                cleanup_logger.error(f"Error en callback de emergencia: {str(e)}")
    
    async def _cleanup_loop(self):
        """Loop principal de cleanup con intervalos dinámicos."""
        while self.is_running:
            try:
                # Actualizar métricas del sistema
                await self._update_system_metrics()
                
                # Determinar nivel de cleanup
                self.current_cleanup_level = self.system_load.get_cleanup_level()
                
                # Obtener intervalo dinámico
                interval = self.get_dynamic_interval()
                
                cleanup_logger.debug(
                    "Ejecutando ciclo de cleanup",
                    level=self.current_cleanup_level.value,
                    interval_seconds=interval,
                    load_score=self.system_load.load_score
                )
                
                # Ejecutar limpieza
                start_time = time.time()
                await self._perform_cleanup()
                duration = (time.time() - start_time) * 1000
                
                # Actualizar métricas
                self.metrics.cleanup_duration_ms = duration
                self.metrics.last_cleanup_at = datetime.now()
                self.metrics.total_cleanups += 1
                
                # Calcular promedio de duración
                self.metrics.avg_cleanup_duration_ms = (
                    (self.metrics.avg_cleanup_duration_ms * (self.metrics.total_cleanups - 1) + duration) 
                    / self.metrics.total_cleanups
                )
                
                # Reportar métricas si están habilitadas
                if METRICS_ENABLED:
                    cleanup_duration(duration)
                
                cleanup_logger.debug(
                    "Ciclo de cleanup completado",
                    duration_ms=duration,
                    total_cleanups=self.metrics.total_cleanups
                )
                
                # Esperar intervalo dinámico
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                cleanup_logger.error(f"Error en cleanup loop: {str(e)}")
                self.metrics.errors.append(f"Cleanup loop error: {str(e)}")
                await asyncio.sleep(5)  # Esperar antes de reintentar
    
    async def _health_check_loop(self):
        """Loop de health check para recovery automático."""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                current_time = datetime.now()
                
                # Verificar si hay problemas
                issues = await self._detect_issues()
                
                if issues:
                    cleanup_logger.warning(
                        "Problemas detectados en health check",
                        issues=issues
                    )
                    
                    # Activar cleanup de emergencia si es crítico
                    if any(issue.get("severity") == "critical" for issue in issues):
                        await self.trigger_emergency_cleanup(f"Health check critical issues: {issues}")
                
                self.last_health_check = current_time
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                cleanup_logger.error(f"Error en health check: {str(e)}")
                await asyncio.sleep(30)
    
    async def _detect_issues(self) -> List[Dict[str, Any]]:
        """Detecta problemas en el sistema que requieren limpieza."""
        issues = []
        
        try:
            # Verificar memoria
            memory_info = psutil.virtual_memory()
            if memory_info.percent > 85:
                issues.append({
                    "type": "memory_high",
                    "severity": "critical" if memory_info.percent > 95 else "warning",
                    "value": memory_info.percent
                })
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                issues.append({
                    "type": "cpu_high",
                    "severity": "critical" if cpu_percent > 95 else "warning",
                    "value": cpu_percent
                })
            
            # Verificar conexiones zombie
            zombie_connections = await self._find_zombie_connections()
            if len(zombie_connections) > 50:
                issues.append({
                    "type": "zombie_connections",
                    "severity": "warning",
                    "value": len(zombie_connections)
                })
            
            # Verificar canales Redis vacíos
            if self.redis_integration:
                empty_channels = await self._find_empty_redis_channels()
                if len(empty_channels) > 20:
                    issues.append({
                        "type": "empty_redis_channels",
                        "severity": "warning",
                        "value": len(empty_channels)
                    })
            
        except Exception as e:
            cleanup_logger.error(f"Error detectando problemas: {str(e)}")
            issues.append({
                "type": "detection_error",
                "severity": "critical",
                "error": str(e)
            })
        
        return issues
    
    async def _perform_cleanup(self):
        """Ejecuta el ciclo completo de limpieza."""
        cleanup_type = CleanupType.CONNECTIONS
        
        try:
            # Limpiar conexiones inactivas
            await self._cleanup_inactive_connections()
            
            # Limpiar canales Redis vacíos (solo en niveles medios/altos)
            if self.current_cleanup_level in [CleanupLevel.MEDIUM, CleanupLevel.HIGH, CleanupLevel.EMERGENCY]:
                await self._cleanup_empty_redis_channels()
            
            # Limpiar buffers de memoria (solo en niveles altos)
            if self.current_cleanup_level in [CleanupLevel.HIGH, CleanupLevel.EMERGENCY]:
                await self._cleanup_unused_buffers()
            
            # Garbage collection (en todos los niveles pero con diferentes frecuencias)
            await self._perform_optimized_gc()
            
        except Exception as e:
            cleanup_logger.error(f"Error en cleanup: {str(e)}")
            self.metrics.errors.append(f"Cleanup error: {str(e)}")
            if METRICS_ENABLED:
                cleanup_errors()
    
    async def _perform_full_cleanup(self):
        """Ejecuta una limpieza completa del sistema."""
        cleanup_logger.info("Iniciando limpieza completa del sistema")
        
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        # Limpiar todo
        await self._cleanup_inactive_connections()
        await self._cleanup_empty_redis_channels()
        await self._cleanup_unused_buffers()
        await self._perform_optimized_gc(force=True)
        
        # Verificar cleanup de Redis
        if self.redis_integration:
            await self._cleanup_redis_pubsub_channels()
        
        duration = (time.time() - start_time) * 1000
        final_memory = self._get_memory_usage()
        memory_freed = max(0, initial_memory - final_memory)
        
        cleanup_logger.info(
            "Limpieza completa finalizada",
            duration_ms=duration,
            memory_freed_mb=memory_freed,
            connections_cleaned=self.metrics.connections_removed
        )
    
    async def _cleanup_inactive_connections(self):
        """Limpia conexiones WebSocket inactivas."""
        inactive_count = 0
        current_time = datetime.now()
        
        try:
            # Encontrar conexiones inactivas
            inactive_connections = await self._find_inactive_connections()
            
            for connection_id in inactive_connections:
                try:
                    await self.ws_manager.disconnect(connection_id)
                    inactive_count += 1
                    
                    cleanup_logger.debug(
                        "Conexión inactiva desconectada",
                        connection_id=connection_id,
                        inactive_time=str(current_time - self.ws_manager.active_connections.get(connection_id, {}).get('connected_at', current_time))
                    )
                    
                except Exception as e:
                    cleanup_logger.warning(
                        f"Error desconectando conexión inactiva {connection_id}: {str(e)}"
                    )
                    self.metrics.errors.append(f"Connection cleanup error: {str(e)}")
            
            # Actualizar métricas
            self.metrics.connections_removed += inactive_count
            
            if METRICS_ENABLED:
                cleanup_connections_removed(inactive_count)
            
            cleanup_logger.debug(
                f"Limpieza de conexiones inactivas completada: {inactive_count} eliminadas"
            )
            
        except Exception as e:
            cleanup_logger.error(f"Error limpiando conexiones inactivas: {str(e)}")
            self.metrics.errors.append(f"Inactive connections cleanup error: {str(e)}")
    
    async def _cleanup_empty_redis_channels(self):
        """Limpia canales Redis vacíos o inactivos."""
        if not self.redis_integration:
            return
        
        cleaned_count = 0
        
        try:
            # Encontrar canales vacíos
            empty_channels = await self._find_empty_redis_channels()
            
            for channel_name in empty_channels:
                try:
                    # Verificar si el canal realmente está vacío
                    subscriber_count = await self.redis_integration.get_subscriber_count(channel_name)
                    
                    if subscriber_count == 0:
                        # Limpiar el canal
                        await self.redis_integration.cleanup_channel(channel_name)
                        cleaned_count += 1
                        
                        cleanup_logger.debug(
                            "Canal Redis vacío limpiado",
                            channel_name=channel_name
                        )
                
                except Exception as e:
                    cleanup_logger.warning(
                        f"Error limpiando canal Redis {channel_name}: {str(e)}"
                    )
                    self.metrics.errors.append(f"Redis channel cleanup error: {str(e)}")
            
            # Actualizar métricas
            self.metrics.redis_channels_cleaned += cleaned_count
            
            if METRICS_ENABLED:
                cleanup_channels_cleaned(cleaned_count)
            
            cleanup_logger.debug(
                f"Limpieza de canales Redis completada: {cleaned_count} limpiados"
            )
            
        except Exception as e:
            cleanup_logger.error(f"Error limpiando canales Redis: {str(e)}")
            self.metrics.errors.append(f"Redis channels cleanup error: {str(e)}")
    
    async def _cleanup_unused_buffers(self):
        """Limpia buffers de memoria no utilizados."""
        freed_memory = 0.0
        current_time = datetime.now()
        
        try:
            # Encontrar buffers no utilizados
            unused_buffers = await self._find_unused_buffers()
            
            for buffer_id in unused_buffers:
                try:
                    # Liberar buffer
                    if buffer_id in self.buffer_registry:
                        del self.buffer_registry[buffer_id]
                    
                    if buffer_id in self.buffer_last_access:
                        del self.buffer_last_access[buffer_id]
                    
                    # Estimar memoria liberada (aproximación)
                    freed_memory += 0.1  # 100KB por buffer promedio
                    
                    cleanup_logger.debug(
                        "Buffer no utilizado liberado",
                        buffer_id=buffer_id
                    )
                
                except Exception as e:
                    cleanup_logger.warning(
                        f"Error liberando buffer {buffer_id}: {str(e)}"
                    )
                    self.metrics.errors.append(f"Buffer cleanup error: {str(e)}")
            
            # Actualizar métricas
            self.metrics.memory_freed_mb += freed_memory
            
            if METRICS_ENABLED:
                cleanup_memory_freed(freed_memory)
            
            cleanup_logger.debug(
                f"Limpieza de buffers completada: {freed_memory:.2f} MB liberados"
            )
            
        except Exception as e:
            cleanup_logger.error(f"Error limpiando buffers: {str(e)}")
            self.metrics.errors.append(f"Buffers cleanup error: {str(e)}")
    
    async def _perform_optimized_gc(self, force: bool = False):
        """Ejecuta recolección de basura optimizada."""
        try:
            if force or self.current_cleanup_level == CleanupLevel.EMERGENCY:
                # GC completo y agresivo
                collected = gc.collect()
                cleanup_logger.debug(f"GC completo ejecutado: {collected} objetos recolectados")
                
            elif self.current_cleanup_level == CleanupLevel.HIGH:
                # GC con más frecuencia
                collected = gc.collect(2)  # Generación 2
                cleanup_logger.debug(f"GC generación 2: {collected} objetos recolectados")
                
            elif self.current_cleanup_level == CleanupLevel.MEDIUM:
                # GC moderado
                collected = gc.collect(1)  # Generación 1
                cleanup_logger.debug(f"GC generación 1: {collected} objetos recolectados")
                
            else:
                # GC mínimo
                collected = gc.collect(0)  # Generación 0
                cleanup_logger.debug(f"GC generación 0: {collected} objetos recolectados")
            
        except Exception as e:
            cleanup_logger.error(f"Error en garbage collection: {str(e)}")
            self.metrics.errors.append(f"GC error: {str(e)}")
    
    async def _find_inactive_connections(self) -> Set[str]:
        """Encuentra conexiones WebSocket inactivas."""
        inactive = set()
        current_time = datetime.now()
        
        try:
            for connection_id, connection_info in self.ws_manager.active_connections.items():
                # Verificar inactividad basada en last_ping
                last_ping = getattr(connection_info, 'last_ping', connection_info.connected_at)
                inactive_duration = (current_time - last_ping).total_seconds()
                
                if inactive_duration > self.connection_timeout_seconds:
                    inactive.add(connection_id)
                    
                    cleanup_logger.debug(
                        "Conexión inactiva detectada",
                        connection_id=connection_id,
                        inactive_seconds=inactive_duration,
                        last_ping=last_ping.isoformat()
                    )
        
        except Exception as e:
            cleanup_logger.error(f"Error detectando conexiones inactivas: {str(e)}")
        
        return inactive
    
    async def _find_empty_redis_channels(self) -> Set[str]:
        """Encuentra canales Redis vacíos o inactivos."""
        empty_channels = set()
        
        if not self.redis_integration:
            return empty_channels
        
        try:
            # Obtener lista de canales conocidos
            channels = await self.redis_integration.list_channels()
            
            for channel_name in channels:
                try:
                    # Verificar suscriptores activos
                    subscriber_count = await self.redis_integration.get_subscriber_count(channel_name)
                    
                    # Verificar último mensaje
                    last_message = await self.redis_integration.get_last_message_time(channel_name)
                    
                    current_time = datetime.now()
                    if last_message:
                        idle_time = (current_time - last_message).total_seconds()
                    else:
                        idle_time = float('inf')  # Sin mensajes = definitivamente vacío
                    
                    # Considerar vacío si no hay suscriptores y lleva >1 hora sin mensajes
                    if subscriber_count == 0 and idle_time > self.redis_channel_timeout_seconds:
                        empty_channels.add(channel_name)
                
                except Exception as e:
                    cleanup_logger.warning(
                        f"Error verificando canal Redis {channel_name}: {str(e)}"
                    )
        
        except Exception as e:
            cleanup_logger.error(f"Error detectando canales Redis vacíos: {str(e)}")
        
        return empty_channels
    
    async def _find_unused_buffers(self) -> Set[str]:
        """Encuentra buffers de memoria no utilizados."""
        unused = set()
        current_time = datetime.now()
        
        try:
            for buffer_id, last_access in self.buffer_last_access.items():
                idle_time = (current_time - last_access).total_seconds()
                
                if idle_time > self.memory_buffer_timeout_seconds:
                    unused.add(buffer_id)
        
        except Exception as e:
            cleanup_logger.error(f"Error detectando buffers no utilizados: {str(e)}")
        
        return unused
    
    async def _find_zombie_connections(self) -> List[str]:
        """Encuentra conexiones zombie (hang de red)."""
        zombie = []
        current_time = datetime.now()
        
        try:
            for connection_id, connection_info in self.ws_manager.active_connections.items():
                # Verificar múltiples indicadores de zombie
                connected_at = getattr(connection_info, 'connected_at', current_time)
                idle_time = (current_time - connected_at).total_seconds()
                
                # Considerar zombie si lleva >30 minutos conectado sin actividad
                if idle_time > 1800:  # 30 minutos
                    zombie.append(connection_id)
        
        except Exception as e:
            cleanup_logger.error(f"Error detectando conexiones zombie: {str(e)}")
        
        return zombie
    
    async def _update_system_metrics(self):
        """Actualiza métricas del sistema."""
        try:
            # Métricas de CPU y memoria
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            # Métricas de conexiones
            active_connections = len(self.ws_manager.active_connections)
            
            # Métricas de Redis
            redis_channel_count = 0
            if self.redis_integration:
                channels = await self.redis_integration.list_channels()
                redis_channel_count = len(channels)
            
            # Métricas de buffers
            buffer_count = len(self.buffer_registry)
            
            # Actualizar métricas del sistema
            self.system_load = SystemLoadMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_info.percent,
                active_connections=active_connections,
                buffer_count=buffer_count,
                redis_channel_count=redis_channel_count
            )
            
        except Exception as e:
            cleanup_logger.error(f"Error actualizando métricas del sistema: {str(e)}")
    
    def _get_memory_usage(self) -> float:
        """Obtiene el uso actual de memoria en MB."""
        try:
            # Usar tracemalloc si está disponible
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024  # Convertir a MB
        except:
            # Fallback a psutil
            return psutil.Process().memory_info().rss / 1024 / 1024
    
    def register_buffer(self, buffer_id: str, buffer_data: Any):
        """Registra un buffer para tracking de uso."""
        with self._lock:
            self.buffer_registry[buffer_id] = buffer_data
            self.buffer_last_access[buffer_id] = datetime.now()
    
    def update_buffer_access(self, buffer_id: str):
        """Actualiza el último acceso de un buffer."""
        with self._lock:
            if buffer_id in self.buffer_registry:
                self.buffer_last_access[buffer_id] = datetime.now()
    
    async def _cleanup_redis_pubsub_channels(self):
        """Limpieza específica de canales pub/sub de Redis."""
        if not self.redis_integration:
            return
        
        try:
            # Limpiar canales pub/sub inactivos
            await self.redis_integration.cleanup_inactive_channels()
            
            cleanup_logger.debug("Limpieza de canales pub/sub Redis completada")
            
        except Exception as e:
            cleanup_logger.error(f"Error limpiando canales pub/sub: {str(e)}")
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del sistema de cleanup."""
        return {
            "is_running": self.is_running,
            "current_level": self.current_cleanup_level.value,
            "emergency_mode": self.emergency_mode,
            "dynamic_interval_seconds": self.get_dynamic_interval(),
            "metrics": self.metrics.to_dict(),
            "system_load": {
                "cpu_usage": self.system_load.cpu_usage,
                "memory_usage": self.system_load.memory_usage,
                "active_connections": self.system_load.active_connections,
                "buffer_count": self.system_load.buffer_count,
                "redis_channel_count": self.system_load.redis_channel_count,
                "load_score": self.system_load.load_score
            },
            "tracking": {
                "inactive_connections_count": len(self.inactive_connections),
                "empty_redis_channels_count": len(self.empty_redis_channels),
                "unused_buffers_count": len(self.unused_buffers),
                "registered_buffers_count": len(self.buffer_registry)
            },
            "health_check": {
                "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
                "interval_seconds": self.health_check_interval
            }
        }


# Instancia global del cleanup agresivo
aggressive_cleanup = AggressiveConnectionCleanup()


# Funciones de utilidad para integración con el WebSocket manager
async def initialize_aggressive_cleanup():
    """Inicializa el sistema de cleanup agresivo."""
    await aggressive_cleanup.start()
    cleanup_logger.info("Sistema de cleanup agresivo inicializado globalmente")


async def shutdown_aggressive_cleanup():
    """Detiene el sistema de cleanup agresivo."""
    await aggressive_cleanup.stop()
    cleanup_logger.info("Sistema de cleanup agresivo detenido")


async def emergency_cleanup(reason: str = "Manual emergency cleanup"):
    """Ejecuta un cleanup de emergencia."""
    await aggressive_cleanup.trigger_emergency_cleanup(reason)


# Funciones para manejo de buffers con tracking automático
def track_buffer(buffer_id: str, buffer_data: Any):
    """Registra un buffer para tracking automático de cleanup."""
    aggressive_cleanup.register_buffer(buffer_id, buffer_data)


def update_buffer_tracking(buffer_id: str):
    """Actualiza el tracking de un buffer."""
    aggressive_cleanup.update_buffer_access(buffer_id)


# Decorador para funciones críticas que requieren cleanup de emergencia
def critical_operation_with_cleanup(operation_func):
    """Decorador para operaciones críticas con cleanup automático en caso de error."""
    async def wrapper(*args, **kwargs):
        try:
            return await operation_func(*args, **kwargs)
        except Exception as e:
            cleanup_logger.error(
                f"Operación crítica falló, activando cleanup de emergencia",
                operation=operation_func.__name__,
                error=str(e)
            )
            await emergency_cleanup(f"Critical operation failed: {operation_func.__name__}")
            raise
    
    return wrapper