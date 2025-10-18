# 🔐 MIS SECRETS PARA DESPLIEGUE - GRUPO_GAD

**Fecha**: 18 Octubre 2025  
**Usuario**: eevan@eevans  
**Status**: ✅ 8 de 15 completados | ⚠️ 7 pendientes  

---

## 📊 RESUMEN EJECUTIVO

| Categoría | Completados | Pendientes | Status |
|-----------|-------------|------------|--------|
| **Tier 1: Seguridad** | 2/2 | 0 | ✅ |
| **Tier 2: Base Datos** | 4/4 | 0 | ✅ |
| **Tier 3: Redis** | 1/1 | 0 | ✅ |
| **Tier 4: Docker** | 0/2 | 2 | ⚠️ |
| **Tier 5: Backups** | 0/2 | 2 | ⚠️ |
| **Tier 6: Servidor** | 0/2 | 2 | ⚠️ |
| **Tier 7: Opcional** | 0/2 | 2 | 🟡 |
| **TOTAL** | **8/15** | **7** | **53%** |

---

## ✅ SECRETS COMPLETADOS (8/15)

### TIER 1: SEGURIDAD ✅ COMPLETO

#### 1️⃣ SSH_PRIVATE_KEY ✅
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACAbky9NQTr6M/mkb/UdXf/fOHLuvERYxKtR6VeMMG6XQQAAAJDvLHIb7yxy
GwAAAAtzc2gtZWQyNTUxOQAAACAbky9NQTr6M/mkb/UdXf/fOHLuvERYxKtR6VeMMG6XQQ
AAAEBM3dbGYyRTpcBfo7H7/rlYvslppucBVNTqghtQK93PmRuTL01BOvoz+aRv9R1d/984
cu68RFjEq1HpV4wwbpdBAAAADGVldmFuQGVldmFucwE=
-----END OPENSSH PRIVATE KEY-----
```

**SSH Public Key** (para agregar en servidor):
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBuTL01BOvoz+aRv9R1d/984cu68RFjEq1HpV4wwbpdB eevan@eevans
```

**Cómo usar en GitHub**:
1. Ve a: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions
2. Click "New repository secret"
3. Name: `SSH_PRIVATE_KEY`
4. Value: [pega el contenido completo arriba]

**Cómo usar en servidor**:
```bash
# En tu servidor de producción, agrega la clave pública:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBuTL01BOvoz+aRv9R1d/984cu68RFjEq1HpV4wwbpdB eevan@eevans" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

#### 2️⃣ SECRET_KEY ✅
```
1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d
```

**Cómo usar**:
- GitHub Secrets: Name `SECRET_KEY`, Value arriba
- Railway: Environment Variable `SECRET_KEY`
- .env local: `SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d`

---

### TIER 2: BASE DE DATOS ✅ COMPLETO

#### 3️⃣ POSTGRES_USER ✅
```
gcp_user
```

#### 4️⃣ POSTGRES_PASSWORD ✅
```
E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=
```

#### 5️⃣ POSTGRES_DB ✅
```
gcp_db
```

#### 6️⃣ DATABASE_URL ✅ (⚠️ Requiere actualización para Fly.io)
**Actual (desarrollo)**:
```
postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@localhost:5432/gcp_db
```

**Para Fly.io** (se genera automáticamente):
```bash
# Crear PostgreSQL en Fly.io
flyctl postgres create --name grupo-gad-db --region mia
flyctl postgres attach grupo-gad-db --app grupo-gad

# Esto automáticamente crea el secret DATABASE_URL con formato:
postgresql://postgres:[auto-password]@grupo-gad-db.internal:5432/grupo_gad

# Verificar
flyctl secrets list | grep DATABASE_URL
```

**Otras plataformas** (solo si NO usas Fly.io):
```bash
# Formato genérico:
postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@[HOST]:[PORT]/gcp_db

# Railway:
postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@containers.railway.app:5432/gcp_db

# Google Cloud SQL:
postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@34.123.45.67:5432/gcp_db

# AWS RDS:
postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@grupo-gad-db.c6xyz.us-east-1.rds.amazonaws.com:5432/gcp_db
```

---

### TIER 3: REDIS ✅ COMPLETO

#### 7️⃣ REDIS_URL ✅ (⚠️ Requiere actualización para Fly.io)
**Actual (desarrollo)**:
```
redis://localhost:6379
```

**Para Fly.io** (se genera automáticamente):
```bash
# Crear Redis en Fly.io (Upstash - gratis)
flyctl redis create --name grupo-gad-redis --region global --plan free
flyctl redis attach grupo-gad-redis --app grupo-gad

