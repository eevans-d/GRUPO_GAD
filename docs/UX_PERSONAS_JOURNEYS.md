# 👥 USER PERSONAS & JOURNEY MAPS

---

## PERSONA 1: "LUIS" - EL JEFE/ADMINISTRADOR

### Perfil Demográfico
- **Edad:** 45 años
- **Rol:** Jefe de operaciones
- **Experiencia Tech:** Media-Alta (usa Excel, WhatsApp, navegador)
- **Dispositivo Principal:** Laptop/Escritorio

### Motivaciones
- ✅ Mantener grupo organizado y productivo
- ✅ Ver progreso real-time
- ✅ Identificar cuellos de botella rápidamente
- ✅ Minimizar tiempo en tareas administrativas

### Frustraciones Actuales
- ❌ No sabe qué están haciendo los miembros en tiempo real
- ❌ Crear tarea toma 3.5 minutos
- ❌ Dashboard sin filtros = 10 min buscando
- ❌ Miembros dicen "no sabía que había tarea" → se perdieron notificaciones

### Contexto de Uso
```
08:00 AM  → Llega a oficina
08:05     → Abre Dashboard para ver estado
08:15     → Crea 3 nuevas tareas (wizard lento)
09:00     → Revisa avance (datos viejos, refreshea manual)
14:00     → Intenta buscar tarea específica (scroll 20 min)
16:00     → Sale, pero antes chequea si se completaron tareas
```

### Tareas Clave
1. **Crear tarea** → Tipo, código, descripción, efectivos
2. **Visualizar progreso** → Estados, asignación, ubicación
3. **Comunicar cambios** → Notificaciones a miembros
4. **Reportear** → Métricas, cumplimiento, tiempos

### Painpoints Específicos de Luis
```
MAÑANA:
Abre dashboard lento (5+ seg) → Dashboard overcrowded
Crea tarea → Wizard sin progreso (¿cuántos pasos?) → Abandon si prisa
No ve notificaciones → Se pierde feedback de miembros
No sabe si tarea llegó → "¿Se enteraron?"

TARDE:
Buscar tarea completada → 10+ min sin filtros
No sabe si miembro está en tarea o disponible → Info oculta
Dashboard stale → Refresh manual cada vez
```

### Quién es su Ayuda
- 🤖 Bot Telegram (para notificaciones rápidas)
- 📊 Dashboard web (para decisiones)
- 👥 Miembros directamente (fallback: WhatsApp/llamada)

---

## PERSONA 2: "CARLOS" - EL MIEMBRO/AGENTE

### Perfil Demográfico
- **Edad:** 28 años
- **Rol:** Agente operativo / Efectivo
- **Experiencia Tech:** Media (WhatsApp power user, no sabe APIs)
- **Dispositivo Principal:** Smartphone (Android)

### Motivaciones
- ✅ Saber qué hacer hoy (tareas claras)
- ✅ Completar tareas sin confusión
- ✅ Recibir instrucciones rápidas
- ✅ Feedback sobre su desempeño

### Frustraciones Actuales
- ❌ No recibe notificación cuando lo asignan
- ❌ No entiende qué tiene que hacer (contexto falta)
- ❌ Proceso de "finalizar" es complejo
- ❌ No sabe si terminó bien o falta algo

### Contexto de Uso
```
08:00 AM  → Abre Telegram varias veces (¿hay asignaciones?)
09:00     → Recibe tarea de Luis (si no falla notif)
09:05     → Lee tarea pero falta info ("¿qué hago exacto?")
10:00     → Finaliza tarea (proceso confuso: ¿qué botones?)
14:00     → Chequea si Luis vio que terminó
```

### Tareas Clave
1. **Ver asignaciones** → Qué tengo pendiente
2. **Entender contexto** → Qué, dónde, cómo, cuándo
3. **Completar tarea** → Reportar estado, evidencia
4. **Confirmación** → Saber que llegó al jefe

