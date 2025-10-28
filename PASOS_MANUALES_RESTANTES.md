# Pasos Manuales Restantes para Producción

## Estado Actual

✅ DATABASE_URL seteada en secrets  
✅ REDIS_URL seteada en secrets  
⚠️ App **NO reiniciada** aún → los secretos no se aplicaron  
⚠️ Health: `database="error: 'NoneType' object has no attribute 'connect'"`

---

## Paso 1: Reiniciar Máquinas (CRÍTICO)

```bash
flyctl machines restart --app grupo-gad --force
```

**Qué hace:** Reinicia las máquinas para que tomen los nuevos secretos DATABASE_URL y REDIS_URL.

**Esperado:** Mensaje "Machine restarted successfully"

**Esperar:** ~30-60 segundos para que arranque.

---

## Paso 2: Verificar Health

```bash
curl -s https://grupo-gad.fly.dev/health/ready | python3 -m json.tool
```

**Esperado:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "websocket_manager": "ok",
    "ws_pubsub": "ok"
  }
}
```

**Si falla:** Ver logs con `flyctl logs --app grupo-gad`

---

## Paso 3: Ejecutar Migraciones Alembic

```bash
flyctl ssh console --app grupo-gad
```

Dentro del contenedor:

```bash
cd /app
alembic upgrade head
exit
```

**Esperado:** 
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx
INFO  [alembic.runtime.migration] Running upgrade xxxxx -> yyyyy
```

---

## Paso 4: Verificar Health de Nuevo

```bash
curl -s https://grupo-gad.fly.dev/health/ready | python3 -m json.tool
```

Debe mostrar `"status": "ready"` con todos los checks en `"ok"`.

---

## Paso 5: Smoke Tests Básicos

```bash
# Test endpoint API básico
curl https://grupo-gad.fly.dev/api/v1/health

# Ver logs en tiempo real
flyctl logs --app grupo-gad
```

---

## Paso 6: (Opcional) Desactivar ALLOW_NO_DB

Editar `fly.toml` y comentar o eliminar:

```toml
# ALLOW_NO_DB = "1"  # Ya no necesario
```

Desplegar:

```bash
flyctl deploy --app grupo-gad
```

---

## Troubleshooting

### Si database sigue en error después del reinicio

1. Ver DATABASE_URL real:
```bash
flyctl ssh console --app grupo-gad
printenv DATABASE_URL
exit
```

2. Si la URL es incorrecta, corregir:
```bash
flyctl secrets set DATABASE_URL='postgres://...' --app grupo-gad
flyctl machines restart --app grupo-gad --force
```

### Si Redis no conecta

Ver REDIS_URL:
```bash
flyctl ssh console --app grupo-gad
printenv REDIS_URL
exit
```

---

## Resumen

1. ✅ Secretos seteados
2. ⚠️ **DEBES HACER:** `flyctl machines restart --app grupo-gad --force`
3. ⚠️ **DEBES HACER:** Verificar `/health/ready`
4. ⚠️ **DEBES HACER:** Ejecutar migraciones
5. ⚠️ **DEBES HACER:** Validar funcionamiento

**Tiempo estimado:** 5 minutos

