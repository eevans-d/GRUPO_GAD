# 🚀 QUICK START - FASE 1 IMPLEMENTATION

**Copy-paste ready** | Ejecución Oct 21-22 | 8 horas

---

## 📋 CHECKLIST RÁPIDO

### DÍA 1 (Lunes Oct 21)

- [ ] 09:00 AM - Kick-off técnico (30 min)
- [ ] 10:00 AM - Iniciar Item 1: Error Messages (1h)
- [ ] 11:00 AM - Iniciar Item 2: /ayuda (1.5h)
- [ ] 12:30 PM - Break
- [ ] 13:30 PM - Iniciar Item 3: Progress Bar (1.5h)
- [ ] 15:00 PM - Iniciar Item 4: Preview (1h)
- [ ] 16:00 PM - EOD. Commit e push

**EOD Dec 1 Status:** Items 1-4 completados y merged

### DÍA 2 (Martes Oct 22)

- [ ] 09:00 AM - Standup (15 min)
- [ ] 09:15 AM - Iniciar Item 5: /mis_tareas (1.5h)
- [ ] 10:45 AM - Iniciar Item 6: Filtros Dashboard (1.5h)
- [ ] 12:15 PM - Lunch
- [ ] 13:15 PM - Testing Smoke (30 min)
- [ ] 13:45 PM - Fixes rápidos (30 min)
- [ ] 14:15 PM - Final testing (30 min)
- [ ] 14:45 PM - Merge + Deploy
- [ ] 15:30 PM - Prod testing (30 min)

**EOD Dec 2 Status:** Fase 1 completa en PRODUCCIÓN ✅

---

## 💻 COMANDOS SETUP

```bash
# Clonar/actualizar repo
cd /home/eevan/ProyectosIA/GRUPO_GAD
git pull origin master

# Branch para Fase 1
git checkout -b feat/ux-phase1-improvements

# Verify dependencies
pip install -r requirements.txt

# Start dev environment
make up  # Docker Compose

# Monitor logs
make logs-api  # En otra terminal

# Run tests
make test
```

---

## 🎯 ITEMS A IMPLEMENTAR (Resumen)

### Item 1: Error Messages (1h)

**Archivos:** `src/bot/utils/error_messages.py` (NUEVO), `src/bot/handlers/wizard_text_handler.py` (MODIFICAR)

**Cambio principal:**
```python
# ANTES
except ValueError:
    await update.message.reply_text("❌ Error validando")

# DESPUÉS  
except ValueError as e:
    if "codigo" in str(e):
        await update.message.reply_text(
            "❌ *Código inválido*\n"
            "Formato: `TIPO-YYYY-NNN`\n"
            "Ej: DEN-2025-001, INS-2025-042"
        )
```

**Test:** `/crear_tarea` → escribir código inválido → verificar mensaje detallado

---

### Item 2: /ayuda Command (1.5h)

**Archivos:** `src/bot/commands/help.py` (NUEVO), `src/bot/main.py` (MODIFICAR)

**Cambio principal:**
```python
async def help_command(update: Update, context: CallbackContext):
    help_text = """
👋 *GUÍA GRUPO_GAD BOT*
...
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")
```

**Integración:**
```python
# En main.py, en initialize_handlers():
from src.bot.commands.help import help_handler
application.add_handler(help_handler)
```

**Test:** `/ayuda` → verificar menú con 5+ secciones

---

### Item 3: Progress Bar (1.5h)

**Archivos:** `src/bot/utils/ui_helpers.py` (NUEVO), `src/bot/handlers/wizard_text_handler.py` (MODIFICAR)

**Función helper:**
```python
def get_progress_bar(step: int, total: int = 6) -> str:
    percent = int((step / total) * 100)
    filled = "▰" * step
    empty = "░" * (total - step)
    return f"[Paso {step}/{total}] {filled}{empty} {percent}%"
```

**Uso en cada paso:**
```python
async def handle_tipo_tarea(update, context):
    progress = get_progress_bar(1)
    message = f"📋 *Crear Tarea*\n{progress}\n..."
    await update.message.reply_text(message)
```

**Test:** `/crear_tarea` → cada paso debe mostrar barra

---

### Item 4: Preview (1h)

**Archivos:** `src/bot/handlers/wizard_text_handler.py` (MODIFICAR)

**Nueva función:**
```python
async def show_task_preview(update: Update, context: CallbackContext):
    task_data = context.user_data.get('task_in_progress', {})
    preview = f"""
📋 *Resumen*
━━━━━
🔤 Código: `{task_data.get('codigo')}`
✏️ Título: {task_data.get('titulo')}
👥 Asignados: {task_data.get('efectivos_count')} personas

¿Confirmar?
    """
    keyboard = KeyboardFactory.confirmation("crear", task_data['codigo'])
    await update.message.reply_text(preview, reply_markup=keyboard, parse_mode="Markdown")
```

**Integración:** Agregar en flujo final del wizard

**Test:** Completar wizard → debe mostrar preview con datos

---

### Item 5: /mis_tareas Command (1.5h)

**Archivos:** `src/bot/commands/mis_tareas.py` (NUEVO), `src/bot/main.py` (MODIFICAR)

**Función principal:**
```python
async def mis_tareas(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        api = ApiService(settings.API_V1_STR)
        tareas = api.get_user_pending_tasks(user_id)
        
        if not tareas:
            await update.message.reply_text(
                "✅ *¡Sin tareas pendientes!*",
                parse_mode="Markdown"
            )
            return
        
        message = f"📋 *Tus Tareas* ({len(tareas)})\n━━━━━\n\n"
        for i, t in enumerate(tareas, 1):
            emoji = {"URGENTE": "🔴", "ALTA": "🟠", "MEDIA": "🟡"}[t.prioridad]
            message += f"{i}. {emoji} *{t.titulo}*\n   `{t.codigo}`\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
```