### Painpoints Específicos de Carlos
```
MAÑANA:
No recibe notificación → Se pierde tarea
Bot menú confuso → "¿Qué hago aquí?"
Sin contexto en tarea → "¿Qué es exactamente?"

DURANTE TAREA:
No sabe si va por buen camino
Sin acceso a dashboard (solo en bot)
Confundido por formato/codes

FINALIZACIÓN:
Proceso wizard inverso complejo
"¿Qué información necesita?"
Sin confirmación visual
No sabe si se enteró jefe
```

### Quién es su Ayuda
- 📱 Bot Telegram (su herramienta principal)
- 📞 Llamada a Luis si algo no funciona
- 👥 Otros compañeros (preguntan)

---

## JOURNEY MAP: LUIS (Admin Creando Tarea)

```
FASE: Decisión → Inicio → Entrada → Wizard → Confirmación → Submit

┌─ EMOCIÓN / ESTADO ────────────────────────────────────────────┐
│                                                               │
│  😊 Motivado    😐 Neutral      😠 Frustrado    ✅ Exitoso  │
│      ↓              ↓                 ↓             ↑         │
│  "Necesito    "Abriendo bot"   "¿Dónde? Lento!"  "¡Hecho!"  │
│   crear una                                                  │
│   tarea"                                                     │
├─────────────────────────────────────────────────────────────┤
│ TOUCHPOINT         ACCIÓN                PAIN POINT          │
├─────────────────────────────────────────────────────────────┤
│ 1. Bot Menú     Toca "Crear Tarea"   ❌ Menú poco claro    │
│    (2s)                               ❌ Sin progreso info  │
├─────────────────────────────────────────────────────────────┤
│ 2. Tipo Tarea   Selecciona tipo      ❌ No sé qué significa│
│    (15s)                              ❌ Sin ayuda inline   │
├─────────────────────────────────────────────────────────────┤
│ 3. Código       Escribe código       ❌ Formato incierto   │
│    (45s)                              ❌ No valida en vivo │
├─────────────────────────────────────────────────────────────┤
│ 4. Título       Escribe título       ❌ ¿Cuántos caract?   │
│    (30s)                                                    │
├─────────────────────────────────────────────────────────────┤
│ 5. Descripción  Escribe desc         ❌ Field sin límite   │
│    (45s)                              ❌ Sin rich text      │
├─────────────────────────────────────────────────────────────┤
│ 6. Asignar      Busca efectivos      ❌ Memorizar IDs!!!   │
│    (60s)                              ❌ Sin autocomplete   │
├─────────────────────────────────────────────────────────────┤
│ 7. ¿Confirma?   Ver resumen          ❌ Sin preview        │
│    (10s)        Toca ✅ Confirmar     ❌ No puede editar    │
├─────────────────────────────────────────────────────────────┤
│ 8. Enviar       Task creada          ✅ Feedback éxito     │
│    (1s)         Notif a efectivos     ⚠️ No ve si recibieron
└─────────────────────────────────────────────────────────────┘

TIEMPO TOTAL: ~3.5 minutos
TAPS/CLICKS: 10-15
FRUSTRACIÓN: Media (especialmente paso 6)
```

### Oportunidades de Mejora (Marca 🔴)
1. **Barra de progreso** → Saber dónde estoy
2. **Ayuda contextual** → Explicar cada campo
3. **Validación real-time** → Código correcto ahora
4. **Autocompletar efectivos** → No memorizar IDs
5. **Preview antes confirmar** → Editar si es necesario
6. **Confirmación visual** → "¡Notificado a 2 efectivos!"

---

## JOURNEY MAP: CARLOS (Agente Completando Tarea)

