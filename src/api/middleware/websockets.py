# -*- coding: utf-8 -*-
"""
Middleware para WebSockets de GRUPO_GAD.

Proporciona funcionalidades de:
- Logging de eventos WebSocket
- Integración con sistema de autenticación
- Monitoreo de conexiones
- Notificaciones automáticas
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.websockets import (
    websocket_manager,
    WSMessage,
    EventType,
    notify_dashboard_update,
    send_system_alert
)
from src.core.logging import get_logger

# Logger para middleware WebSocket
ws_middleware_logger = get_logger("websockets.middleware")


class WebSocketEventEmitter:
    """
    Emisor de eventos WebSocket que se integra con el sistema.
    
    Permite a otras partes del sistema enviar notificaciones
    en tiempo real a través de WebSockets.
    """
    
    def __init__(self):
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self):
        """Inicia el procesador de eventos."""
        if self._is_running:
            return
        
        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_events())
        
        ws_middleware_logger.info("WebSocketEventEmitter iniciado")
    
    async def stop(self):
        """Detiene el procesador de eventos."""
        self._is_running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            except RuntimeError as e:  # Diferente event loop entre tests (escenario de TestClient)
                # En entorno de pruebas multi-loop (pytest + TestClient + uvicorn en hilo)
                # puede intentarse await de una tarea ligada a otro loop.
                ws_middleware_logger.debug(
                    "Ignorando RuntimeError al detener emitter (loop distinto)",
                    error=str(e)
                )
            finally:
                # Evitar reuso de la misma tarea en otro loop posterior
                self._processing_task = None
        
        ws_middleware_logger.info("WebSocketEventEmitter detenido")
    
    async def emit_task_event(self, event_type: str, task_id: int, 
                             task_data: Dict[str, Any], user_id: Optional[int] = None):
        """
        Emite evento relacionado con tareas.
        
        Args:
            event_type: Tipo de evento (created, updated, status_changed, etc.)
            task_id: ID de la tarea
            task_data: Datos de la tarea
            user_id: ID del usuario objetivo (opcional)
        """
        event = {
            "type": "task_event",
            "event_type": event_type,
            "task_id": task_id,
            "task_data": task_data,
            "user_id": user_id,
            "timestamp": datetime.now()
        }
        
        await self._event_queue.put(event)
    
    async def emit_efectivo_event(self, event_type: str, efectivo_id: int,
                                 efectivo_data: Dict[str, Any]):
        """
        Emite evento relacionado con efectivos.
        
        Args:
            event_type: Tipo de evento
            efectivo_id: ID del efectivo
            efectivo_data: Datos del efectivo
        """
        event = {
            "type": "efectivo_event",
            "event_type": event_type,
            "efectivo_id": efectivo_id,
            "efectivo_data": efectivo_data,
            "timestamp": datetime.now()
        }
        
        await self._event_queue.put(event)
    
    async def emit_system_event(self, event_type: str, title: str, 
                               content: str, level: str = "info"):
        """
        Emite evento del sistema.
        
        Args:
            event_type: Tipo de evento
            title: Título del evento
            content: Contenido del evento
            level: Nivel del evento (info, warning, error, alert)
        """
        event = {
            "type": "system_event",
            "event_type": event_type,
            "title": title,
            "content": content,
            "level": level,
            "timestamp": datetime.now()
        }
        
        await self._event_queue.put(event)
    
    async def emit_dashboard_update(self, dashboard_data: Dict[str, Any]):
        """
        Emite actualización del dashboard.
        
        Args:
            dashboard_data: Datos actualizados del dashboard
        """
        event = {
            "type": "dashboard_update",
            "dashboard_data": dashboard_data,
            "timestamp": datetime.now()
        }
        
        await self._event_queue.put(event)
    
    async def _process_events(self):
        """Procesa eventos en cola de manera asíncrona."""
        while self._is_running:
            try:
                # Esperar por evento con timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # Timeout normal, continuar loop
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                ws_middleware_logger.error(f"Error procesando evento WebSocket: {str(e)}")
                await asyncio.sleep(1)  # Evitar spam de errores
    
    async def _handle_event(self, event: Dict[str, Any]):
        """
        Maneja un evento específico.
        
        Args:
            event: Datos del evento
        """
        try:
            event_type = event.get("type")
            
            if event_type == "task_event":
                await self._handle_task_event(event)
            elif event_type == "efectivo_event":
                await self._handle_efectivo_event(event)
            elif event_type == "system_event":
                await self._handle_system_event(event)
            elif event_type == "dashboard_update":
                await self._handle_dashboard_update(event)
            else:
                ws_middleware_logger.warning(f"Tipo de evento desconocido: {event_type}")
                
        except Exception as e:
            ws_middleware_logger.error(f"Error manejando evento {event.get('type')}: {str(e)}")
    
    async def _handle_task_event(self, event: Dict[str, Any]):
        """Maneja eventos de tareas."""
        task_id = event["task_id"]
        task_data = event["task_data"]
        user_id = event.get("user_id")
        sub_event_type = event["event_type"]
        
        # Mapear tipos de eventos
        ws_event_type = {
            "created": EventType.TASK_CREATED,
            "updated": EventType.TASK_UPDATED,
            "status_changed": EventType.TASK_STATUS_CHANGED,
            "assigned": EventType.TASK_ASSIGNED
        }.get(sub_event_type, EventType.TASK_UPDATED)
        
        message = WSMessage(
            event_type=ws_event_type,
            data={
                "task_id": task_id,
                "task_data": task_data,
                "sub_event_type": sub_event_type
            },
            target_user_id=user_id
        )
        
        if user_id:
            sent_count = await websocket_manager.send_to_user(user_id, message)
        else:
            sent_count = await websocket_manager.broadcast(message)
        
        ws_middleware_logger.debug(
            "Evento de tarea enviado",
            task_id=task_id,
            event_type=sub_event_type,
            sent_to_connections=sent_count
        )
    
    async def _handle_efectivo_event(self, event: Dict[str, Any]):
        """Maneja eventos de efectivos."""
        efectivo_id = event["efectivo_id"]
        efectivo_data = event["efectivo_data"]
        sub_event_type = event["event_type"]
        
        ws_event_type = {
            "status_changed": EventType.EFECTIVO_STATUS_CHANGED,
            "location_update": EventType.EFECTIVO_LOCATION_UPDATE
        }.get(sub_event_type, EventType.EFECTIVO_STATUS_CHANGED)
        
        message = WSMessage(
            event_type=ws_event_type,
            data={
                "efectivo_id": efectivo_id,
                "efectivo_data": efectivo_data,
                "sub_event_type": sub_event_type
            }
        )
        
        sent_count = await websocket_manager.broadcast(message)
        
        ws_middleware_logger.debug(
            "Evento de efectivo enviado",
            efectivo_id=efectivo_id,
            event_type=sub_event_type,
            sent_to_connections=sent_count
        )
    
    async def _handle_system_event(self, event: Dict[str, Any]):
        """Maneja eventos del sistema."""
        title = event["title"]
        content = event["content"]
        level = event["level"]
        
        await send_system_alert(title, content, level)
        
        ws_middleware_logger.info(
            "Evento del sistema enviado",
            title=title,
            level=level
        )
    
    async def _handle_dashboard_update(self, event: Dict[str, Any]):
        """Maneja actualizaciones del dashboard."""
        dashboard_data = event["dashboard_data"]
        
        await notify_dashboard_update(dashboard_data)
        
        ws_middleware_logger.debug("Actualización del dashboard enviada")


# Instancia global del emisor de eventos
websocket_event_emitter = WebSocketEventEmitter()


# Funciones helper para usar desde otras partes del sistema
async def emit_task_created(task_id: int, task_data: Dict[str, Any]):
    """Emite evento de tarea creada."""
    await websocket_event_emitter.emit_task_event("created", task_id, task_data)


async def emit_task_updated(task_id: int, task_data: Dict[str, Any], user_id: Optional[int] = None):
    """Emite evento de tarea actualizada."""
    await websocket_event_emitter.emit_task_event("updated", task_id, task_data, user_id)


async def emit_task_status_changed(task_id: int, old_status: str, new_status: str, 
                                  task_data: Dict[str, Any]):
    """Emite evento de cambio de estado de tarea."""
    data = task_data.copy()
    data.update({
        "old_status": old_status,
        "new_status": new_status
    })
    await websocket_event_emitter.emit_task_event("status_changed", task_id, data)


async def emit_efectivo_status_changed(efectivo_id: int, old_status: str, new_status: str,
                                      efectivo_data: Dict[str, Any]):
    """Emite evento de cambio de estado de efectivo."""
    data = efectivo_data.copy()
    data.update({
        "old_status": old_status,
        "new_status": new_status
    })
    await websocket_event_emitter.emit_efectivo_event("status_changed", efectivo_id, data)


async def emit_system_maintenance(title: str, content: str):
    """Emite evento de mantenimiento del sistema."""
    await websocket_event_emitter.emit_system_event("maintenance", title, content, "alert")


async def emit_dashboard_refresh(dashboard_data: Dict[str, Any]):
    """Emite actualización completa del dashboard."""
    await websocket_event_emitter.emit_dashboard_update(dashboard_data)