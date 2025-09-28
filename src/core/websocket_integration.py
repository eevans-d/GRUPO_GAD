# -*- coding: utf-8 -*-
"""
Integración de WebSockets con modelos de GRUPO_GAD.

Proporciona hooks para eventos de base de datos que automáticamente
envían notificaciones WebSocket cuando ocurren cambios en los modelos.
"""

from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.api.middleware.websockets import WebSocketEventEmitter
from src.core.logging import get_logger

# Logger para integración
integration_logger = get_logger("websockets.integration")


class WebSocketModelIntegrator:
    """
    Integrador de WebSockets con modelos de SQLAlchemy.
    
    Escucha eventos de cambios en los modelos y emite
    notificaciones WebSocket correspondientes.
    """
    
    def __init__(self, emitter: WebSocketEventEmitter):
        self.enabled = True
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self.emitter = emitter
        
    def enable(self):
        """Habilita la integración."""
        self.enabled = True
        integration_logger.info("Integración WebSocket-Modelos habilitada")
    
    def disable(self):
        """Deshabilita la integración."""
        self.enabled = False
        integration_logger.info("Integración WebSocket-Modelos deshabilitada")
    
    async def queue_event(self, event_type: str, model_name: str, 
                         instance_data: Dict[str, Any]):
        """
        Encola un evento para procesamiento asíncrono.
        
        Args:
            event_type: Tipo de evento (insert, update, delete)
            model_name: Nombre del modelo
            instance_data: Datos de la instancia
        """
        if not self.enabled:
            return
        
        event = {
            "event_type": event_type,
            "model_name": model_name,
            "instance_data": instance_data,
            "timestamp": datetime.now()
        }
        
        await self._event_queue.put(event)
    
    async def process_events(self):
        """Procesa eventos de la cola de manera asíncrona."""
        while True:
            try:
                event = await self._event_queue.get()
                await self._handle_model_event(event)
            except Exception as e:
                integration_logger.error(f"Error procesando evento de modelo: {str(e)}")
                await asyncio.sleep(1)  # Evitar spam de errores
    
    async def _handle_model_event(self, event: Dict[str, Any]):
        """
        Maneja un evento específico de modelo.
        
        Args:
            event: Datos del evento
        """
        try:
            event_type = event["event_type"]
            model_name = event["model_name"]
            instance_data = event["instance_data"]
            
            integration_logger.debug(
                "Procesando evento de modelo",
                model=model_name,
                event_type=event_type,
                instance_id=instance_data.get("id")
            )
            
            if model_name == "Tarea":
                await self._handle_tarea_event(event_type, instance_data)
            elif model_name == "Efectivo":
                await self._handle_efectivo_event(event_type, instance_data)
            elif model_name == "Usuario":
                await self._handle_usuario_event(event_type, instance_data)
            
        except Exception as e:
            integration_logger.error(f"Error manejando evento de modelo: {str(e)}")
    
    async def _handle_tarea_event(self, event_type: str, instance_data: Dict[str, Any]):
        """Maneja eventos de tareas."""
        task_id = instance_data.get("id")
        
        if not task_id:
            integration_logger.warning("Evento de tarea sin ID, ignorando")
            return
        
        if event_type == "insert":
            await self.emitter.emit_task_event("created", int(task_id), instance_data)
            
        elif event_type == "update":
            # Verificar si cambió el estado
            old_estado = instance_data.get("_old_estado")
            new_estado = instance_data.get("estado")
            
            if old_estado and new_estado and old_estado != new_estado:
                # Agregar información del cambio de estado
                instance_data["_status_change"] = {
                    "old": str(old_estado),
                    "new": str(new_estado)
                }
                await self.emitter.emit_task_event("status_changed", int(task_id), instance_data)
            else:
                await self.emitter.emit_task_event("updated", int(task_id), instance_data)
        
        # Actualizar dashboard después de cambios en tareas
        await self._trigger_dashboard_update()
    
    async def _handle_efectivo_event(self, event_type: str, instance_data: Dict[str, Any]):
        """Maneja eventos de efectivos."""
        efectivo_id = instance_data.get("id")
        
        if not efectivo_id:
            integration_logger.warning("Evento de efectivo sin ID, ignorando")
            return
        
        if event_type == "insert":
            await self.emitter.emit_efectivo_event("created", int(efectivo_id), instance_data)
            
        elif event_type == "update":
            # Verificar si cambió el estado
            old_estado = instance_data.get("_old_estado")
            new_estado = instance_data.get("estado")
            
            if old_estado and new_estado and old_estado != new_estado:
                # Agregar información del cambio de estado
                instance_data["_status_change"] = {
                    "old": str(old_estado),
                    "new": str(new_estado)
                }
                await self.emitter.emit_efectivo_event("status_changed", int(efectivo_id), instance_data)
            else:
                await self.emitter.emit_efectivo_event("updated", int(efectivo_id), instance_data)
    
    async def _handle_usuario_event(self, event_type: str, instance_data: Dict[str, Any]):
        """Maneja eventos de usuarios."""
        # Por ahora solo loggear, se puede expandir después
        integration_logger.debug(
            f"Evento de usuario: {event_type}",
            user_id=instance_data.get("id"),
            email=instance_data.get("email")
        )
    
    async def _trigger_dashboard_update(self):
        """Dispara una actualización del dashboard."""
        try:
            # Simular datos del dashboard
            # TODO: Implementar consulta real a la base de datos
            _dashboard_data = {
                "total_tasks": 25,
                "active_tasks": 12,
                "completed_tasks": 8,
                "pending_tasks": 5,
                "active_efectivos": 18,
                "available_efectivos": 15,
                "busy_efectivos": 3,
                "alerts_count": 2,
                "last_updated": datetime.now().isoformat()
            }
            
            await self.emitter.emit_system_event("dashboard_refresh", "Dashboard actualizado", 
                                                "Datos del dashboard actualizados automáticamente")
            
        except Exception as e:
            integration_logger.error(f"Error actualizando dashboard: {str(e)}")


