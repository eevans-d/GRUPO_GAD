# ✅ Checklist de Validación Completo - Bot GRUPO_GAD

## 📋 Información General

**Fecha de creación:** 11 de octubre de 2025  
**Autor:** Sistema de Documentación Automática  
**Versión del Bot:** 1.0.0  
**Propósito:** Checklist exhaustivo para testing manual de todas las funcionalidades implementadas.

---

## 🎯 Instrucciones de Uso

### Cómo usar este checklist:

1. **Preparación:**
   - Bot debe estar corriendo (`python src/bot/main.py`)
   - API debe estar activa (`http://localhost:8000/health` retorna 200)
   - Tener token configurado en `.env`

2. **Ejecución:**
   - Marcar cada ítem con ✅ cuando pase
   - Marcar con ❌ si falla
   - Anotar bugs encontrados en la sección final

3. **Severidad de Errores:**
   - 🔴 **Crítico** - Bloqueante, impide uso básico
   - 🟡 **Medio** - Funcionalidad afectada pero no bloqueante
   - 🟢 **Bajo** - Cosmético o edge case

---

## 📱 FASE 0: Configuración Inicial

### Pre-requisitos

- [ ] **ENV-01:** Archivo `.env` existe en directorio raíz
- [ ] **ENV-02:** `TELEGRAM_TOKEN` configurado correctamente
- [ ] **ENV-03:** `ADMIN_CHAT_ID` configurado
- [ ] **ENV-04:** `WHITELIST_IDS` contiene tu Telegram ID
- [ ] **ENV-05:** `DATABASE_URL` o `POSTGRES_*` configurados
- [ ] **ENV-06:** `API_V1_STR` apunta a `/api/v1`

### Inicio del Bot

- [ ] **START-01:** Comando `python src/bot/main.py` ejecuta sin errores
- [ ] **START-02:** Log muestra "Bot iniciado y escuchando..."
- [ ] **START-03:** No hay errores de importación en logs
- [ ] **START-04:** Bot responde en Telegram

---

## 🏠 FASE 1: Menú Principal (MVP con Botones)

### Comando /start

- [ ] **F1-START-01:** `/start` muestra mensaje de bienvenida
- [ ] **F1-START-02:** Mensaje incluye emoji 🤖
- [ ] **F1-START-03:** Mensaje usa formato Markdown (texto en negrita)
- [ ] **F1-START-04:** Aparecen 5 botones en el menú

**Resultado esperado:**
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

### Botones del Menú Principal

- [ ] **F1-BTN-01:** Botón "📋 Crear Tarea" visible y clickeable
- [ ] **F1-BTN-02:** Botón "✅ Finalizar Tarea" visible y clickeable
- [ ] **F1-BTN-03:** Botón "📊 Mis Tareas" visible y clickeable
- [ ] **F1-BTN-04:** Botón "🔍 Buscar" visible y clickeable
- [ ] **F1-BTN-05:** Botón "ℹ️ Ayuda" visible y clickeable

### Navegación: Ayuda

- [ ] **F1-HELP-01:** Click en "ℹ️ Ayuda" muestra comandos disponibles
- [ ] **F1-HELP-02:** Mensaje incluye `/start`, `/crear`, `/finalizar`
- [ ] **F1-HELP-03:** Aparece botón "⬅️ Volver"
- [ ] **F1-HELP-04:** Click en "⬅️ Volver" regresa al menú principal

**Resultado esperado:**
```
ℹ️ Comandos Disponibles

/start - Mostrar menú principal
/crear - Crear nueva tarea
/finalizar - Finalizar tarea pendiente

[⬅️ Volver]
```

### Navegación: Opciones Temporales

- [ ] **F1-TEMP-01:** Click en "📊 Mis Tareas" muestra mensaje temporal
- [ ] **F1-TEMP-02:** Click en "🔍 Buscar" muestra mensaje temporal
- [ ] **F1-TEMP-03:** Mensajes temporales incluyen botón "⬅️ Volver"