```
FASE: Notificación → Lectura → Ubicación → Ejecución → Reportar

┌─ EMOCIÓN / ESTADO ────────────────────────────────────────────┐
│                                                               │
│  ❓ Confundido   😊 Motivado    😊 Trabajando   ✅ Exitoso  │
│       ↓              ↓               ↓             ↑         │
│  "¿Nueva      "Entendí qué"    "Haciendo"    "Reporté"     │
│   tarea?"                                                   │
├─────────────────────────────────────────────────────────────┤
│ TOUCHPOINT         ACCIÓN                PAIN POINT          │
├─────────────────────────────────────────────────────────────┤
│ 1. Notif      Telegram ping      ❌ SIN NOTIFICACIÓN (falla)
│    (0s)       Abre mensaje        ❌ Notif mal formada      │
├─────────────────────────────────────────────────────────────┤
│ 2. Lee Tarea  "Voy a revisar    ❌ "Inspeccionar calle 10"
│    (15s)       calle 10 oeste"   ❌ Muy vago ¿QUÉ BUSCAR?   │
│               (NO ENTIENDE)       ❌ Sin contexto ubicación │
├─────────────────────────────────────────────────────────────┤
│ 3. Se orienta Abre Maps          ⚠️ Manualmente, sin ayuda  │
│    (90s)      (El bot no ayuda)   ❌ Pierde tiempo           │
├─────────────────────────────────────────────────────────────┤
│ 4. Ejecuta    Hace la tarea      ✅ Fase sin dolor         │
│    (varies)                       ⚠️ Sin feedback en vivo   │
├─────────────────────────────────────────────────────────────┤
│ 5. Reporta    /finalizar_tarea   ❌ Wizard invertido confuso
│    (120s)     → Paso 1,2,3...    ❌ "¿Qué información?"    │
│               → Confirma          ❌ Sin preview             │
├─────────────────────────────────────────────────────────────┤
│ 6. Envía      Tarea completa     ❌ SIN CONFIRMACIÓN        │
│    (1s)       (fin de proceso)    ❌ "¿Se enteró Luis?"     │
│                                   ❌ No sabe su desempeño   │
└─────────────────────────────────────────────────────────────┘

TIEMPO TOTAL: 3-5 minutos de admin overhead
FRUSTRACIONES: Alta (notificación, contexto, confirmación)
POSIBLES ABANDONOS: Paso 2 (no entiende), Paso 5 (complejo)
```

### Oportunidades de Mejora (Marca 🔴)
1. **Notificaciones confiables** → WebSocket reconexión automática
2. **Contexto rico** → GPS, foto, instrucciones detalladas
3. **Confirmación simple** → Un click "✅ Completada"
4. **Feedback visual** → "✅ Reportado a Luis"
5. **Dashboard personal** → Ver progreso de mis tareas
6. **Estadísticas** → "Has completado 47 tareas, promedio 25 min"

---

## MATRIZ DE SATISFACCIÓN ACTUAL

```
           LUIS (Admin)        CARLOS (Miembro)
           ────────────        ────────────────
Crear       6/10               -
Asignar     5/10               -
Notificar   4/10               3/10 ← CRÍTICO
Ejecutar    -                  7/10
Reportar    7/10               5/10
Visualizar  6/10               2/10
Ayuda       5/10               3/10

PROMEDIO    5.8/10             4.0/10 ← URGENTE
```

---

## RECOMENDACIONES POR PERSONA

### Para LUIS (Admin)
- **Priority 1:** Filtros + búsqueda rápida (salva 5 min/día)
- **Priority 2:** Progress bar en wizard (reduce abandon)
- **Priority 3:** Autocompletar efectivos (reduce errores)
- **Priority 4:** Real-time updates en dashboard (confianza)

### Para CARLOS (Miembros)
- **Priority 1:** Notificaciones confiables (CRÍTICO)
- **Priority 2:** Contexto rico en tarea (evita confusión)
- **Priority 3:** Botón simple "completada" (reduce friction)
- **Priority 4:** Feedback visual inmediato (motivación)

