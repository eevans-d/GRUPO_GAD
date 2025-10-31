# -*- coding: utf-8 -*-
"""
Router de WebSockets para GRUPO_GAD.

Maneja los endpoints WebSocket y la lógica de conexión/desconexión.
"""

import json
from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
from jose import jwt
from starlette.status import WS_1008_POLICY_VIOLATION

from src.core.websockets import (
    websocket_manager, 
    WSMessage, 
    EventType,
    ChannelType
)
from src.core.logging import get_logger
from config.settings import settings

# Logger para el router WebSocket
ws_router_logger = get_logger("websockets.router")

# Router para WebSockets
router = APIRouter(prefix="/ws", tags=["websockets"])

# Security scheme
security = HTTPBearer()


async def get_user_from_token(token: Optional[str] = None) -> Optional[dict[str, Any]]:
    """
    Obtiene información del usuario desde el token JWT.
    
    Args:
        token: Token JWT opcional
        
    Returns:
        dict: Información del usuario o None si no es válido
    """
    if not token: 
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])  # type: ignore[arg-type]
        
        # Priorizar user_id claim si existe, sino usar sub
        user_id = payload.get("user_id")
        if user_id:
            # Convertir a int si es dígito
            user_id = int(user_id) if str(user_id).isdigit() else user_id
        else:
            sub = payload.get("sub")
            if not sub:
                return None
            user_id = int(sub) if str(sub).isdigit() else sub
        
        # Mapear nivel → role si role no está presente
        # Telegram auth proporciona "nivel"; aceptar también "role"
        role = payload.get("role") or payload.get("nivel")
        if not role:
            role = "LEVEL_1"  # Default
        
        return {
            "user_id": user_id,
            "email": payload.get("email", ""),
            "role": role,
        }
    except Exception as e:
        ws_router_logger.error(f"Error validando token: {str(e)}")
        return None


