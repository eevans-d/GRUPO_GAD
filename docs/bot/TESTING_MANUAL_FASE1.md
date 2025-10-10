# 🧪 Guía de Testing Manual - Fase 1 MVP

**Fecha:** 10 de Octubre, 2025  
**Fase:** 1 - MVP Botones Interactivos  
**Estado:** ✅ Implementado, listo para pruebas

---

## 🎯 Objetivo

Validar que el menú interactivo con botones funciona correctamente en Telegram.

---

## 📋 Pre-Requisitos

### 1. Bot de Telegram

Si aún no tienes un bot de prueba:

```
1. Abrir Telegram
2. Buscar: @BotFather
3. Enviar: /newbot
4. Nombre: GAD Test Bot (o cualquier nombre)
5. Username: gad_test_bot (debe terminar en _bot)
6. Copiar el TOKEN que te da
```

### 2. Configurar Variables de Entorno

```bash
# En tu archivo .env o .env.production
TELEGRAM_TOKEN=tu_token_aqui
ADMIN_CHAT_ID=tu_chat_id
WHITELIST_IDS=[tu_user_id]
```

**Tip:** Para obtener tu `chat_id`:
1. Envía un mensaje a tu bot
2. Ve a: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
3. Busca `"chat":{"id":123456789}`

### 3. Iniciar el Bot

**Opción A: Local (desarrollo)**
```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD
python3 src/bot/main.py
```

**Opción B: Docker**
```bash
docker-compose up bot -d
docker-compose logs -f bot
```

---

## ✅ Casos de Prueba

### Test 1: Comando /start

**Pasos:**
1. Abrir Telegram
2. Buscar tu bot
3. Enviar: `/start`

**Resultado Esperado:**
```
🤖 Bienvenido a GAD Bot

Sistema de Gestión de Agentes y Tareas.

Selecciona una opción del menú:

[📋 Crear Tarea]
[✅ Finalizar Tarea]
[📊 Mis Tareas]
[🔍 Buscar]
[ℹ️ Ayuda]
```

**Criterio de Éxito:**
- ✅ Mensaje con formato Markdown
- ✅ 5 botones visibles
- ✅ Emojis correctos

---

### Test 2: Botón "Ayuda"

**Pasos:**
1. Click en botón "ℹ️ Ayuda"

**Resultado Esperado:**
```
ℹ️ Ayuda - GAD Bot

Comandos disponibles:
• /start - Menú principal
• /crear - Crear tarea (texto)
• /finalizar - Finalizar tarea (texto)

Botones interactivos:
• 📋 Crear Tarea - Wizard guiado
• ✅ Finalizar - Selector de tareas
• 📊 Mis Tareas - Lista personal

Estado:
✅ Menú principal - Funcional
🚧 Wizard de creación - En desarrollo
🚧 Finalizar con botones - En desarrollo

[🔙 Volver]
```

**Criterio de Éxito:**
- ✅ Texto formateado con Markdown
- ✅ Botón "Volver" visible
- ✅ Sin errores en logs

---

### Test 3: Botón "Volver"

**Pasos:**
1. Desde pantalla de Ayuda
2. Click en "🔙 Volver"

**Resultado Esperado:**
- ✅ Regresa al menú principal
- ✅ Muestra los 5 botones originales

---

### Test 4: Botón "Crear Tarea"

**Pasos:**
1. Click en "📋 Crear Tarea"

**Resultado Esperado:**
```
📝 Crear Nueva Tarea

Paso 1: Selecciona el tipo de tarea:

[🔧 OPERATIVO]
[📄 ADMINISTRATIVO]
[🚨 EMERGENCIA]
[❌ Cancelar]
```

**Criterio de Éxito:**
- ✅ 4 botones visibles
- ✅ Texto claro
- ✅ Botón "Cancelar" presente

---

### Test 5: Seleccionar Tipo de Tarea

**Pasos:**
1. Desde selector de tipos
2. Click en "🔧 OPERATIVO"

**Resultado Esperado:**
```
✅ Tipo Seleccionado: OPERATIVO

🚧 El wizard completo se implementará en la Fase 2.

Por ahora, usa el comando:
/crear <codigo> <titulo> OPERATIVO <id_delegado> <id_asignado1> ...

[🔙 Volver]
```

**Criterio de Éxito:**
- ✅ Muestra tipo seleccionado
- ✅ Indica que es MVP
- ✅ Botón "Volver" funcional

---

### Test 6: Cancelar Wizard

**Pasos:**
1. Click en "📋 Crear Tarea"
2. Click en "❌ Cancelar"

**Resultado Esperado:**
```
❌ Creación Cancelada

Volviendo al menú principal...

[5 botones del menú principal]
```

**Criterio de Éxito:**
- ✅ Mensaje de cancelación
- ✅ Regresa al menú principal
- ✅ State limpiado (verificar en logs)

---

