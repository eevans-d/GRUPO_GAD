"""
Servicio de caché con Redis para mejorar rendimiento.

Este módulo provee una capa de abstracción sobre Redis para
cachear datos frecuentemente consultados (estadísticas, listados, etc.).
"""

import json
from datetime import timedelta
from typing import Any, Optional

from src.core.logging import get_logger

# Logger estructurado
cache_logger = get_logger(__name__)


class CacheService:
    """
    Servicio de caché con Redis.
    
    Maneja operaciones de get/set/delete/clear con soporte para:
    - TTL (Time To Live) configurable
    - Serialización automática JSON
    - Manejo robusto de errores
    - Prefijos para organizar keys
    """

    def __init__(self, redis_url: str, prefix: str = "gad:"):
        """
        Inicializa el servicio de caché.
        
        Args:
            redis_url: URL de conexión a Redis (ej: redis://localhost:6379/0)
            prefix: Prefijo para todas las keys (ej: "gad:", "test:")
        """
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis: Optional[Any] = None
        self._connected = False

    async def connect(self) -> None:
        """Conecta al servidor Redis."""
        if self._connected:
            cache_logger.warning("CacheService ya está conectado")
            return

        try:
            from redis import asyncio as aioredis

            from urllib.parse import urlparse
            import os
            parsed = urlparse(self.redis_url)
            insecure_tls = (
                os.getenv("REDIS_INSECURE_TLS") in ("1", "true", "True")
                and parsed.hostname and parsed.hostname.endswith(".upstash.io")
            )
            extra_kwargs = dict(
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                retry_on_timeout=True,
            )
            if insecure_tls and parsed.scheme == "rediss":
                # Mitigación temporal: desactivar validación de certificado
                extra_kwargs["ssl_cert_reqs"] = None
                cache_logger.warning(
                    "REDIS_INSECURE_TLS=1 activo: deshabilitando verificación de certificado TLS para Redis"
                )
            self._redis = aioredis.from_url(
                self.redis_url,
                **extra_kwargs,
            )
            
            # Verificar conexión
            await self._redis.ping()
            self._connected = True
            cache_logger.info(
                "CacheService conectado exitosamente",
                redis_url=self.redis_url,
                prefix=self.prefix,
            )

        except ImportError:
            cache_logger.error("redis[asyncio] no está instalado")
            raise
        except Exception as e:
            # Fallback para Upstash: si falla TLS, intentar puerto no-TLS 6380
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.redis_url)
                if parsed.hostname and parsed.hostname.endswith(".upstash.io"):
                    userinfo = ""
                    if parsed.username or parsed.password:
                        u = parsed.username or ""
                        p = parsed.password or ""
                        userinfo = f"{u}:{p}@" if (u or p) else ""
                    fallback_url = f"redis://{userinfo}{parsed.hostname}:6380{parsed.path or '/0'}"
                    cache_logger.warning(
                        "Fallo TLS al conectar a Upstash; intentando fallback no-TLS en 6380",
                        error=str(e),
                    )
                    from redis import asyncio as aioredis2
                    self._redis = aioredis2.from_url(
                        fallback_url,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        socket_keepalive=True,
                        health_check_interval=30,
                        retry_on_timeout=True,
                    )
                    await self._redis.ping()
                    self.redis_url = fallback_url
                    self._connected = True
                    cache_logger.info("CacheService conectado (fallback no-TLS)")
                    return
            except Exception as e2:
                cache_logger.error(
                    "Error conectando a Redis (TLS y fallback)",
                    error_primary=str(e),
                    error_fallback=str(e2),
                )
            # Si no hubo fallback o también falló, mantener estado desconectado y relanzar
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Desconecta del servidor Redis."""
        if self._redis is not None and self._connected:
            try:
                await self._redis.aclose()
                cache_logger.info("CacheService desconectado")
            except Exception as e:
                cache_logger.error(f"Error desconectando Redis: {e}")
            finally:
                self._redis = None
                self._connected = False

    def _make_key(self, key: str) -> str:
        """Construye la key completa con prefijo."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché.
        
        Args:
            key: Clave sin prefijo (ej: "stats:user:123")
            
        Returns:
            Valor deserializado o None si no existe/error
        """
        if not self._connected or self._redis is None:
            cache_logger.warning("get() llamado sin conexión Redis")
            return None

        full_key = self._make_key(key)

        try:
            value = await self._redis.get(full_key)
            if value is None:
                cache_logger.debug("Cache MISS", key=full_key)
                return None

            # Deserializar JSON
            deserialized = json.loads(value)
            cache_logger.debug("Cache HIT", key=full_key)
            return deserialized

        except json.JSONDecodeError as e:
            cache_logger.error(f"Error deserializando cache key {full_key}: {e}")
            # Eliminar key corrupta
            await self.delete(key)
            return None
        except Exception as e:
            cache_logger.error(f"Error obteniendo cache key {full_key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Guarda un valor en el caché.
        
        Args:
            key: Clave sin prefijo (ej: "stats:user:123")
            value: Valor a cachear (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = sin expiración)
            
        Returns:
            True si se guardó exitosamente, False en caso de error
        """
        if not self._connected or self._redis is None:
            cache_logger.warning("set() llamado sin conexión Redis")
            return False

        full_key = self._make_key(key)

        try:
            # Serializar a JSON
            serialized = json.dumps(value, default=str)  # default=str para datetime
            
            # Guardar en Redis con TTL opcional
            if ttl is not None:
                await self._redis.setex(full_key, ttl, serialized)
            else:
                await self._redis.set(full_key, serialized)

            cache_logger.debug("Cache SET", key=full_key, ttl=ttl)
            return True

        except (TypeError, ValueError) as e:
            cache_logger.error(f"Error serializando valor para key {full_key}: {e}")
            return False
        except Exception as e:
            cache_logger.error(f"Error guardando cache key {full_key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Elimina una key del caché.
        
        Args:
            key: Clave sin prefijo
            
        Returns:
            True si se eliminó, False si no existía o hubo error
        """
        if not self._connected or self._redis is None:
            cache_logger.warning("delete() llamado sin conexión Redis")
            return False

        full_key = self._make_key(key)

        try:
            deleted = await self._redis.delete(full_key)
            if deleted > 0:
                cache_logger.debug("Cache DELETE", key=full_key)
                return True
            return False
        except Exception as e:
            cache_logger.error(f"Error eliminando cache key {full_key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Elimina todas las keys que coincidan con un patrón.
        
        Args:
            pattern: Patrón con wildcards (ej: "stats:user:*")
            
        Returns:
            Número de keys eliminadas
        """
        if not self._connected or self._redis is None:
            cache_logger.warning("delete_pattern() llamado sin conexión Redis")
            return 0

        full_pattern = self._make_key(pattern)

        try:
            # Buscar keys que coincidan
            keys = []
            async for key in self._redis.scan_iter(match=full_pattern):
                keys.append(key)

            if not keys:
                return 0

            # Eliminar en batch
            deleted = await self._redis.delete(*keys)
            cache_logger.info(
                "Cache DELETE PATTERN",
                pattern=full_pattern,
                deleted=deleted,
            )
            return deleted

        except Exception as e:
            cache_logger.error(f"Error eliminando patrón {full_pattern}: {e}")
            return 0

    async def clear(self) -> bool:
        """
        Limpia TODAS las keys con el prefijo configurado.
        
        ⚠️ USAR CON PRECAUCIÓN en producción.
        
        Returns:
            True si se limpió exitosamente
        """
        if not self._connected or self._redis is None:
            cache_logger.warning("clear() llamado sin conexión Redis")
            return False

        try:
            deleted = await self.delete_pattern("*")
            cache_logger.warning(
                "Cache CLEAR ejecutado",
                deleted=deleted,
                prefix=self.prefix,
            )
            return True
        except Exception as e:
            cache_logger.error(f"Error limpiando cache: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Dict con métricas (keys_count, memory_used, hit_rate, etc.)
        """
        if not self._connected or self._redis is None:
            return {
                "connected": False,
                "error": "Redis no conectado",
            }

        try:
            # INFO stats de Redis
            info = await self._redis.info("stats")
            
            # Contar keys con nuestro prefijo
            key_count = 0
            async for _ in self._redis.scan_iter(match=f"{self.prefix}*"):
                key_count += 1

            return {
                "connected": True,
                "keys_count": key_count,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0),
                ),
                "evicted_keys": info.get("evicted_keys", 0),
                "prefix": self.prefix,
            }

        except Exception as e:
            cache_logger.error(f"Error obteniendo stats: {e}")
            return {
                "connected": True,
                "error": str(e),
            }

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calcula el hit rate del caché."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Instancia global (será inicializada en startup de FastAPI)
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Dependency injection para FastAPI.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(cache: CacheService = Depends(get_cache_service)):
            data = await cache.get("mykey")
    """
    if _cache_service is None:
        raise RuntimeError("CacheService no ha sido inicializado")
    return _cache_service


def init_cache_service(redis_url: str, prefix: str = "gad:") -> CacheService:
    """
    Inicializa la instancia global de CacheService.
    
    Debe ser llamado en el startup de FastAPI.
    
    Args:
        redis_url: URL de conexión a Redis
        prefix: Prefijo para keys
        
    Returns:
        Instancia de CacheService
    """
    global _cache_service
    _cache_service = CacheService(redis_url=redis_url, prefix=prefix)
    cache_logger.info("CacheService global inicializado", prefix=prefix)
    return _cache_service


async def shutdown_cache_service() -> None:
    """
    Cierra la conexión Redis al hacer shutdown de FastAPI.
    """
    global _cache_service
    if _cache_service is not None:
        await _cache_service.disconnect()
        _cache_service = None
        cache_logger.info("CacheService global cerrado")
