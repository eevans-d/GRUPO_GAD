"""
Router para operaciones de caché y monitoreo.

Expone endpoints para consultar estadísticas del caché
y realizar operaciones administrativas (invalidación).
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from src.core.cache import CacheService, get_cache_service
from src.core.logging import get_logger

cache_router_logger = get_logger(__name__)
router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats", response_model=dict[str, Any])
async def get_cache_stats(
    cache: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """
    Obtiene estadísticas del caché Redis.
    
    Returns:
        - connected: bool - Estado de conexión
        - keys_count: int - Número de keys con prefijo "gad:"
        - keyspace_hits: int - Hits acumulados
        - keyspace_misses: int - Misses acumulados
        - hit_rate: float - Porcentaje de hit rate
        - evicted_keys: int - Keys expulsadas por memoria
        - prefix: str - Prefijo configurado
    """
    try:
        stats = await cache.get_stats()
        return stats
    except Exception as e:
        cache_router_logger.error(f"Error obteniendo stats de caché: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}",
        )


@router.post("/invalidate/{key}")
async def invalidate_cache_key(
    key: str,
    cache: CacheService = Depends(get_cache_service),
) -> JSONResponse:
    """
    Invalida (elimina) una key específica del caché.
    
    Args:
        key: Clave a eliminar (sin prefijo)
        
    Returns:
        Confirmación de eliminación
    """
    try:
        deleted = await cache.delete(key)
        if deleted:
            cache_router_logger.info(f"Cache key invalidada: {key}")
            return JSONResponse(
                content={"message": f"Key '{key}' eliminada del caché"},
                status_code=status.HTTP_200_OK,
            )
        else:
            return JSONResponse(
                content={"message": f"Key '{key}' no existía en el caché"},
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        cache_router_logger.error(f"Error invalidando key {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando key: {str(e)}",
        )


@router.post("/invalidate-pattern/{pattern:path}")
async def invalidate_cache_pattern(
    pattern: str,
    cache: CacheService = Depends(get_cache_service),
) -> JSONResponse:
    """
    Invalida todas las keys que coincidan con un patrón.
    
    Args:
        pattern: Patrón con wildcards (ej: "stats:user:*")
        
    Returns:
        Número de keys eliminadas
        
    Examples:
        - POST /cache/invalidate-pattern/stats:user:*
        - POST /cache/invalidate-pattern/stats:*
    """
    try:
        deleted = await cache.delete_pattern(pattern)
        cache_router_logger.info(f"Cache pattern invalidado: {pattern}, eliminados: {deleted}")
        return JSONResponse(
            content={
                "message": f"Patrón '{pattern}' invalidado",
                "deleted_count": deleted,
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        cache_router_logger.error(f"Error invalidando patrón {pattern}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando patrón: {str(e)}",
        )


@router.post("/clear")
async def clear_cache(
    cache: CacheService = Depends(get_cache_service),
) -> JSONResponse:
    """
    Limpia TODAS las keys del caché con prefijo "gad:".
    
    ⚠️ USAR CON PRECAUCIÓN: Esta operación es irreversible.
    
    Returns:
        Confirmación de limpieza
    """
    try:
        await cache.clear()
        cache_router_logger.warning("Cache completamente limpiado (CLEAR)")
        return JSONResponse(
            content={"message": "Caché limpiado exitosamente"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        cache_router_logger.error(f"Error limpiando caché: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando caché: {str(e)}",
        )
