"""
Endpoint de estadísticas optimizado con caché Redis.

Este módulo implementa endpoints para obtener estadísticas
de tareas con caché en Redis para mejorar el rendimiento.
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_user
from src.api.models.tarea import Tarea
from src.api.models.usuario import Usuario
from src.core.cache import CacheService, get_cache_service
from src.core.database import get_db_session
from src.core.logging import get_logger
from src.shared.constants import TaskStatus

stats_logger = get_logger(__name__)
router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/user/{user_id}")  # type: ignore[misc]
async def get_user_statistics(
    user_id: int,
    days: int = Query(default=30, ge=1, le=365, description="Días hacia atrás"),
    use_cache: bool = Query(default=True, description="Usar caché Redis"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
    current_user: Usuario = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Obtiene estadísticas de tareas de un usuario con caché opcional.
    
    **Métricas incluidas:**
    - total: Tareas totales en el período
    - completadas: Tareas finalizadas
    - en_progreso: Tareas activas
    - promedio_duracion_horas: Tiempo promedio de finalización
    - productividad_diaria: Tareas completadas por día
    - estados: Distribución por estado
    
    **Caché:**
    - TTL: 5 minutos (300 segundos)
    - Key: `stats:user:{user_id}:days:{days}`
    - Invalidación: Al crear/finalizar tareas (TBD)
    
    Args:
        user_id: ID del usuario en la base de datos
        days: Número de días hacia atrás (default: 30)
        use_cache: Si False, fuerza recálculo (bypass caché)
        
    Returns:
        Diccionario con estadísticas del usuario
    """
    # Verificar permisos (el usuario solo puede ver sus propias stats)
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estadísticas de otro usuario",
        )
    
    cache_key = f"stats:user:{user_id}:days:{days}"
    
    # Intentar obtener del caché si está habilitado
    if use_cache:
        cached_stats = await cache.get(cache_key)
        if cached_stats is not None:
            stats_logger.info(
                "Estadísticas servidas desde caché",
                user_id=user_id,
                days=days,
                cache_key=cache_key,
            )
            # Agregar metadata de caché
            cached_stats["_cache"] = {
                "hit": True,
                "source": "redis",
                "key": cache_key,
            }
            return cached_stats
    
    # Calcular estadísticas desde DB
    stats_logger.info(
        "Calculando estadísticas desde DB",
        user_id=user_id,
        days=days,
        cache_enabled=use_cache,
    )
    
    try:
        # Fecha límite
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query: Tareas del usuario en el período
        stmt = (
            select(Tarea)
            .where(Tarea.delegado_usuario_id == user_id)
            .where(Tarea.created_at >= cutoff_date)
            .where(Tarea.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        tareas = result.scalars().all()
        
        # Calcular métricas
        total = len(tareas)
        completadas = sum(1 for t in tareas if t.estado == TaskStatus.COMPLETED)
        en_progreso = sum(1 for t in tareas if t.estado == TaskStatus.IN_PROGRESS)
        programadas = sum(1 for t in tareas if t.estado == TaskStatus.PROGRAMMED)
        canceladas = sum(1 for t in tareas if t.estado == TaskStatus.CANCELLED)
        pausadas = sum(1 for t in tareas if t.estado == TaskStatus.PAUSED)
        
        # Calcular duración promedio (solo tareas completadas con inicio y fin)
        duraciones = []
        for tarea in tareas:
            if (
                tarea.estado == TaskStatus.COMPLETED
                and tarea.inicio_real
                and tarea.fin_real
            ):
                duracion_horas = (tarea.fin_real - tarea.inicio_real).total_seconds() / 3600
                duraciones.append(duracion_horas)
        
        promedio_duracion = (
            sum(duraciones) / len(duraciones) if duraciones else 0.0
        )
        
        # Productividad diaria
        productividad = completadas / days if days > 0 else 0.0
        
        stats = {
            "user_id": user_id,
            "period_days": days,
            "total": total,
            "completadas": completadas,
            "en_progreso": en_progreso,
            "programadas": programadas,
            "canceladas": canceladas,
            "pausadas": pausadas,
            "promedio_duracion_horas": round(promedio_duracion, 2),
            "productividad_diaria": round(productividad, 2),
            "estados": {
                "COMPLETED": completadas,
                "IN_PROGRESS": en_progreso,
                "PROGRAMMED": programadas,
                "CANCELLED": canceladas,
                "PAUSED": pausadas,
            },
            "calculated_at": datetime.utcnow().isoformat(),
            "_cache": {
                "hit": False,
                "source": "database",
            },
        }
        
        # Guardar en caché con TTL de 5 minutos
        if use_cache:
            await cache.set(cache_key, stats, ttl=300)
            stats_logger.info(
                "Estadísticas guardadas en caché",
                user_id=user_id,
                cache_key=cache_key,
                ttl=300,
            )
        
        return stats
        
    except Exception as e:
        stats_logger.error(
            f"Error calculando estadísticas para user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculando estadísticas: {str(e)}",
        )


@router.post("/invalidate/user/{user_id}")  # type: ignore[misc]
async def invalidate_user_statistics(
    user_id: int,
    cache: CacheService = Depends(get_cache_service),
    current_user: Usuario = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Invalida el caché de estadísticas de un usuario.
    
    Se debe llamar este endpoint cuando:
    - El usuario crea una nueva tarea
    - El usuario finaliza una tarea
    - Se modifica una tarea existente
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Confirmación de invalidación
    """
    # Verificar permisos
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para invalidar estadísticas de otro usuario",
        )
    
    try:
        # Invalidar todas las variaciones de días (7, 30, 90, etc.)
        pattern = f"stats:user:{user_id}:*"
        deleted = await cache.delete_pattern(pattern)
        
        stats_logger.info(
            "Caché de estadísticas invalidado",
            user_id=user_id,
            pattern=pattern,
            deleted=deleted,
        )
        
        return {
            "message": f"Estadísticas del usuario {user_id} invalidadas",
            "deleted_keys": deleted,
            "pattern": pattern,
        }
        
    except Exception as e:
        stats_logger.error(f"Error invalidando estadísticas de user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando estadísticas: {str(e)}",
        )
