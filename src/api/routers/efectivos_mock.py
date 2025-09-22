# -*- coding: utf-8 -*-
"""
Endpoint para simular efectivos/usuarios en el mapa.

Extiende el router geo con datos simulados de efectivos 
hasta que se implemente geolocalización real.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta
from random import uniform, choice

from fastapi import APIRouter, Depends, Query
from src.api.dependencies import get_current_active_user
from src.api.routers.geo import _haversine_approx_distance_m

router = APIRouter()

# Ubicaciones base para efectivos simulados en Buenos Aires
EFECTIVOS_BASE_LOCATIONS = [
    # Comisarías y destacamentos principales
    (-34.6037, -58.3816, "1era Comisaría - Centro"),
    (-34.6092, -58.3732, "Prefectura - Puerto Madero"), 
    (-34.5889, -58.3974, "4ta Comisaría - Recoleta"),
    (-34.6158, -58.3731, "3era Comisaría - San Telmo"),
    (-34.5493, -58.4582, "13ra Comisaría - Belgrano"),
    (-34.6283, -58.3712, "2da Comisaría - La Boca"),
    (-34.5836, -58.4425, "14ta Comisaría - Palermo"),
    (-34.6472, -58.4642, "5ta Comisaría - Barracas"),
    (-34.7297, -58.2663, "Comisaría Quilmes"),
    (-34.5019, -58.5161, "Comisaría San Isidro"),
]

EFECTIVOS_NAMES = [
    "Cabo García", "Sgt. Rodriguez", "Of. Martinez", "Cabo López", 
    "Sgt. Fernández", "Of. González", "Cabo Pérez", "Sgt. Díaz",
    "Of. Morales", "Cabo Silva", "Sgt. Romero", "Of. Castro",
    "Cabo Herrera", "Sgt. Vargas", "Of. Mendoza", "Cabo Torres"
]

@router.get("/geo/efectivos/mock", summary="Efectivos simulados para desarrollo")
async def mock_efectivos(
    *,
    center_lat: float = Query(..., description="Latitud del centro"),
    center_lng: float = Query(..., description="Longitud del centro"), 
    radius_m: int = Query(10000, ge=100, le=50000, description="Radio en metros"),
    count: int = Query(8, ge=1, le=20, description="Número de efectivos a simular"),
    current_user: Any = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Simula efectivos/usuarios en el mapa para desarrollo y testing.
    
    Genera efectivos ficticios distribuidos alrededor del centro especificado
    con estados simulados (patrullando, en base, respondiendo, etc).
    
    Returns:
        usuarios: Lista de efectivos simulados con posiciones y estados
    """
    usuarios: List[Dict[str, Any]] = []
    
    # Seleccionar ubicaciones base dentro del radio
    
    locations_in_range = [
        (lat, lng, name) for lat, lng, name in EFECTIVOS_BASE_LOCATIONS
        if _haversine_approx_distance_m(center_lat, center_lng, lat, lng) <= radius_m
    ]
    
    # Si no hay ubicaciones base en rango, crear algunas aleatorias cerca del centro
    if not locations_in_range:
        # Distribución aleatoria en un radio de ~2km del centro
        for i in range(min(count, 6)):
            # Offset aleatorio en grados (aprox 0.02 grados = ~2km)
            lat_offset = uniform(-0.02, 0.02)
            lng_offset = uniform(-0.02, 0.02)
            locations_in_range.append((
                center_lat + lat_offset,
                center_lng + lng_offset,
                f"Patrulla Móvil {i+1}"
            ))
    
    # Generar efectivos simulados
    estados_disponibles = ["patrullando", "en_base", "respondiendo", "en_transito", "disponible"]
    
    for i in range(min(count, len(locations_in_range) + 3)):
        if i < len(locations_in_range):
            base_lat, base_lng, location_name = locations_in_range[i]
            # Pequeña variación de posición (patrullando cerca de la base)
            lat = base_lat + uniform(-0.005, 0.005)  # ~500m variación
            lng = base_lng + uniform(-0.005, 0.005)
        else:
            # Efectivos adicionales en posiciones aleatorias
            lat = center_lat + uniform(-0.015, 0.015)
            lng = center_lng + uniform(-0.015, 0.015)
            location_name = f"Zona Patrullaje {i-len(locations_in_range)+1}"
        
        # Calcular distancia del centro
        distance_m = int(_haversine_approx_distance_m(center_lat, center_lng, lat, lng))
        
        # Estado simulado
        estado = choice(estados_disponibles)
        
        # Nombre del efectivo
        nombre = EFECTIVOS_NAMES[i % len(EFECTIVOS_NAMES)]
        
        # Simular ID único
        entity_id = f"EF-{datetime.now().year}-{1000 + i:04d}"
        
        usuarios.append({
            "lat": lat,
            "lng": lng,
            "entity_id": entity_id,
            "distance_m": distance_m,
            "nombre": nombre,
            "estado": estado,
            "ubicacion": location_name,
            "ultima_actualizacion": (datetime.now() - timedelta(minutes=uniform(1, 15))).isoformat(),
            # Campos adicionales para el popup del mapa
            "rango": choice(["Cabo", "Sargento", "Oficial"]),
            "unidad": choice(["Móvil 101", "Móvil 205", "Móvil 318", "Pie"]),
            "radio_activo": choice([True, False, True, True])  # 75% con radio activo
        })
    
    return {
        "usuarios": usuarios,
        "metadata": {
            "tipo": "simulacion",
            "centro": {"lat": center_lat, "lng": center_lng},
            "radio_m": radius_m,
            "efectivos_simulados": len(usuarios),
            "generado_en": datetime.now().isoformat()
        }
    }