### Test 7: Botón "Finalizar Tarea"

**Pasos:**
1. Click en "✅ Finalizar Tarea"

**Resultado Esperado:**
```
✅ Finalizar Tarea

🚧 Esta función se implementará en la Fase 3.
Por ahora, usa el comando /finalizar <codigo>

[🔙 Volver]
```

**Criterio de Éxito:**
- ✅ Mensaje temporal
- ✅ Indica Fase 3
- ✅ Botón "Volver" funcional

---

### Test 8: Botón "Mis Tareas"

**Pasos:**
1. Click en "📊 Mis Tareas"

**Resultado Esperado:**
```
📊 Mis Tareas

🚧 Lista de tareas en desarrollo.
Próximamente: visualización completa.

[🔙 Volver]
```

**Criterio de Éxito:**
- ✅ Mensaje temporal
- ✅ Botón "Volver" funcional

---

### Test 9: Navegación Múltiple

**Pasos:**
1. `/start` → Menú principal
2. Click "Ayuda" → Ver ayuda
3. Click "Volver" → Menú principal
4. Click "Crear Tarea" → Selector tipos
5. Click "OPERATIVO" → Confirmación
6. Click "Volver" → Menú principal
7. Click "Finalizar" → Mensaje temporal
8. Click "Volver" → Menú principal

**Criterio de Éxito:**
- ✅ Todas las transiciones funcionan
- ✅ Ningún error en logs
- ✅ No hay botones rotos

---

### Test 10: Callback Inmediato

**Pasos:**
1. Click en cualquier botón
2. Observar tiempo de respuesta

**Criterio de Éxito:**
- ✅ Sin "spinner" infinito
- ✅ Respuesta en < 2 segundos
- ✅ Acknowledgment inmediato

---

## 🔍 Verificación de Logs

Durante las pruebas, revisa los logs:

```bash
# Si ejecutas local
# Los logs aparecen en consola y en logs/bot.log

# Si ejecutas con Docker
docker-compose logs -f bot
```

**Buscar:**
- ✅ `Callback procesado: menu:ayuda:general`
- ✅ `user_id=<tu_id>`
- ✅ Sin errores (traceback, exception)

---

## 📊 Checklist de Testing

### Funcionalidad Básica
- [ ] /start muestra menú con botones
- [ ] Los 5 botones son clicables
- [ ] Emojis se muestran correctamente
- [ ] Texto usa formato Markdown

### Navegación
- [ ] "Ayuda" abre pantalla de ayuda
- [ ] "Volver" regresa al menú principal
- [ ] "Crear Tarea" abre selector de tipos
- [ ] "Finalizar Tarea" muestra mensaje temporal
- [ ] "Mis Tareas" muestra mensaje temporal

### Wizard de Creación
- [ ] Selector de tipos muestra 4 botones
- [ ] Click en tipo guarda en state
- [ ] Confirmación muestra tipo seleccionado
- [ ] "Cancelar" limpia state y vuelve al menú

### Performance
- [ ] Callbacks responden en < 2 segundos
- [ ] Sin spinners infinitos
- [ ] Sin errores en logs

### State Management
- [ ] State se guarda en context.user_data
- [ ] State se limpia al cancelar
- [ ] Logs muestran callbacks procesados

---

## 🐛 Problemas Conocidos (Esperados)

### 1. Wizard Incompleto
- **Esperado:** Solo muestra selector de tipo
- **Motivo:** Fase 2 no implementada aún
- **Fix:** Fase 2 (siguiente)

### 2. Lista de Tareas Vacía
- **Esperado:** Mensaje temporal
- **Motivo:** Fase 3 no implementada aún
- **Fix:** Fase 3

### 3. Búsqueda No Funcional
- **Esperado:** No implementado
- **Motivo:** Feature futura
- **Fix:** Post-Fase 3

---

## 🚨 Reportar Issues

Si encuentras un error **inesperado**:

1. **Captura el error:**
   ```bash
   docker-compose logs bot > error.log
   ```

2. **Reporta con:**
   - Pasos para reproducir
   - Resultado esperado vs real
   - Logs relevantes
   - Screenshots de Telegram

---

## ✅ Criterio de Aprobación

**Fase 1 MVP se considera exitosa si:**

- ✅ 9/10 tests pasan sin errores
- ✅ Navegación básica funciona
- ✅ Callbacks responden correctamente
- ✅ Sin errores críticos en logs
- ✅ State management funciona

---

## 🎉 Siguiente Paso

Una vez aprobada la Fase 1:

**Implementar Fase 2:**
- Wizard multi-step completo
- Input de texto entre steps
- Validaciones por paso
- Resumen antes de confirmar

**Estimado:** 5 horas

---

**Última actualización:** 10 de Octubre, 2025  
**Autor:** GitHub Copilot  
**Ref:** docs/TELEGRAM_INTERACTIVE_BUTTONS_PLAN.md
