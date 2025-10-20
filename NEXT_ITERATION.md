# 📋 NEXT ITERATION - PostgreSQL + Production Hardening

**Sesión Actual**: ✅ COMPLETADA - App en Fly.io
**Próxima Sesión**: 🔄 DATABASE_URL + Migraciones + Secrets

---

## 📊 Estado Actual

```
✅ APP LIVE: https://grupo-gad.fly.dev/health
✅ WebSockets: https://grupo-gad.fly.dev/ws/stats
✅ API Docs: https://grupo-gad.fly.dev/docs

⚠️ DATABASE: Deshabilitada (ALLOW_NO_DB=1)
⚠️ SECRETS: No configurados
⚠️ MIGRACIONES: No ejecutadas
```

---

## 🎯 Próximos Pasos (20-30 minutos)

### PASO 1: Obtener DATABASE_URL (5 minutos)

**Opción A: Render.com (⚡ MÁS RÁPIDO)**
```
1. Ir a https://render.com/dashboard
2. New → PostgreSQL
3. Name: grupo-gad-db
4. Free tier (5GB, 90 días)
5. Copiar DATABASE_URL
```

**Opción B: Supabase.com (⭐ RECOMENDADO)**
```
1. Ir a https://supabase.com
2. New Project
3. Name: grupo-gad
4. Free tier (500MB)
5. Settings → Database → Connection pooling
6. Copiar postgresql://...
```

**Opción C: Railway.app (Reutilizar anterior)**
```
1. Si aún tienes la DB de Railway, copiar URL
2. Cambiar dependencia de Railway a Fly.io
```

---

### PASO 2: Configurar DATABASE_URL en Fly.io (3 minutos)

Una vez que tengas la URL:

```bash
export PATH="/home/eevan/.fly/bin:$PATH"
export FLY_API_TOKEN="[TU_TOKEN_AQUI]"

# Comando
flyctl secrets set \
  DATABASE_URL="postgresql://user:pass@host:5432/db" \
  --app grupo-gad

# Verificar
flyctl secrets list -a grupo-gad
```

---

### PASO 3: Habilitar Release Command (2 minutos)

Editar `fly.toml`:

```toml
[deploy]
  release_command = "alembic upgrade head"  # 👈 DESCOMENTA ESTA LÍNEA
  strategy = "rolling"
```

Luego:

```bash
git add fly.toml
git commit -m "enable: release_command for database migrations"
git push origin master
```

---

### PASO 4: Redeploy con DB (5 minutos)

```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD

flyctl deploy --local-only -a grupo-gad
```

**Qué sucede**:
1. Build imagen Docker
2. Push a registry
3. **Ejecuta `alembic upgrade head`** (crea tablas)
4. Inicia máquinas con DB funcional

**Ver logs de migraciones**:
```bash
flyctl logs -a grupo-gad --follow
```

---

### PASO 5: Verificar DB Funcional (2 minutos)

```bash
# 1. Health check debe mostrar timestamp actualizado
curl https://grupo-gad.fly.dev/health | jq .

# 2. Ver logs
flyctl logs -a grupo-gad --no-tail | grep -i "database\|migration\|alembic"

# 3. (Opcional) SSH a máquina para verificar DB
flyctl ssh console -a grupo-gad
# Dentro:
# psql $DATABASE_URL -c "\dt"  # Ver tablas creadas
```

---

### PASO 6: Limpiar Variables Temporales (2 minutos)

Una vez que DATABASE_URL esté funcionando, remover ALLOW_NO_DB:

```bash
# Editar fly.toml
# Remover o comentar: ALLOW_NO_DB = "1"

git add fly.toml
git commit -m "cleanup: remove ALLOW_NO_DB now that DATABASE_URL is configured"
git push origin master

flyctl deploy --local-only -a grupo-gad
```

---

## 🔐 Configurar Secrets (Fase 2 - Opcional)

Para autenticación JWT y otros:

```bash
# Generar SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Configurar en Fly.io
flyctl secrets set \
  SECRET_KEY="[GENERATED_HEX]" \
  JWT_SECRET_KEY="[GENERATED_HEX]" \
  --app grupo-gad

# Verificar
flyctl secrets list -a grupo-gad
```

---

## 📋 Checklist Completo

