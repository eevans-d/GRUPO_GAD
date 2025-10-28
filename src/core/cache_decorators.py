"""
Cache Decorators for FastAPI Endpoints

Provides decorators for automatic caching of endpoint results with:
- Configurable TTL
- Automatic invalidation on mutations
- Key generation from function args
- Async support
"""

import functools
import hashlib
import json
from typing import Any, Awaitable, Callable, Optional, TypeVar

from src.core.logging import get_logger

cache_logger = get_logger(__name__)

# Type variables
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# Permite a los tests inyectar un CacheService falso parcheando este módulo.
# En producción, si este override es None, usaremos src.core.cache._cache_service.
_cache_service: Optional[Any] = None


def _get_effective_cache_service() -> Optional[Any]:
    """Devuelve el CacheService efectivo.

    Prioridad:
    1) Variable local parcheable en tests: src.core.cache_decorators._cache_service
    2) Instancia global real: src.core.cache._cache_service
    """
    if _cache_service is not None:
        return _cache_service
    try:
        from src.core.cache import _cache_service as _global_cache_service  # type: ignore
        return _global_cache_service
    except Exception:
        return None


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a cache key from function name and arguments.
    
    Args:
        func_name: Name of the function being cached
        args: Positional arguments (excluding self/db)
        kwargs: Keyword arguments (excluding db)
    
    Returns:
        Cache key string
    """
    # Build cache key from args/kwargs, excluding AsyncSession (db) and Depends()
    cacheable_args = []
    
    for arg in args:
        # Skip non-serializable types
        if not isinstance(arg, (str, int, float, bool, type(None))):
            continue
        cacheable_args.append(str(arg))
    
    # Filter kwargs - skip technical ones
    cacheable_kwargs = {
        k: str(v) for k, v in kwargs.items()
        if not k.startswith("_") and k not in ["db", "current_user"] 
        and isinstance(v, (str, int, float, bool, type(None)))
    }
    
    # Create serializable dict for hashing
    key_data = {
        "func": func_name,
        "args": cacheable_args,
        "kwargs": sorted(cacheable_kwargs.items())
    }
    
    # Create hash
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"{func_name}:{key_hash}"


def cache_result(
    ttl_seconds: int = 300,
    key_prefix: str = "endpoint"
) -> Callable[[F], F]:
    """
    Decorator to cache endpoint results in Redis.
    
    Usage:
        @cache_result(ttl_seconds=300)
        async def get_usuarios(db: AsyncSession = Depends(get_db_session)):
            # ... endpoint code
    
    Args:
        ttl_seconds: Time to live in seconds (default: 300 = 5 minutes)
        key_prefix: Prefix for cache key (helps organize by endpoint type)
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Skip if cache not initialized
            _svc = _get_effective_cache_service()
            if _svc is None:
                cache_logger.debug(f"Cache not initialized, calling {func.__name__} directly")
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = _generate_cache_key(f"{key_prefix}:{func.__name__}", args, kwargs)
            
            try:
                # Try to get from cache
                cached_result = await _svc.get(cache_key)
                if cached_result is not None:
                    cache_logger.debug(f"Cache HIT: {cache_key}")
                    return cached_result
                
                cache_logger.debug(f"Cache MISS: {cache_key}")
            except Exception as e:
                cache_logger.warning(f"Cache get error for {cache_key}: {e}")
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                await _svc.set(
                    key=cache_key,
                    value=result,
                    ttl=ttl_seconds  # TTL in seconds
                )
                cache_logger.debug(f"Cached result for {cache_key} (TTL: {ttl_seconds}s)")
            except Exception as e:
                cache_logger.warning(f"Cache set error for {cache_key}: {e}")
            
            return result
        
        return wrapper  # type: ignore
    
    return decorator


def invalidate_cache(pattern: str) -> Callable[[F], F]:
    """
    Decorator to invalidate cache entries matching a pattern after function execution.
    
    Usage:
        @invalidate_cache("endpoint:create_usuario:*")
        async def create_usuario(usuario_in: UsuarioCreate):
            # ... create user
    
    Args:
        pattern: Cache key pattern to invalidate (supports * wildcard)
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            _svc = _get_effective_cache_service()
            # Call the actual function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache after successful execution
            if _svc is not None:
                try:
                    deleted_count = await _svc.delete_pattern(pattern)
                    if deleted_count > 0:
                        cache_logger.debug(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
                except Exception as e:
                    cache_logger.warning(f"Cache invalidation error for pattern {pattern}: {e}")
            
            return result
        
        return wrapper  # type: ignore
    
    return decorator


def cache_and_invalidate(
    ttl_seconds: int = 300,
    key_prefix: str = "endpoint",
    invalidate_patterns: Optional[list[str]] = None
) -> Callable[[F], F]:
    """
    Decorator that combines caching and automatic invalidation.
    
    Caches the result AND invalidates related cache patterns.
    
    Usage:
        @cache_and_invalidate(
            ttl_seconds=600,
            invalidate_patterns=["endpoint:list_usuarios:*"]
        )
        async def create_usuario(usuario_in: UsuarioCreate):
            # ... create user
    
    Args:
        ttl_seconds: Time to live for cache
        key_prefix: Prefix for cache key
        invalidate_patterns: List of patterns to invalidate after execution
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Invalidate related cache patterns
            if invalidate_patterns:
                _svc = _get_effective_cache_service()
                if _svc is not None:
                    for pattern in invalidate_patterns:
                        try:
                            deleted_count = await _svc.delete_pattern(pattern)
                            if deleted_count > 0:
                                cache_logger.debug(f"Invalidated {deleted_count} entries: {pattern}")
                        except Exception as e:
                            cache_logger.warning(f"Cache invalidation error for {pattern}: {e}")
            
            return result
        
        return wrapper  # type: ignore
    
    return decorator
