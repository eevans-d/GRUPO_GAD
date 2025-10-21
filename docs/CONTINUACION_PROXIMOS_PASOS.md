# ▶️ CONTINUACIÓN - PRÓXIMOS PASOS EXACTOS

**Fase:** Sprint 1 - Tácticas 1-8  
**Estado:** 1/8 completada, 1 en progreso  
**Tiempo restante:** 6.5-7.5 horas

---

## ⏳ AHORA MISMO: Completar Táctica 2

### Paso 1: Crear Handler de Confirmación

**Archivo:** `src/bot/handlers/callback_handler.py`

Agregar después de la función `_handle_tipo_callback`:

```python
async def _handle_confirmation_callback(
    update: Update,
    query: any,
    confirm_action: str,
    task_data: dict,
    context: CallbackContext
) -> None:
    """
    Maneja confirmación de tarea (YES/NO).
    
    Args:
        confirm_action: "yes" o "no"
    """
    if confirm_action == "yes":
        # Proceder a crear tarea
        await query.edit_message_text("✅ Tarea creada exitosamente!")
    else:
        # Cancelar y volver al menú
        await query.edit_message_text("❌ Wizard cancelado")
```

### Paso 2: Agregar Botones de Confirmación

En `src/bot/utils/keyboards.py`, agregar:

```python
@staticmethod
def task_confirmation() -> InlineKeyboardMarkup:
    """Botones de confirmación."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ Cancelar", callback_data="confirm:no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
```

### Paso 3: Llamar desde callback_handler

Después del último paso (Step 5), mostrar confirmación:

```python
# Al final del wizard
keyboard = KeyboardFactory.task_confirmation()
summary = format_task_summary(wizard_data)
await query.edit_message_text(summary, reply_markup=keyboard, parse_mode="Markdown")
```

---

## 📋 TÁCTICAS 3-8 (EN ORDEN DE IMPLEMENTACIÓN)

### Táctica 3: Mensajes Personalizados (30 min)

**Archivo:** `src/bot/commands/start.py`

Cambiar:
```python
# ANTES
welcome_text = (
    "🤖 *Bienvenido a GAD Bot*\n\n"
    "Sistema de Gestión de Agentes y Tareas."
)

# DESPUÉS
user_name = update.message.from_user.first_name or "Usuario"
welcome_text = (
    f"👋 ¡Hola, {user_name}!\n\n"
    "Soy el Bot de Gestión GRUPO_GAD 🏛️"
)
```

### Táctica 4: Emojis Semánticos (45 min)

**Crear:** `src/bot/utils/emojis.py`

```python
class TaskEmojis:
    PENDING = "⏳"
    ACTIVE = "🔄"
    COMPLETED = "✅"
    FAILED = "❌"
```

Usar en todos los mensajes del bot.

### Táctica 5: Ayuda Contextual (1 hora)

**Archivo:** `src/bot/handlers/wizard_text_handler.py`

Crear función:
```python
def get_step_help(step: int) -> str:
    helps = {
        1: "Tipos: OPERATIVO, ADMINISTRATIVO, EMERGENCIA",
        2: "Formato: TIP-2025-001",
        3: "Máximo 200 caracteres",
        # ...
    }
    return helps.get(step, "Ayuda no disponible")
```

### Táctica 6: Teclado Mejorado (1 hora)

**Archivo:** `src/bot/utils/keyboards.py`

Mejorar `KeyboardFactory.task_types()`:

```python
keyboard = [
    [InlineKeyboardButton("🔧 OPERATIVO", callback_data="tipo:OP")],
    [InlineKeyboardButton("📄 ADMINISTRATIVO", callback_data="tipo:AD")],
    [InlineKeyboardButton("❓ ¿Cuál elegir?", callback_data="help:tipos")],
]
```

### Táctica 7: Validación Real-time (1.5 horas)

**Archivo:** `src/bot/handlers/wizard_text_handler.py`

Agregar validaciones en cada `_handle_*_input`:

```python
def validate_codigo(code: str) -> tuple[bool, str]:
    """Valida formato de código."""
    if not re.match(r'^[A-Z]{2,3}-\d{4}-\d{3}$', code):
        return False, "❌ Formato inválido. Usa: `TIP-2025-001`"
    return True, ""

# Usar en handler
is_valid, error = validate_codigo(text_input)
if not is_valid:
    await update.message.reply_text(error)
    return
```

### Táctica 8: Dashboard Responsive (6 horas)

**Archivo:** `dashboard/templates/admin_dashboard.html`

Agregar CSS media queries:

```css
@media (max-width: 768px) {
    .dashboard-container {
        grid-template-columns: 1fr;
    }
    .side-panel {
        max-height: 50vh;
    }
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Completar Táctica 2 (confirmación)
- [ ] Implementar Táctica 3 (personalizados)
- [ ] Crear Táctica 4 (emojis)
- [ ] Agregar Táctica 5 (ayuda)
- [ ] Mejorar Táctica 6 (teclado)
- [ ] Validar Táctica 7 (real-time)
- [ ] Responsive Táctica 8 (dashboard)
- [ ] Testing en bot Telegram
- [ ] Merge a master
- [ ] Deploy a producción

---

## 🎯 TIEMPO ESTIMADO

- Táctica 2-7: 5.5 horas
- Táctica 8: 6 horas
- Testing: 1-2 horas
- **Total Sprint 1:** 8-9 horas ✅

---

## 📚 REFERENCIAS

- Análisis completo: `UX_ANALYSIS_COMPREHENSIVE.md`
- Tácticas detalladas: `UX_IMPLEMENTATION_TACTICS.md`
- Roadmap: `UX_IMPROVEMENTS_ROADMAP.md`
- Progreso: `SPRINT1_PROGRESS.md`