# Esto automáticamente crea el secret REDIS_URL con formato:
redis://[token]@fly.upstash.io:6379

# Verificar
flyctl secrets list | grep REDIS_URL
```

**Otras plataformas** (solo si NO usas Fly.io):
```bash
# Railway:
redis://default:xyz123token@containers.railway.app:6379

# Google Cloud Memorystore:
redis://10.0.0.3:6379

# AWS ElastiCache:
rediss://default:token@grupo-gad-cache.abc123.use1.cache.amazonaws.com:6379/0
```

**Status**: ⏳ SE GENERARÁ EN FLY.IO DEPLOY

---

## ⚠️ SECRETS PENDIENTES (7/15)

### TIER 4: DOCKER REGISTRY (2 pendientes)

#### 8️⃣ DOCKER_USERNAME ⚠️
**Acción requerida**: Proporcionar tu usuario de DockerHub

**Pasos**:
1. Ve a https://hub.docker.com
2. Si no tienes cuenta, crea una
3. Tu username es lo que aparece después de hub.docker.com/u/[USERNAME]

**Ejemplo**:
```
eevans-d
```

**Dónde obtener**:
- URL: https://hub.docker.com/settings/general

---

#### 9️⃣ DOCKER_PASSWORD ⚠️
**Acción requerida**: Generar Access Token de DockerHub

**Pasos**:
1. Ve a https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Description: "GRUPO_GAD CI/CD"
4. Access permissions: "Read, Write, Delete"
5. Click "Generate"
6. **COPIA EL TOKEN INMEDIATAMENTE** (no se mostrará de nuevo)

**Formato esperado**:
```
dckr_pat_ABC123XYZ...
```

**⚠️ IMPORTANTE**: 
- NO uses tu contraseña de DockerHub
- Usa solo Access Tokens
- Guarda el token en lugar seguro

---

### TIER 5: AWS BACKUPS (2 pendientes)

#### 🔟 BACKUP_ACCESS_KEY ⚠️
**Acción requerida**: Generar AWS Access Key

**Pasos**:
1. Ve a AWS Console → IAM → Users
2. Selecciona tu usuario (o crea uno para backups)
3. Tab "Security credentials"
4. Click "Create access key"
5. Select "Application running on AWS compute service"
6. Click "Next" → "Create access key"
7. **DESCARGA EL CSV** con las credenciales

**Formato esperado**:
```
AKIA2ABCDEFGHIJKLMNO
```

**Permisos necesarios** (IAM Policy):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::grupo-gad-backups/*",
        "arn:aws:s3:::grupo-gad-backups"
      ]
    }
  ]
}
```

---

#### 1️⃣1️⃣ BACKUP_SECRET_KEY ⚠️
**Acción requerida**: Obtener junto con Access Key

**Pasos**:
- Se genera automáticamente en el paso anterior
- Aparece en el CSV descargado
- **GUÁRDALA DE FORMA SEGURA** (no se puede recuperar después)

**Formato esperado**:
```
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**⚠️ CRÍTICO**: 
- Esta clave NO se puede recuperar
- Si la pierdes, debes generar una nueva Access Key completa
- Guárdala en gestor de contraseñas (1Password, LastPass, etc.)

---

### TIER 6: SERVIDOR SSH (2 pendientes)

### 🔴 5. SERVER_HOST

**Descripción**: IP o dominio del servidor de producción

**Valor Esperado**: `grupo-gad.fly.dev` (Fly.io auto-generado)

**Acción Requerida**:
```bash
# Fly.io genera automáticamente el dominio al hacer deploy
flyctl launch  # Crea app y genera: [app-name].fly.dev

# Ver tu dominio actual
flyctl info --app grupo-gad | grep Hostname

# Si quieres dominio custom
flyctl certs create tu-dominio.com --app grupo-gad
# Luego agregar DNS CNAME: tu-dominio.com → grupo-gad.fly.dev
```

**Valor para usar**:
```bash
# OPCIÓN 1: Dominio Fly.io (automático)
SERVER_HOST=grupo-gad.fly.dev

# OPCIÓN 2: Dominio custom (si configuraste)
SERVER_HOST=api.tuempresa.com
```

**Status**: ⏳ SE GENERARÁ EN DEPLOY

---

#### 1️⃣3️⃣ SERVER_USERNAME ⚠️ (NO REQUERIDO para Fly.io)
**Acción requerida**: Usuario SSH del servidor

**⚠️ IMPORTANTE para Fly.io**:
```bash
# Fly.io NO usa SSH tradicional con usuario/contraseña
# Acceso a la VM se hace con:
flyctl ssh console --app grupo-gad