---

## 📝 FASE 2: Wizard de Creación Multi-Step

### Iniciar Wizard - Paso 1: Tipo de Tarea

- [ ] **F2-W01-01:** Click en "📋 Crear Tarea" desde menú
- [ ] **F2-W01-02:** Aparece selector de tipo con 3 opciones
- [ ] **F2-W01-03:** Botones muestran: "🔧 OPERATIVO", "📄 ADMINISTRATIVO", "🚨 EMERGENCIA"
- [ ] **F2-W01-04:** Aparece botón "❌ Cancelar"

**Resultado esperado:**
```
Paso 1/6: Tipo de Tarea

Selecciona el tipo de tarea:

[🔧 OPERATIVO]
[📄 ADMINISTRATIVO]
[🚨 EMERGENCIA]
[❌ Cancelar]
```

### Wizard - Paso 2: Código

- [ ] **F2-W02-01:** Al seleccionar tipo (ej: OPERATIVO), avanza a paso 2
- [ ] **F2-W02-02:** Mensaje solicita código de tarea
- [ ] **F2-W02-03:** Indica formato esperado (máx 20 caracteres)
- [ ] **F2-W02-04:** Botón "❌ Cancelar" disponible

**Resultado esperado:**
```
Paso 2/6: Código de Tarea

Tipo seleccionado: OPERATIVO

Envía el código de la tarea (máximo 20 caracteres):
Ejemplo: TSK-2025-001

[❌ Cancelar]
```

### Wizard - Validación de Código

- [ ] **F2-W02-V01:** Enviar código vacío muestra error
- [ ] **F2-W02-V02:** Enviar código > 20 caracteres muestra error
- [ ] **F2-W02-V03:** Enviar código válido (ej: "TSK001") avanza a paso 3
- [ ] **F2-W02-V04:** Errores muestran botón "🔄 Reintentar"

**Test case - Código vacío:**
```
Usuario: [envía mensaje vacío o solo espacios]

Bot:
❌ Error: El código no puede estar vacío.
[🔄 Reintentar] [❌ Cancelar]
```

**Test case - Código muy largo:**
```
Usuario: TSK-2025-CODIGO-EXCESIVAMENTE-LARGO-QUE-EXCEDE-20

Bot:
❌ Error: El código debe tener máximo 20 caracteres.
[🔄 Reintentar] [❌ Cancelar]
```

### Wizard - Paso 3: Título

- [ ] **F2-W03-01:** Mensaje solicita título de tarea
- [ ] **F2-W03-02:** Indica formato esperado (máx 200 caracteres)
- [ ] **F2-W03-03:** Muestra código guardado en paso anterior

**Resultado esperado:**
```
Paso 3/6: Título de la Tarea

Código: TSK001

Envía el título de la tarea (máximo 200 caracteres):
Ejemplo: Reparar servidor de base de datos

[❌ Cancelar]
```

### Wizard - Validación de Título

- [ ] **F2-W03-V01:** Enviar título vacío muestra error
- [ ] **F2-W03-V02:** Enviar título > 200 caracteres muestra error
- [ ] **F2-W03-V03:** Enviar título válido (ej: "Patrullaje Sector Norte") avanza a paso 4

**Test case - Título válido:**
```
Usuario: Patrullaje Sector Norte

Bot:
Paso 4/6: Delegado Responsable
...
```

### Wizard - Paso 4: Delegado

- [ ] **F2-W04-01:** Mensaje solicita ID de delegado
- [ ] **F2-W04-02:** Muestra lista de delegados disponibles (si API funciona)
- [ ] **F2-W04-03:** Indica que debe enviar solo el número

**Resultado esperado (con API):**
```
Paso 4/6: Delegado Responsable

Delegados disponibles:
👤 María González (ID: 5)
👤 Carlos Ramírez (ID: 8)
👤 Ana Torres (ID: 12)

Envía el ID del delegado:

[❌ Cancelar]
```

