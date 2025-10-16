# 🎬 GUÍA VISUAL: Configurar Secrets en GitHub (Con Screenshots ASCII)

## 📍 PASO 1: IR A GITHUB SETTINGS

```
┌─────────────────────────────────────────────────────────┐
│  GitHub - GRUPO_GAD Repository                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Code  Pull Requests  Issues  Actions  Wiki  Settings ← │
│                                                          │
│  (Haz click en Settings)                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Ubicación**: Esquina superior derecha del repositorio

---

## 📍 PASO 2: VER MENÚ DE SEGURIDAD

```
┌──────────────────────────────────────────────────────────┐
│  Settings Page - Left Menu                              │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  General                                                 │
│  Access                                                  │
│  Security                                                │
│    ├─ Secrets and variables ← AQUÍ                       │
│    │  ├─ Actions                                         │
│    │  ├─ Dependabot                                      │
│    │  └─ Codespaces                                      │
│    └─ ...                                                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Ubicación**: Menú izquierdo → Security → Secrets and variables → Actions

---

## 📍 PASO 3: PÁGINA DE SECRETS

```
┌───────────────────────────────────────────────────────────┐
│  Actions secrets and variables                            │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  [🟢 New repository secret]  [🔍 Search]                 │
│                                                            │
│  Repository secrets                                       │
│  ─────────────────────────────────────────────────────────│
│  No secrets yet                                            │
│  (O si ya tienes algunos, los verás aquí)                 │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

**Botón clave**: "New repository secret" (verde, arriba a la derecha)

---

## 📍 PASO 4: CREAR NUEVO SECRET

```
┌─────────────────────────────────────────────────────────┐
│  New secret                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Name *                                                 │
│  ┌───────────────────────────────────────────────────┐ │
│  │ SSH_PRIVATE_KEY                                   │ │
│  └───────────────────────────────────────────────────┘ │
│  (No spaces, case-sensitive)                           │
│                                                         │
│  Value *                                                │
│  ┌───────────────────────────────────────────────────┐ │
│  │ -----BEGIN RSA PRIVATE KEY-----                    │ │
│  │ MIIEpAIBAAKCAQEA2x5...                            │ │
│  │ ...                                               │ │
│  │ -----END RSA PRIVATE KEY-----                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  [Cancel]  [🟢 Add secret]                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Campos**:
- **Name**: Nombre del secret (ej: SSH_PRIVATE_KEY)
- **Value**: El valor secreto (ej: contenido de tu clave SSH)

---

## 📍 PASO 5: CONFIRMACIÓN

```
┌─────────────────────────────────────────────────────────┐
│  Actions secrets and variables                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ Secret SSH_PRIVATE_KEY created successfully        │
│                                                         │
│  Repository secrets                                     │
│  ─────────────────────────────────────────────────────── │
│                                                         │
│  SSH_PRIVATE_KEY  ✏️  🗑️                              │
│  POSTGRES_USER    ✏️  🗑️                              │
│  DATABASE_URL     ✏️  🗑️                              │
│  ...                                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Resultado**: El secret aparece en la lista con botones para editar (✏️) o eliminar (🗑️)

---

## 📋 LISTA COMPLETA: TODOS LOS 15 SECRETS

Una vez termines, verás algo así:

```
┌─────────────────────────────────────────────────────────┐
│  Repository secrets (15 total)                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ BACKUP_ACCESS_KEY         ✏️  🗑️                   │
│ ✅ BACKUP_SECRET_KEY         ✏️  🗑️                   │
│ ✅ CLOUDFLARE_TOKEN          ✏️  🗑️                   │
│ ✅ DATABASE_URL              ✏️  🗑️                   │
│ ✅ DOCKER_PASSWORD           ✏️  🗑️                   │
│ ✅ DOCKER_USERNAME           ✏️  🗑️                   │
│ ✅ MONITORING_TOKEN          ✏️  🗑️                   │
│ ✅ POSTGRES_DB               ✏️  🗑️                   │
│ ✅ POSTGRES_PASSWORD         ✏️  🗑️                   │
│ ✅ POSTGRES_USER             ✏️  🗑️                   │
│ ✅ REDIS_URL                 ✏️  🗑️                   │
│ ✅ SECRET_KEY                ✏️  🗑️                   │
│ ✅ SERVER_HOST               ✏️  🗑️                   │
│ ✅ SERVER_USERNAME           ✏️  🗑️                   │
│ ✅ SSH_PRIVATE_KEY           ✏️  🗑️                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 WORKFLOW: CÓMO SE VE CUANDO ESTÁ EN USO

### Cuando GitHub Actions usa tus secrets:

```
GitHub Actions Job Logs
═════════════════════════════════════════════════════════

Step 1: Configure SSH
  ✓ mkdir -p ~/.ssh
  ✓ echo "***" > ~/.ssh/id_rsa        ← Secret oculto (**)
  ✓ chmod 600 ~/.ssh/id_rsa

Step 2: Connect to Server
  ✓ ssh -i ~/.ssh/id_rsa ubuntu@prod.example.com
  ✓ Connected!

Step 3: Deploy Application
  ✓ DATABASE_URL configured (***...)
  ✓ REDIS_URL configured (***...)
  ✓ SECRET_KEY configured (***...)
  
✓ Deployment successful!

═════════════════════════════════════════════════════════
```

**Nota**: Los secrets se muestran como `***` en los logs (GitHub los oculta automáticamente)

---

## 🎯 FLUJO COMPLETO (5 minutos)