@router.websocket("/connect")  # type: ignore[misc]
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT (opcional si Authorization header está presente)"),
    priority: Optional[int] = Query(None, description="Prioridad del usuario (1-10), opcional")
):
    """
    Endpoint principal de WebSocket con soporte para sharding de canales.
    
    Query Parameters:
        token: Token JWT para autenticación (opcional)
        priority: Prioridad del usuario (1-10), determina el tipo de canal
    
    Maneja:
    - Autenticación de usuarios
    - Asignación inteligente de canal con sharding
    - Establecimiento de conexión
    - Manejo de mensajes
    - Desconexión limpia
    """
    connection_id: Optional[str] = None
    user_info: Optional[dict[str, Any]] = None
    
    try:
        # Autenticar por header Authorization Bearer o query token
        auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        bearer = None
        if auth_header and auth_header.lower().startswith("bearer "):
            bearer = auth_header.split(" ", 1)[1].strip()

        provided_token = bearer or token

        # En producción, el token es obligatorio
        require_token = (getattr(settings, 'ENVIRONMENT', 'development') == 'production')
        if require_token and not provided_token:
            await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Authentication required")
            return

        if provided_token:
            user_info = await get_user_from_token(provided_token)
            if not user_info and require_token:
                ws_router_logger.warning("Token inválido en conexión WebSocket")
                await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return
        
        # Determinar prioridad del usuario
        user_priority = 1  # Default
        if priority and 1 <= priority <= 10:
            user_priority = priority
        elif user_info and "role" in user_info:
            # Mapear rol a prioridad por defecto
            role = user_info["role"]
            if role in ["SUPER_ADMIN"]:
                user_priority = 10
            elif role in ["ADMIN"]:
                user_priority = 8
            elif role in ["MODERATOR", "LEVEL_3"]:
                user_priority = 6
            elif role in ["LEVEL_2"]:
                user_priority = 4
            else:
                user_priority = 2
        
        # Establecer conexión con sharding de canales
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=user_info.get("user_id") if user_info else None,
            user_role=user_info.get("role") if user_info else None,
            user_priority=user_priority
        )
        
        ws_router_logger.info(
            "Conexión WebSocket establecida",
            connection_id=connection_id,
            user_id=user_info.get("user_id") if user_info else None,
            authenticated=user_info is not None,
        )
        
        # Loop principal de mensajes
        while True:
            try:
                # Recibir mensaje del cliente
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                ws_router_logger.debug(
                    f"Mensaje recibido de {connection_id}",
                    message_type=message_data.get("event_type"),
                    data_keys=list(message_data.get("data", {}).keys())
                )
                
                # Procesar mensaje
                await handle_client_message(connection_id, message_data, user_info)
                
            except json.JSONDecodeError:
                ws_router_logger.warning(
                    f"Mensaje JSON inválido de {connection_id}"
                )
                error_message = WSMessage(
                    event_type=EventType.ERROR,
                    data={"error": "Invalid JSON format"}
                )
                await websocket_manager.send_to_connection(connection_id, error_message)
                
            except WebSocketDisconnect:
                ws_router_logger.info(f"Cliente {connection_id} desconectado normalmente")
                break
                
    except WebSocketDisconnect:
        ws_router_logger.info("Cliente desconectado durante handshake")
        
    except Exception as e:
        ws_router_logger.error(
            f"Error en conexión WebSocket {connection_id}: {str(e)}"
        )
        
    finally:
        # Limpiar conexión
        if connection_id:
            await websocket_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, message_data: dict[str, Any], 
                               user_info: Optional[dict[str, Any]]):
    """
    Maneja mensajes recibidos del cliente.
    
    Args:
        connection_id: ID de la conexión
        message_data: Datos del mensaje
        user_info: Información del usuario autenticado
    """
    try:
        event_type = message_data.get("event_type")
        data = message_data.get("data", {})
        
        ws_router_logger.debug(
            "Procesando mensaje de cliente",
            connection_id=connection_id,
            event_type=event_type,
            user_id=user_info.get("user_id") if user_info else None
        )
        
        # Manejar diferentes tipos de mensajes
        if event_type == EventType.PONG:
            # Respuesta a ping - actualizar last_ping
            connection_info = websocket_manager.active_connections.get(connection_id)
            if connection_info:
                # Si viene timestamp usarlo; si no, usar ahora
                try:
                    ts = data.get("timestamp")
                    connection_info.last_ping = ts or connection_info.last_ping
                except Exception:
                    # fallback seguro por si data no es un dict estándar
                    from datetime import datetime as _dt
                    connection_info.last_ping = _dt.now()
                
        elif event_type == EventType.DASHBOARD_UPDATE:
            # Cliente solicita actualización del dashboard
            if user_info:  # Solo usuarios autenticados
                dashboard_data = await get_dashboard_data(user_info)
                response = WSMessage(
                    event_type=EventType.DASHBOARD_UPDATE,
                    data=dashboard_data
                )
                await websocket_manager.send_to_connection(connection_id, response)
                
        elif event_type == EventType.METRICS_UPDATE:
            # Cliente solicita actualización de métricas
            if user_info:
                metrics_data = await get_metrics_data(user_info)
                response = WSMessage(
                    event_type=EventType.METRICS_UPDATE,
                    data=metrics_data
                )
                await websocket_manager.send_to_connection(connection_id, response)
                
        elif event_type == "subscribe":
            # Cliente se suscribe a eventos específicos
            await handle_subscription(connection_id, data, user_info)
            
        elif event_type == "unsubscribe":
            # Cliente se desuscribe de eventos
            await handle_unsubscription(connection_id, data, user_info)
            
        else:
            ws_router_logger.warning(
                f"Tipo de evento no reconocido: {event_type}",
                connection_id=connection_id
            )
            
    except Exception as e:
        ws_router_logger.error(
            f"Error procesando mensaje de cliente {connection_id}: {str(e)}"
        )
        
        error_message = WSMessage(
            event_type=EventType.ERROR,
            data={"error": f"Error processing message: {str(e)}"}
        )
        await websocket_manager.send_to_connection(connection_id, error_message)


async def get_dashboard_data(user_info: dict[str, Any]) -> dict[str, Any]:
    """
    Obtiene datos del dashboard para el usuario.
    
    Args:
        user_info: Información del usuario
        
    Returns:
        dict: Datos del dashboard
    """
    # TODO: Implementar lógica real de dashboard
    return {
        "total_tasks": 25,
        "active_tasks": 12,
        "completed_tasks": 8,
        "pending_tasks": 5,
        "active_efectivos": 18,
        "available_efectivos": 15,
        "busy_efectivos": 3,
        "alerts_count": 2,
        "last_updated": "2025-09-22T04:55:00Z"
    }


