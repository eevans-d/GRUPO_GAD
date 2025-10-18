# 🔐 REFERENCIA RÁPIDA - TODOS LOS SECRETS

**Imprime esta página para tener a mano durante el despliegue**

---

## 📊 TABLA MAESTRA - 15 SECRETS REQUERIDOS

| # | Secret | Tipo | Prioridad | Generación | Validación |
|---|--------|------|-----------|-----------|-----------|
| 1 | `SSH_PRIVATE_KEY` | RSA Key | 🔴 | `cat ~/.ssh/id_rsa` | Comienza con `-----BEGIN RSA` |
| 2 | `SECRET_KEY` | Token | 🔴 | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | 32+ caracteres |
| 3 | `DATABASE_URL` | String | 🔴 | `postgresql://user:pass@host:5432/db` | `psql $DB -c "SELECT 1"` |
| 4 | `POSTGRES_USER` | String | 🔴 | `postgres` o customizado | Alfanumérico, sin espacios |
| 5 | `POSTGRES_PASSWORD` | String | 🔴 | `openssl rand -base64 20` | 20+ caracteres |
| 6 | `POSTGRES_DB` | String | 🔴 | `grupogad` | Alfanumérico, guiones, guiones bajos |
| 7 | `REDIS_URL` | String | 🔴 | `redis://localhost:6379/0` | `redis-cli -u $REDIS ping` |
| 8 | `DOCKER_USERNAME` | String | 🔴 | Tu user de DockerHub | 3-32 caracteres |
| 9 | `DOCKER_PASSWORD` | Token | 🔴 | Token de Hub.docker.com | Token activo |
| 10 | `BACKUP_ACCESS_KEY` | String | 🔴 | AWS IAM → Security credentials | Comienza con `AKIA` |
| 11 | `BACKUP_SECRET_KEY` | String | 🔴 | AWS IAM → Security credentials | 40+ caracteres |
| 12 | `SERVER_HOST` | String | 🔴 | IP o dominio | `ping $HOST` funciona |
| 13 | `SERVER_USERNAME` | String | 🔴 | `ubuntu`, `root`, etc | SSH login funciona |
| 14 | `CLOUDFLARE_TOKEN` | Token | 🟡 | dash.cloudflare.com | Token válido y activo |
| 15 | `MONITORING_TOKEN` | Token | 🟡 | Tu plataforma de monitoreo | Token válido |

🔴 Crítico (obligatorio) | 🟡 Opcional (recomendado)

---

## 🎯 ORDEN DE SETUP RECOMENDADO

### Fase 1: Seguridad (5 min)
```bash
# 1. SSH_PRIVATE_KEY - Generar/obtener
cat ~/.ssh/id_rsa  # O generar si no existe

# 2. SECRET_KEY - Generar token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Passwords - Generar seguros
openssl rand -base64 20  # Para POSTGRES_PASSWORD
openssl rand -base64 20  # Para REDIS_PASSWORD (si aplica)
```

### Fase 2: Base de Datos (10 min)
```bash
# 1. Provisionar PostgreSQL en tu plataforma (Railway/GCP/AWS)
# 2. Obtener DATABASE_URL: postgresql://user:pass@host:5432/db
# 3. Test: psql $DATABASE_URL -c "SELECT 1"
# 4. Obtener POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
```

### Fase 3: Cache (5 min)
```bash
# 1. Provisionar Redis en tu plataforma
# 2. Obtener REDIS_URL: redis://user:pass@host:6379
# 3. Test: redis-cli -u $REDIS_URL PING
```

### Fase 4: Registry & Backups (5 min)
```bash
# 1. Docker: DOCKER_USERNAME + DOCKER_PASSWORD
#    - Ve a hub.docker.com/settings/security
# 2. AWS S3: BACKUP_ACCESS_KEY + BACKUP_SECRET_KEY
#    - Ve a AWS IAM → Security credentials
```

### Fase 5: Servidor (5 min)
```bash
# 1. SERVER_HOST: IP o dominio del servidor
# 2. SERVER_USERNAME: Usuario SSH
# 3. Test: ssh $SERVER_USERNAME@$SERVER_HOST "echo OK"
```

### Fase 6: Opcional (5 min)
```bash
# 1. CLOUDFLARE_TOKEN: Si usas Cloudflare
# 2. MONITORING_TOKEN: Si usas monitoreo externo
```

---

## 🚀 CÓMO AGREGAR SECRETS EN CADA PLATAFORMA

### GITHUB ACTIONS (Required for CI/CD)
```
1. Ve a: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions
2. Click "New repository secret"
3. Name: SSH_PRIVATE_KEY
4. Value: [pega contenido de ~/.ssh/id_rsa]
5. Repite para cada secret
```

### RAILWAY.APP (Recomendado)
```
1. Railway Dashboard
2. Proyecto → Variables
3. Agregar variable → Name: DATABASE_URL
4. Value: postgresql://...
5. Repite para cada variable
```