# Instancia global del integrador (se inicializa con emitter cuando esté disponible)
websocket_integrator: Optional[WebSocketModelIntegrator] = None


def initialize_websocket_integrator(emitter: WebSocketEventEmitter) -> WebSocketModelIntegrator:
    """
    Inicializa el integrador de WebSocket con el emitter proporcionado.
    
    Args:
        emitter: Instancia del emisor de eventos WebSocket
        
    Returns:
        WebSocketModelIntegrator: Instancia del integrador inicializada
    """
    global websocket_integrator
    
    if websocket_integrator is None:
        websocket_integrator = WebSocketModelIntegrator(emitter)
        integration_logger.info("Integrador WebSocket inicializado")
    
    return websocket_integrator


def get_websocket_integrator() -> Optional[WebSocketModelIntegrator]:
    """
    Obtiene la instancia del integrador WebSocket.
    
    Returns:
        WebSocketModelIntegrator o None si no está inicializado
    """
    return websocket_integrator


# Funciones helper para usar desde los modelos
async def notify_task_change(event_type: str, task_instance: Any):
    """
    Notifica cambio en tarea.
    
    Args:
        event_type: Tipo de evento
        task_instance: Instancia de la tarea
    """
    try:
        instance_data = {
            "id": task_instance.id,
            "titulo": getattr(task_instance, 'titulo', None),
            "estado": getattr(task_instance, 'estado', None),
            "prioridad": getattr(task_instance, 'prioridad', None),
            "fecha_creacion": getattr(task_instance, 'created_at', None),
            "fecha_actualizacion": getattr(task_instance, 'updated_at', None)
        }
        
        # Agregar estado anterior si está disponible
        if hasattr(task_instance, '_sa_instance_state'):
            history = task_instance._sa_instance_state.committed_state
            if history and 'estado' in history:
                instance_data["_old_estado"] = history['estado']
        
        integrator = get_websocket_integrator()
        if integrator:
            await integrator.queue_event(event_type, "Tarea", instance_data)
        
    except Exception as e:
        integration_logger.error(f"Error notificando cambio de tarea: {str(e)}")


async def notify_efectivo_change(event_type: str, efectivo_instance: Any):
    """
    Notifica cambio en efectivo.
    
    Args:
        event_type: Tipo de evento
        efectivo_instance: Instancia del efectivo
    """
    try:
        instance_data = {
            "id": efectivo_instance.id,
            "nombre": getattr(efectivo_instance, 'nombre', None),
            "apellido": getattr(efectivo_instance, 'apellido', None),
            "estado_disponibilidad": getattr(efectivo_instance, 'estado_disponibilidad', None),
            "rango": getattr(efectivo_instance, 'rango', None),
            "fecha_actualizacion": getattr(efectivo_instance, 'updated_at', None)
        }
        
        # Agregar estado anterior si está disponible
        if hasattr(efectivo_instance, '_sa_instance_state'):
            history = efectivo_instance._sa_instance_state.committed_state
            if history and 'estado_disponibilidad' in history:
                instance_data["_old_estado_disponibilidad"] = history['estado_disponibilidad']
        
        integrator = get_websocket_integrator()
        if integrator:
            await integrator.queue_event(event_type, "Efectivo", instance_data)
        
    except Exception as e:
        integration_logger.error(f"Error notificando cambio de efectivo: {str(e)}")


# Event listeners para SQLAlchemy
def setup_sqlalchemy_events():
    """
    Configura los event listeners de SQLAlchemy para WebSockets.
    
    Estos listeners se activan automáticamente cuando ocurren
    cambios en la base de datos.
    """
    
    @event.listens_for(Engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        """Listener para conexiones a la base de datos."""
        integration_logger.debug("Nueva conexión a la base de datos establecida")
    
    @event.listens_for(Engine, "before_execute") 
    def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
        """Listener para ejecuciones de consultas."""
        integration_logger.debug(f"Ejecutando consulta: {str(clauseelement)[:100]}...")
    
    integration_logger.info("Event listeners de SQLAlchemy configurados para WebSockets")


# Funciones para inicializar/finalizar
async def start_websocket_integration():
    """Inicia la integración de WebSockets con modelos."""
    integrator = get_websocket_integrator()
    if not integrator:
        integration_logger.error("No se puede iniciar integración: integrador no inicializado")
        return
        
    integrator.enable()
    setup_sqlalchemy_events()
    
    # Iniciar procesador de eventos
    integrator._processing_task = asyncio.create_task(
        integrator.process_events()
    )
    
    integration_logger.info("Integración WebSocket-Modelos iniciada")


async def stop_websocket_integration():
    """Detiene la integración de WebSockets con modelos."""
    integrator = get_websocket_integrator()
    if not integrator:
        integration_logger.warning("No se puede detener integración: integrador no inicializado")
        return
        
    integrator.disable()
    
    if integrator._processing_task:
        integrator._processing_task.cancel()
        try:
            await integrator._processing_task
        except asyncio.CancelledError:
            pass
    
    integration_logger.info("Integración WebSocket-Modelos detenida")