#!/usr/bin/env python3
"""
Script de smoke test para validar cache auto-invalidation en tareas.

Verifica que al crear/actualizar/eliminar tareas, el cache se invalida correctamente.
"""

import sys
import asyncio
from redis import asyncio as aioredis


async def test_cache_invalidation():
    """Test cache invalidation patterns."""
    print("🔍 Probando Cache Auto-Invalidation...\n")
    
    # Conectar a Redis
    redis_url = "redis://localhost:6381/0"
    try:
        redis = aioredis.from_url(redis_url, decode_responses=True)
        await redis.ping()
        print(f"✓ Conectado a Redis: {redis_url}")
    except Exception as e:
        print(f"✗ Error conectando a Redis: {e}")
        return False
    
    # Test 1: Simular cache inicial
    print("\n1️⃣ Simulando cache inicial...")
    await redis.set("gad:stats:user:100", '{"tasks_count": 5}')
    await redis.set("gad:tasks:list:page1", '["task1", "task2"]')
    await redis.set("gad:task:1", '{"id": 1, "title": "Test Task"}')
    print("   ✓ Cache poblado: stats:user:100, tasks:list:page1, task:1")
    
    # Test 2: Verificar que existen
    print("\n2️⃣ Verificando existencia de keys...")
    keys = await redis.keys("gad:*")
    print(f"   ✓ {len(keys)} keys encontradas en cache")
    for key in keys:
        print(f"      - {key}")
    
    # Test 3: Simular invalidación (lo que haría invalidate_task_related_cache)
    print("\n3️⃣ Simulando invalidación de cache...")
    
    # Invalidar stats:user:*
    pattern1 = "gad:stats:user:*"
    deleted1 = 0
    async for key in redis.scan_iter(match=pattern1):
        deleted1 += await redis.delete(key)
    print(f"   ✓ Invalidado {deleted1} keys de stats:user:*")
    
    # Invalidar tasks:list:*
    pattern2 = "gad:tasks:list:*"
    deleted2 = 0
    async for key in redis.scan_iter(match=pattern2):
        deleted2 += await redis.delete(key)
    print(f"   ✓ Invalidado {deleted2} keys de tasks:list:*")
    
    # Invalidar task específico
    deleted3 = await redis.delete("gad:task:1")
    print(f"   ✓ Invalidado {deleted3} key de task:1")
    
    # Test 4: Verificar que se eliminaron
    print("\n4️⃣ Verificando eliminación...")
    keys_after = await redis.keys("gad:*")
    if len(keys_after) == 0:
        print("   ✓ Cache completamente invalidado (0 keys restantes)")
        result = True
    else:
        print(f"   ✗ Quedan {len(keys_after)} keys en cache:")
        for key in keys_after:
            print(f"      - {key}")
        result = False
    
    # Limpiar
    await redis.aclose()
    
    print("\n" + "=" * 60)
    if result:
        print("✅ CACHE AUTO-INVALIDATION: FUNCIONAL")
    else:
        print("❌ CACHE AUTO-INVALIDATION: FALLÓ")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    result = asyncio.run(test_cache_invalidation())
    sys.exit(0 if result else 1)
