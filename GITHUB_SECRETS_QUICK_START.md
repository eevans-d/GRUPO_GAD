# ⚡ GUÍA RÁPIDA: Setup Secrets en 10 minutos

## 🎯 RESUMEN ULTRA-RÁPIDO

**URL**: `https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions`

**Pasos**:
1. Abre URL arriba
2. Click "New repository secret" (botón verde)
3. Ingresa nombre (ej: `SSH_PRIVATE_KEY`)
4. Pega valor
5. Click "Add secret"
6. Repite 15 veces
7. ¡Listo!

---

## 📋 TABLA RÁPIDA: DÓNDE OBTENER CADA SECRET

| Secret | Dónde Obtenerlo | Urgencia |
|--------|-----------------|----------|
| **SSH_PRIVATE_KEY** | `cat ~/.ssh/id_rsa` en tu PC | 🔴 |
| **SERVER_HOST** | IP del servidor (ej: 192.168.1.1) | 🔴 |
| **SERVER_USERNAME** | Usuario SSH (ej: ubuntu) | 🔴 |
| **DATABASE_URL** | PostgreSQL en producción | 🔴 |
| **REDIS_URL** | Redis en producción | 🔴 |
| **SECRET_KEY** | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | 🔴 |
| **POSTGRES_USER** | Usuario para BD (ej: app_user) | 🔴 |
| **POSTGRES_PASSWORD** | `openssl rand -base64 20` | 🔴 |
| **POSTGRES_DB** | Nombre BD (ej: app_prod) | 🔴 |
| **DOCKER_USERNAME** | Tu usuario DockerHub | 🔴 |
| **DOCKER_PASSWORD** | Token de DockerHub | 🔴 |
| **CLOUDFLARE_TOKEN** | API Token Cloudflare | 🟡 |
| **MONITORING_TOKEN** | Token de monitoreo | 🟡 |
| **BACKUP_ACCESS_KEY** | AWS Access Key ID | 🔴 |
| **BACKUP_SECRET_KEY** | AWS Secret Access Key | 🔴 |

🔴 = Requerido | 🟡 = Opcional

---

## 🚀 PASO 1: ACCEDER A SECRETS

```
GitHub UI → Tu Repo (GRUPO_GAD)
  ↓
Settings (pestaña arriba a la derecha)
  ↓
Secrets and variables → Actions (menú izquierdo)
  ↓
¡Listo! Ya estás en la página de secrets
```

---

## 🔧 PASO 2: CREAR CADA SECRET (Repetir 15 veces)

```
1. Click botón verde "New repository secret"

2. Escribe nombre exacto:
   SSH_PRIVATE_KEY
   (respeta mayúsculas)

3. Pega el valor en el campo Value

4. Click "Add secret"

5. ✅ Verás un mensaje de confirmación
```

---

## 📋 CHECKLIST: INGRESAR LOS 15 SECRETS

### Tier 1: CREDENTIALS BÁSICAS (5-7 min)

- [ ] **SSH_PRIVATE_KEY** - Valor: `cat ~/.ssh/id_rsa`
- [ ] **SERVER_HOST** - Valor: Tu IP servidor (ej: 192.168.1.100)
- [ ] **SERVER_USERNAME** - Valor: ubuntu, ec2-user, etc.
- [ ] **SECRET_KEY** - Valor: Token aleatorio generado

### Tier 2: DATABASE (2-3 min)

- [ ] **DATABASE_URL** - Valor: `postgresql://user:pass@host:5432/db`
- [ ] **POSTGRES_USER** - Valor: nombre_usuario
- [ ] **POSTGRES_PASSWORD** - Valor: contraseña_fuerte
- [ ] **POSTGRES_DB** - Valor: nombre_base_datos

### Tier 3: REDIS & DOCKER (2-3 min)

- [ ] **REDIS_URL** - Valor: `redis://host:6379`
- [ ] **DOCKER_USERNAME** - Valor: tu_usuario_dockerhub
- [ ] **DOCKER_PASSWORD** - Valor: token_dockerhub

### Tier 4: BACKUPS & OPCIONALES (1-2 min)

- [ ] **BACKUP_ACCESS_KEY** - Valor: AWS Access Key ID
- [ ] **BACKUP_SECRET_KEY** - Valor: AWS Secret Key
- [ ] **CLOUDFLARE_TOKEN** - Valor: (opcional)
- [ ] **MONITORING_TOKEN** - Valor: (opcional)

---

## 🔑 GENERAR VALORES RÁPIDOS (TERMINAL)

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

---

## ✅ VERIFICACIÓN FINAL

Una vez ingreses los 15 secrets, verás en la página:

```
✅ SSH_PRIVATE_KEY
✅ SERVER_HOST
✅ SERVER_USERNAME
✅ DATABASE_URL
✅ REDIS_URL
✅ SECRET_KEY
✅ POSTGRES_USER
✅ POSTGRES_PASSWORD
✅ POSTGRES_DB
✅ DOCKER_USERNAME
✅ DOCKER_PASSWORD
✅ CLOUDFLARE_TOKEN (si configuraste)
✅ MONITORING_TOKEN (si configuraste)
✅ BACKUP_ACCESS_KEY
✅ BACKUP_SECRET_KEY
```

Cada uno con un botón ✏️ para editar

---

## 🎬 DESPUÉS: ACTIVAR PIPELINE

### Opción 1: Automático
- El próximo push a `master` activará el pipeline

### Opción 2: Manual
```
GitHub UI → Actions → ci-cd workflow
  ↓
Click "Run workflow"
  ↓
Selecciona "master"
  ↓
Click "Run workflow"
```

---

## 🐛 ERRORES COMUNES

| Error | Solución |
|-------|----------|
| "Secret not found" | Verifica el nombre exacto (mayúsculas) |
| "Connection refused" | DATABASE_URL o REDIS_URL inválidos |
| "Auth failed" | DOCKER_PASSWORD o SSH_PRIVATE_KEY incorrecto |
| "Key format invalid" | SSH_PRIVATE_KEY sin headers `-----BEGIN RSA PRIVATE KEY-----` |

---

## 💡 TIPS

✅ Copia/Pega completo (incluye saltos de línea)
✅ No dejes espacios al inicio/final
✅ Respeta mayúsculas en nombres
✅ Usa contraseñas/tokens fuertes
✅ Guarda los valores en un gestor de contraseñas

---

## ⏱️ TIEMPO TOTAL

- **Recopilación de valores**: ~5 min
- **Ingreso de 15 secrets en UI**: ~7 min
- **TOTAL**: ~12 minutos

---

## 🚀 ¡LISTO!

Una vez completado:
✅ Todos los secrets configurados
✅ CI/CD activado
✅ Deployment automático a producción
✅ **PROYECTO 100% COMPLETADO** 🎉

---

**Guía Rápida - GRUPO_GAD**  
*Octubre 16, 2025*
