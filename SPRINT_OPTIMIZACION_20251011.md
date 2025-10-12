# 🚀 Sprint de Optimización - 11 Octubre 2025

## 📋 Objetivos del Sprint

Realizar mejoras de performance, validación completa y optimizaciones técnicas al sistema GRUPO_GAD, enfocándonos en:
- ✅ Validación de calidad (tests)
- 📊 Observabilidad (estado del sistema)
- ⚡ Performance (queries optimizadas)
- 💾 Escalabilidad (caché Redis)
- 🔧 Mejoras adicionales según hallazgos

---

## ⏱️ Planificación Temporal

```
SPRINT DURATION: 2.5-3.5 horas
START TIME: [11 Octubre 2025]

┌─────────────────────────────────────────────────────┐
│ FASE 1: DIAGNÓSTICO         │ 10-15 min │ 🔍      │
│ FASE 2: VALIDACIÓN          │ 20-30 min │ ✅      │
│ FASE 3: OPTIMIZACIÓN DB     │ 45-60 min │ ⚡      │
│ FASE 4: CACHÉ REDIS         │ 60-90 min │ 💾      │
│ FASE 5: MEJORAS ADICIONALES │ 20-30 min │ 🔧      │
└─────────────────────────────────────────────────────┘
TOTAL: 155-225 minutos (2.5-3.75 horas)
```

---

## 🎯 FASE 1: Diagnóstico del Sistema (C)

**Tiempo estimado:** 10-15 minutos  
**Prioridad:** 🔴 Crítica  
**Estado:** 🔄 En Progreso

### Objetivos
- [ ] Verificar estado de servicios Docker
- [ ] Revisar logs recientes
- [ ] Verificar métricas de Prometheus
- [ ] Identificar bottlenecks actuales
- [ ] Documentar baseline de performance

### Tareas Específicas

#### 1.1 Estado de Servicios
```bash
# Verificar que todo está corriendo
docker compose ps

# Estado de salud
docker compose ps --format json | jq '.[].Health'

# Recursos utilizados
docker stats --no-stream
```

**Criterios de éxito:**
- ✅ Todos los servicios en estado "Up" y "healthy"
- ✅ Uso de recursos < 80%
- ✅ Sin containers en restart loop

#### 1.2 Análisis de Logs
```bash
# Logs del bot (últimas 100 líneas)
docker logs gad_bot_dev --tail 100

# Buscar errores
docker logs gad_bot_dev 2>&1 | grep -i "error\|exception\|warning" | tail -20

# Logs de la API
docker logs gad_api_dev --tail 100 | grep -i "error"

# Logs de PostgreSQL
docker logs gad_postgres_dev --tail 50
```

**Criterios de éxito:**
- ✅ Sin errores críticos en últimos 100 logs
- ✅ Warnings documentados y entendidos
- ✅ Conexiones a DB estables

#### 1.3 Métricas de Performance
```bash
# Métricas HTTP
curl -s http://localhost:8000/metrics | grep -E "http_requests_total|http_request_duration"

# Métricas WebSocket
curl -s http://localhost:8000/metrics | grep -E "websocket_"

# Uso de DB
docker exec gad_postgres_dev psql -U postgres -d grupogad -c "
  SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables 
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
  LIMIT 10;
"
```

**Criterios de éxito:**
- ✅ Response time promedio < 200ms
- ✅ Queries DB < 50ms (p95)
- ✅ Sin memory leaks

#### 1.4 Baseline Documentado
```bash
# Crear snapshot de estado actual
cat > /tmp/baseline_$(date +%Y%m%d_%H%M%S).txt << EOF
=== BASELINE PERFORMANCE ===
Timestamp: $(date -Iseconds)

Services:
$(docker compose ps)

Resources:
$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}")

Recent Errors:
$(docker logs gad_bot_dev 2>&1 | grep -i error | tail -5)
$(docker logs gad_api_dev 2>&1 | grep -i error | tail -5)
EOF
```

### Entregables Fase 1
- [ ] `BASELINE_PERFORMANCE.md` con métricas actuales
- [ ] Lista de issues identificados
- [ ] Priorización de optimizaciones

---

## ✅ FASE 2: Validación con Tests (A)

**Tiempo estimado:** 20-30 minutos  
**Prioridad:** 🔴 Crítica  
**Estado:** ⏳ Pendiente

### Objetivos
- [ ] Ejecutar suite completa de tests
- [ ] Verificar cobertura de código
- [ ] Corregir tests fallidos (si los hay)
- [ ] Validar nuevos comandos del bot

### Tareas Específicas

#### 2.1 Setup del Entorno de Testing
```bash
# Activar virtualenv (ya hecho)
source .venv/bin/activate

# Verificar dependencias de testing
pip list | grep -E "pytest|coverage"

# Si falta algo, instalar
pip install pytest pytest-cov pytest-asyncio
```

