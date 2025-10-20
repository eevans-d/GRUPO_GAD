# Problemas Críticos Encontrados - Oct 20, 2025

## Resumen Ejecutivo

Durante el intento de despliegue a Fly.io, se descubrieron **múltiples problemas críticos** que impedían que la aplicación funcionara correctamente:

## 1. ❌ HEALTHCHECK INCORRECTO EN DOCKERFILE

**Problema:**
- `Dockerfile.api` tenía: `HEALTHCHECK ... /api/v1/health`
- Pero la app expone: `/health`
- **Resultado:** Healthcheck siempre fallaba → máquina se reiniciaba infinitamente

**Solución:**
- ✅ Cambiar healthcheck a `/health` (commit e43692d)

---

## 2. ❌ PUERTO INCORRECTO EN CONFIGURACIÓN

**Problema:**
- `fly.toml` configuraba `PORT=8080` e `internal_port=8080`
- Pero `start.sh` iniciaba la app en puerto **8000**
- **Resultado:** Fly.io no encontraba a la app escuchando en el puerto esperado

**Solución:**
- ✅ Cambiar `fly.toml`: `PORT=8000`, `internal_port=8000` (commit e7ecaa7)
- ✅ Hacer `start.sh` configurable via variable `PORT` (commit e7ecaa7)

---

## 3. ❌ DATABASE_URL INVÁLIDA BLOQUEABA EL STARTUP

**Problema:**
- La `DATABASE_URL` en Fly.io existía pero **apuntaba a una base de datos inexistente** (probablemente de Railway)
- `release_command = "alembic upgrade head"` intentaba conectarse → **FALLABA**
- El app no podía iniciar

**Solución:**
- ✅ Deshabilitar `release_command` (commit d6eb87d)
- ✅ Agregar `ALLOW_NO_DB=1` para permitir iniciar sin DB (commit 659d2d1)

---

## 4. ❌ REDIS CAUSABA HANG EN EL STARTUP

**Problema CRÍTICO:**
- `config/settings.py` tenía: `REDIS_HOST = "redis"` (valor por defecto)
- `src/api/main.py` (lifespan) intentaba conectarse a Redis en el startup:
  ```python
  if redis_host:
      await pubsub.start(websocket_manager)  # SE CUELGA AQUÍ
  ```
- En Fly.io, el host `redis` **NO EXISTE** → conexión se cuelga indefinidamente
- **Resultado:** App no iniciaba nunca, se congelaba en el startup

**Solución:**
- ✅ Cambiar `REDIS_HOST: Optional[str] = None` (default) (commit aebaddc)
- ✅ Solo conectar a Redis si `REDIS_HOST` está explícitamente configurado

---

## 5. ⚠️ POSTGRES TAMBIÉN TIENE PROBLEMA SIMILAR

**Observación:**
- `config/settings.py` requiere `POSTGRES_USER` y `POSTGRES_PASSWORD`
- En Fly.io, estas variables **no están configuradas** (solo existe `DATABASE_URL`)
- Posible problema futuro cuando se intente usar Postgres sin `ALLOW_NO_DB`

**Recomendación:**
- Hacer campos Postgres opcionales también

---

## Commits Relacionados

1. **e43692d** - fix: correct healthcheck endpoint path from /api/v1/health to /health
2. **e7ecaa7** - fix: correct port configuration (8000) and make it configurable via PORT env var
3. **d6eb87d** - fix: disable release_command - DATABASE_URL in Fly.io is invalid
4. **659d2d1** - fix: add ALLOW_NO_DB=1 to allow app to start without database
5. **aebaddc** - fix: make REDIS_HOST optional (default None) to avoid startup hang when Redis unavailable

---

## Estado Actual

**Cambios completados:**
- ✅ Healthcheck corregido
- ✅ Puerto configurado correctamente
- ✅ Database no obligatoria
- ✅ Redis no obligatorio

**Próximo paso:**
- Esperar a que el deploy en Fly.io termine con estas correcciones
- Verificar que `/health` responda correctamente
- Confirmar que la app está escuchando en `0.0.0.0:8000`

---

## Verificación Requerida

Una vez que el deploy termine:

```bash
# 1. Health check
curl https://grupo-gad.fly.dev/health

# 2. API Docs
curl https://grupo-gad.fly.dev/docs

# 3. WebSocket stats
curl https://grupo-gad.fly.dev/ws/stats

# 4. Full status
curl https://grupo-gad.fly.dev/health/ready
```

---

**Generado:** 2025-10-20 05:35 UTC
**Status:** En espera de deploy con correcciones
