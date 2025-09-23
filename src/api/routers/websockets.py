# -*- coding: utf-8 -*-
"""
Router de WebSockets para GRUPO_GAD.

Maneja los endpoints WebSocket y la lógica de conexión/desconexión.
"""

import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from starlette.status import WS_1008_POLICY_VIOLATION

from src.core.websockets import (
    websocket_manager, 
    WSMessage, 
    EventType
)
from src.core.logging import get_logger
from config.settings import settings

# Logger para el router WebSocket
ws_router_logger = get_logger("websockets.router")

# Router para WebSockets
router = APIRouter(prefix="/ws", tags=["websockets"])

# Security scheme
security = HTTPBearer()


async def get_user_from_token(token: Optional[str] = None) -> Optional[dict]:
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
        sub = payload.get("sub")
        if not sub:
            return None
        # Nota: En una implementación real, recuperaríamos el usuario desde DB
        return {
            "user_id": int(sub) if str(sub).isdigit() else sub,
            "email": payload.get("email", ""),
            "role": payload.get("role", "LEVEL_1"),
        }
    except Exception as e:
        ws_router_logger.error(f"Error validando token: {str(e)}")
        return None


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT (opcional si Authorization header está presente)")
):
    """
    Endpoint principal de WebSocket.
    
    Query Parameters:
        token: Token JWT para autenticación (opcional)
    
    Maneja:
    - Autenticación de usuarios
    - Establecimiento de conexión
    - Manejo de mensajes
    - Desconexión limpia
    """
    connection_id: Optional[str] = None
    user_info: Optional[dict] = None
    
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
        
        # Establecer conexión
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=user_info.get("user_id") if user_info else None,
            user_role=user_info.get("role") if user_info else None
        )
        
        ws_router_logger.info(
            f"Conexión WebSocket establecida",
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
        ws_router_logger.info(f"Cliente desconectado durante handshake")
        
    except Exception as e:
        ws_router_logger.error(
            f"Error en conexión WebSocket {connection_id}: {str(e)}"
        )
        
    finally:
        # Limpiar conexión
        if connection_id:
            await websocket_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, message_data: dict, 
                               user_info: Optional[dict]):
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
            f"Procesando mensaje de cliente",
            connection_id=connection_id,
            event_type=event_type,
            user_id=user_info.get("user_id") if user_info else None
        )
        
        # Manejar diferentes tipos de mensajes
        if event_type == EventType.PONG:
            # Respuesta a ping - actualizar last_ping
            connection_info = websocket_manager.active_connections.get(connection_id)
            if connection_info:
                connection_info.last_ping = data.get("timestamp", connection_info.last_ping)
                
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


async def get_dashboard_data(user_info: dict) -> dict:
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


async def get_metrics_data(user_info: dict) -> dict:
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


async def handle_subscription(connection_id: str, data: dict, user_info: Optional[dict]):
    """
    Maneja suscripciones a eventos específicos.
    
    Args:
        connection_id: ID de la conexión
        data: Datos de suscripción
        user_info: Información del usuario
    """
    events = data.get("events", [])
    
    ws_router_logger.info(
        f"Cliente {connection_id} suscrito a eventos",
        events=events,
        user_id=user_info.get("user_id") if user_info else None
    )
    
    # TODO: Implementar lógica de suscripciones específicas
    response = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={
            "title": "Suscripción confirmada",
            "content": f"Suscrito a {len(events)} tipos de eventos",
            "level": "info"
        }
    )
    await websocket_manager.send_to_connection(connection_id, response)


async def handle_unsubscription(connection_id: str, data: dict, user_info: Optional[dict]):
    """
    Maneja desuscripciones de eventos.
    
    Args:
        connection_id: ID de la conexión
        data: Datos de desuscripción
        user_info: Información del usuario
    """
    events = data.get("events", [])
    
    ws_router_logger.info(
        f"Cliente {connection_id} desuscrito de eventos",
        events=events,
        user_id=user_info.get("user_id") if user_info else None
    )
    
    # TODO: Implementar lógica de desuscripciones


@router.get("/stats")
async def get_websocket_stats():
    """
    Endpoint para obtener estadísticas de WebSockets.
    
    Returns:
        dict: Estadísticas de conexiones activas
    """
    stats = websocket_manager.get_stats()
    
    ws_router_logger.debug("Estadísticas WebSocket solicitadas", stats=stats)
    
    return {
        "status": "ok",
        "stats": stats,
        "timestamp": "2025-09-22T04:55:00Z"
    }