```
┌─────────────────────────┐
│ 1. Acceder a GitHub UI  │
│ (Settings → Secrets)    │
└────────────┬────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 2. Click "New repository secret"        │
│    (Botón verde)                        │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 3. Ingresar nombre y valor              │
│    (Ej: SSH_PRIVATE_KEY)                │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 4. Click "Add secret"                   │
│    (Confirmar)                          │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 5. Ver confirmación ✅                  │
│    Secret aparece en la lista           │
└────────────┬────────────────────────────┘
             ↓
┌──────────────────────────────────────────────┐
│ 6. Repetir pasos 2-5 para los 15 secrets    │
│    (Total: ~12 minutos)                      │
└────────────┬─────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────┐
│ 7. ¡Listo! 15 secrets configurados ✅       │
│    Pipeline se activa automáticamente        │
│    Deployment a producción comienza          │
└──────────────────────────────────────────────┘
```

---

## 💾 CHECKLIST VISUAL

Conforme ingreses cada secret, marca el que completaste:

```
TIER 1: CREDENTIALS BÁSICAS
─────────────────────────────────────────────────────────
☐ SSH_PRIVATE_KEY       Tiempo: ~2 min
☐ SERVER_HOST           Tiempo: ~1 min
☐ SERVER_USERNAME       Tiempo: ~1 min
☐ SECRET_KEY            Tiempo: ~1 min

TIER 2: DATABASE
─────────────────────────────────────────────────────────
☐ DATABASE_URL          Tiempo: ~1 min
☐ POSTGRES_USER         Tiempo: ~1 min
☐ POSTGRES_PASSWORD     Tiempo: ~1 min
☐ POSTGRES_DB           Tiempo: ~1 min

TIER 3: REDIS & DOCKER
─────────────────────────────────────────────────────────
☐ REDIS_URL             Tiempo: ~1 min
☐ DOCKER_USERNAME       Tiempo: ~1 min
☐ DOCKER_PASSWORD       Tiempo: ~1 min

TIER 4: BACKUPS & OPCIONALES
─────────────────────────────────────────────────────────
☐ BACKUP_ACCESS_KEY     Tiempo: ~1 min
☐ BACKUP_SECRET_KEY     Tiempo: ~1 min
☐ CLOUDFLARE_TOKEN      Tiempo: ~1 min (OPCIONAL)
☐ MONITORING_TOKEN      Tiempo: ~1 min (OPCIONAL)

═════════════════════════════════════════════════════════
✅ TOTAL: 15 secrets | TIEMPO: ~15 minutos
```

---

## 🔍 VER WORKFLOW EN ACCIÓN

Una vez configurados los secrets:

```
1. Ve a GitHub
   ↓
2. Pestaña "Actions"
   ↓
3. Verás el workflow ejecutándose
   ↓
4. Cada job muestra con ✅ o ❌

┌───────────────────────────────────────────┐
│  ci-cd workflow                           │
├───────────────────────────────────────────┤
│                                           │
│  ✅ lint              (3 min)             │
│  ✅ test              (5 min)             │
│  ✅ security-scan     (2 min)             │
│  ✅ build             (4 min)             │
│  ✅ deploy-staging    (2 min)             │
│  ✅ deploy-production (3 min)             │
│                                           │
│  ✅ All checks passed!                   │
│                                           │
└───────────────────────────────────────────┘
```

---

## ⚠️ ERRORES COMUNES (VISUAL)

### Error 1: Secret no encontrado

```
❌ Error in job "deploy":
   Error: Secret 'DATABASE_URL' is not accessible 
   in this workflow
```

**Causa**: Nombre del secret incorrecto  
**Solución**: Verifica que sea exactamente igual

### Error 2: Autenticación fallida

```
❌ Error: Failed to connect
   psql: error: FATAL:
   password authentication failed
```

**Causa**: DATABASE_URL con credenciales incorrectas  
**Solución**: Verifica que PostgreSQL está corriendo y las credenciales son correctas

### Error 3: SSH Key format inválido

```
❌ Error: Permission denied (publickey)
   Invalid key format
```

**Causa**: SSH_PRIVATE_KEY sin headers `-----BEGIN RSA PRIVATE KEY-----`  
**Solución**: Copia la clave completa con headers

---

## 🎓 REFERENCIA: DÓNDE ESTÁ CADA COSA

```
Navegación en GitHub UI:

GitHub UI
  ├─ Tu Repositorio (GRUPO_GAD)
  │   ├─ [Code Tab]
  │   ├─ [Pull Requests]
  │   ├─ [Issues]
  │   ├─ [Actions] ← VER WORKFLOWS AQUÍ
  │   └─ [Settings] ← VER SECRETS AQUÍ
  │       ├─ General
  │       ├─ Access
  │       └─ Security
  │           └─ Secrets and variables
  │               ├─ Actions ← AQUÍ CONFIGURAS SECRETS
  │               ├─ Dependabot
  │               └─ Codespaces
```

---

## 🎉 RESULTADO FINAL

```
Una vez que configures los 15 secrets:

┌─────────────────────────────────────────────────────┐
│ 🎊 ¡PROYECTO 100% COMPLETADO! 🎊                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ✅ TASK 1: Staging Test (100%)                    │
│ ✅ TASK 3: Performance Optimization (100%)        │
│ ✅ LIMPIEZA: Documentation (100%)                 │
│ ✅ TASK 2: GitHub Secrets (100%)                  │
│                                                     │
│ 🚀 CI/CD Pipeline: ACTIVO                         │
│ 🚀 Deployment: AUTOMÁTICO                         │
│ 🚀 Producción: ACTIVO                             │
│                                                     │
│ Global Progress: 100% ✨                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Guía Visual - GitHub Secrets**  
*GRUPO_GAD - Octubre 16, 2025*