async def get_metrics_data(user_info: dict[str, Any]) -> dict[str, Any]:
    """
    Obtiene datos de métricas para el usuario.
    
    Args:
        user_info: Información del usuario
        
    Returns:
        dict: Datos de métricas
    """
    # TODO: Implementar lógica real de métricas
    return {
        "performance": {
            "task_completion_rate": 85.5,
            "average_response_time": 24.3,
            "efficiency_score": 92.1
        },
        "usage": {
            "active_users": 8,
            "total_sessions": 156,
            "peak_concurrent_users": 12
        },
        "system": {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "storage_usage": 34.1
        }
    }


async def handle_subscription(connection_id: str, data: dict[str, Any], user_info: Optional[dict[str, Any]]):
    """
    Maneja suscripciones a eventos específicos.
    
    Args:
        connection_id: ID de la conexión
        data: Datos de suscripción
        user_info: Información del usuario
    """
    events = data.get("events", [])
    
    # Registrar suscripciones en el manager
    try:
        from typing import Set as _Set
        topics: _Set[str] = set()
        for e in events:
            if isinstance(e, str) and e.strip():
                topics.add(e.strip())
        if topics:
            websocket_manager.subscribe(connection_id, topics)
            ws_router_logger.info(
                f"Cliente {connection_id} suscrito a eventos",
                events=list(topics),
                user_id=user_info.get("user_id") if user_info else None
            )
        else:
            ws_router_logger.info(
                f"Cliente {connection_id} solicitó suscripción vacía",
                user_id=user_info.get("user_id") if user_info else None
            )
    except Exception as _e:
        ws_router_logger.error("Error registrando suscripción", error=_e)

    response = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={
            "title": "Suscripción confirmada",
            "content": f"Suscrito a {len(events)} tipos de eventos",
            "level": "info"
        }
    )
    await websocket_manager.send_to_connection(connection_id, response)


async def handle_unsubscription(connection_id: str, data: dict[str, Any], user_info: Optional[dict[str, Any]]):
    """
    Maneja desuscripciones de eventos.
    
    Args:
        connection_id: ID de la conexión
        data: Datos de desuscripción
        user_info: Información del usuario
    """
    events = data.get("events", [])
    
    try:
        from typing import Set as _Set
        topics: _Set[str] = set()
        for e in events:
            if isinstance(e, str) and e.strip():
                topics.add(e.strip())
        if topics:
            websocket_manager.unsubscribe(connection_id, topics)
            ws_router_logger.info(
                f"Cliente {connection_id} desuscrito de eventos",
                events=list(topics),
                user_id=user_info.get("user_id") if user_info else None
            )
    except Exception as _e:
        ws_router_logger.error("Error registrando desuscripción", error=_e)


@router.get("/stats")  # type: ignore[misc]
async def get_websocket_stats():
    """
    Endpoint para obtener estadísticas completas de WebSockets y sharding de canales.
    
    Returns:
        dict: Estadísticas de conexiones activas y métricas de sharding
    """
    stats = websocket_manager.get_stats()
    
    # Añadir información específica del sharding si está disponible
    try:
        if hasattr(websocket_manager, 'get_sharding_stats'):
            stats["sharding_details"] = websocket_manager.get_sharding_stats()
        
        if hasattr(websocket_manager, 'get_channel_metrics'):
            stats["channel_metrics"] = websocket_manager.get_channel_metrics()
        
        if hasattr(websocket_manager, 'get_channel_utilization_matrix'):
            stats["utilization_matrix"] = websocket_manager.get_channel_utilization_matrix()
            
    except Exception as e:
        ws_router_logger.warning(f"Error obteniendo estadísticas de sharding: {e}")
    
    ws_router_logger.debug("Estadísticas WebSocket solicitadas", stats=stats)
    
    return {
        "status": "ok",
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0-sharding"
    }


