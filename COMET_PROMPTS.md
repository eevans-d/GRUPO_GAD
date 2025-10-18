# 🤖 PROMPTS PARA COMET (Asistente del Navegador)

**Fecha**: 18 Octubre 2025  
**Objetivo**: Configurar secrets automáticamente con Comet  
**Repositorio**: eevans-d/GRUPO_GAD  

---

## 📋 INSTRUCCIONES GENERALES

1. **Abre tu navegador** (Chrome, Edge, etc.)
2. **Ve a GitHub** y asegúrate de estar logueado
3. **Abre Comet** (extensión del navegador)
4. **Copia y pega** el prompt completo
5. **Comet ejecutará** las acciones automáticamente

---

## 🔐 PROMPT 1: CONFIGURAR JWT_SECRET_KEY EN GITHUB ACTIONS

### 📍 Paso Previo
Primero, ve manualmente a esta URL:
```
https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions
```

### 🤖 Prompt para Comet

```
Necesito que configures un secret en GitHub Actions para mi repositorio eevans-d/GRUPO_GAD.

TAREA:
1. Navega a la página de secrets si no estás ahí: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

2. Haz click en el botón "New repository secret"

3. En el campo "Name", escribe exactamente:
   JWT_SECRET_KEY

4. En el campo "Secret", escribe exactamente (copialo completo sin espacios):
   KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU

5. Haz click en el botón "Add secret"

6. Confirma que el secret "JWT_SECRET_KEY" aparece en la lista de secrets

VALIDACIÓN:
- Verifica que en la lista aparezca: "JWT_SECRET_KEY" con fecha de hoy
- No debe mostrar el valor (es correcto que esté oculto)
- Debe decir "Updated X seconds ago"

¿Puedes realizar estos pasos?
```

---

## 🔐 PROMPT 2: VERIFICAR TODOS LOS SECRETS DE GITHUB

Este prompt le pedirá a Comet que verifique cuáles secrets ya tienes configurados:

### 🤖 Prompt para Comet

```
Necesito que verifiques los secrets configurados en mi repositorio de GitHub.

TAREA:
1. Ve a: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

2. Lista TODOS los secrets que aparecen en la página, indicando:
   - Nombre del secret
   - Fecha de última actualización
   
3. Compara con esta lista de secrets requeridos:
   ✅ DEBE EXISTIR:
   - SSH_PRIVATE_KEY
   - SECRET_KEY
   - JWT_SECRET_KEY (el que acabamos de agregar)
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_DB
   - DATABASE_URL
   - REDIS_URL
   - DOCKER_USERNAME
   - DOCKER_PASSWORD
   - BACKUP_ACCESS_KEY
   - BACKUP_SECRET_KEY
   - SERVER_HOST
   - SERVER_USERNAME
   
4. Indica cuáles secrets FALTAN de la lista

5. Si encuentras secrets que NO están en la lista, indícamelos también

¿Puedes hacer esta verificación?
```

---

## 🔐 PROMPT 3: AGREGAR TODOS LOS SECRETS RESTANTES (AVANZADO)

⚠️ **SOLO USA ESTE PROMPT CUANDO TENGAS TODOS LOS VALORES**

Este es un prompt mega-completo que agrega todos los secrets de una vez:

### 🤖 Prompt para Comet

```
Necesito que agregues múltiples secrets en GitHub Actions para mi repositorio eevans-d/GRUPO_GAD.

CONTEXTO:
- Repositorio: https://github.com/eevans-d/GRUPO_GAD
- Página de secrets: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

TAREA:
Ve a la página de secrets y agrega los siguientes secrets UNO POR UNO:

1. SECRET_KEY
   Valor: 1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d

2. JWT_SECRET_KEY
   Valor: KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU

3. POSTGRES_USER
   Valor: gcp_user

4. POSTGRES_PASSWORD
   Valor: E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=

5. POSTGRES_DB
   Valor: gcp_db

PROCESO PARA CADA SECRET:
1. Click en "New repository secret"
2. Campo "Name": [nombre del secret]
3. Campo "Secret": [valor del secret]
4. Click "Add secret"
5. Esperar confirmación
6. Continuar con el siguiente

VALIDACIÓN FINAL:
- Confirma que los 5 secrets aparecen en la lista
- Indica si alguno falló

⚠️ IMPORTANTE: No agregues SSH_PRIVATE_KEY todavía (es muy largo y requiere formato especial)

¿Puedes realizar esta tarea?
```

---

## 📝 PROMPT 4: AGREGAR SSH_PRIVATE_KEY (ESPECIAL)

Este secret es especial porque es multi-línea:

### 🤖 Prompt para Comet

```
Necesito agregar el secret SSH_PRIVATE_KEY que es un texto multi-línea.

TAREA:
1. Ve a: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

2. Click en "New repository secret"

3. En "Name" escribe: SSH_PRIVATE_KEY

4. En "Secret", pega exactamente este texto (incluyendo las líneas BEGIN y END):

-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACAbky9NQTr6M/mkb/UdXf/fOHLuvERYxKtR6VeMMG6XQQAAAJDvLHIb7yxy
GwAAAAtzc2gtZWQyNTUxOQAAACAbky9NQTr6M/mkb/UdXf/fOHLuvERYxKtR6VeMMG6XQQ
AAAEBM3dbGYyRTpcBfo7H7/rlYvslppucBVNTqghtQK93PmRuTL01BOvoz+aRv9R1d/984
cu68RFjEq1HpV4wwbpdBAAAADGVldmFuQGVldmFucwE=
-----END OPENSSH PRIVATE KEY-----

5. Click "Add secret"

6. Verifica que SSH_PRIVATE_KEY aparece en la lista

IMPORTANTE:
- NO modifiques el formato del texto
- Debe incluir TODAS las líneas (BEGIN, contenido, END)
- No agregues espacios adicionales

¿Puedes hacerlo?
```