### Fase 1: Base de Datos (Completar AHORA)
- [ ] Obtener DATABASE_URL de Supabase/Render/Railway
- [ ] Configurar en Fly.io: `flyctl secrets set DATABASE_URL="..."`
- [ ] Descomenta `release_command` en fly.toml
- [ ] Redeploy: `flyctl deploy --local-only`
- [ ] Verificar logs: `flyctl logs -a grupo-gad --follow`
- [ ] Confirmar health check: `curl https://grupo-gad.fly.dev/health`

### Fase 2: Secrets (Para autenticación)
- [ ] Generar SECRET_KEY
- [ ] Generar JWT_SECRET_KEY
- [ ] Configurar en Fly.io: `flyctl secrets set`
- [ ] Redeploy para aplicar

### Fase 3: Testing E2E (Validación)
- [ ] Health check respondiendo
- [ ] WebSocket conexión funciona
- [ ] API endpoints con DB funcionan
- [ ] Logs limpios (sin errores)

### Fase 4: Monitoreo (Optional)
- [ ] Configurar uptime monitoring
- [ ] Configurar alertas (crashes, CPU > 80%)
- [ ] Setup log aggregation (opcional)

---

## 🆘 Troubleshooting

### Si redeploy falla en migraciones:

```bash
# Ver error específico
flyctl logs -a grupo-gad --no-tail | grep -i "error\|migration"

# Rollback (no ejecutar migrations)
# Editar fly.toml y comentar release_command
# git commit && push && redeploy
```

### Si health check sigue fallando:

```bash
# Ver logs detallados
flyctl logs -a grupo-gad --follow

# Buscar errores de conexión DB
# Si dice "CONNECTION_REFUSED", verificar DATABASE_URL
# Si dice "PERMISSION DENIED", verificar credentials

# Reiniciar máquinas
flyctl machines restart -a grupo-gad
```

### Si migraciones tardan mucho:

```bash
# Eso es normal en primera ejecución (puede tomar 30-60s)
# No cancelar deploy
# Ver progreso con flyctl logs
```

---

## 📊 Métricas Esperadas Post-DB

```json
{
  "status": "ok",
  "environment": "production",
  "timestamp": 1760934737.286844,
  "database": {
    "connected": true,
    "migrations_applied": true,
    "tables": [
      "governments",
      "departments",
      "sessions",
      "...more tables"
    ]
  }
}
```

---

## 🚀 Comandos de Referencia Rápida

```bash
# Ver estado
flyctl status -a grupo-gad

# Ver máquinas
flyctl machines list -a grupo-gad

# Ver secrets
flyctl secrets list -a grupo-gad

# Ver logs en vivo
flyctl logs -a grupo-gad --follow

# Redeploy
flyctl deploy --local-only -a grupo-gad

# SSH a máquina
flyctl ssh console -a grupo-gad

# Ver DATABASE_URL (cuidado: expone credenciales)
flyctl machines exec -a grupo-gad "echo $DATABASE_URL"
```

---

## 📝 Documentos de Referencia

- `SUPABASE_SETUP.md` - Setup paso a paso de PostgreSQL
- `QUICK_FIX_DB.md` - Alternativas de hosteo DB
- `DEPLOYMENT_SUCCESS_OCT20.md` - Resumen de despliegue actual
- `FINAL_STATUS_OCT20.md` - Checklist y arquitectura

---

## ⏱️ ETA Total

```
PASO 1 (Database URL):     5 min  ✅
PASO 2 (Fly.io config):    3 min  
PASO 3 (Release command):  2 min  
PASO 4 (Redeploy):         5 min  
PASO 5 (Verificación):     2 min  
PASO 6 (Limpieza):         2 min  
────────────────────────────────
TOTAL:                    20 min
```

**Luego**:
- Secrets: +5 min
- E2E Testing: +10 min
- **PRODUCTION READY: ~35 min**

---

## ✨ Resultado Final

Una vez completado:

```
https://grupo-gad.fly.dev/ ✅ FULLY OPERATIONAL
├─ API: FastAPI + SQLAlchemy + PostgreSQL
├─ WebSockets: Real-time ready
├─ Database: Migraciones ejecutadas
├─ Secrets: Configurados (JWT, etc)
├─ Logging: Estructurado
└─ Monitoring: Activo
```

---

**Status**: 🟡 WAITING FOR DB CONFIGURATION  
**Next Action**: Obtener DATABASE_URL y ejecutar PASO 1-5

¿Listo para continuar? 🚀