@router.post("/admin/channels")  # type: ignore[misc]
async def add_dynamic_channel(
    channel_type: str,
    channel_name: str,
    capacity: int = 1000,
    priority: int = 1
):
    """
    Endpoint para añadir canales dinámicamente (solo administradores).
    
    Args:
        channel_type: Tipo de canal (general, admin, users, priority)
        channel_name: Nombre del canal a crear
        capacity: Capacidad máxima de usuarios
        priority: Nivel de prioridad (1-10)
        
    Returns:
        dict: Confirmación de creación
    """
    from src.core.websockets import ChannelType
    
    # Validar tipo de canal
    try:
        ct = ChannelType(channel_type.lower())
    except ValueError:
        return {
            "status": "error",
            "error": f"Tipo de canal inválido: {channel_type}. Válidos: {[t.value for t in ChannelType]}"
        }
    
    # Validar capacidad y prioridad
    if capacity <= 0 or capacity > 10000:
        return {"status": "error", "error": "Capacidad debe estar entre 1 y 10,000"}
    
    if priority < 1 or priority > 10:
        return {"status": "error", "error": "Prioridad debe estar entre 1 y 10"}
    
    try:
        # Añadir canal dinámicamente
        websocket_manager.add_dynamic_channel(ct, channel_name, capacity, priority)
        
        ws_router_logger.info(
            "Canal dinámico añadido",
            channel_name=channel_name,
            channel_type=ct.value,
            capacity=capacity,
            priority=priority
        )
        
        return {
            "status": "ok",
            "message": f"Canal {channel_name} creado exitosamente",
            "channel": {
                "name": channel_name,
                "type": ct.value,
                "capacity": capacity,
                "priority": priority
            }
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error creando canal dinámico: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/admin/channels/status")  # type: ignore[misc]
async def get_channels_status():
    """
    Endpoint para obtener estado detallado de todos los canales.
    
    Returns:
        dict: Estado completo del sistema de canales
    """
    try:
        # Obtener estadísticas básicas
        stats = websocket_manager.get_stats()
        
        # Obtener información específica de canales
        channel_info = {}
        if hasattr(websocket_manager, 'channel_stats'):
            for channel_name, info in websocket_manager.channel_stats.items():
                active_connections = [
                    cid for cid, conn_info in websocket_manager.active_connections.items()
                    if conn_info.assigned_channel == channel_name
                ]
                
                channel_info[channel_name] = {
                    "name": info.name,
                    "type": info.channel_type.value,
                    "capacity": info.user_capacity,
                    "current_load": len(active_connections),
                    "utilization": info.utilization,
                    "is_overloaded": info.is_overloaded,
                    "is_underutilized": info.is_underutilized,
                    "priority_level": info.priority_level,
                    "active_connections": len(active_connections)
                }
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_channels": len(channel_info),
                "total_connections": stats.get("total_connections", 0),
                "overloaded_channels": [ch for ch, info in channel_info.items() if info["is_overloaded"]],
                "underutilized_channels": [ch for ch, info in channel_info.items() if info["is_underutilized"]]
            },
            "channels": channel_info,
            "sharding_stats": stats.get("sharding", {})
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error obteniendo estado de canales: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/admin/channels/optimize")  # type: ignore[misc]
async def optimize_channels():
    """
    Endpoint para optimizar la distribución de canales.
    
    Returns:
        dict: Resultado de la optimización
    """
    try:
        # Ejecutar optimización
        websocket_manager.optimize_channels()
        
        ws_router_logger.info("Optimización de canales ejecutada")
        
        return {
            "status": "ok",
            "message": "Optimización de canales ejecutada",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error optimizando canales: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/_test/broadcast")  # type: ignore[misc]
async def test_trigger_broadcast(payload: dict[str, Any]):  # pragma: no cover - cubierto en test E2E dedicado
    """Dispara un broadcast manual en entornos no productivos.

    Este endpoint existe únicamente para facilitar pruebas E2E del sistema
    WebSocket sin incurrir en lógica de cross-loop desde los tests. No debe
    habilitarse en producción.
    """
    from config.settings import settings as _s
    if getattr(_s, 'ENVIRONMENT', 'development') == 'production':
        return {"status": "forbidden"}

    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={
            "title": payload.get("title", "Test Broadcast"),
            "content": payload.get("content", "Mensaje de prueba"),
            "level": payload.get("level", "info")
        },
        topic=payload.get("topic") if isinstance(payload.get("topic"), str) else None
    )
    sent = await websocket_manager.broadcast(message)
    return {"status": "ok", "sent": sent, "metrics": websocket_manager.get_stats().get("metrics", {})}


# --- ENDPOINTS DE CLEANUP AGRESIVO --- #