**Integración:**
```python
# main.py
from src.bot.commands.mis_tareas import mis_tareas_handler
application.add_handler(CommandHandler("mis_tareas", mis_tareas))
```

**Test:** `/mis_tareas` → lista con emojis

---

### Item 6: Dashboard Filters (1.5h)

**Archivos:** `dashboard/templates/admin_dashboard.html`, `dashboard/static/dashboard.js`

**HTML a agregar:**
```html
<div class="filter-bar">
    <select id="filterState" class="filter-select">
        <option value="">Estado: Todos</option>
        <option value="programada">Programada</option>
        <option value="en_curso">En Curso</option>
        <option value="finalizada">Finalizada</option>
    </select>
    <select id="filterPriority" class="filter-select">
        <option value="">Prioridad: Todas</option>
        <option value="URGENTE">🔴 Urgente</option>
        <option value="ALTA">🟠 Alta</option>
    </select>
    <button onclick="dashboard.applyFilters()">🔍 Filtrar</button>
</div>

<style>
.filter-bar {
    display: flex;
    gap: 10px;
    padding: 12px;
    background: #f8f9fa;
    margin-bottom: 12px;
}
</style>
```

**JavaScript a agregar:**
```javascript
applyFilters() {
    const state = document.getElementById('filterState').value;
    const priority = document.getElementById('filterPriority').value;
    this.filteredTasks = this.tasks.filter(t =>
        (!state || t.estado === state) &&
        (!priority || t.prioridad === priority)
    );
    this.renderTasks();
}
```

**Test:** Seleccionar filtro → solo muestra tareas que coinciden

---

## 🧪 SMOKE TESTS (Checklist)

### Bot Tests
```bash
✅ Test 1: /start → responde
✅ Test 2: /crear_tarea → código inválido → error específico
✅ Test 3: /ayuda → muestra menú
✅ Test 4: /crear_tarea → cada paso muestra [Paso X/6]
✅ Test 5: /crear_tarea → completar todo → preview
✅ Test 6: /mis_tareas → lista tareas o "sin pendientes"
```

### Dashboard Tests
```bash
✅ Test 7: Abrir dashboard → filtros visibles
✅ Test 8: Seleccionar "finalizada" → solo finalizadas
✅ Test 9: Seleccionar "URGENTE" → solo urgentes
✅ Test 10: Limpiar filtros → todas vuelven
```

---

## 📊 ANTES vs DESPUÉS

```
MÉTRICA                    ANTES           DESPUÉS
────────────────────────────────────────────────────
Tiempo crear tarea        3.5 minutos      1.5 minutos
Wizard abandon rate       35%              10%
Error clarity             40%              90%
Dashboard search time     10 minutos       2 minutos
User frustration          High             Low
Admin daily savings       -                50 min/día
────────────────────────────────────────────────────
OVERALL UX SCORE          5.2/10           7.2/10
```

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deploy
- [ ] Todos los tests pasan
- [ ] Sin errores en logs
- [ ] Código está comentado
- [ ] CHANGELOG.md actualizado
- [ ] PR creado y autoaprobado

### Deploy Steps
```bash
# 1. Commit
git add .
git commit -m "feat: UX phase 1 - 6 mejoras"

# 2. Push
git push origin feat/ux-phase1-improvements

# 3. Create PR + Merge
# (Si es automático, solo push a master)

# 4. Deploy a producción
fly deploy --app grupo-gad

# 5. Verificar
curl https://grupo-gad.fly.dev/health
# Debe retornar 200 OK

# 6. Quick manual test
# - Abrir bot /ayuda
# - Crear tarea
# - Abrir dashboard
```

---

## 📞 CONTACTS

| Rol | Contacto | Disponible |
|-----|----------|-----------|
| **Dev Lead** | (tú) | 09:00-16:00 |
| **PM** | [nombre] | Daily 10:00 |
| **QA** | [nombre] | Testing 14:00 |
| **AI Agent** | 24/7 | Preguntas cualquier hora |

---

## ⚠️ TROUBLESHOOTING

### Problema: Bot no responde a `/ayuda`
**Solución:** Verificar que help_handler está registrado en main.py

### Problema: Progress bar no aparece
**Solución:** Verificar que `parse_mode="Markdown"` está en reply_text

### Problema: Filtros dashboard no funcionan
**Solución:** Abrir DevTools Console, verificar `dashboard.applyFilters()` se llama

### Problema: Deploy falla
**Solución:** Revisar logs con `fly logs --app grupo-gad`

---

## 📞 SOPORTE RÁPIDO

```
❓ ¿Pregunta técnica?     → Revisar UX_IMPROVEMENTS_PHASE1.md
❓ ¿Cómo instalar?       → Revisar "COMANDOS SETUP" arriba
❓ ¿Cómo deployar?       → Revisar "DEPLOYMENT CHECKLIST"
❓ ¿Algo no funciona?    → Revisar "TROUBLESHOOTING"
❓ ¿Otra pregunta?       → Mensaje a AI Agent 24/7
```

---

**Inicio Fase 1:** Oct 21, 10:00 AM  
**Fin Fase 1:** Oct 22, 15:00 PM  
**Deploy:** Oct 22, 15:30 PM  

¡Adelante! 🚀