#### 2.2 Ejecutar Tests Unitarios
```bash
# Tests completos con verbose
pytest -v

# Tests solo del bot
pytest tests/bot/ -v

# Con cobertura
pytest --cov=src --cov-report=term-missing --cov-report=html

# Tests específicos de comandos nuevos
pytest tests/bot/test_historial.py -v
pytest tests/bot/test_estadisticas.py -v
```

**Criterios de éxito:**
- ✅ Todos los tests pasan (0 failed)
- ✅ Cobertura ≥ 75% en código nuevo
- ✅ No hay warnings críticos

#### 2.3 Tests de Integración
```bash
# Test de API health
curl -f http://localhost:8000/api/v1/health || echo "API not responding"

# Test de métricas
curl -f http://localhost:8000/metrics || echo "Metrics not available"

# Test de WebSocket (si está corriendo)
python scripts/ws_smoke_test.py
```

#### 2.4 Análisis de Cobertura
```bash
# Generar reporte HTML
pytest --cov=src --cov-report=html

# Ver archivos con baja cobertura
coverage report --sort=cover | head -20

# Identificar funciones sin tests
coverage report -m | grep -E "0%|[0-4][0-9]%"
```

### Entregables Fase 2
- [ ] Reporte de tests pasando/fallando
- [ ] Reporte de cobertura (HTML)
- [ ] Lista de funciones sin cobertura
- [ ] Fixes aplicados (si fueron necesarios)

---

## ⚡ FASE 3: Optimización de Queries (D)

**Tiempo estimado:** 45-60 minutos  
**Prioridad:** 🟡 Alta  
**Estado:** ⏳ Pendiente

### Objetivos
- [ ] Analizar queries lentas en el historial
- [ ] Crear índices optimizados
- [ ] Implementar query plan analysis
- [ ] Benchmarking pre/post optimización

### Tareas Específicas

#### 3.1 Análisis de Queries Actuales

**Archivo:** `src/bot/services/api_service.py`

Queries a analizar:
1. `get_user_pending_tasks(user_id)` - Usado por `/historial` y `/finalizar`
2. `get_user_tasks(user_id, filter, page, limit)` - Usado por `/historial` con paginación
3. `get_user_stats(user_id)` - Usado por `/estadisticas`

```sql
-- En PostgreSQL, analizar query actual
EXPLAIN ANALYZE
SELECT * FROM tasks 
WHERE user_id = 123 
  AND estado = 'pending'
ORDER BY created_at DESC
LIMIT 10;
```

**Métricas a capturar:**
- Execution time
- Seq Scan vs Index Scan
- Rows examined vs returned
- Buffers used

#### 3.2 Creación de Índices Optimizados

**Archivo a crear:** `alembic/versions/YYYYMMDD_add_performance_indexes.py`

```sql
-- Índices propuestos:

-- 1. Índice compuesto para historial filtrado por usuario y estado
CREATE INDEX idx_tasks_user_estado_created 
ON tasks(user_id, estado, created_at DESC);

-- 2. Índice para búsquedas por código
CREATE INDEX idx_tasks_codigo 
ON tasks(codigo);

-- 3. Índice para queries de estadísticas (agregaciones)
CREATE INDEX idx_tasks_user_tipo 
ON tasks(user_id, tipo) WHERE estado != 'deleted';

-- 4. Índice parcial solo para tareas activas (más común)
CREATE INDEX idx_tasks_user_active 
ON tasks(user_id, created_at DESC) 
WHERE estado IN ('pending', 'in_progress');

-- 5. Índice para finalización de tareas
CREATE INDEX idx_tasks_finalize 
ON tasks(id, user_id, estado) 
WHERE estado = 'pending';
```

**Implementación:**
```bash
# Generar migración
alembic revision -m "add_performance_indexes"

# Editar archivo generado y agregar índices

# Aplicar migración
alembic upgrade head

# Verificar índices creados
docker exec gad_postgres_dev psql -U postgres -d grupogad -c "
  SELECT 
    schemaname, tablename, indexname, indexdef
  FROM pg_indexes
  WHERE tablename = 'tasks'
  ORDER BY indexname;
"
```

#### 3.3 Optimización de Queries en Código

**Archivo:** `src/api/repositories/task_repository.py`

Optimizaciones:
1. **Eager loading** para relaciones (evitar N+1)
2. **Select only needed columns** (proyección)
3. **Pagination eficiente** con keyset pagination
4. **Query hints** para forzar uso de índices

```python
# Antes (ineficiente)
tasks = session.query(Task).filter(Task.user_id == user_id).all()

# Después (optimizado)
tasks = (
    session.query(Task)
    .filter(Task.user_id == user_id)
    .filter(Task.estado == 'pending')
    .order_by(Task.created_at.desc())
    .limit(10)
    .options(joinedload(Task.assignees))  # Eager load
    .all()
)
```