# NO NECESITAS configurar este secret para Fly.io
```

**Solo si usas VPS/EC2 tradicional** (NO Fly.io):
- **AWS EC2**: `ec2-user` (Amazon Linux) o `ubuntu` (Ubuntu)
- **Google Cloud**: `tu-username-google` o `ubuntu`
- **DigitalOcean**: `root` o `ubuntu`
- **Linode**: `root`
- **Railway**: No aplica (gestión automática)

**Cómo verificar**:
```bash
# Test SSH:
ssh [usuario]@[SERVER_HOST] "whoami"

# Ejemplo:
ssh ubuntu@192.168.1.100 "whoami"
# Debe responder: ubuntu
```

---

### TIER 7: OPCIONALES (2 pendientes)

#### 1️⃣4️⃣ CLOUDFLARE_TOKEN 🟡 (Opcional)
**Acción requerida**: Solo si usas Cloudflare

**Pasos**:
1. Ve a https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Template: "Edit zone DNS"
4. Zone Resources: Include → Specific zone → grupo-gad.com
5. Click "Continue to summary" → "Create Token"
6. **COPIA EL TOKEN**

**Formato esperado**:
```
aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
```

**¿Lo necesito?**:
- ✅ SÍ: Si usas Cloudflare para DNS/SSL/CDN
- ❌ NO: Si usas Railway/GCP/AWS directamente

---

#### 1️⃣5️⃣ MONITORING_TOKEN 🟡 (Opcional)
**Acción requerida**: Solo si usas servicio de monitoreo

**Servicios soportados**:
- **Datadog**: https://app.datadoghq.com/organization-settings/api-keys
- **New Relic**: https://one.newrelic.com/admin-portal/api-keys/home
- **Sentry**: https://sentry.io/settings/account/api/auth-tokens/

**Formato esperado** (depende del servicio):
```
# Datadog:
1234567890abcdef1234567890abcdef

# Sentry:
sntrys_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# New Relic:
NRAK-XXXXXXXXXXXXXXXXXXXXXXXX
```

**¿Lo necesito?**:
- ✅ SÍ: Si quieres monitoreo avanzado (recomendado en producción)
- ❌ NO: Para desarrollo o despliegues iniciales

---

## 📋 CHECKLIST DE CONFIGURACIÓN

### Fase 1: Secrets Completados ✅
- [x] SSH_PRIVATE_KEY generado
- [x] SECRET_KEY generado
- [x] POSTGRES_USER definido
- [x] POSTGRES_PASSWORD generado
- [x] POSTGRES_DB definido
- [x] DATABASE_URL (local) configurado
- [x] REDIS_URL (local) configurado
- [x] SSH Public Key obtenida

### Fase 2: Pendientes Críticos ⚠️
- [ ] **DOCKER_USERNAME**: Obtener de hub.docker.com
- [ ] **DOCKER_PASSWORD**: Generar Access Token
- [ ] **BACKUP_ACCESS_KEY**: Generar en AWS IAM
- [ ] **BACKUP_SECRET_KEY**: Obtener junto con Access Key
- [ ] **SERVER_HOST**: Definir según plataforma elegida
- [ ] **SERVER_USERNAME**: Definir según plataforma elegida

### Fase 3: Actualizar para Producción ⚠️
- [ ] **DATABASE_URL**: Actualizar localhost por host real
- [ ] **REDIS_URL**: Actualizar localhost por host real

### Fase 4: Opcionales 🟡
- [ ] **CLOUDFLARE_TOKEN**: Si usas Cloudflare
- [ ] **MONITORING_TOKEN**: Si usas monitoreo

---

## 🚀 PRÓXIMOS PASOS

### 1. Completar Secrets Pendientes (15-20 min)

```bash
# Checklist rápido:
echo "✅ Secrets completados: 8/15 (53%)"
echo ""
echo "⚠️ Pendientes críticos:"
echo "  1. DOCKER_USERNAME (hub.docker.com)"
echo "  2. DOCKER_PASSWORD (Access Token)"
echo "  3. BACKUP_ACCESS_KEY (AWS IAM)"
echo "  4. BACKUP_SECRET_KEY (AWS IAM)"
echo "  5. SERVER_HOST (Railway/GCP/AWS/VPS)"
echo "  6. SERVER_USERNAME (ubuntu/ec2-user/root)"
echo ""
echo "🟡 Opcionales:"
echo "  7. CLOUDFLARE_TOKEN"
echo "  8. MONITORING_TOKEN"
```

### 2. Elegir Plataforma de Deployment (5 min)

**Opciones**:
- ✈️ **Railway** (Recomendado - más simple)
  - Pros: Setup automático, free tier, PostgreSQL + Redis incluidos
  - Contras: Menos control, $20-28/mes en producción
  
- ☁️ **Google Cloud Run** (Premium)
  - Pros: Muy escalable, pay-per-use
  - Contras: Más complejo, requiere Cloud SQL + Memorystore
  
- 🚀 **AWS ECS** (Enterprise)
  - Pros: Control total, escalabilidad
  - Contras: Más caro, curva de aprendizaje
  
- 🖥️ **VPS** (DigitalOcean/Linode)
  - Pros: Control total, precio fijo
  - Contras: Mantenimiento manual

### 3. Agregar Secrets en GitHub (10 min)

```bash
# URL directa:
open https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