**Resultado esperado (sin API - fallback):**
```
Paso 4/6: Delegado Responsable

Envía el ID del delegado responsable:
Ejemplo: 5

[❌ Cancelar]
```

### Wizard - Validación de Delegado

- [ ] **F2-W04-V01:** Enviar texto no numérico muestra error
- [ ] **F2-W04-V02:** Enviar número válido (ej: "5") avanza a paso 5
- [ ] **F2-W04-V03:** Error muestra formato esperado

**Test case - ID inválido:**
```
Usuario: María

Bot:
❌ Error: Debes enviar un número válido.
Ejemplo: 5

[🔄 Reintentar] [❌ Cancelar]
```

### Wizard - Paso 5: Asignados

- [ ] **F2-W05-01:** Mensaje solicita IDs de agentes asignados
- [ ] **F2-W05-02:** Indica formato separado por comas
- [ ] **F2-W05-03:** Muestra lista de agentes disponibles (si API funciona)
- [ ] **F2-W05-04:** Indica que debe enviar al menos 1 agente

**Resultado esperado:**
```
Paso 5/6: Agentes Asignados

Agentes disponibles:
👤 Pedro López (ID: 10)
👤 Laura Martínez (ID: 15)
👤 José García (ID: 20)

Envía los IDs separados por comas:
Ejemplo: 10,15,20

[❌ Cancelar]
```

### Wizard - Validación de Asignados

- [ ] **F2-W05-V01:** Enviar lista vacía muestra error
- [ ] **F2-W05-V02:** Enviar formato inválido (letras) muestra error
- [ ] **F2-W05-V03:** Enviar lista válida (ej: "10,15,20") avanza a paso 6
- [ ] **F2-W05-V04:** Espacios alrededor de comas se ignoran (ej: "10, 15, 20")

**Test case - Lista válida:**
```
Usuario: 10,15,20

Bot:
Paso 6/6: Resumen
...
```

**Test case - Formato inválido:**
```
Usuario: 10,abc,20

Bot:
❌ Error: Formato inválido. Usa números separados por comas.
Ejemplo: 10,15,20

[🔄 Reintentar] [❌ Cancelar]
```

### Wizard - Paso 6: Resumen y Confirmación

- [ ] **F2-W06-01:** Muestra resumen completo de la tarea
- [ ] **F2-W06-02:** Incluye todos los datos: tipo, código, título, delegado, asignados
- [ ] **F2-W06-03:** Aparecen botones "✅ Confirmar" y "❌ Cancelar"
- [ ] **F2-W06-04:** Datos se muestran en formato legible

**Resultado esperado:**
```
Paso 6/6: Resumen

📋 Revisa los datos antes de crear:

Tipo: OPERATIVO
Código: `TSK001`
Título: Patrullaje Sector Norte

👤 Delegado: ID 5
👥 Asignados: IDs [10, 15, 20]

¿Confirmar creación?

[✅ Confirmar] [❌ Cancelar]
```

### Wizard - Confirmación

- [ ] **F2-W06-C01:** Click en "✅ Confirmar" intenta crear tarea
- [ ] **F2-W06-C02:** Si API responde OK, muestra mensaje de éxito
- [ ] **F2-W06-C03:** Si API falla, muestra mensaje de error amigable
- [ ] **F2-W06-C04:** Después de confirmar, wizard se limpia del contexto

**Resultado esperado (éxito):**
```
✅ Tarea creada exitosamente!

Código: TSK001
Título: Patrullaje Sector Norte

[🏠 Volver al Menú]
```

**Resultado esperado (error API - mock):**
```
⚠️ Nota: API no disponible (modo demo)

Los datos se han validado correctamente:
- Tipo: OPERATIVO
- Código: TSK001
- Título: Patrullaje Sector Norte
- Delegado: 5
- Asignados: [10, 15, 20]

En producción, la tarea se crearía en la base de datos.

[🏠 Volver al Menú]
```

