# ⚙️ GUÍA DE IMPLEMENTACIÓN FASE 1

**Duración:** 2 días (Oct 21-22) | **Equipo:** 1 desarrollador | **Horas:** 8

---

## 🎯 OBJETIVO SPRINT

Implementar 6 mejoras críticas para reducir frustración de usuarios en 40% y aumentar velocidad de interacción en 3x.

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### DÍA 1 (Oct 21) - Items 1, 2, 3, 4 [5 horas]

#### ✅ TAREA 1: Error Messages Contextuales (1h)

**Paso 1:** Localizar validaciones
```bash
grep -r "ValueError\|ValidationError" src/bot/
# → Buscar en: wizard_text_handler.py, callback_handler.py
```

**Paso 2:** Crear módulo de errores
```python
# src/bot/utils/error_messages.py (nuevo)
class ErrorMessages:
    @staticmethod
    def codigo_invalido():
        return (
            "❌ *Código inválido*\n\n"
            "Formato: `TIPO-YYYY-NNN`\n"
            "Ejemplos válidos:\n"
            "• DEN-2025-001 (Denuncia)\n"
            "• INS-2025-042 (Inspección)\n\n"
            "Intenta nuevamente:"
        )
    
    @staticmethod
    def titulo_muy_largo():
        return (
            "❌ *Título muy largo*\n\n"
            "Máximo 100 caracteres, tienes: {actual}\n\n"
            "Sé más conciso. Ejemplo:\n"
            "✅ 'Inspección obra calle 10' (28 chars)\n\n"
            "Intenta de nuevo:"
        )
```

**Paso 3:** Usar en handlers
```python
# src/bot/handlers/wizard_text_handler.py (modificar)
from src.bot.utils.error_messages import ErrorMessages

try:
    validate_task_code(codigo_input)
except ValueError as e:
    await update.message.reply_text(
        ErrorMessages.codigo_invalido(),
        parse_mode="Markdown"
    )
```

**Verificación:**
```bash
# Test: /crear_tarea → escribir "ABC" → debería mostrar mensaje detallado
```

---

#### ✅ TAREA 2: Comando `/ayuda` (1.5h)

**Paso 1:** Crear archivo
```bash
touch src/bot/commands/help.py
```

**Paso 2:** Implementar
```python
# Copiar código de la sección anterior (UX_IMPROVEMENTS_PHASE1.md)
# ~50 líneas de código
```

**Paso 3:** Registrar handlers
```python
# src/bot/main.py (modificar)
from src.bot.commands.help import help_handler, help_handler_en

# En función initialize_handlers():
application.add_handler(help_handler)
application.add_handler(help_handler_en)
```

**Paso 4:** Integrar con menú principal
```python
# src/bot/utils/keyboards.py (modificar main_menu())
keyboard = [
    [InlineKeyboardButton("📋 Crear Tarea", callback_data="menu:crear:start")],
    [InlineKeyboardButton("❓ Ayuda", callback_data="menu:ayuda:general")],  # NEW
    # ... resto
]
```

**Verificación:**
```bash
# Test: /ayuda → debe mostrar menú con 5+ secciones bien formateadas
```

---

#### ✅ TAREA 3: Barra de Progreso (1.5h)

**Paso 1:** Crear función helper
```python
# src/bot/utils/ui_helpers.py (nuevo)
def get_progress_bar(step: int, total: int = 6) -> str:
    """Genera barra visual de progreso con formato."""
    percent = int((step / total) * 100)
    filled = "▰" * step
    empty = "░" * (total - step)
    return f"[Paso {step}/{total}] {filled}{empty} {percent}%"

def format_wizard_header(step: int, title: str) -> str:
    """Header formateado para paso de wizard."""
    progress = get_progress_bar(step)
    return (
        f"📋 *{title}*\n"
        f"{progress}\n"
        f"━━━━━━━━━━━━━━━━━"
    )
```

