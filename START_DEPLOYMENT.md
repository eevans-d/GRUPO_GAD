# 🚀 DESPLIEGUE - Instrucciones Paso a Paso

**Fecha**: 20 Octubre 2025  
**App**: grupo-gad  
**Estado**: ✅ flyctl instalado, listo para login y deploy

---

## ✅ COMPLETADO

- [x] flyctl instalado (v0.3.195)
- [x] Script de despliegue creado (DEPLOY_NOW.sh)
- [x] Dockerfile verificado (libpq-dev + libpq5 presentes)
- [x] fly.toml verificado (app: grupo-gad)

---

## 📋 PRÓXIMOS PASOS (REQUIEREN TU ACCIÓN)

### PASO 1: Autenticación en Fly.io (2 minutos)

**Opción A - Automático con el script:**
```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD
./DEPLOY_NOW.sh
# El script te pedirá login cuando sea necesario
```

**Opción B - Manual:**
```bash
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl auth login
```

**¿Qué pasará?**
1. Se abrirá tu navegador
2. Te pedirá que te autentiques en fly.io
3. Una vez autenticado, volverás a la terminal
4. flyctl guardará el token en `~/.flyrc`

---

### PASO 2: Desplegar la Aplicación (5-10 minutos)

**Una vez autenticado, ejecuta:**

```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD
./DEPLOY_NOW.sh
```

**El script hará:**
1. ✅ Verificar flyctl
2. ✅ Verificar autenticación
3. ✅ Verificar fly.toml y Dockerfile
4. ✅ Mostrar estado actual de la app
5. ❓ Preguntarte si quieres desplegar
6. 🚀 Ejecutar: `flyctl deploy --app grupo-gad --no-cache`

**Timeline esperado:**
```
0:00 - Inicio build
0:30 - Compilando Python packages (con libpq-dev ✅)
1:00 - Build Docker completado
1:30 - Push image a registry
2:00 - Release machine (alembic upgrade head)
2:30 - Production machine startup
3:00 - Health checks
3:30 - ✅ DEPLOYMENT COMPLETE
```

---

### PASO 3: Verificar Despliegue (1 minuto)

```bash
# Health check
curl https://grupo-gad.fly.dev/health

# Esperado:
# {"status": "ok", "timestamp": "...", "uptime": 123.45}

# Ver logs
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl logs --app grupo-gad

# Ver status
flyctl status --app grupo-gad
```

---

## ⚠️ SI ALGO FALLA

### Error: "DATABASE_URL not set"

**Causa**: PostgreSQL no creada  
**Solución**:
```bash
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl postgres create --name grupo-gad-db --region mia
flyctl postgres attach grupo-gad-db --app grupo-gad
flyctl deploy --app grupo-gad
```

### Error: "Health check failures"

**Causa**: Secrets faltantes  
**Solución**:
```bash
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl secrets set \
  SECRET_KEY="1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d" \
  JWT_SECRET_KEY="KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU" \
  --app grupo-gad
```

### Error: Build sigue fallando

**Ver logs detallados**:
```bash
export PATH="/home/eevan/.fly/bin:$PATH"
flyctl logs --app grupo-gad
```

**Consultar**: `DEEP_DEPLOYMENT_ANALYSIS.md` (sección Troubleshooting)

---

## 🎯 COMANDO RÁPIDO (Todo en Uno)

Si ya estás autenticado y solo quieres desplegar:

```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD && \
export PATH="/home/eevan/.fly/bin:$PATH" && \
flyctl deploy --app grupo-gad --no-cache
```

---

## 📊 ESTADO ACTUAL

```
✅ flyctl: v0.3.195 instalado
✅ Script: DEPLOY_NOW.sh creado
✅ Dockerfile: FIXED (libpq-dev + libpq5)
✅ fly.toml: Válido (app: grupo-gad)
⏳ Login: PENDIENTE (requiere tu acción)
⏳ Deploy: PENDIENTE (después de login)
```

---

## 🚀 EMPEZAR AHORA

**EJECUTA ESTO:**

```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD
./DEPLOY_NOW.sh
```

El script te guiará paso a paso. ¡Es interactivo y fácil de seguir!

---

## 📞 REFERENCIAS

- **Script de Deploy**: `DEPLOY_NOW.sh` (nuevo, este archivo)
- **Análisis Completo**: `DEEP_DEPLOYMENT_ANALYSIS.md`
- **Acciones Inmediatas**: `IMMEDIATE_ACTION.md`
- **Diagramas Visuales**: `DEPLOYMENT_DIAGRAMS.md`

---

**¡Listo para desplegar! 🎉**