#### 3.4 Benchmarking

**Script a crear:** `scripts/benchmark_queries.py`

```python
import time
import statistics
from sqlalchemy import create_engine, text

def benchmark_query(engine, query, iterations=100):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text(query))
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'p95': statistics.quantiles(times, n=20)[18],  # 95th percentile
        'min': min(times),
        'max': max(times)
    }
```

**Métricas objetivo:**
- Queries simples: < 10ms (p95)
- Queries con joins: < 50ms (p95)
- Queries de agregación: < 100ms (p95)
- Paginación: < 20ms (p95)

### Entregables Fase 3
- [ ] Migración de Alembic con índices
- [ ] Queries optimizadas en repositorios
- [ ] Reporte de benchmarking (before/after)
- [ ] Documentación de índices en README

---

## 💾 FASE 4: Implementación de Caché Redis (E)

**Tiempo estimado:** 60-90 minutos  
**Prioridad:** 🟡 Alta  
**Estado:** ⏳ Pendiente

### Objetivos
- [ ] Configurar cliente Redis
- [ ] Implementar caché para estadísticas
- [ ] Estrategia de invalidación
- [ ] Monitoring de caché (hit rate)

### Tareas Específicas

#### 4.1 Setup de Redis

**Archivo:** `docker-compose.yml`

Verificar que Redis está configurado:
```yaml
redis:
  image: redis:7-alpine
  container_name: gad_redis_dev
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 3
```

```bash
# Levantar Redis
docker compose up -d redis

# Verificar conexión
docker exec gad_redis_dev redis-cli ping
# Debe responder: PONG

# Ver info
docker exec gad_redis_dev redis-cli INFO stats
```

#### 4.2 Cliente Redis en Python

**Archivo a crear:** `src/core/cache.py`

```python
# -*- coding: utf-8 -*-
"""
Sistema de caché con Redis para optimizar performance.
"""

import json
from typing import Any, Optional
from redis import Redis
from redis.exceptions import RedisError
from loguru import logger
from config.settings import get_settings


class CacheService:
    """Servicio de caché con Redis."""
    
    def __init__(self):
        settings = get_settings()
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        self._enabled = settings.CACHE_ENABLED
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor del caché.
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor deserializado o None si no existe
        """
        if not self._enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except RedisError as e:
            logger.error(f"Redis error on GET {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Guarda valor en caché.
        
        Args:
            key: Clave del caché
            value: Valor a guardar (será serializado a JSON)
            ttl: Tiempo de vida en segundos (default: 5 minutos)
            
        Returns:
            True si se guardó exitosamente
        """
        if not self._enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Redis error on SET {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina clave del caché."""
        if not self._enabled:
            return False
        
        try:
            self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except RedisError as e:
            logger.error(f"Redis error on DELETE {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Elimina todas las claves que coincidan con el patrón.
        
        Args:
            pattern: Patrón de Redis (ej: "user:*", "stats:user:123:*")
            
        Returns:
            Número de claves eliminadas
        """
        if not self._enabled:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cache DELETE PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except RedisError as e:
            logger.error(f"Redis error on DELETE PATTERN {pattern}: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del caché."""
        if not self._enabled:
            return {"enabled": False}
        
        try:
            info = self.redis.info("stats")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "keys": self.redis.dbsize()
            }
        except RedisError as e:
            logger.error(f"Redis error getting stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    @staticmethod
    def _calculate_hit_rate(info: dict) -> float:
        """Calcula hit rate del caché."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return round((hits / total * 100) if total > 0 else 0, 2)


# Singleton global
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """Obtiene instancia singleton del servicio de caché."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
```

#### 4.3 Integración con Comando `/estadisticas`

**Archivo:** `src/bot/commands/estadisticas.py`

```python
# Agregar imports
from src.core.cache import get_cache_service

async def estadisticas(update: Update, context: CallbackContext) -> None:
    """Muestra estadísticas con caché."""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Usuario"
    
    try:
        # Intentar obtener del caché
        cache = get_cache_service()
        cache_key = f"stats:user:{user_id}"
        
        cached_stats = cache.get(cache_key)
        if cached_stats:
            logger.info(f"Estadísticas servidas desde caché para user {user_id}")
            stats_text = _format_statistics(cached_stats, user_name)
            await update.message.reply_text(stats_text, parse_mode="Markdown")
            return
        
        # Si no está en caché, calcular
        loading_msg = await update.message.reply_text("📊 Calculando...")
        
        api_service = ApiService(...)
        tareas = await api_service.get_user_pending_tasks(user_id)
        stats = _calculate_statistics(tareas, user_id)
        
        # Guardar en caché (5 minutos)
        cache.set(cache_key, stats, ttl=300)
        
        await loading_msg.delete()
        stats_text = _format_statistics(stats, user_name)
        await update.message.reply_text(stats_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error...")
```

