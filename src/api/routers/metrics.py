# -*- coding: utf-8 -*-
"""
Router de métricas para GRUPO_GAD.

Este router expone endpoints para métricas de Prometheus.
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.core.logging import get_logger
from src.core.websockets import websocket_manager
from src.observability.metrics import update_all_metrics_from_manager

# Logger para el router de métricas
metrics_logger = get_logger("api.routers.metrics")

# Router para métricas
router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get("/prometheus", response_class=Response)
async def prometheus_metrics() -> Response:
    """
    Endpoint para métricas en formato Prometheus.
    Estas métricas pueden ser consumidas por Prometheus para monitoreo.
    """
    # Actualizar métricas desde el estado actual del WebSocketManager
    try:
        # Obtener estadísticas actuales del WebSocketManager
        ws_stats = websocket_manager.get_stats()
        # Actualizar métricas Prometheus con estas estadísticas
        update_all_metrics_from_manager(ws_stats)
    except Exception as e:
        metrics_logger.error(f"Error actualizando métricas: {str(e)}")
    
    # Generar respuesta en formato Prometheus
    content = generate_latest()
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)