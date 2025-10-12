# 📖 Testing Manual Completo - Bot GRUPO_GAD Telegram

## 📋 Información del Documento

**Versión:** 1.0.0  
**Fecha:** 11 de octubre de 2025  
**Autor:** Sistema de Documentación Automática  
**Propósito:** Guía maestra para testing manual exhaustivo del bot de Telegram

---

## 🎯 Alcance del Documento

Este documento proporciona una guía completa para realizar testing manual del bot de Telegram de GRUPO_GAD, cubriendo:

- ✅ **Setup inicial** - Configuración de entorno y prerequisites
- ✅ **Escenarios de prueba** - Casos de uso funcionales y edge cases
- ✅ **Procedimientos paso a paso** - Instrucciones detalladas para cada test
- ✅ **Criterios de aceptación** - Resultados esperados para cada escenario
- ✅ **Registro de bugs** - Template para documentar defectos encontrados

---

## 📚 Índice de Contenidos

1. [Prerequisites y Setup](#prerequisites-y-setup)
2. [Arquitectura del Bot](#arquitectura-del-bot)
3. [Escenarios de Prueba](#escenarios-de-prueba)
4. [Procedimientos de Testing](#procedimientos-de-testing)
5. [Bugs Conocidos](#bugs-conocidos)
6. [Reporte de Testing](#reporte-de-testing)

---

## 🔧 Prerequisites y Setup

### Documentos de Referencia

Antes de comenzar, revisa estos documentos:

1. **[CONFIGURACION_ENTORNO.md](./CONFIGURACION_ENTORNO.md)**
   - Variables de entorno requeridas
   - Configuración de `.env`
   - Troubleshooting de configuración

2. **[SETUP_BOTFATHER.md](./SETUP_BOTFATHER.md)**
   - Crear bot en Telegram con @BotFather
   - Obtener token
   - Configurar comandos

3. **[API_ENDPOINTS.md](./API_ENDPOINTS.md)**
   - Endpoints utilizados por el bot
   - Contratos de API
   - Endpoints mock vs implementados

4. **[CHECKLIST_VALIDACION_COMPLETO.md](./CHECKLIST_VALIDACION_COMPLETO.md)**
   - Checklist detallado de 150+ items
   - Para uso durante testing

### Setup Rápido (5 minutos)

```bash
# 1. Clonar repositorio
git clone https://github.com/eevans-d/GRUPO_GAD.git
cd GRUPO_GAD

# 2. Instalar dependencias
pip install -r requirements.txt
# o con poetry:
poetry install

# 3. Configurar .env
cp .env.example .env
nano .env
# Configurar: TELEGRAM_TOKEN, ADMIN_CHAT_ID, WHITELIST_IDS

# 4. Verificar configuración
python -c "from config.settings import settings; print('Token:', settings.TELEGRAM_TOKEN[:10] + '...')"

# 5. Ejecutar bot
python src/bot/main.py
```

**Output esperado:**
```
2025-10-11 10:30:00 | INFO | Iniciando el bot...
2025-10-11 10:30:01 | INFO | Bot iniciado y escuchando...
```

### Verificación Pre-Testing

- [ ] Bot ejecutando sin errores
- [ ] Token de Telegram configurado
- [ ] Tu Telegram ID en whitelist
- [ ] API opcional corriendo (para tests de integración)
- [ ] Logs generándose en `logs/bot.log`

---

## 🏗️ Arquitectura del Bot

### Componentes Principales

```
src/bot/
├── main.py                     # Punto de entrada
├── commands/                   # Comandos /start, /crear, /finalizar
│   ├── start.py
│   ├── crear_tarea.py
│   └── finalizar_tarea.py
├── handlers/                   # Manejadores de eventos
│   ├── __init__.py            # Registro de handlers
│   ├── callback_handler.py    # Botones interactivos (646 líneas)
│   ├── wizard_text_handler.py # Inputs de texto del wizard (290 líneas)
│   └── message_handler.py     # Mensajes genéricos
├── services/                   # Integración con API
│   └── api_service.py         # Cliente HTTP para API REST
└── utils/                      # Utilidades
    └── keyboards.py           # Factory de teclados inline
```

### Flujo de Datos

```
Usuario en Telegram
    ↓
Telegram Bot API
    ↓
python-telegram-bot library
    ↓
Handlers registrados (commands → callbacks → text → messages)
    ↓
Lógica de negocio (validaciones, state management)
    ↓
API Service (opcional)
    ↓
API REST (/api/v1/...)
    ↓
Base de datos PostgreSQL
```

### State Management

El bot utiliza `context.user_data` para persistir estado entre interacciones:

```python
# Wizard de creación
context.user_data['wizard'] = {
    'active': True,
    'current_step': 2,
    'data': {
        'tipo': 'operativo',
        'codigo': 'TSK001',
        'titulo': 'Patrullaje',
        'delegado_id': 5,
        'asignados': [10, 15, 20]
    }
}

# Finalización de tarea
context.user_data['finalizar_task'] = {
    'codigo': 'TSK001',
    'titulo': 'Patrullaje Sector Norte',
    'tipo': 'operativo'
}

# Paginación
context.user_data['pagination'] = {
    'current_page': 0,
    'total_pages': 3,
    'items': [...]  # Lista completa de tareas
}
```

---

## 🧪 Escenarios de Prueba

### Matriz de Escenarios

| ID | Escenario | Tipo | Prioridad | Complejidad | Tiempo Est. |
|----|-----------|------|-----------|-------------|-------------|
| **FASE 0: Setup** |
| S0-01 | Configurar entorno | Setup | 🔴 Crítica | Baja | 5 min |
| S0-02 | Validar variables de entorno | Setup | 🔴 Crítica | Baja | 2 min |
| **FASE 1: Menú Principal** |
| S1-01 | Comando /start | Funcional | 🔴 Crítica | Baja | 1 min |
| S1-02 | Navegación de menú | Funcional | 🔴 Crítica | Baja | 3 min |
| S1-03 | Botón Ayuda | Funcional | 🟡 Media | Baja | 1 min |
| S1-04 | Botones temporales | Funcional | 🟢 Baja | Baja | 2 min |
| **FASE 2: Wizard de Creación** |
| S2-01 | Wizard flujo completo | Funcional | 🔴 Crítica | Alta | 5 min |
| S2-02 | Validación de código | Validación | 🔴 Crítica | Media | 3 min |
| S2-03 | Validación de título | Validación | 🔴 Crítica | Media | 3 min |
| S2-04 | Validación de delegado | Validación | 🔴 Crítica | Media | 3 min |
| S2-05 | Validación de asignados | Validación | 🔴 Crítica | Media | 3 min |
| S2-06 | Cancelación de wizard | Funcional | 🟡 Media | Baja | 2 min |
| S2-07 | Resumen y confirmación | Funcional | 🔴 Crítica | Media | 2 min |
| S2-08 | Reinicio durante wizard | Edge Case | 🟡 Media | Media | 3 min |
| **FASE 3: Finalizar Tarea** |
| S3-01 | Lista vacía | Funcional | 🟡 Media | Baja | 1 min |
| S3-02 | Lista con 3 tareas | Funcional | 🔴 Crítica | Media | 2 min |
| S3-03 | Lista con paginación (8 tareas) | Funcional | 🔴 Crítica | Alta | 5 min |
| S3-04 | Navegación entre páginas | Funcional | 🔴 Crítica | Media | 3 min |
| S3-05 | Selección y confirmación | Funcional | 🔴 Crítica | Media | 2 min |
| S3-06 | Finalización exitosa | Funcional | 🔴 Crítica | Media | 2 min |
| S3-07 | Error 404 (tarea no encontrada) | Error | 🟡 Media | Media | 2 min |
| S3-08 | Error 403 (sin permisos) | Error | 🟡 Media | Media | 2 min |
| S3-09 | Error genérico (API caída) | Error | 🟡 Media | Media | 2 min |
| S3-10 | Cancelación | Funcional | 🟢 Baja | Baja | 1 min |
| **SEGURIDAD** |
| SEC-01 | Usuario no autorizado | Seguridad | 🔴 Crítica | Media | 3 min |
| SEC-02 | Rate limiting | Seguridad | 🟡 Media | Media | 5 min |

**Total:** 24 escenarios | **Tiempo total estimado:** ~60-75 minutos

---

## 📝 Procedimientos de Testing

### S0-01: Configurar Entorno

**Objetivo:** Verificar que el entorno está correctamente configurado.

**Prerequisites:**
- Python 3.10+
- pip o poetry instalado
- Acceso a Telegram

**Pasos:**
1. Clonar repositorio
2. Instalar dependencias: `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env`
4. Configurar variables:
   - `TELEGRAM_TOKEN` (de @BotFather)
   - `ADMIN_CHAT_ID` (de @userinfobot)
   - `WHITELIST_IDS` (tu Telegram ID en array JSON)
5. Ejecutar: `python src/bot/main.py`

**Resultado esperado:**
```
✅ Bot inicia sin errores
✅ Log muestra "Bot iniciado y escuchando..."
✅ No hay errores de importación
✅ Archivo logs/bot.log se crea
```

**Criterios de aceptación:**
- [ ] Bot ejecuta sin exceptions
- [ ] Logs se generan correctamente
- [ ] Variables de entorno se cargan

---

### S1-01: Comando /start

**Objetivo:** Validar que el comando `/start` muestra el menú principal con botones.

**Prerequisites:**
- Bot corriendo
- Usuario autorizado en whitelist

**Pasos:**
1. Abrir Telegram
2. Buscar tu bot (ej: `@grupogad_bot`)
3. Enviar `/start`

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

**Criterios de aceptación:**
- [ ] Mensaje con emoji 🤖
- [ ] Texto en negrita (Markdown)
- [ ] 5 botones visibles y clickeables
- [ ] Botones en orden correcto

**Bugs conocidos:** Ninguno

---

### S2-01: Wizard Flujo Completo

**Objetivo:** Completar el wizard de creación de tarea end-to-end.

**Prerequisites:**
- Bot corriendo
- Usuario autorizado

**Pasos:**

1. **Iniciar wizard**
   - Enviar `/start`
   - Click en "📋 Crear Tarea"
   - **Esperas:** Selector de tipo (OPERATIVO/ADMINISTRATIVO/EMERGENCIA)

2. **Seleccionar tipo**
   - Click en "🔧 OPERATIVO"
   - **Esperas:** Solicitud de código

3. **Ingresar código**
   - Enviar: `TSK001`
   - **Esperas:** Solicitud de título

4. **Ingresar título**
   - Enviar: `Patrullaje Sector Norte`
   - **Esperas:** Solicitud de delegado

5. **Ingresar delegado**
   - Enviar: `5`
   - **Esperas:** Solicitud de asignados

6. **Ingresar asignados**
   - Enviar: `10,15,20`
   - **Esperas:** Resumen completo

7. **Revisar resumen**
   - Verificar que todos los datos sean correctos:
     ```
     Tipo: OPERATIVO
     Código: `TSK001`
     Título: Patrullaje Sector Norte
     Delegado: ID 5
     Asignados: IDs [10, 15, 20]
     ```
   - Click en "✅ Confirmar"

8. **Verificar creación**
   - **Esperas (con API):** Mensaje "✅ Tarea creada exitosamente!"
   - **Esperas (sin API):** Mensaje de demo con datos validados

**Tiempo estimado:** 5 minutos

**Criterios de aceptación:**
- [ ] Todos los pasos se completan sin errores
- [ ] Datos se guardan correctamente en cada paso
- [ ] Resumen muestra información correcta
- [ ] Confirmación muestra mensaje apropiado
- [ ] Wizard se limpia del contexto

**Variaciones a probar:**
- Tipos diferentes: ADMINISTRATIVO, EMERGENCIA
- Códigos diferentes: `T-2025-001`, `ADMIN-01`
- Múltiples asignados: `10`, `10,15`, `10,15,20,25`

---

### S2-02: Validación de Código

**Objetivo:** Validar que el campo código rechaza inputs inválidos.

**Prerequisites:**
- Wizard iniciado en paso 2 (código)

**Test Case 1: Código vacío**

**Pasos:**
1. En paso 2 (código), enviar mensaje vacío
2. Verificar mensaje de error

**Resultado esperado:**
```
❌ Error: El código no puede estar vacío.

[🔄 Reintentar] [❌ Cancelar]
```

**Test Case 2: Código muy largo**

**Pasos:**
1. Enviar código con >20 caracteres: `TSK-2025-CODIGO-EXCESIVAMENTE-LARGO`

**Resultado esperado:**
```
❌ Error: El código debe tener máximo 20 caracteres.

[🔄 Reintentar] [❌ Cancelar]
```

**Test Case 3: Código válido**

**Pasos:**
1. Enviar código válido: `TSK001`

**Resultado esperado:**
```
Paso 3/6: Título de la Tarea

Código: TSK001
...
```

**Criterios de aceptación:**
- [ ] Vacío rechazado con error específico
- [ ] >20 chars rechazado con error específico
- [ ] Código válido acepta y avanza
- [ ] Botones de error funcionan

---

### S3-03: Lista con Paginación (8 tareas)

**Objetivo:** Validar la paginación de la lista de tareas pendientes.

**Prerequisites:**
- API mock o real que retorne 8 tareas
- Bot corriendo

**Setup:**
Para este test, necesitas modificar temporalmente `api_service.py` para retornar 8 tareas mock:

```python
def get_user_pending_tasks(self, telegram_id: int) -> List[Tarea]:
    """Mock: retorna 8 tareas para testing de paginación."""
    return [
        Tarea(id=i, tipo="operativo", codigo=f"TSK00{i}", 
              titulo=f"Tarea de prueba {i}", estado="pending", prioridad="media")
        for i in range(1, 9)
    ]
```

**Pasos:**

1. **Iniciar finalización**
   - Enviar `/finalizar`
   - **Esperas:** Lista paginada con 5 tareas (página 1/2)

2. **Verificar página 1**
   - Verificar que se muestran tareas TSK001 a TSK005
   - Verificar indicador "Página 1/2"
   - Verificar botones: `[  ][➡️] [⬅️ Volver]`
   - Verificar que botón ◀️ NO aparece (estamos en página 1)

3. **Navegar a página 2**
   - Click en ➡️
   - **Esperas:** Tareas TSK006 a TSK008
   - Verificar indicador "Página 2/2"
   - Verificar botones: `[◀️][  ] [⬅️ Volver]`
   - Verificar que botón ➡️ NO aparece (estamos en última página)

4. **Navegar de regreso a página 1**
   - Click en ◀️
   - **Esperas:** Tareas TSK001 a TSK005 de nuevo
   - Verificar que la lista no cambió (no se re-consultó API)

5. **Seleccionar tarea de página 2**
   - Click en ➡️ para ir a página 2
   - Click en "TSK007: ..."
   - **Esperas:** Confirmación con detalles de TSK007

**Tiempo estimado:** 5 minutos

**Criterios de aceptación:**
- [ ] Paginación se activa con 6+ tareas
- [ ] 5 tareas por página máximo
- [ ] Indicador de página correcto
- [ ] Botones de navegación muestran/ocultan correctamente
- [ ] Navegación funciona en ambas direcciones
- [ ] Selección funciona en cualquier página
- [ ] Lista no se pierde al navegar

**Edge cases adicionales:**
- Exactamente 5 tareas (sin paginación)
- Exactamente 6 tareas (2 páginas: 5+1)
- 10 tareas (2 páginas: 5+5)
- 11 tareas (3 páginas: 5+5+1)

---

### S3-06: Finalización Exitosa

**Objetivo:** Validar el flujo completo de finalización con respuesta exitosa de la API.

**Prerequisites:**
- Lista de tareas disponible
- API mock que retorne 200 OK

**Setup Mock (opcional):**
```python
def finalize_task(self, task_code: str, telegram_id: int) -> Tarea:
    """Mock: retorna tarea finalizada."""
    return Tarea(
        id=1,
        tipo="operativo",
        codigo=task_code,
        titulo="Patrullaje Sector Norte",
        estado="completed",
        prioridad="media"
    )
```

**Pasos:**

1. Enviar `/finalizar`
2. Click en primera tarea (ej: "TSK001: ...")
3. En confirmación, click en "✅ Confirmar"
4. **Esperas:** Mensaje de éxito

**Resultado esperado:**
```
✅ Tarea finalizada exitosamente!

TSK001: Patrullaje Sector Norte

[🏠 Volver al Menú]
```

**Verificaciones adicionales:**
- [ ] Click en "🏠 Volver al Menú" regresa a menú principal
- [ ] Contexto `finalizar_task` se limpió
- [ ] Log registra: `User X finalized task TSK001`

**Criterios de aceptación:**
- [ ] Mensaje de éxito se muestra
- [ ] Código y título correctos
- [ ] Botón de regreso funciona
- [ ] State se limpia

---

### S3-07: Error 404 (Tarea No Encontrada)

**Objetivo:** Validar manejo de error cuando tarea no existe.

**Setup Mock:**
```python
def finalize_task(self, task_code: str, telegram_id: int) -> Tarea:
    """Mock: simula 404."""
    raise requests.exceptions.HTTPError(
        response=MockResponse(status_code=404)
    )
```

**Pasos:**
1. Enviar `/finalizar`
2. Click en tarea
3. Click en "✅ Confirmar"

**Resultado esperado:**
```
❌ Error: Tarea no encontrada

La tarea TSK001 no existe o ya fue finalizada.

[🔄 Ver Lista] [🏠 Menú]
```

**Criterios de aceptación:**
- [ ] Mensaje específico para 404
- [ ] Menciona código de tarea
- [ ] Sugiere causas posibles
- [ ] Botones de recuperación disponibles
- [ ] Log registra error: `Task TSK001 not found (404)`

---

### SEC-01: Usuario No Autorizado

**Objetivo:** Validar que usuarios no en whitelist no pueden usar el bot.

**Setup:**
1. Obtener Telegram ID de usuario no autorizado
2. Verificar que NO está en `WHITELIST_IDS` de `.env`

**Pasos:**
1. Usuario no autorizado envía `/start`

**Resultado esperado:**
```
❌ Acceso No Autorizado

No tienes permisos para usar este bot.

Contacta al administrador para solicitar acceso.
```

**O simplemente sin respuesta (bot ignora el mensaje).**

**Criterios de aceptación:**
- [ ] Usuario recibe mensaje de error o es ignorado
- [ ] No puede ejecutar ningún comando
- [ ] No puede usar botones
- [ ] Log registra intento: `Unauthorized access attempt by user X`
- [ ] Admin recibe notificación (opcional)

---

## 🐛 Bugs Conocidos

### Actualizados: 11 de octubre de 2025

| ID | Severidad | Fase | Descripción | Workaround | Estado |
|----|-----------|------|-------------|------------|--------|
| BUG-001 | 🟡 Media | F2 | Wizard: texto muy largo en resumen se trunca visualmente | Limitar título a 100 chars en UI | Pendiente |
| BUG-002 | 🟢 Baja | F3 | Paginación: última página con 1 tarea muestra mucho espacio vacío | Agregar mensaje informativo | Pendiente |
| BUG-003 | 🟡 Media | API | Endpoints `/tasks/create`, `/tasks/finalize` no implementados en API real | Usar endpoints estándar o implementar | Bloqueante |
| BUG-004 | 🟢 Baja | F1 | Botones "Buscar" y "Mis Tareas" muestran mensaje genérico | Funcionalidad pendiente (roadmap) | Esperado |

**Nota:** BUG-003 es conocido y esperado. Los endpoints mock se simulan localmente hasta que la API los implemente.

---

## 📊 Reporte de Testing

### Template de Reporte

```markdown
# Reporte de Testing Manual - Bot GRUPO_GAD

**Tester:** [Nombre]  
**Fecha:** [DD/MM/YYYY]  
**Versión del Bot:** 1.0.0  
**Branch:** feature/telegram-interactive-buttons  
**Commit:** [hash]  
**Ambiente:** Development / Staging  
**Duración:** [HH:MM]

## Resumen Ejecutivo

- **Escenarios ejecutados:** X / 24
- **Escenarios pasados:** X
- **Escenarios fallidos:** X
- **Bugs encontrados:** X
- **Bugs críticos:** X 🔴
- **Bugs medios:** X 🟡
- **Bugs bajos:** X 🟢

## Estado General

✅ **APROBADO** - El bot está listo para merge a master  
⚠️ **APROBADO CON OBSERVACIONES** - Bugs menores documentados  
❌ **NO APROBADO** - Bugs críticos bloqueantes

## Detalle de Escenarios

| ID | Escenario | Estado | Tiempo | Notas |
|----|-----------|--------|--------|-------|
| S0-01 | Setup entorno | ✅ | 5min | Sin problemas |
| S1-01 | Comando /start | ✅ | 1min | - |
| S2-01 | Wizard completo | ✅ | 5min | - |
| ... | ... | ... | ... | ... |

## Bugs Encontrados

### BUG-XXX: [Título corto]

**Severidad:** 🔴/🟡/🟢  
**Fase:** F1/F2/F3  
**Descripción:** [Qué pasó]

**Pasos para reproducir:**
1. [Paso 1]
2. [Paso 2]
3. [Resultado inesperado]

**Resultado esperado:** [Qué debería pasar]  
**Resultado real:** [Qué pasó]  
**Screenshot:** [Link o adjunto]

**Impacto:**
- [ ] Bloqueante
- [ ] Funcionalidad afectada
- [ ] Cosmético

## Recomendaciones

1. [Recomendación 1]
2. [Recomendación 2]

## Conclusión

[Párrafo de conclusión sobre el estado general del bot]
```

---

## 📞 Soporte y Contacto

### Documentación

- **Configuración:** [CONFIGURACION_ENTORNO.md](./CONFIGURACION_ENTORNO.md)
- **Setup BotFather:** [SETUP_BOTFATHER.md](./SETUP_BOTFATHER.md)
- **API Endpoints:** [API_ENDPOINTS.md](./API_ENDPOINTS.md)
- **Checklist:** [CHECKLIST_VALIDACION_COMPLETO.md](./CHECKLIST_VALIDACION_COMPLETO.md)

### Contacto

- **Equipo de Desarrollo:** dev@grupogad.gob.ec
- **Slack:** #grupo-gad-support
- **GitHub Issues:** https://github.com/eevans-d/GRUPO_GAD/issues

### Recursos Externos

- **Telegram Bot API:** https://core.telegram.org/bots/api
- **python-telegram-bot:** https://docs.python-telegram-bot.org/

---

## ✅ Checklist Final de Testing

Antes de dar por completado el testing, verificar:

- [ ] Todos los escenarios críticos (🔴) ejecutados
- [ ] Al menos 80% de escenarios medios (🟡) ejecutados
- [ ] Todos los bugs documentados con template
- [ ] Reporte de testing completado
- [ ] Screenshots/videos de bugs adjuntados
- [ ] Logs guardados para revisión posterior
- [ ] Comunicación a equipo de desarrollo sobre bugs críticos

---

**Última actualización:** 11 de octubre de 2025  
**Versión del documento:** 1.0.0  
**Mantenedor:** Equipo de Desarrollo GRUPO_GAD

**Historial de cambios:**
- v1.0.0 (11/10/2025) - Documento inicial creado