# Agregar uno por uno:
# 1. Click "New repository secret"
# 2. Name: SSH_PRIVATE_KEY
# 3. Value: [copiar de este documento]
# 4. Click "Add secret"
# 5. Repetir para los 15 secrets
```

### 4. Configurar Plataforma Elegida (10-15 min)

**Railway** (ejemplo):
```bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Link proyecto
railway link

# Agregar secrets
railway variables set SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d
railway variables set POSTGRES_USER=gcp_user
# ... etc
```

### 5. Deploy y Validación (15-20 min)

```bash
# Push a master (activa CI/CD)
git push origin master

# Verificar health
curl https://tu-proyecto.railway.app/health
# Esperado: {"status":"ok"}

# Verificar WebSocket
curl https://tu-proyecto.railway.app/docs
# Buscar /ws/connect en Swagger UI
```

---

## 🔧 COMANDOS ÚTILES

### Validar Secrets Locales

```bash
#!/bin/bash
echo "🔍 Validando secrets completados..."

# SSH Key
if [ -f ~/.ssh/id_ed25519 ]; then
  echo "✅ SSH_PRIVATE_KEY existe"
else
  echo "❌ SSH_PRIVATE_KEY falta"
fi

# Test DATABASE_URL (local)
psql "postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@localhost:5432/gcp_db" -c "SELECT 1" && echo "✅ DATABASE_URL válida" || echo "❌ DATABASE_URL inválida"

# Test REDIS_URL (local)
redis-cli -u redis://localhost:6379 PING | grep -q PONG && echo "✅ REDIS_URL válida" || echo "❌ REDIS_URL inválida"

# Check SECRET_KEY
SECRET_KEY="1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d"
if [ ${#SECRET_KEY} -ge 32 ]; then
  echo "✅ SECRET_KEY válida (${#SECRET_KEY} chars)"
else
  echo "❌ SECRET_KEY muy corta"
fi
```

### Generar .env Local

```bash
cat > .env.local << 'ENVFILE'
# Generado: 18 Octubre 2025
ENVIRONMENT=development

# Tier 1: Seguridad
SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d

# Tier 2: Base de Datos
POSTGRES_USER=gcp_user
POSTGRES_PASSWORD=E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=
POSTGRES_DB=gcp_db
DATABASE_URL=postgresql://gcp_user:E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=@localhost:5432/gcp_db

# Tier 3: Redis
REDIS_URL=redis://localhost:6379

# Pendientes (actualizar antes de producción)
# DOCKER_USERNAME=
# DOCKER_PASSWORD=
# BACKUP_ACCESS_KEY=
# BACKUP_SECRET_KEY=
# SERVER_HOST=
# SERVER_USERNAME=
# CLOUDFLARE_TOKEN=
# MONITORING_TOKEN=
ENVFILE

chmod 600 .env.local
echo "✅ .env.local creado"
```

---

## 📖 DOCUMENTACIÓN RELACIONADA

- **DEPLOYMENT_SECRETS_COMPLETE.md**: Guía completa de todos los secrets
- **DEPLOYMENT_SECRETS_REFERENCE.md**: Referencia rápida
- **RAILWAY_DEPLOYMENT_COMPLETE.md**: Guía específica de Railway
- **GITHUB_SECRETS_GUIDE.md**: Configuración GitHub Actions

---

## 🎯 ESTADO ACTUAL

```
✅ Completado: 8/15 secrets (53%)
⚠️  Pendiente:  7/15 secrets (47%)

Tiempo estimado para completar:
├─ Docker tokens:     5 min
├─ AWS credentials:   10 min
├─ Servidor info:     5 min
└─ Opcionales:        10 min
────────────────────────────
TOTAL:                30 min

Próximo paso: Obtener DOCKER_USERNAME y DOCKER_PASSWORD
```

---

**Última actualización**: 18 Octubre 2025  
**Usuario**: eevan@eevans  
**Status**: ⚠️ 47% pendiente - Listo para completar