**Paso 2:** Usar en wizard
```python
# src/bot/handlers/wizard_text_handler.py (modificar cada paso)

async def handle_tipo_tarea(update, context):
    from src.bot.utils.ui_helpers import format_wizard_header
    
    header = format_wizard_header(1, "Crear Nueva Tarea")
    message = (
        f"{header}\n\n"
        f"📝 *Selecciona el tipo:*\n"
        f"... resto del mensaje"
    )
```

**Verificación:**
```bash
# Test: /crear_tarea → cada paso debe mostrar [Paso X/6] con barra
```

---

#### ✅ TAREA 4: Preview + Confirmación (1h)

**Paso 1:** Crear función preview
```python
# src/bot/handlers/wizard_text_handler.py (agregar)

async def show_task_preview(update: Update, context: CallbackContext):
    """Mostrar preview de tarea antes de confirmar."""
    task_data = context.user_data.get('task_in_progress', {})
    
    preview = f"""
📋 *Resumen de Tarea*
━━━━━━━━━━━━━━━━
🔤 *Código:* `{task_data.get('codigo', 'N/A')}`
✏️ *Título:* {task_data.get('titulo', 'N/A')}
📝 *Descripción:* {task_data.get('descripcion', 'N/A')[:80]}...
🏷️ *Tipo:* {task_data.get('tipo', 'N/A')}
⚡ *Prioridad:* {task_data.get('prioridad', 'N/A')}
👥 *Asignados:* {task_data.get('efectivos_count', 0)} personas

*¿Todo correcto?*
    """
    
    keyboard = KeyboardFactory.confirmation("crear_tarea_confirm", task_data.get('codigo', ''))
    await update.message.reply_text(preview, reply_markup=keyboard, parse_mode="Markdown")
```

**Paso 2:** Agregar a flujo
```python
# En callback_handler.py, en callback de paso final:
if data.startswith("crear:confirm"):
    await show_task_preview(update, context)
```

**Verificación:**
```bash
# Test: /crear_tarea → completar todos pasos → debe mostrar preview
```

---

### DÍA 2 (Oct 22) - Items 5, 6 [3 horas]

#### ✅ TAREA 5: Comando `/mis_tareas` (1.5h)

**Paso 1:** Crear archivo
```bash
touch src/bot/commands/mis_tareas.py
```

**Paso 2:** Implementar
```python
# Copiar código de UX_IMPROVEMENTS_PHASE1.md (~45 líneas)
```

**Paso 3:** Registrar
```python
# src/bot/main.py
from src.bot.commands.mis_tareas import mis_tareas_handler

application.add_handler(CommandHandler("mis_tareas", mis_tareas))
application.add_handler(CommandHandler("mytasks", mis_tareas))  # English
```

**Paso 4:** Agregar a menú
```python
# src/bot/utils/keyboards.py (main_menu)
keyboard = [
    [InlineKeyboardButton("📋 Crear Tarea", ...)],
    [InlineKeyboardButton("📊 Mis Tareas", ...)],  # NEW
    # ... resto
]
```

**Verificación:**
```bash
# Test: /mis_tareas → debe listar tareas con emojis de prioridad
# Test: Sin tareas → debe mostrar mensaje de "sin pendientes"
```

---

#### ✅ TAREA 6: Filtros en Dashboard (1.5h)

**Paso 1:** Modificar HTML
```bash
# Editar: dashboard/templates/admin_dashboard.html
# Encontrar: <div class="map-section"> (línea ~50)
# INSERTAR ANTES: Sección de filtros (ver código en UX_IMPROVEMENTS_PHASE1.md)
```

**Paso 2:** Agregar CSS
```html
<!-- Pegar bloque <style> de filter-bar -->
```

**Paso 3:** Implementar funciones JS
```javascript
// dashboard/static/dashboard.js
// Agregar métodos: applyFilters(), clearFilters(), renderTasks()
// (Ver código en UX_IMPROVEMENTS_PHASE1.md)
```