### Wizard - Cancelación

- [ ] **F2-CANCEL-01:** Click en "❌ Cancelar" en cualquier paso limpia el wizard
- [ ] **F2-CANCEL-02:** Mensaje de confirmación de cancelación aparece
- [ ] **F2-CANCEL-03:** Regresa al menú principal
- [ ] **F2-CANCEL-04:** Datos no se guardan en API

**Resultado esperado:**
```
❌ Creación de tarea cancelada.

Ningún dato fue guardado.

[🏠 Volver al Menú]
```

### Wizard - Casos de Borde

- [ ] **F2-EDGE-01:** Enviar comando `/start` durante wizard cancela wizard
- [ ] **F2-EDGE-02:** Enviar comando `/crear` durante wizard reinicia wizard
- [ ] **F2-EDGE-03:** Múltiples usuarios simultáneos no interfieren entre sí
- [ ] **F2-EDGE-04:** Wizard se mantiene después de reiniciar bot (si `context` persiste)

---

## ✅ FASE 3: Finalizar Tarea con Lista Paginada

### Iniciar Finalización

- [ ] **F3-INIT-01:** Click en "✅ Finalizar Tarea" desde menú principal
- [ ] **F3-INIT-02:** Bot obtiene tareas pendientes del usuario (via API)
- [ ] **F3-INIT-03:** Si hay tareas, muestra lista
- [ ] **F3-INIT-04:** Si no hay tareas, muestra mensaje especial

### Lista Vacía

- [ ] **F3-EMPTY-01:** Mensaje indica "No tienes tareas pendientes"
- [ ] **F3-EMPTY-02:** Incluye emoji visual (ej: ✅ o 🎉)
- [ ] **F3-EMPTY-03:** Botón "⬅️ Volver" disponible

**Resultado esperado:**
```
✅ No tienes tareas pendientes

¡Buen trabajo! Todas tus tareas están completadas.

[⬅️ Volver]
```

### Lista con Tareas (1-5 items)

- [ ] **F3-LIST-01:** Cada tarea se muestra como botón
- [ ] **F3-LIST-02:** Formato: "Código: Título" (título truncado a 30 chars)
- [ ] **F3-LIST-03:** Máximo 5 tareas por página
- [ ] **F3-LIST-04:** Botón "⬅️ Volver" al final
- [ ] **F3-LIST-05:** No aparecen botones de paginación si hay ≤5 tareas

**Resultado esperado (3 tareas):**
```
📋 Tareas Pendientes (3)

Selecciona la tarea a finalizar:

[TSK001: Patrullaje Sector Norte]
[TSK002: Actualizar reporte mensual]
[TSK003: Mantenimiento de vehículos]

[⬅️ Volver]
```

### Lista con Paginación (6+ items)

- [ ] **F3-PAGE-01:** Con 6+ tareas, solo se muestran 5 por página
- [ ] **F3-PAGE-02:** Botones de navegación ◀️ ➡️ aparecen
- [ ] **F3-PAGE-03:** Indicador de página actual (ej: "Página 1/2")
- [ ] **F3-PAGE-04:** Botón ◀️ deshabilitado en primera página
- [ ] **F3-PAGE-05:** Botón ➡️ deshabilitado en última página

**Test case - 8 tareas (2 páginas):**

**Página 1:**
```
📋 Tareas Pendientes (8) - Página 1/2

[TSK001: Patrullaje Sector Norte]
[TSK002: Actualizar reporte mensual]
[TSK003: Mantenimiento de vehículos]
[TSK004: Inspección de equipos]
[TSK005: Revisión de inventario]

[  ][➡️] [⬅️ Volver]
```