### GOOGLE CLOUD RUN
```bash
gcloud run deploy grupo-gad \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --set-env-vars REDIS_URL=$REDIS_URL \
  --set-env-vars SECRET_KEY=$SECRET_KEY
```

### AWS ECS
```bash
# En task definition JSON:
"environment": [
  {"name": "DATABASE_URL", "value": "postgresql://..."},
  {"name": "REDIS_URL", "value": "redis://..."},
  {"name": "SECRET_KEY", "value": "..."}
]
```

### VPS (Docker Compose)
```bash
# .env file
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...

# O directamente en docker-compose.yml
environment:
  - DATABASE_URL=postgresql://...
  - REDIS_URL=redis://...
```

---

## ✅ VALIDACIÓN RÁPIDA

```bash
#!/bin/bash
echo "🔍 Validando Secrets..."

# 1. Check SSH Key
if [ -f ~/.ssh/id_rsa ]; then
  echo "✅ SSH_PRIVATE_KEY existe"
else
  echo "❌ SSH_PRIVATE_KEY falta"
fi

# 2. Check DATABASE_URL
if [ ! -z "$DATABASE_URL" ]; then
  psql "$DATABASE_URL" -c "SELECT 1" && echo "✅ DATABASE_URL válida" || echo "❌ DATABASE_URL inválida"
else
  echo "⚠️  DATABASE_URL no configurada"
fi

# 3. Check REDIS_URL
if [ ! -z "$REDIS_URL" ]; then
  redis-cli -u "$REDIS_URL" PING | grep -q PONG && echo "✅ REDIS_URL válida" || echo "❌ REDIS_URL inválida"
else
  echo "⚠️  REDIS_URL no configurada"
fi

# 4. Check SECRET_KEY
if [ ! -z "$SECRET_KEY" ] && [ ${#SECRET_KEY} -ge 32 ]; then
  echo "✅ SECRET_KEY válida (${#SECRET_KEY} chars)"
else
  echo "❌ SECRET_KEY inválida o muy corta"
fi

# 5. Check Docker
if docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"; then
  echo "✅ Docker credentials válidas"
else
  echo "❌ Docker credentials inválidas"
fi
```

---

## 📋 CHECKLIST DE DEPLOYMENT

### Antes de Deployer
- [ ] Todos los 15 secrets generados
- [ ] SSH key testeable
- [ ] DATABASE_URL conecta
- [ ] REDIS_URL conecta
- [ ] Docker credentials válidas
- [ ] AWS credentials válidas
- [ ] SERVER_HOST accesible
- [ ] firewall allows 80/443

### Durante Deploy
- [ ] Git push completado
- [ ] railway.json válido
- [ ] Docker build exitoso
- [ ] Migrations ejecutadas
- [ ] Health check responde
- [ ] WebSocket conecta

### Post-Deploy
- [ ] `/health` responde ✅
- [ ] `/health/ready` responde ✅
- [ ] WebSocket `/ws/connect` conecta ✅
- [ ] Database sincronizada ✅
- [ ] Redis cache activo ✅
- [ ] Backups configurados ✅
- [ ] Logs accesibles ✅

---

## 🔧 TROUBLESHOOTING RÁPIDO

| Problema | Check | Fix |
|----------|-------|-----|
| "DATABASE_URL not found" | `echo $DATABASE_URL` | Agregar en secrets |
| "redis: Connection refused" | `redis-cli ping` | Verificar REDIS_URL |
| "Docker pull rate limited" | `docker login` | Re-login o usar token |
| "SSH permission denied" | `ssh-keygen -y -f key` | Verificar SSH_PRIVATE_KEY |
| "WebSocket timeout" | `curl -v /ws/connect` | Aumentar timeout |
| "Migrations failed" | `alembic current` | Revisar estado DB |

---

## 📞 COMANDOS ÚTILES

```bash
# Generar valores
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
openssl rand -base64 20
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Testear conexiones
psql postgresql://user:pass@host:5432/db -c "SELECT 1"
redis-cli -u redis://user:pass@host:6379 PING
docker login -u username -p password

# Ver secretos (sin valores sensibles)
env | grep -E "DATABASE|REDIS|SECRET|DOCKER" | cut -d= -f1

# Railway
railway variables
railway logs
railway status

# AWS
aws sts get-caller-identity
aws s3 ls --recursive

# Docker
docker ps
docker logs grupo-gad
docker exec grupo-gad bash
```

---

## 🎯 RESUMEN 30 SEGUNDOS

```
1. Genera secrets: SSH, SECRET_KEY, passwords
2. Provisiona BD: PostgreSQL + Redis
3. Obtiene URLs: DATABASE_URL, REDIS_URL
4. Setup Docker: DOCKER_USERNAME, DOCKER_PASSWORD
5. Setup Backups: AWS credentials
6. Setup Servidor: HOST, USERNAME
7. Agrega a GitHub/Railway
8. Deploy: git push origin master
9. Valida: curl /health ✅
```

---

**Última actualización**: 18 Octubre 2025  
**Estado**: ✅ Production-Ready
