# 🔐 GUÍA COMPLETA: Configurar Secrets en GitHub UI

**Última actualización**: Octubre 16, 2025  
**Status**: Production-ready  
**Tiempo estimado**: 5-10 minutos  
**Dificultad**: ⭐ Muy fácil

---

## 📋 RESUMEN EJECUTIVO

Esta guía te ayudará a configurar los **15 secrets** necesarios para que el **CI/CD pipeline de GRUPO_GAD** funcione correctamente. Una vez configurados, el pipeline se activará automáticamente y desplegará tu aplicación a producción.

### Prerequisitos
- ✅ Acceso a la cuenta de GitHub del repositorio
- ✅ Rol: Owner o Admin del repositorio
- ✅ Los valores de los 15 secrets (ver tabla más abajo)

---

## 🚀 PASO A PASO: ACCEDER A GITHUB SECRETS

### PASO 1: Ir al repositorio en GitHub

1. Abre tu navegador y ve a:
   ```
   https://github.com/eevans-d/GRUPO_GAD
   ```

2. Asegúrate de estar logueado en tu cuenta de GitHub

### PASO 2: Acceder a Settings

1. En la página del repositorio, busca la pestaña **Settings** (en la barra superior)
2. Haz click en **Settings**

   ![Settings ubicación: esquina superior derecha del repositorio]

### PASO 3: Acceder a Secrets and Variables

1. En el menú izquierdo, busca **Secrets and variables**
2. Haz click en **Actions**

   ![Menú izquierdo → Security → Secrets and variables → Actions]

### PASO 4: Crear nuevo Secret

1. Haz click en el botón verde **New repository secret**

   ![Botón verde "New repository secret" en la esquina superior derecha]

---

## 📝 LOS 15 SECRETS A CONFIGURAR

Aquí están los **15 secrets** que necesitas crear. Sigue la tabla y configura cada uno:

| # | Nombre del Secret | Valor/Descripción | Tipo | Requerido |
|---|-------------------|-------------------|------|-----------|
| 1 | `SSH_PRIVATE_KEY` | Tu clave privada SSH para acceder al servidor | Private Key (PEM format) | ✅ |
| 2 | `SERVER_HOST` | IP o dominio del servidor de producción | IP/Domain (ej: 192.168.1.100 o prod.example.com) | ✅ |
| 3 | `SERVER_USERNAME` | Usuario SSH para acceder al servidor | Username (ej: ubuntu, ec2-user) | ✅ |
| 4 | `DATABASE_URL` | URL de conexión a PostgreSQL en producción | PostgreSQL URL (ej: postgresql://user:pass@host:5432/dbname) | ✅ |
| 5 | `REDIS_URL` | URL de conexión a Redis en producción | Redis URL (ej: redis://host:6379) | ✅ |
| 6 | `SECRET_KEY` | Clave secreta para JWT y encriptación | String aleatorio largo (32+ caracteres) | ✅ |
| 7 | `POSTGRES_USER` | Usuario de PostgreSQL | Username (ej: grupogad_user) | ✅ |
| 8 | `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Contraseña fuerte (16+ caracteres) | ✅ |
| 9 | `POSTGRES_DB` | Nombre de base de datos | Database name (ej: grupogad_prod) | ✅ |
| 10 | `DOCKER_USERNAME` | Usuario de Docker Registry (DockerHub, ECR, etc.) | Username | ✅ |
| 11 | `DOCKER_PASSWORD` | Token/contraseña de Docker Registry | Access Token o Password | ✅ |
| 12 | `CLOUDFLARE_TOKEN` | Token de Cloudflare para DNS/certificados | API Token | ⏳ |
| 13 | `MONITORING_TOKEN` | Token para servicio de monitoreo (opcional) | API Token | ⏳ |
| 14 | `BACKUP_ACCESS_KEY` | Access key para almacenamiento de backups | AWS Access Key ID o equivalente | ✅ |
| 15 | `BACKUP_SECRET_KEY` | Secret key para almacenamiento de backups | AWS Secret Access Key o equivalente | ✅ |

**Leyenda**:
- ✅ = Requerido para CI/CD
- ⏳ = Opcional (solo si usas estos servicios)

---

## 🔧 CÓMO OBTENER CADA SECRET

### 1️⃣ SSH_PRIVATE_KEY

**¿Dónde obtenerla?**
- Si ya tienes clave SSH configurada:
  ```bash
  cat ~/.ssh/id_rsa
  ```
- Si no tienes, genera una nueva:
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
  cat ~/.ssh/id_rsa
  ```

**Cómo configurarla en GitHub**:
1. Abre la clave completa con `cat ~/.ssh/id_rsa`
2. Copia TODO el contenido (incluye `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----`)
3. En GitHub: Pega el contenido en el campo de valor

### 2️⃣ SERVER_HOST

**¿Dónde obtenerla?**
- IP del servidor: `ifconfig` o `ip addr` en el servidor
- Dominio: Tu dominio registrado (ej: api.grupogad.com)

**Ejemplo**:
```
192.168.1.100
o
prod-api.example.com
```

### 3️⃣ SERVER_USERNAME

**¿Dónde obtenerla?**
- Usuario del sistema en tu servidor
- Típicamente: `ubuntu`, `ec2-user`, `root`, `admin`

**Cómo verificar**:
```bash
whoami
```

### 4️⃣ DATABASE_URL

**¿Dónde obtenerla?**
- PostgreSQL en tu servidor de producción

**Formato**:
```
postgresql://[usuario]:[contraseña]@[host]:[puerto]/[base_de_datos]
```

**Ejemplos**:
```
postgresql://grupogad:mypassword123@db.prod.com:5432/grupogad_prod
postgresql://admin:securepass@192.168.1.50:5432/app_db
```

### 5️⃣ REDIS_URL

**¿Dónde obtenerla?**
- Redis en tu servidor de producción

**Formato**:
```
redis://[host]:[puerto]
```

**Ejemplos**:
```
redis://cache.prod.com:6379
redis://192.168.1.60:6379
redis://:password@redis.prod.com:6379
```

### 6️⃣ SECRET_KEY

**¿Dónde obtenerla?**
- Genera una clave aleatoria fuerte

**Opción 1: Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Opción 2: OpenSSL**
```bash
openssl rand -base64 32
```

**Opción 3: Online** (si confías):
- Copia de un generador online de tokens seguros

**Ejemplo**:
```
4x7p-Q2z9mK_bL8vR5tJ3nXc6yH1wF0sG8dE9aB
```

### 7️⃣ POSTGRES_USER

**¿Dónde obtenerla?**
- Usuario que vas a crear en PostgreSQL para la aplicación

**Ejemplo**:
```
grupogad_app_user
```

### 8️⃣ POSTGRES_PASSWORD

**¿Dónde obtenerla?**
- Contraseña fuerte que vas a usar para PostgreSQL

**Genera una contraseña fuerte**:
```bash
openssl rand -base64 20
```

**Ejemplo**:
```
K7mX9zP3vL6bQ2nR8tJ1
```

### 9️⃣ POSTGRES_DB

**¿Dónde obtenerla?**
- Nombre de la base de datos a crear

**Ejemplo**:
```
grupogad_production
```

### 🔟 DOCKER_USERNAME

**¿Dónde obtenerla?**

**Para DockerHub**:
1. Ve a https://hub.docker.com
2. Login en tu cuenta
3. Tu username es lo que ves en la esquina superior derecha

**Para AWS ECR**:
- Tu usuario de AWS o token específico del ECR

**Para GitLab/GitHub Container Registry**:
- Tu nombre de usuario o token de acceso

### 1️⃣1️⃣ DOCKER_PASSWORD

**¿Dónde obtenerla?**

**Para DockerHub**:
1. Ve a https://hub.docker.com/settings/security
2. Crea un nuevo **Access Token**
3. Copia el token completo

**Para AWS ECR**:
```bash
# Genera un token temporal
aws ecr get-authorization-token --region us-east-1
```

**Para GitHub Container Registry**:
1. Ve a https://github.com/settings/tokens
2. Crea un nuevo token (PAT) con permisos `write:packages`

### 1️⃣2️⃣ CLOUDFLARE_TOKEN (Opcional)

**¿Dónde obtenerla?**
1. Ve a https://dash.cloudflare.com/profile/api-tokens
2. Crea un nuevo API Token
3. Dale permisos para DNS y SSL/TLS

### 1️⃣3️⃣ MONITORING_TOKEN (Opcional)

**¿Dónde obtenerla?**
- Depende del servicio de monitoreo que uses (DataDog, New Relic, etc.)
- Normalmente en: Settings → API Tokens

### 1️⃣4️⃣ BACKUP_ACCESS_KEY

**¿Dónde obtenerla?**

**Para AWS S3**:
1. Ve a https://console.aws.amazon.com/iam
2. Crea un nuevo usuario o usa uno existente
3. Crea una clave de acceso (Access Key)
4. Copia el `Access Key ID`

**Para Backblaze B2**:
1. Ve a https://secure.backblaze.com/app_keys.htm
2. Crea una nueva clave de aplicación
3. Copia el Application Key ID

### 1️⃣5️⃣ BACKUP_SECRET_KEY

**¿Dónde obtenerla?**

**Para AWS S3**:
1. Mismo lugar que Access Key (IAM)
2. Copia el `Secret Access Key`

**Para Backblaze B2**:
1. Mismo lugar que Application Key ID
2. Copia el `Application Key`

---

## ✅ PROCEDIMIENTO: CREAR CADA SECRET EN GITHUB UI

### Repetir estos pasos para CADA uno de los 15 secrets:

#### **PASO A**: Click en "New repository secret"
![Botón "New repository secret"]

#### **PASO B**: Ingresa el nombre del secret
- En el campo **Name**, escribe exactamente el nombre (ej: `SSH_PRIVATE_KEY`)
- ⚠️ Respeta mayúsculas/minúsculas (es IMPORTANTE)

#### **PASO C**: Ingresa el valor del secret
- En el campo **Value**, pega el valor secreto
- ⚠️ Los valores son confidenciales, no los compartas

#### **PASO D**: Click en "Add secret"
- Espera a que se guarde (verás un ✅ verde)

#### **PASO E**: Verifica que aparezca en la lista

---

## 🎯 CHECKLIST: VERIFICAR SECRETS CONFIGURADOS

Una vez hayas ingresado todos, verifica que aparezcan en la lista:

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
✅ CLOUDFLARE_TOKEN (opcional)
✅ MONITORING_TOKEN (opcional)
✅ BACKUP_ACCESS_KEY
✅ BACKUP_SECRET_KEY
```

**Total**: 13 requeridos + 2 opcionales = 15 secrets

---

## 🚀 DESPUÉS DE CONFIGURAR LOS SECRETS

### Opción 1: CI/CD Se Activa Automáticamente
- El pipeline se ejecutará automáticamente en el próximo push
- Verifica en: **Actions** → Última run

### Opción 2: Ejecutar Pipeline Manualmente
1. Ve a la pestaña **Actions**
2. Selecciona el workflow **ci-cd** o el que uses
3. Haz click en **Run workflow**
4. Selecciona **master** como rama
5. Haz click en **Run workflow**

### Monitorear el Deployment
1. En **Actions**, verás la ejecución del workflow
2. Haz click para ver detalles
3. Espera a que todas las jobs pasen (✅ verde)
4. Verifica en tu servidor de producción

---

## 🐛 SOLUCIONAR PROBLEMAS

### ❌ "Secret is not accessible in this workflow"

**Causa**: El secret no está bien nombrado o tiene espacios

**Solución**:
- Verifica que el nombre sea exactamente igual al usado en el workflow
- Sin espacios al principio/final
- Respeta mayúsculas/minúsculas

### ❌ "Authentication failed"

**Causa**: El valor del secret es incorrecto

**Solución**:
1. Edita el secret (click en el ✏️)
2. Verifica el valor
3. Copia nuevamente desde la fuente original
4. Guarda

### ❌ "Connection refused to database"

**Causa**: DATABASE_URL es inaccesible

**Solución**:
- Verifica que la base de datos está corriendo
- Verifica que la URL es correcta
- Prueba la conexión manualmente desde tu servidor

### ❌ "Docker authentication failed"

**Causa**: DOCKER_PASSWORD o DOCKER_USERNAME inválidos

**Solución**:
1. Verifica las credenciales en Docker Registry
2. Para DockerHub, usa un Access Token (no la contraseña)
3. Asegúrate de que el token no ha expirado

### ❌ "Key invalid format"

**Causa**: SSH_PRIVATE_KEY tiene formato incorrecto

**Solución**:
1. Copia la clave completa con headers:
   ```
   -----BEGIN RSA PRIVATE KEY-----
   [contenido]
   -----END RSA PRIVATE KEY-----
   ```
2. Sin líneas en blanco extra al principio/final

---

## 📸 SCREENSHOTS (Descritos)

### Screenshot 1: Ubicación de Settings
```
Repository → Settings (esquina superior derecha)
```

### Screenshot 2: Secrets and variables menu
```
Settings → Security → Secrets and variables → Actions
```

### Screenshot 3: New repository secret button
```
Botón verde "New repository secret" (esquina superior derecha)
```

### Screenshot 4: Formulario para crear secret
```
Name: [campo de texto]
Value: [campo de texto grande]
[Botón] Add secret
```

### Screenshot 5: Lista de secrets configurados
```
Lista mostrando todos los secrets creados
Cada uno con un ✅ y botón de edición (✏️)
```

---

## ⏱️ TIEMPO ESTIMADO

| Tarea | Tiempo |
|-------|--------|
| Obtener SSH_PRIVATE_KEY | 2 min |
| Obtener DATABASE_URL | 2 min |
| Obtener REDIS_URL | 2 min |
| Obtener SECRET_KEY | 1 min |
| Obtener credenciales Docker | 2 min |
| Obtener credenciales AWS/Backblaze | 2 min |
| Ingresar 15 secrets en GitHub UI | 5-7 min |
| Verificar secrets en lista | 1 min |
| **TOTAL** | **~15-20 minutos** |

---

## 💡 TIPS Y MEJORES PRÁCTICAS

### ✅ HACER
- ✅ Usar contraseñas/tokens fuertes y únicos
- ✅ Regenerar tokens después de usarlos (para seguridad)
- ✅ Guardar los valores en un gestor de contraseñas (1Password, LastPass, etc.)
- ✅ Rotar secrets periódicamente
- ✅ Usar diferentes usuarios para desarrollo y producción

### ❌ NO HACER
- ❌ Compartir secrets en mensajes, emails o documentos
- ❌ Hardcodear secrets en el código
- ❌ Usar credenciales débiles
- ❌ Reutilizar el mismo secret para múltiples servicios
- ❌ Guardar secrets en archivos de configuración

---

## 🔒 SEGURIDAD

### GitHub oculta automáticamente los secrets
- Los secrets no aparecen en logs públicos
- GitHub redacta los valores en los outputs
- Solo el repositorio/workflows pueden accederlos

### Auditoría de acceso
- Ve a: **Settings** → **Audit log**
- Verifica quién accedió a los secrets

### Rotación de secrets
1. Si un secret se compromete, créalo nuevo en GitHub
2. Actualiza el valor en los sistemas externos (AWS, Docker, etc.)
3. Elimina el antiguo

---

## ✨ SIGUIENTE PASO: VALIDAR DEPLOYMENT

Una vez configurados los 15 secrets:

1. **Push a master** (o espera a que el workflow se ejecute)
2. **Ve a Actions** en GitHub
3. **Espera** a que el workflow se complete (✅ todas las jobs verdes)
4. **Verifica** en tu servidor de producción que la aplicación esté corriendo
5. **Prueba** accediendo a los endpoints:
   ```bash
   curl https://tu-dominio.com/health
   curl https://tu-dominio.com/metrics
   ```

---

## 📞 SUPPORT

Si encuentras problemas:

1. Revisa el archivo `DEPLOYMENT_CHECKLIST.md`
2. Consulta los logs en GitHub Actions (Actions → workflow → detalles)
3. Verifica que los valores de los secrets sean correctos
4. Si es un error de conectividad, verifica firewall/security groups en AWS

---

## 🎉 CONCLUSIÓN

Una vez completada esta guía:

✅ **Todos los 15 secrets configurados**  
✅ **CI/CD pipeline activado**  
✅ **Deployment automático a producción**  
✅ **Proyecto 100% completado**

---

**Creado**: Octubre 16, 2025  
**Última actualización**: Octubre 16, 2025  
**Versión**: 1.0  

*Guía completa para configurar GitHub Secrets - GRUPO_GAD Proyecto*