**Página 2:**
```
📋 Tareas Pendientes (8) - Página 2/2

[TSK006: Capacitación personal]
[TSK007: Auditoría trimestral]
[TSK008: Reparar sistema eléctrico]

[◀️][  ] [⬅️ Volver]
```

### Navegación entre Páginas

- [ ] **F3-NAV-01:** Click en ➡️ avanza a página siguiente
- [ ] **F3-NAV-02:** Click en ◀️ retrocede a página anterior
- [ ] **F3-NAV-03:** Lista se mantiene (no se re-consulta API innecesariamente)
- [ ] **F3-NAV-04:** Indicador de página se actualiza correctamente

### Selección de Tarea

- [ ] **F3-SEL-01:** Click en tarea (ej: "TSK001: ...") muestra confirmación
- [ ] **F3-SEL-02:** Pantalla de confirmación incluye detalles completos
- [ ] **F3-SEL-03:** Datos mostrados: código, título, tipo
- [ ] **F3-SEL-04:** Botones "✅ Confirmar" y "❌ Cancelar" disponibles

**Resultado esperado:**
```
✅ Finalizar Tarea

¿Estás seguro de finalizar esta tarea?

Código: TSK001
Título: Patrullaje Sector Norte
Tipo: OPERATIVO

[✅ Confirmar] [❌ Cancelar]
```

### Confirmación de Finalización

- [ ] **F3-CONF-01:** Click en "✅ Confirmar" llama a API
- [ ] **F3-CONF-02:** Si API responde 200, muestra mensaje de éxito
- [ ] **F3-CONF-03:** Mensaje incluye código y título de tarea finalizada
- [ ] **F3-CONF-04:** Botón "🏠 Volver al Menú" disponible

**Resultado esperado (éxito):**
```
✅ Tarea finalizada exitosamente!

TSK001: Patrullaje Sector Norte

[🏠 Volver al Menú]
```

### Manejo de Errores - Tarea no Encontrada

- [ ] **F3-ERR-404-01:** Si API retorna 404, muestra mensaje específico
- [ ] **F3-ERR-404-02:** Indica que la tarea no existe o ya fue finalizada
- [ ] **F3-ERR-404-03:** Botón "🔄 Ver Lista" para reintentar

**Resultado esperado:**
```
❌ Error: Tarea no encontrada

La tarea TSK001 no existe o ya fue finalizada.

[🔄 Ver Lista] [🏠 Menú]
```

### Manejo de Errores - Sin Permisos

- [ ] **F3-ERR-403-01:** Si API retorna 403, muestra mensaje de permisos
- [ ] **F3-ERR-403-02:** Indica que el usuario no está autorizado
- [ ] **F3-ERR-403-03:** Botón "🏠 Menú" disponible

**Resultado esperado:**
```
❌ Error: Sin permisos

No tienes autorización para finalizar esta tarea.
Contacta al delegado responsable.

[🏠 Volver al Menú]
```

### Manejo de Errores - Error Genérico

- [ ] **F3-ERR-GEN-01:** Si API falla (500, timeout, etc.), muestra error genérico
- [ ] **F3-ERR-GEN-02:** Mensaje amigable sin detalles técnicos
- [ ] **F3-ERR-GEN-03:** Botones "🔄 Reintentar" y "🏠 Menú" disponibles

**Resultado esperado:**
```
⚠️ Error al finalizar tarea

Ocurrió un problema al conectar con el servidor.
Por favor, intenta nuevamente.

[🔄 Reintentar] [🏠 Menú]
```

### Cancelación

- [ ] **F3-CANCEL-01:** Click en "❌ Cancelar" regresa a la lista
- [ ] **F3-CANCEL-02:** No se llama a la API
- [ ] **F3-CANCEL-03:** Contexto no se limpia (lista se mantiene)

### Casos de Borde

- [ ] **F3-EDGE-01:** API retorna lista vacía después de tener tareas
- [ ] **F3-EDGE-02:** Usuario en página 2, se finaliza tarea, lista se actualiza
- [ ] **F3-EDGE-03:** Dos usuarios finalizan la misma tarea simultáneamente (uno debe recibir 404)
- [ ] **F3-EDGE-04:** Timeout de API (>10s) muestra error amigable