---

## 🎯 ESTRATEGIA RECOMENDADA

### Orden de Ejecución:

```
┌─────────────────────────────────────────┐
│ FASE 1: UN SECRET A LA VEZ (SEGURO)    │
└─────────────────────────────────────────┘
1. Usa PROMPT 1 → Agregar JWT_SECRET_KEY
2. Usa PROMPT 2 → Verificar qué hay
3. Si falta SECRET_KEY, crea prompt individual
4. Si falta POSTGRES_*, crea prompts individuales

┌─────────────────────────────────────────┐
│ FASE 2: BATCH (RÁPIDO)                  │
└─────────────────────────────────────────┘
5. Usa PROMPT 3 → Agregar 5 secrets juntos
6. Usa PROMPT 4 → Agregar SSH_PRIVATE_KEY

┌─────────────────────────────────────────┐
│ FASE 3: VALIDACIÓN                      │
└─────────────────────────────────────────┘
7. Usa PROMPT 2 → Verificar todos
```

---

## 💡 TIPS PARA USAR COMET

### ✅ Hacer:
- ✅ Estar logueado en GitHub antes de iniciar
- ✅ Copiar el prompt COMPLETO (no editar)
- ✅ Verificar manualmente después
- ✅ Usar un prompt a la vez
- ✅ Esperar confirmación entre cada uno

### ❌ No Hacer:
- ❌ Modificar los valores en el prompt
- ❌ Ejecutar múltiples prompts simultáneamente
- ❌ Confiar ciegamente (siempre verifica)
- ❌ Usar valores de ejemplo (usa tus valores reales)

---

## 🔍 VALIDACIÓN MANUAL

Después de que Comet termine, verifica manualmente:

```bash
# Ve a: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

# Deberías ver:
✅ SSH_PRIVATE_KEY          Updated X minutes ago
✅ SECRET_KEY               Updated X minutes ago
✅ JWT_SECRET_KEY           Updated X minutes ago
✅ POSTGRES_USER            Updated X minutes ago
✅ POSTGRES_PASSWORD        Updated X minutes ago
✅ POSTGRES_DB              Updated X minutes ago
✅ DATABASE_URL             Updated X minutes ago (si ya lo tenías)
✅ REDIS_URL                Updated X minutes ago (si ya lo tenías)
```

---

## 🚨 SI COMET NO PUEDE HACERLO

Si Comet no puede ejecutar algún paso, aquí está la **alternativa manual simplificada**:

### Proceso Manual Rápido (5 minutos):

1. **Abre**: https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions

2. **Para cada secret**:
   ```
   Click "New repository secret"
   → Name: [nombre]
   → Secret: [valor de MY_DEPLOYMENT_SECRETS.md]
   → Click "Add secret"
   ```

3. **Lista de secrets a agregar**:
   ```
   JWT_SECRET_KEY = KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU
   SECRET_KEY = 1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d
   POSTGRES_USER = gcp_user
   POSTGRES_PASSWORD = E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=
   POSTGRES_DB = gcp_db
   ```

4. **SSH_PRIVATE_KEY** (copiar completo de MY_DEPLOYMENT_SECRETS.md)

---

## ⚠️ FLY.IO - NO PUEDE HACERLO COMET

❌ **Comet NO puede configurar secrets en Fly.io** porque requiere CLI (línea de comandos).

### Para Fly.io DEBES usar terminal:

```bash
# Opción 1: Manual (recomendado)
flyctl secrets set JWT_SECRET_KEY=KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU --app grupo-gad
flyctl secrets set SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d --app grupo-gad

# Opción 2: Script automatizado (más fácil)
export JWT_SECRET_KEY=KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU
export SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d
export POSTGRES_USER=gcp_user
export POSTGRES_PASSWORD=E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=
export POSTGRES_DB=gcp_db

./scripts/deploy_flyio.sh --full
```

---

## 📊 RESUMEN DE CAPACIDADES

| Plataforma | Comet Puede | Método Alternativo |
|------------|-------------|-------------------|
| **GitHub Actions** | ✅ SÍ | Manual en UI |
| **Fly.io** | ❌ NO | Terminal (flyctl) |
| **Railway** | ❌ NO | Manual en UI |
| **Heroku** | ❌ NO | Terminal (heroku config) |
| **AWS** | ❌ NO | AWS Console |
| **GCP** | ❌ NO | GCP Console |

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### 1. GitHub Actions (5 min con Comet)
```
→ Usa PROMPT 1 para JWT_SECRET_KEY
→ Usa PROMPT 2 para verificar
→ Usa PROMPT 3 para batch (si Comet lo soporta)
→ Usa PROMPT 4 para SSH_PRIVATE_KEY
```

### 2. Fly.io (2 min en terminal)
```bash
# Copia y pega en terminal:
export JWT_SECRET_KEY=KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU
./scripts/deploy_flyio.sh --full
```

---

**Última actualización**: 18 Octubre 2025  
**Archivo de referencia**: MY_DEPLOYMENT_SECRETS.md  
**Siguiente acción**: Copiar PROMPT 1 a Comet en GitHub
