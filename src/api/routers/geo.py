# -*- coding: utf-8 -*-
"""
Router geoespacial para el dashboard.

Provee el endpoint /api/v1/geo/map/view consumido por dashboard.js
para obtener:
- usuarios (efectivos) cercanos al centro
- tareas (incluye emergencias segun prioridad)

Nota: Como aún no hay geolocalización en usuarios/efectivos,
devolvemos una lista vacía para "usuarios" y usamos la ubicación
de las tareas (ubicacion_lat/lon) si está disponible.
"""

from __future__ import annotations

from math import cos, radians, hypot
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_user
from src.api.models.tarea import Tarea
from src.core.database import get_db_session
from src.shared.constants import TaskPriority

router = APIRouter()


def _haversine_approx_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia aproximada en metros usando proyección local simple.

    Suficiente para radios pequeños (<= 20km) sin depender de paquetes externos.
    """
    # 1 grado latitud ~ 111_320 m; longitud escala con cos(lat)
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 40075000.0 * cos(radians(lat1)) / 360.0
    dlat_m: float = (lat2 - lat1) * m_per_deg_lat
    dlon_m: float = (lon2 - lon1) * m_per_deg_lon
    return hypot(dlat_m, dlon_m)


@router.get("/geo/map/view", summary="Vista de mapa para dashboard")
async def map_view(
    *,
    center_lat: float = Query(..., description="Latitud del centro"),
    center_lng: float = Query(..., description="Longitud del centro"),
    radius_m: int = Query(10000, ge=100, le=100000, description="Radio en metros"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Any = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Retorna los datos para renderizar el mapa:
    - usuarios: [] por ahora (placeholder)
    - tareas: tareas con ubicacion dentro del radio dado

    Formato esperado por dashboard.js:
    {
      "usuarios": [{"lat": float, "lng": float, "entity_id": str, "distance_m": int}],
      "tareas": [{"lat": float, "lng": float, "entity_id": str, "distance_m": int, "priority": "CRITICA|..."}]
    }
    """
    # 1) Usuarios/efectivos: placeholder hasta tener geolocalización
    usuarios: List[Dict[str, Any]] = []

    # 2) Seleccionar tareas con coordenadas no nulas
    stmt = select(Tarea).where(
        and_(Tarea.ubicacion_lat.is_not(None), Tarea.ubicacion_lon.is_not(None))
    )
    result = await db.execute(stmt)
    tareas_db: List[Tarea] = list(result.scalars())

    tareas: List[Dict[str, Any]] = []
    for t in tareas_db:
        try:
            lat = float(t.ubicacion_lat) if t.ubicacion_lat is not None else None
            lon = float(t.ubicacion_lon) if t.ubicacion_lon is not None else None
        except Exception:
            lat = None
            lon = None

        if lat is None or lon is None:
            continue

        dist_m = _haversine_approx_distance_m(center_lat, center_lng, lat, lon)
        if dist_m <= float(radius_m):
            # Mapear prioridad a texto esperado por frontend: usa nombre en mayúsculas
            priority_str = "MEDIUM"
            try:
                # Si es Enum TaskPriority (int Enum), convertir por valor
                if isinstance(t.prioridad, TaskPriority):
                    priority_val = int(t.prioridad)
                else:
                    priority_val = int(t.prioridad) if t.prioridad is not None else 2
                mapping = {
                    1: "BAJA",
                    2: "MEDIA",
                    3: "ALTA",
                    4: "URGENTE",
                    5: "CRITICA",
                }
                priority_str = mapping.get(priority_val, "MEDIA")
            except Exception:
                priority_str = "MEDIA"

            tareas.append(
                {
                    "lat": lat,
                    "lng": lon,
                    "entity_id": str(t.uuid),
                    "distance_m": int(round(dist_m)),
                    "priority": priority_str,
                }
            )

    return {"usuarios": usuarios, "tareas": tareas}