---

## 🚀 Comandos Directos

### Comando /crear

- [ ] **CMD-CREAR-01:** `/crear` inicia wizard directamente
- [ ] **CMD-CREAR-02:** Funciona igual que botón "📋 Crear Tarea"
- [ ] **CMD-CREAR-03:** Salta menú principal

### Comando /finalizar

- [ ] **CMD-FINAL-01:** `/finalizar` muestra lista de tareas pendientes
- [ ] **CMD-FINAL-02:** Funciona igual que botón "✅ Finalizar Tarea"
- [ ] **CMD-FINAL-03:** Salta menú principal

---

## 🔒 Seguridad y Permisos

### Whitelist

- [ ] **SEC-WL-01:** Usuario no en whitelist NO puede usar el bot
- [ ] **SEC-WL-02:** Mensaje de error amigable para usuarios no autorizados
- [ ] **SEC-WL-03:** Admin puede recibir notificación de intento no autorizado

### Rate Limiting

- [ ] **SEC-RL-01:** Bot no permite spam (máx X mensajes por minuto)
- [ ] **SEC-RL-02:** Mensaje de advertencia si se excede el límite

---

## 📊 Logging y Monitoreo

### Logs Estructurados

- [ ] **LOG-01:** Cada acción importante se registra en logs
- [ ] **LOG-02:** Logs incluyen: timestamp, nivel, user_id, acción
- [ ] **LOG-03:** Errores se registran con stack trace
- [ ] **LOG-04:** Archivo `logs/bot.log` se crea automáticamente

### Formato de Logs

**Verificar en `logs/bot.log`:**
```
2025-10-11 10:30:00 | INFO | User 123456789 executed /start
2025-10-11 10:30:15 | INFO | User 123456789 started wizard for task creation
2025-10-11 10:31:45 | INFO | User 123456789 created task TSK001
2025-10-11 10:32:00 | ERROR | API call failed: Connection timeout
```

---

## 📝 Registro de Bugs Encontrados

**Instrucciones:** Anotar aquí los bugs encontrados durante el testing.

### Bug Template:

```
Bug ID: BUG-XXX
Severidad: 🔴/🟡/🟢
Fase: F1/F2/F3
Descripción: [Qué pasó]
Pasos para reproducir:
  1. [Paso 1]
  2. [Paso 2]
  3. [Resultado inesperado]
Resultado esperado: [Qué debería pasar]
Resultado real: [Qué pasó]
Screenshot: [Si aplica]
Notas adicionales: [Contexto adicional]
```

### Bugs Encontrados:

---

## ✅ Resumen de Validación

### Estadísticas

- **Total de checks:** 150+
- **Checks pasados:** ____ / 150+
- **Porcentaje:** _____%
- **Bugs críticos (🔴):** ____
- **Bugs medios (🟡):** ____
- **Bugs bajos (🟢):** ____

### Estado General

- [ ] ✅ **APROBADO** - Todos los checks críticos pasan
- [ ] ⚠️ **APROBADO CON OBSERVACIONES** - Bugs menores encontrados
- [ ] ❌ **NO APROBADO** - Bugs críticos bloqueantes

### Recomendaciones

1. [Recomendación 1]
2. [Recomendación 2]
3. [Recomendación 3]

---

## 📞 Contacto

**Tester:** _____________________  
**Fecha de validación:** _____________________  
**Tiempo total:** _____ horas  
**Ambiente:** Development / Staging / Production

**Notas finales:**
```
[Espacio para comentarios finales del tester]
```

---

**Última actualización:** 11 de octubre de 2025  
**Mantenedor:** Equipo de Desarrollo GRUPO_GAD  
**Próxima revisión:** Antes de merge a master
