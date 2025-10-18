# 🔐 GitHub Secrets - Guía Completa

**Última actualización**: Octubre 18, 2025  
**Status**: Production-ready  
**Tiempo**: 5-15 minutos según detalle  

---

## 🎯 Quick Start (5 minutos)

### Acceso Rápido
**URL directa**: `https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions`

### Proceso Simple
1. Abre la URL arriba
2. Click "New repository secret" (botón verde)
3. Ingresa nombre exacto (ej: `SSH_PRIVATE_KEY`)
4. Pega el valor
5. Click "Add secret"
6. Repite para los 15 secrets

---

## 📋 Los 15 Secrets Requeridos

| # | Secret | Dónde Obtener | Prioridad |
|---|--------|---------------|-----------|
| 1 | `SSH_PRIVATE_KEY` | `cat ~/.ssh/id_rsa` | 🔴 |
| 2 | `SERVER_HOST` | IP del servidor (ej: 192.168.1.100) | 🔴 |
| 3 | `SERVER_USERNAME` | Usuario SSH (ubuntu, ec2-user) | 🔴 |
| 4 | `DATABASE_URL` | PostgreSQL URL en producción | 🔴 |
| 5 | `REDIS_URL` | Redis URL (redis://host:6379) | 🔴 |
| 6 | `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | 🔴 |
| 7 | `POSTGRES_USER` | Nombre usuario BD | 🔴 |
| 8 | `POSTGRES_PASSWORD` | `openssl rand -base64 20` | 🔴 |
| 9 | `POSTGRES_DB` | Nombre base de datos | 🔴 |
| 10 | `DOCKER_USERNAME` | Usuario DockerHub | 🔴 |
| 11 | `DOCKER_PASSWORD` | Token DockerHub | 🔴 |
| 12 | `BACKUP_ACCESS_KEY` | AWS Access Key ID | 🔴 |
| 13 | `BACKUP_SECRET_KEY` | AWS Secret Key | 🔴 |
| 14 | `CLOUDFLARE_TOKEN` | API Token Cloudflare | 🟡 |
| 15 | `MONITORING_TOKEN` | Token monitoreo | 🟡 |

🔴 Requerido | 🟡 Opcional

---

## 🔑 Comandos Útiles

### Generar SECRET_KEY
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Generar POSTGRES_PASSWORD
```bash
openssl rand -base64 20
```

### Obtener SSH_PRIVATE_KEY
```bash
cat ~/.ssh/id_rsa
```
**Nota**: Si no existe, crea una:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

### Verificar SSH_PUBLIC_KEY en servidor
```bash
cat ~/.ssh/id_rsa.pub
# Agregar esta clave al servidor en ~/.ssh/authorized_keys
```

---

## ✅ Checklist de Configuración

### Tier 1: Credentials Básicas (5-7 min)
- [ ] `SSH_PRIVATE_KEY` - Clave privada SSH completa
- [ ] `SERVER_HOST` - IP o dominio del servidor
- [ ] `SERVER_USERNAME` - Usuario SSH (ubuntu, root, etc.)
- [ ] `SECRET_KEY` - Token generado

### Tier 2: Database (2-3 min)
- [ ] `DATABASE_URL` - `postgresql://user:pass@host:5432/db`
- [ ] `POSTGRES_USER` - Nombre usuario PostgreSQL
- [ ] `POSTGRES_PASSWORD` - Contraseña fuerte (16+ chars)
- [ ] `POSTGRES_DB` - Nombre base de datos

### Tier 3: Redis & Docker (2-3 min)
- [ ] `REDIS_URL` - URL conexión Redis
- [ ] `DOCKER_USERNAME` - Usuario Docker Registry
- [ ] `DOCKER_PASSWORD` - Token/password Docker

### Tier 4: Backups & Opcionales (1-2 min)
- [ ] `BACKUP_ACCESS_KEY` - AWS/S3 Access Key
- [ ] `BACKUP_SECRET_KEY` - AWS/S3 Secret Key
- [ ] `CLOUDFLARE_TOKEN` - (opcional si usas Cloudflare)
- [ ] `MONITORING_TOKEN` - (opcional si usas monitoreo externo)

---

## 📖 Guía Detallada Paso a Paso

### 1. Acceder a GitHub Secrets

**Opción A: URL directa**
```
https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions
```

**Opción B: Navegación manual**
1. Ve a `https://github.com/eevans-d/GRUPO_GAD`
2. Click en **Settings** (pestaña superior derecha)
3. En menú izquierdo: **Secrets and variables** → **Actions**

### 2. Crear Cada Secret

**Para CADA uno de los 15 secrets:**

1. Click botón verde **"New repository secret"**
2. **Name**: Escribe el nombre EXACTO (respeta mayúsculas)
   - Ejemplo: `SSH_PRIVATE_KEY` (no `ssh_private_key`)
3. **Secret**: Pega el valor
   - Para `SSH_PRIVATE_KEY`: Todo el contenido incluye `-----BEGIN` y `-----END`
   - Para tokens: Solo el token (sin espacios extra)
4. Click **"Add secret"**
5. Verás mensaje de confirmación ✅

### 3. Verificación

Una vez configurados los 15, verás en la página:

```
✅ SSH_PRIVATE_KEY          Updated X seconds ago
✅ SERVER_HOST              Updated X seconds ago
✅ SERVER_USERNAME          Updated X seconds ago
✅ DATABASE_URL             Updated X seconds ago
✅ REDIS_URL                Updated X seconds ago
✅ SECRET_KEY               Updated X seconds ago
✅ POSTGRES_USER            Updated X seconds ago
✅ POSTGRES_PASSWORD        Updated X seconds ago
✅ POSTGRES_DB              Updated X seconds ago
✅ DOCKER_USERNAME          Updated X seconds ago
✅ DOCKER_PASSWORD          Updated X seconds ago
✅ BACKUP_ACCESS_KEY        Updated X seconds ago
✅ BACKUP_SECRET_KEY        Updated X seconds ago
✅ CLOUDFLARE_TOKEN         Updated X seconds ago (opcional)
✅ MONITORING_TOKEN         Updated X seconds ago (opcional)
```

Cada secret tiene un botón ✏️ **Update** para editar.

---

## 🔐 Detalles de Cada Secret

### 1. SSH_PRIVATE_KEY

**Propósito**: Permitir al pipeline CI/CD conectarse al servidor vía SSH

**Cómo obtenerla**:
```bash
cat ~/.ssh/id_rsa
```

**Formato esperado**:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(muchas líneas)
...
-----END RSA PRIVATE KEY-----
```

**⚠️ IMPORTANTE**: 
- Copia TODO el contenido (incluye `-----BEGIN` y `-----END`)
- NO compartas esta clave públicamente
- Si usas GitHub CLI/actions, asegúrate que el servidor tiene la clave pública en `~/.ssh/authorized_keys`

**Configurar clave pública en servidor**:
```bash
# En tu PC local
cat ~/.ssh/id_rsa.pub

# En el servidor (SSH manual)
echo "PEGA_LA_CLAVE_PUBLICA_AQUI" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

### 2. SERVER_HOST

**Propósito**: IP o dominio del servidor donde se despliega

**Ejemplos válidos**:
- `192.168.1.100` (IP privada)
- `52.10.20.30` (IP pública)
- `prod.example.com` (dominio)

**Cómo obtenerla**:
```bash
# Si estás EN el servidor
curl ifconfig.me

# Si conoces el dominio
dig +short prod.example.com
```

---

### 3. SERVER_USERNAME

**Propósito**: Usuario SSH para conectarse al servidor

**Ejemplos comunes**:
- `ubuntu` (AWS EC2 Ubuntu)
- `ec2-user` (AWS EC2 Amazon Linux)
- `root` (servidores VPS tradicionales)
- `deploy` (usuario custom creado para deploy)

**Cómo verificar**:
```bash
# Prueba conectarte manualmente
ssh SERVER_USERNAME@SERVER_HOST
```

---

### 4. DATABASE_URL

**Propósito**: URL completa de conexión a PostgreSQL en producción

**Formato**:
```
postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

**Ejemplo real**:
```
postgresql://grupogad_user:SecurePass123@192.168.1.100:5432/grupogad_prod
```

**⚠️ IMPORTANTE**:
- Debe ser la BD de **producción** (no desarrollo)
- El usuario debe tener permisos completos
- Verifica que el host sea accesible desde el servidor de deploy

---

### 5. REDIS_URL

**Propósito**: URL de conexión a Redis en producción

**Formato**:
```
redis://[HOST]:[PORT]
```

**Ejemplo**:
```
redis://192.168.1.100:6379
```

**Con autenticación**:
```
redis://:PASSWORD@192.168.1.100:6379
```

---

### 6. SECRET_KEY

**Propósito**: Clave secreta para JWT, cookies, encriptación

**Generar**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Resultado** (ejemplo):
```
vK3_sH9pL2mN6qR8tU4wY7zF1xC5bD0eA
```

**⚠️ IMPORTANTE**:
- Debe ser único y aleatorio
- Mínimo 32 caracteres
- NO uses valores predecibles (tu nombre, fechas, etc.)
- Guarda este valor en un password manager

---

### 7-9. PostgreSQL Credentials

**POSTGRES_USER**: Nombre de usuario PostgreSQL
- Ejemplo: `grupogad_user`, `app_prod`, `postgres`

**POSTGRES_PASSWORD**: Contraseña del usuario
```bash
openssl rand -base64 20
```
- Resultado: `xY9mP3nQ7rT5wZ2vK8fH4jL`
- Mínimo 16 caracteres, incluye números y símbolos

**POSTGRES_DB**: Nombre de la base de datos
- Ejemplo: `grupogad_prod`, `app_production`, `maindb`

---

### 10-11. Docker Credentials

**DOCKER_USERNAME**: Tu usuario en Docker Registry

**Dónde obtenerlo**:
- DockerHub: Tu username (ej: `eevans-d`)
- AWS ECR: `AWS` (literal)
- GitHub Container Registry: Tu GitHub username

**DOCKER_PASSWORD**: Token de acceso

**DockerHub**:
1. Ve a https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Dale un nombre: "GRUPO_GAD_CI_CD"
4. Copia el token generado

**⚠️ NO uses tu contraseña personal**, siempre usa tokens.

---

### 12-13. Backup Credentials

**BACKUP_ACCESS_KEY** y **BACKUP_SECRET_KEY**

**AWS S3**:
1. Ve a AWS IAM Console
2. Crea usuario: `grupogad-backup-user`
3. Asigna policy: `AmazonS3FullAccess` (o custom restringido)
4. Crea Access Key
5. Copia **Access Key ID** → `BACKUP_ACCESS_KEY`
6. Copia **Secret Access Key** → `BACKUP_SECRET_KEY`

**Alternativas**:
- **Wasabi**: Similar a AWS S3
- **DigitalOcean Spaces**: Compatible S3
- **Backblaze B2**: Keys de aplicación

---

### 14-15. Opcionales

**CLOUDFLARE_TOKEN** (si usas Cloudflare):
1. Ve a https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Template: "Edit zone DNS"
4. Copia token generado

**MONITORING_TOKEN** (si usas Sentry, Datadog, etc.):
- Sentry: Project Settings → Client Keys (DSN)
- Datadog: Organization Settings → API Keys

---

## 🎨 Capturas de Pantalla (Guía Visual)

### Paso 1: Acceder a Settings
```
GitHub Repo → Settings (tab superior derecha)
```

### Paso 2: Ir a Secrets
```
Menú izquierdo → Secrets and variables → Actions
```

### Paso 3: Crear Secret
```
Botón verde "New repository secret"
├── Name: SSH_PRIVATE_KEY
├── Secret: [paste entire private key]
└── Add secret (botón verde)
```

### Resultado
```
Lista de secrets configurados:
✅ SSH_PRIVATE_KEY
✅ SERVER_HOST
... (15 total)
```

---

## 🚨 Troubleshooting

### Error: "Pipeline failing - Secret not found"

**Solución**:
1. Verifica que el nombre del secret sea **EXACTO** (respeta mayúsculas)
2. En GitHub: Secrets → Verifica que exista
3. Revisa logs del workflow para ver qué secret falta

---

### Error: "SSH connection failed"

**Causas comunes**:
1. `SSH_PRIVATE_KEY` no coincide con la clave pública en el servidor
2. `SERVER_HOST` incorrecto
3. `SERVER_USERNAME` incorrecto

**Solución**:
```bash
# Verifica conexión manual
ssh -i ~/.ssh/id_rsa SERVER_USERNAME@SERVER_HOST

# Si falla, asegúrate que la clave pública esté en el servidor
cat ~/.ssh/id_rsa.pub
# Agregar al servidor en ~/.ssh/authorized_keys
```

---

### Error: "Database connection failed"

**Verificar**:
1. `DATABASE_URL` con formato correcto
2. PostgreSQL está corriendo: `systemctl status postgresql`
3. Firewall permite conexiones: `sudo ufw status`
4. Usuario/password correctos

---

## 📚 Recursos Adicionales

**Documentación oficial**:
- GitHub Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- SSH Keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

**Guías en este repo**:
- **Quick Start**: Ver sección al inicio (5 min)
- **Visual Guide**: `docs/github/GITHUB_SECRETS_VISUAL_GUIDE.md` (con screenshots)
- **Full Setup**: `docs/github/GITHUB_SECRETS_SETUP_GUIDE.md` (detallado)

---

## ✅ Después de Configurar

Una vez los 15 secrets estén configurados:

1. **Push cualquier cambio** a `master` o `main`
2. El pipeline CI/CD se activará automáticamente
3. Ve a **Actions** tab para ver el progreso
4. Espera ~5-10 minutos para el primer deploy

**Verificar deploy exitoso**:
```bash
# Conecta al servidor
ssh SERVER_USERNAME@SERVER_HOST

# Verifica que la app esté corriendo
docker ps | grep grupogad

# Verifica logs
docker logs grupogad_api
```

---

**Generado**: 18 Octubre 2025  
**Mantenedor**: @eevans-d  
**Repo**: https://github.com/eevans-d/GRUPO_GAD