#### 4.4 Estrategia de Invalidación

**Eventos que invalidan caché:**
1. Usuario crea tarea → Invalidar `stats:user:{user_id}`
2. Usuario finaliza tarea → Invalidar `stats:user:{user_id}`
3. Tarea asignada a usuario → Invalidar `stats:user:{assigned_user_id}`

**Implementación en API:**

```python
# src/api/routes/tasks.py

from src.core.cache import get_cache_service

@router.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # ... crear tarea ...
    
    # Invalidar caché
    cache = get_cache_service()
    cache.delete(f"stats:user:{task.creator_id}")
    for assignee_id in task.assignee_ids:
        cache.delete(f"stats:user:{assignee_id}")
    
    return new_task
```

#### 4.5 Monitoring de Caché

**Endpoint de métricas:**

```python
# src/api/routes/metrics.py

@router.get("/cache/stats")
async def get_cache_stats():
    """Estadísticas del caché Redis."""
    cache = get_cache_service()
    return cache.get_stats()
```

**Dashboard simple:**

```bash
# Script de monitoring
watch -n 5 'curl -s http://localhost:8000/api/v1/cache/stats | jq'
```

### Entregables Fase 4
- [ ] `src/core/cache.py` implementado
- [ ] Redis configurado y funcionando
- [ ] `/estadisticas` usando caché
- [ ] Estrategia de invalidación implementada
- [ ] Endpoint de monitoring `/cache/stats`
- [ ] Documentación de caché en README

---

## 🔧 FASE 5: Mejoras Adicionales (F)

**Tiempo estimado:** 20-30 minutos  
**Prioridad:** 🟢 Media  
**Estado:** ⏳ Pendiente

### Objetivos
Basados en hallazgos de fases anteriores:

- [ ] Corregir issues encontrados en testing
- [ ] Optimizaciones adicionales identificadas
- [ ] Mejoras de código (refactoring menor)
- [ ] Actualizar documentación con cambios

### Tareas Potenciales

#### 5.1 Refactoring de Código Duplicado
- Extraer funciones comunes
- DRY (Don't Repeat Yourself)
- Crear utilidades compartidas

#### 5.2 Mejoras de Logging
- Estructurar logs con contexto
- Agregar tracing IDs
- Mejorar mensajes de error

#### 5.3 Documentación Actualizada
- README con sección de Performance
- Guía de caché y optimizaciones
- Métricas de benchmarking

#### 5.4 Configuración de Monitoreo
- Alertas en Grafana (si existe)
- Thresholds de performance
- Dashboards de caché

### Entregables Fase 5
- [ ] Issues corregidos
- [ ] Código refactorizado
- [ ] Documentación actualizada
- [ ] Monitoring configurado

---

## 📊 Métricas de Éxito del Sprint

### Performance Targets

| Métrica | Baseline | Target | Medición |
|---------|----------|--------|----------|
| Query time (p95) | ? | < 50ms | EXPLAIN ANALYZE |
| Cache hit rate | 0% | > 80% | Redis INFO |
| API response time | ? | < 200ms | Prometheus |
| Test coverage | ~44% | > 75% | pytest-cov |
| Tests passing | ? | 100% | pytest |

### Mejoras Esperadas

```
┌─────────────────────────────────────────────┐
│ MEJORAS ESTIMADAS POST-SPRINT               │
├─────────────────────────────────────────────┤
│ Performance:      +60-80% más rápido        │
│ Escalabilidad:    +10x requests/segundo     │
│ Carga en DB:      -70% queries repetidas    │
│ User Experience:  -50% tiempo de respuesta  │
│ Confiabilidad:    +30% cobertura de tests   │
└─────────────────────────────────────────────┘
```

---

## 📝 Checklist Final

### Pre-Sprint
- [x] Planificación documentada
- [ ] Entorno preparado (.venv activado)
- [ ] Servicios corriendo
- [ ] Baseline capturado

### Durante Sprint
- [ ] Fase 1 completada (Diagnóstico)
- [ ] Fase 2 completada (Tests)
- [ ] Fase 3 completada (Optimización)
- [ ] Fase 4 completada (Caché)
- [ ] Fase 5 completada (Mejoras)

### Post-Sprint
- [ ] Métricas comparadas (before/after)
- [ ] Documentación actualizada
- [ ] Commits realizados
- [ ] Sprint retrospective documentado

---

## 🎯 Próximos Pasos

Después de este sprint:
1. Validación E2E con Telegram real
2. Deploy a staging
3. Monitoring en producción
4. Planificación de features futuras

---

**Documento vivo - Actualizar según progreso**  
**Creado:** 11 Octubre 2025  
**Estado:** 🚀 INICIANDO  
**Progreso:** 0% → Target: 100%