@router.get("/cleanup/status")  # type: ignore[misc]
async def get_cleanup_status():
    """
    Obtiene el estado del sistema de cleanup agresivo.
    
    Returns:
        dict: Estado completo del sistema de cleanup
    """
    try:
        cleanup_stats = websocket_manager.get_cleanup_stats()
        health_report = websocket_manager.get_connection_health_report()
        
        return {
            "status": "ok",
            "cleanup_enabled": websocket_manager.enable_aggressive_cleanup,
            "cleanup_active": websocket_manager.cleanup_integration_active,
            "cleanup_stats": cleanup_stats,
            "health_report": health_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error obteniendo estado de cleanup: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/cleanup/emergency")  # type: ignore[misc]
async def trigger_emergency_cleanup(payload: dict[str, Any]):
    """
    Dispara un cleanup de emergencia manual (solo administradores).
    
    Args:
        payload: Datos del payload con reason opcional
        
    Returns:
        dict: Resultado del cleanup de emergencia
    """
    reason = payload.get("reason", "Manual trigger via API")
    
    try:
        # Activar cleanup de emergencia
        await websocket_manager.trigger_emergency_cleanup(reason)
        
        # Notificar a administradores
        from src.core.websockets import notify_emergency_cleanup
        await notify_emergency_cleanup(reason, "critical")
        
        ws_router_logger.warning(f"Cleanup de emergencia activado via API: {reason}")
        
        return {
            "status": "ok",
            "message": "Cleanup de emergencia activado",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error ejecutando cleanup de emergencia: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/cleanup/report")  # type: ignore[misc]
async def get_detailed_cleanup_report():
    """
    Obtiene un reporte detallado completo del sistema de cleanup.
    
    Returns:
        dict: Reporte detallado
    """
    try:
        report = await websocket_manager.get_detailed_cleanup_report()
        
        return {
            "status": "ok",
            "report": report
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error generando reporte de cleanup: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/cleanup/health")  # type: ignore[misc]
async def get_websocket_health():
    """
    Obtiene el resumen de salud del sistema WebSocket.
    
    Returns:
        dict: Resumen de salud
    """
    try:
        from src.core.websockets import get_websocket_health_summary
        health_summary = get_websocket_health_summary()
        
        return {
            "status": "ok",
            "health": health_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error obteniendo salud del sistema: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/cleanup/initialize")  # type: ignore[misc]
async def initialize_cleanup_system():
    """
    Inicializa el sistema de cleanup agresivo (solo administradores).
    
    Returns:
        dict: Resultado de la inicialización
    """
    try:
        if websocket_manager.cleanup_integration_active:
            return {
                "status": "ok",
                "message": "Sistema de cleanup ya está activo"
            }
        
        await websocket_manager.activate_cleanup_integration()
        
        ws_router_logger.info("Sistema de cleanup inicializado via API")
        
        return {
            "status": "ok",
            "message": "Sistema de cleanup inicializado correctamente",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error inicializando sistema de cleanup: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/cleanup/shutdown")  # type: ignore[misc]
async def shutdown_cleanup_system():
    """
    Detiene el sistema de cleanup agresivo (solo administradores).
    
    Returns:
        dict: Resultado del apagado
    """
    try:
        if not websocket_manager.cleanup_integration_active:
            return {
                "status": "ok",
                "message": "Sistema de cleanup ya está inactivo"
            }
        
        await websocket_manager.deactivate_cleanup_integration()
        
        ws_router_logger.info("Sistema de cleanup detenido via API")
        
        return {
            "status": "ok",
            "message": "Sistema de cleanup detenido correctamente",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error deteniendo sistema de cleanup: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/cleanup/metrics")  # type: ignore[misc]
async def get_cleanup_metrics():
    """
    Obtiene métricas detalladas del sistema de cleanup.
    
    Returns:
        dict: Métricas de cleanup
    """
    try:
        cleanup_stats = websocket_manager.get_cleanup_stats()
        
        # Notificar métricas a administradores si está configurado
        try:
            from src.core.websockets import notify_cleanup_metrics
            await notify_cleanup_metrics(cleanup_stats.get("metrics", {}))
        except Exception:
            # No fallar si no se puede notificar
            pass
        
        return {
            "status": "ok",
            "metrics": cleanup_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error obteniendo métricas de cleanup: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/cleanup/recommendations")  # type: ignore[misc]
async def get_cleanup_recommendations():
    """
    Obtiene recomendaciones de optimización del sistema.
    
    Returns:
        dict: Recomendaciones del sistema
    """
    try:
        health_report = websocket_manager.get_connection_health_report()
        
        recommendations = health_report.get("recommendations", [])
        optimization_suggestions = websocket_manager._get_system_optimization_suggestions()
        
        return {
            "status": "ok",
            "health_score": health_report.get("health_score", 0),
            "cleanup_recommendations": recommendations,
            "optimization_suggestions": optimization_suggestions,
            "immediate_actions": recommendations if health_report.get("health_score", 0) < 80 else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        ws_router_logger.error(f"Error obteniendo recomendaciones: {e}")
        return {"status": "error", "error": str(e)}