**Paso 4:** Llenar dropdown de usuarios
```javascript
// En initTabs() o init():
async loadUsersForFilter() {
    const users = await this.network.request('/api/v1/users?role=delegado');
    const select = document.getElementById('filterAssigned');
    const json = await users.json();
    json.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.nombre;
        select.appendChild(opt);
    });
}
```

**Verificación:**
```bash
# Test 1: Abrir dashboard → ver filtros debajo del header
# Test 2: Seleccionar estado "finalizada" → solo muestra finalizadas
# Test 3: Seleccionar prioridad "URGENTE" → intersección con estado
# Test 4: Limpiar → vuelven todas
```

---

## 🧪 TESTING PLAN

### Smoke Tests (30 min)

```bash
# TELEGRAM BOT
1. Bot connected: /start → responde
2. Error messages: /crear_tarea → código inválido → mensaje específico
3. Ayuda: /ayuda → menú completo visible
4. Progress: /crear_tarea → cada paso muestra [Paso X/6]
5. Preview: /crear_tarea → completar → preview con datos
6. Mis tareas: /mis_tareas → lista con emojis

# DASHBOARD
7. Filters load: Abrir dashboard → filtros visibles
8. Filter estado: Cambiar a "finalizada" → solo finalizadas
9. Filter prioridad: Seleccionar "URGENTE" → solo urgentes
10. Clear filters: Limpiar → todas las tareas vuelven
```

### User Tests (30 min)

**Con LUIS (Admin):**
- ¿Cuánto tiempo tarda crear tarea? (meta: <1.5 min)
- ¿Progress bar ayuda a no abandonar?
- ¿Preview reduce errores?

**Con CARLOS (Miembro):**
- ¿Recibe notificación cuando lo asignan?
- ¿Encuentra sus tareas con `/mis_tareas`?
- ¿Ayuda es útil?

---

## 📊 MÉTRICAS DE ÉXITO (Post-Implementación)

| Métrica | Anterior | Meta | Instrumento |
|---------|----------|------|-------------|
| Tiempo crear tarea | 3.5 min | 1.5 min | Logging |
| Wizard abandon rate | 35% | 10% | Analytics |
| Error messages clarity | 40% | 90% | User feedback |
| Dashboard search time | 10 min | 2 min | Analytics |
| NPS Bot | - | 35+ | Survey |

---

## 🚀 DEPLOYMENT

### Pre-Deploy Checklist
- [ ] Tests pasan localmente
- [ ] Sin errores en prod logs
- [ ] Cambios documentados en CHANGELOG.md
- [ ] PR crear y mergear a master

### Deploy Steps
```bash
# 1. Commit e push
git add .
git commit -m "feat: UX phase 1 - error messages, help, progress, preview"
git push origin master

# 2. En Fly.io (automático vía GitHub Actions)
# Si manual:
fly deploy --app grupo-gad

# 3. Verificar
curl https://grupo-gad.fly.dev/health
# Debe retornar 200 OK

# 4. Test en producción
# - Abrir bot, /ayuda, /crear_tarea
# - Abrir dashboard, filtrar
```

---

## 📝 CHANGELOG

```markdown
## [1.1.0] - 2025-10-22

### Added
- ✨ Error messages contextuales en validaciones
- ✨ Comando /ayuda con guía completa
- ✨ Barra de progreso en wizard (6 pasos)
- ✨ Preview + confirmación antes de crear tarea
- ✨ Comando /mis_tareas para ver asignaciones
- ✨ Filtros por estado/prioridad en dashboard

### Improved
- 🔧 UX clarity en todos los wizards
- 🔧 Velocidad de creación de tareas (-55%)
- 🔧 Discoverability de funciones

### Fixed
- 🐛 Error messages genéricos
- 🐛 No había ayuda visible
```

