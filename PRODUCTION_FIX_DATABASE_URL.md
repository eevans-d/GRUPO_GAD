# CORRECCIÓN PRODUCCIÓN: Fix DATABASE_URL en Fly.io

**Situación:** Prod está degradada. `/health/ready` reporta `database="error: Connection refused"`.  
**Causa:** `DATABASE_URL` en secrets apunta a `localhost` (no accesible desde Fly).  
**Solución:** Actualizar `DATABASE_URL` a una base accesible (Fly Postgres o externa).

---

## Opción 1: Fly Postgres (Recomendado)

Usa la infraestructura administrada de Fly. Sin latencia de red, backups nativos.

### Pasos

```bash
# 1. Verificar si existe un cluster Postgres de producción
flyctl postgres list

# 2. Si NO existe, crear uno (región DFW, como la app)
flyctl postgres create \
  --org <TU_ORG> \
  --region dfw \
  --name grupo-gad-db \
  --initial-cluster-size 1

# Nota: `<TU_ORG>` es tu nombre de organización en Fly (p.ej. "personal")
# Puedes obtenerlo con: flyctl org list

# 3. Adjuntar el cluster a la app "grupo-gad"
# Esto REEMPLAZA automáticamente el DATABASE_URL actual
flyctl postgres attach \
  --postgres-app grupo-gad-db \
  --app grupo-gad \
  --variable DATABASE_URL

# 4. Verificar que el secreto fue actualizado
flyctl secrets list --app grupo-gad
# Esperado: ves una nueva DATABASE_URL con host *.internal (red privada)

# 5. Reiniciar máquinas para aplicar el nuevo secreto
flyctl machines restart --app grupo-gad --force

# 6. Esperar ~30 segundos; verificar salud
sleep 5
curl https://grupo-gad.fly.dev/health/ready

# 7. Si ves "status": "ready" y "database": "ok" → Éxito ✅
```

### Después de adjuntar DB

Una vez que `/health/ready` muestra `database="ok"`:

```bash
# Ejecutar migraciones Alembic
flyctl ssh console --app grupo-gad

# Dentro del container:
cd /app
alembic upgrade head
echo "✅ Migraciones completadas"
exit
```

---

## Opción 2: Postgres Externo (Railway/Neon)

Si ya usas un proveedor externo o prefieres no usar Fly Postgres.

### Pasos

```bash
# 1. Copiar connection string desde tu proveedor
# Ejemplo Railway: postgresql://user:pass@host.railway.app:5432/db_prod
# Ejemplo Neon: postgresql://user:pass@host.neon.tech/db_prod

CONNECTION_STRING="postgresql://user:pass@host.example.com:5432/db_prod"

# 2. Setear el secreto en Fly
flyctl secrets set DATABASE_URL="$CONNECTION_STRING" --app grupo-gad

# 3. Reiniciar máquinas
flyctl machines restart --app grupo-gad --force

# 4. Esperar ~30 segundos; verificar
sleep 5
curl https://grupo-gad.fly.dev/health/ready

# 5. Si ves "status": "ready" y "database": "ok" → Éxito ✅
```

### Después de setear URL externa

```bash
# Ejecutar migraciones
flyctl ssh console --app grupo-gad
cd /app
alembic upgrade head
echo "✅ Migraciones completadas"
exit
```

---

## Validación Post-Fix

```bash
# 1. Health check completo
curl https://grupo-gad.fly.dev/health/ready

# Esperado:
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "websocket_manager": "ok",
    "ws_pubsub": "ok",
    "active_ws_connections": 0,
    "unique_users": 0
  },
  "timestamp": 1234567890
}

# 2. Verificar logs
flyctl logs --app grupo-gad
# Deberías ver mensajes como:
# "Conexión a la base de datos establecida."
# "Pub/Sub Redis para WebSockets habilitado"
# "CacheService iniciado correctamente"

# 3. (Opcional) Smoke tests
flyctl ssh console --app grupo-gad
python scripts/smoke_test_sprint.sh
exit
```

---

## Limpieza Post-Estabilidad

Una vez que prod esté estable (~1 hora):

```bash
# Desactivar ALLOW_NO_DB en producción (evita degradaciones silenciosas)
# Editar fly.toml, cambiar:
#   ALLOW_NO_DB = "1"
# por:
#   # ALLOW_NO_DB = "0"  (o eliminar la línea)

# Luego deploy:
flyctl deploy --app grupo-gad
```

---

## Troubleshooting

### `curl: (6) Could not resolve host`
- La app aún está arrancando. Espera 30 segundos y reintenta.

### `curl: (7) Failed to connect to grupo-gad.fly.dev:443`
- Posible problema de DNS. Verifica que el app name es correcto: `flyctl apps list`.

### `/health/ready` aún muestra `"database": "error: Connection refused"`
- Verifica que el secreto se actualizó: `flyctl secrets list --app grupo-gad`.
- ¿Ejecutaste `flyctl machines restart --app grupo-gad --force`? Inténtalo de nuevo.
- Revisa logs: `flyctl logs --app grupo-gad` (busca errores de conexión).

### Migraciones fallan con `FATAL: password authentication failed`
- Verifica que el DATABASE_URL es correcto.
- Si usas Fly Postgres, el user por defecto es `postgres`.

---

## Referencias

- **Docs Fly Postgres:** https://fly.io/docs/reference/postgres/
- **Railway connection strings:** https://docs.railway.app/guides/postgresql#connection-options
- **Neon connection strings:** https://neon.tech/docs/manage/console-connection-details
- **AUDIT_PART1_DIAGNOSTIC.md:** Diagnóstico completo (este repo).

---

**Tiempo estimado:** 5–10 minutos.  
**Riesgo:** Bajo (cambios aislados a DB, no afecta código ni secrets adicionales).

