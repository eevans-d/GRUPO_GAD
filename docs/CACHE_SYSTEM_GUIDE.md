# Sistema de Caché para Endpoints - Guía de Implementación

## Visión General

El sistema de caché utiliza Redis para mejorar el rendimiento de endpoints que consultan datos frecuentemente. Se incluyen dos decoradores principales:

- `@cache_result`: Cachea GET requests (READ)
- `@cache_and_invalidate`: Invalida caché después de mutaciones (POST/PUT/DELETE)

## Configuración

### 1. Inicialización en main.py

El caché se inicializa automáticamente en el lifespan de FastAPI:

```python
from src.core.cache import init_cache_service, shutdown_cache_service

async def lifespan(app: FastAPI):
    # Startup
    redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
    cache_service = init_cache_service(redis_url, prefix="gad:")
    await cache_service.connect()
    
    yield
    
    # Shutdown
    await shutdown_cache_service()
```

### 2. Decoradores Disponibles

#### `@cache_result`
Cachea el resultado de un endpoint GET.

```python
@router.get("/items", response_model=List[ItemResponse])
@cache_result(ttl_seconds=300, key_prefix="items")  # Cache 5 min
async def list_items(db: AsyncSession = Depends(get_db_session)):
    # ... fetch data
```

**Parámetros:**
- `ttl_seconds`: Tiempo de vida en segundos (default: 300)
- `key_prefix`: Prefijo para la clave (helps organize cache)

#### `@cache_and_invalidate`
Ejecuta la función Y luego invalida patrones de caché relacionados.

```python
@router.post("/items", response_model=ItemResponse)
@cache_and_invalidate(
    invalidate_patterns=[
        "items:list_items:*",
        "items:get_item:*"
    ]
)
async def create_item(item_in: ItemCreate, db: AsyncSession):
    # ... create item
    # Después de crear, automáticamente invalida la lista
```

**Parámetros:**
- `invalidate_patterns`: Lista de patrones para invalidar (soporta `*` wildcard)

#### `@invalidate_cache`
Solo invalida caché, sin cachear nada.

```python
@router.delete("/items/{item_id}", status_code=204)
@invalidate_cache("items:*")
async def delete_item(item_id: int, db: AsyncSession):
    # ... delete logic
    # Después, invalida todo lo relacionado con items
```

## Ejemplos de Uso

### Exemplo 1: Endpoint GET simple

```python
from src.core.cache_decorators import cache_result

@router.get("/usuarios", response_model=List[UsuarioResponse])
@cache_result(ttl_seconds=300, key_prefix="usuarios")
async def list_usuarios(db: AsyncSession = Depends(get_db_session)):
    query = select(Usuario).offset(0).limit(100)
    result = await db.execute(query)
    usuarios = result.scalars().all()
    return [UsuarioResponse.model_validate(u) for u in usuarios]
```

**Comportamiento:**
1. Primera llamada → DB hit → cache store → return data
2. Segunda llamada (dentro de 5 min) → cache hit → return data (rápido)
3. Después de 5 min → cache expired → DB hit → store → return

### Ejemplo 2: Creación con invalidación

```python
@router.post("/usuarios", response_model=UsuarioResponse)
@cache_and_invalidate(invalidate_patterns=["usuarios:list_usuarios:*"])
async def create_usuario(
    usuario_in: UsuarioCreate,
    db: AsyncSession = Depends(get_db_session)
):
    new_usuario = Usuario(...)
    db.add(new_usuario)
    await db.commit()
    # Automáticamente invalida la lista después
    return new_usuario
```

### Ejemplo 3: Actualización múltiple

```python
@router.put("/usuarios/{id}", response_model=UsuarioResponse)
@cache_and_invalidate(
    invalidate_patterns=[
        "usuarios:list_usuarios:*",
        "usuarios:get_usuario:*",
        "efectivos:*"  # También invalida si Usuario afecta Efectivos
    ]
)
async def update_usuario(id: int, usuario_in: UsuarioUpdate, db: AsyncSession):
    usuario = await db.get(Usuario, id)
    usuario.name = usuario_in.name
    await db.commit()
    return usuario
```

## Estrategia de TTL

Recomendación por tipo de endpoint:

| Tipo de Endpoint | TTL | Razón |
|---|---|---|
| Lista (GET /items) | 300-600 seg | Datos cambian moderadamente |
| Detalle (GET /items/{id}) | 600-1800 seg | Datos individual less prone to change |
| Estadísticas | 60-120 seg | Frecuentemente actualizadas |
| Geo (mapas) | 30-60 seg | Critical, cambios frecuentes |
| Config | 3600+ | Raramente cambia |

## Patrones de Caché

El sistema genera claves automáticamente:

```
{key_prefix}:{func_name}:{hash_of_args}
```

Ejemplos:
```
usuarios:list_usuarios:a1b2c3d4e5f6
usuarios:get_usuario:f6e5d4c3b2a1
tareas:list_tareas:xyz789
```

## Invalidación de Patrones

El wildcard `*` se usa para invalidar múltiples claves:

```python
# Invalida TODAS las claves de usuarios
"usuarios:*"

# Invalida SOLO listas de usuarios
"usuarios:list_usuarios:*"

# Invalida SOLO gets de usuario específico (si args incluyen ID)
"usuarios:get_usuario:*"
```

## Monitoreo

### Stats de Caché

```python
from src.core.cache import _cache_service

stats = await _cache_service.get_stats()
# {
#     "hits": 150,
#     "misses": 50,
#     "hit_rate": 75.0%,
#     "keys_count": 42,
#     "memory_used_mb": 5.2
# }
```

### Logs

El sistema loguea en `DEBUG`:
```
Cache HIT: usuarios:list_usuarios:a1b2c3d4
Cache MISS: usuarios:get_usuario:xyz789
Cached result for usuarios:list_usuarios:a1b2c3d4 (TTL: 300s)
Invalidated 3 cache entries matching pattern: usuarios:*
```

## Consideraciones de Seguridad

1. **No cachees datos sensibles** - No uses caché para datos con info personal o sensible
2. **Invalidación rápida** - Cambia que se invalidate rápidamente tras mutaciones
3. **Permisos** - El caché no valida permisos, es transparente (tu endpoint ya lo hace)

## Resolución de Problemas

### Cache no funciona
1. Verifica Redis está corriendo: `redis-cli ping`
2. Mira logs: `DEBUG` level debería mostrar HIT/MISS
3. Revisa `_cache_service` está inicializado en startup

### Cache stale (data vieja)
1. Reduce TTL seconds
2. Asegúrate que `cache_and_invalidate` tiene el patrón correcto
3. Prueba invalidación manual: `await _cache_service.delete_pattern("usuarios:*")`

### Performance no mejora
1. Verifica que Redis en red está OK (latency)
2. Mira hit rate: si bajo (<50%), quizás TTL muy corto
3. Considera qué endpoints se benefician más (alta frecuencia reads)

## Roadmap

Mejoras futuras:
- [ ] Tag-based invalidation (en lugar de patterns)
- [ ] Warming de caché en startup
- [ ] Distributed cache invalidation (si múltiples servidores)
- [ ] Caché de búsquedas (full-text)
- [ ] Integration con WebSockets para invalidation en tiempo real
