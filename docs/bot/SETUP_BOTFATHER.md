# 🤖 Guía de Setup con @BotFather - Bot GRUPO_GAD

## 📋 Información General

**Fecha de creación:** 11 de octubre de 2025  
**Autor:** Sistema de Documentación Automática  
**Versión del Bot:** 1.0.0  
**Propósito:** Guía paso a paso para crear y configurar el bot de Telegram usando @BotFather.

---

## 🎯 Resumen

Esta guía te ayudará a:
1. ✅ Crear un nuevo bot en Telegram
2. ✅ Obtener el token de autenticación
3. ✅ Configurar comandos del bot
4. ✅ Personalizar nombre y descripción
5. ✅ Configurar foto de perfil (opcional)
6. ✅ Probar el bot localmente

**Tiempo estimado:** 15-20 minutos

---

## 📱 Paso 1: Crear el Bot con @BotFather

### 1.1 Abrir @BotFather

1. Abre Telegram en tu dispositivo (móvil o escritorio)
2. En la barra de búsqueda, escribe: `@BotFather`
3. Selecciona el bot verificado (tiene una marca azul ✓)
4. Presiona **START** o envía `/start`

**Screenshot de referencia:**
```
┌─────────────────────────────────────────┐
│ @BotFather                        ✓     │
├─────────────────────────────────────────┤
│ I can help you create and manage       │
│ Telegram bots. If you're new to bots,  │
│ take a look at the /help command.      │
│                                         │
│ Available commands:                     │
│ /newbot - create a new bot              │
│ /mybots - edit your bots                │
│ ...                                     │
└─────────────────────────────────────────┘
```

### 1.2 Crear Nuevo Bot

1. Envía el comando: `/newbot`
2. @BotFather te pedirá un **nombre** para tu bot

**Diálogo:**
```
BotFather:
Alright, a new bot. How are we going to call it? 
Please choose a name for your bot.

Tú:
GAD Bot
```

**Notas:**
- El **nombre** puede contener espacios
- Puede ser cualquier texto descriptivo
- Ejemplo: `GAD Bot`, `GRUPO_GAD Bot`, `Sistema GAD`

3. @BotFather te pedirá un **username** para tu bot

**Diálogo:**
```
BotFather:
Good. Now let's choose a username for your bot. 
It must end in `bot`. Like this, for example: 
TetrisBot or tetris_bot.

Tú:
grupogad_bot
```

**Requisitos del username:**
- ✅ Debe terminar en `bot` o `_bot`
- ✅ Solo letras, números y guiones bajos
- ✅ Debe ser único (no estar tomado)
- ❌ No puede contener espacios
- ❌ No puede contener caracteres especiales

**Ejemplos válidos:**
- `grupogad_bot`
- `gad_sistema_bot`
- `GrupoGADBot`
- `gadbot`

### 1.3 Obtener el Token

Si el username está disponible, @BotFather te responderá con:

```
BotFather:
Done! Congratulations on your new bot. You will 
find it at t.me/grupogad_bot. You can now add a 
description, about section and profile picture 
for your bot, see /help for a list of commands. 
By the way, when you've finished creating your 
cool bot, ping our Bot Support if you want a 
better username for it. Just make sure the bot 
is fully operational before you do this.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

Keep your token secure and store it safely, it 
can be used by anyone to control your bot.

For a description of the Bot API, see this page: 
https://core.telegram.org/bots/api
```

**🔐 TOKEN CRÍTICO:**
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

**⚠️ IMPORTANTE - SEGURIDAD:**
- ❌ **NUNCA** compartas este token públicamente
- ❌ **NUNCA** lo subas a GitHub sin proteger
- ✅ Guárdalo inmediatamente en tu archivo `.env`
- ✅ Trata este token como una contraseña

### 1.4 Guardar el Token

Copia el token y guárdalo en tu archivo `.env`:

```bash
# Abrir .env con tu editor favorito
nano .env
# o
vim .env
# o
code .env
```

Agregar la línea:
```bash
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

Guardar y cerrar el archivo.

---

## ⚙️ Paso 2: Configurar Comandos del Bot

### 2.1 Abrir Configuración de Comandos

1. En @BotFather, envía: `/mybots`
2. Selecciona tu bot de la lista: `@grupogad_bot`
3. Presiona el botón: **Edit Bot**
4. Presiona el botón: **Edit Commands**

**Diálogo:**
```
BotFather:
Send me a list of commands for your bot. 
Please use this format:

command1 - Description
command2 - Another description
```

### 2.2 Configurar Lista de Comandos

Copia y pega la siguiente lista de comandos:

```
start - 🏠 Mostrar menú principal
crear - ➕ Crear nueva tarea
finalizar - ✅ Finalizar una tarea
ayuda - ❓ Mostrar ayuda
```

**Explicación de comandos:**

| Comando | Descripción | Funcionalidad |
|---------|-------------|---------------|
| `/start` | Mostrar menú principal | Inicia el bot y muestra el menú interactivo con botones |
| `/crear` | Crear nueva tarea | Inicia el wizard de creación de tareas (Fase 2) |
| `/finalizar` | Finalizar tarea | Muestra lista paginada de tareas pendientes para finalizar (Fase 3) |
| `/ayuda` | Mostrar ayuda | Muestra información de ayuda sobre el uso del bot |

**Screenshot de referencia:**
```
┌─────────────────────────────────────────┐
│ @BotFather                        ✓     │
├─────────────────────────────────────────┤
│ Success! Command list updated.          │
│ /help - send commands again             │
└─────────────────────────────────────────┘
```

### 2.3 Verificar Comandos

Para verificar que los comandos se guardaron correctamente:

1. Abre tu bot (`@grupogad_bot`)
2. Escribe `/` en el campo de texto
3. Deberías ver la lista de comandos disponibles

**Vista en Telegram:**
```
┌─────────────────────────────────────────┐
│ /start - 🏠 Mostrar menú principal      │
│ /crear - ➕ Crear nueva tarea           │
│ /finalizar - ✅ Finalizar una tarea     │
│ /ayuda - ❓ Mostrar ayuda               │
└─────────────────────────────────────────┘
```

---

## 🎨 Paso 3: Personalizar el Bot (Opcional)

### 3.1 Configurar Descripción

1. En @BotFather, envía: `/mybots`
2. Selecciona tu bot: `@grupogad_bot`
3. Presiona: **Edit Bot** → **Edit Description**
4. Envía la descripción:

```
🤖 Bot oficial del Sistema GRUPO_GAD

Sistema de Gestión Administrativa Gubernamental para el manejo eficiente de tareas operativas y administrativas.

Funcionalidades:
✅ Crear tareas con asignación de responsables
✅ Seguimiento de tareas pendientes
✅ Finalización con confirmación
✅ Interfaz interactiva con botones

Desarrollado por: Equipo de Desarrollo GRUPO_GAD
Versión: 1.0.0
```

### 3.2 Configurar "About" (Acerca de)

1. En @BotFather: **Edit Bot** → **Edit About**
2. Envía el texto corto (máximo 120 caracteres):

```
Sistema de Gestión de Tareas para Personal Gubernamental. Versión 1.0.0
```

### 3.3 Configurar Foto de Perfil

1. En @BotFather: **Edit Bot** → **Edit Botpic**
2. Envía una imagen cuadrada (recomendado: 512x512 px)
3. Formatos aceptados: JPG, PNG

**Recomendaciones de diseño:**
- Usar colores corporativos del GRUPO_GAD
- Incluir ícono representativo (escudo, logo institucional)
- Fondo sólido o degradado simple
- Evitar texto pequeño (no se lee bien)

**Herramientas para crear imagen:**
- Canva: https://www.canva.com/
- Figma: https://www.figma.com/
- GIMP (gratuito): https://www.gimp.org/

---

## 👤 Paso 4: Obtener Chat ID del Administrador

Para configurar `ADMIN_CHAT_ID`, necesitas tu Chat ID personal:

### 4.1 Método 1: Usar @userinfobot

1. Busca `@userinfobot` en Telegram
2. Presiona **START**
3. Envía cualquier mensaje (ejemplo: `hola`)
4. El bot te responderá con tu información:

```
@userinfobot:
Id: 123456789
First name: Juan
Username: @juanperez
```

Tu `ADMIN_CHAT_ID` es: `123456789`

### 4.2 Método 2: Usar tu propio bot (requiere bot corriendo)

1. Ejecuta el bot localmente (ver Paso 5)
2. Envía `/start` a tu bot
3. Revisa los logs del bot:

```bash
tail -f logs/bot.log
```

Verás algo como:
```
User ID: 123456789 | Message: /start
```

### 4.3 Guardar en .env

Agregar a `.env`:
```bash
ADMIN_CHAT_ID=123456789
```

---

## 🚀 Paso 5: Probar el Bot Localmente

### 5.1 Verificar Configuración

```bash
# Verificar que las variables están configuradas
cat .env | grep TELEGRAM
```

Debe mostrar:
```bash
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
ADMIN_CHAT_ID=123456789
WHITELIST_IDS='[123456789]'
```

### 5.2 Ejecutar el Bot

**Opción A: Python directo**
```bash
# Desde el directorio raíz del proyecto
python src/bot/main.py
```

**Opción B: Docker Compose**
```bash
docker compose up bot
```

**Output esperado:**
```
2025-10-11 10:30:00 | INFO     | src.bot.main:main:40 - Iniciando el bot...
2025-10-11 10:30:01 | INFO     | src.bot.main:main:49 - Bot iniciado y escuchando...
```

### 5.3 Probar Comandos

En Telegram, abre tu bot y prueba:

1. **Comando /start**
   - Envía: `/start`
   - Esperas: Mensaje de bienvenida con botones interactivos

2. **Botón "📝 Nueva Tarea"**
   - Presiona el botón
   - Esperas: Inicio del wizard de creación

3. **Comando /crear**
   - Envía: `/crear`
   - Esperas: Inicio del wizard de creación

4. **Comando /finalizar**
   - Envía: `/finalizar`
   - Esperas: Lista de tareas pendientes (puede estar vacía)

5. **Comando /ayuda**
   - Envía: `/ayuda`
   - Esperas: Mensaje con información de ayuda

### 5.4 Verificar Logs

```bash
# Ver logs en tiempo real
tail -f logs/bot.log

# Ver últimas 50 líneas
tail -50 logs/bot.log

# Buscar errores
grep ERROR logs/bot.log
```

---

## 🔧 Troubleshooting

### Problema: "Error: La variable de entorno TELEGRAM_TOKEN debe estar definida"

**Causa:** El token no está en `.env` o no se está cargando.

**Solución:**
```bash
# 1. Verificar que existe en .env
grep TELEGRAM_TOKEN .env

# 2. Si no existe, agregarlo
echo "TELEGRAM_TOKEN=tu_token_aqui" >> .env

# 3. Si existe, exportar manualmente
export TELEGRAM_TOKEN=$(grep TELEGRAM_TOKEN .env | cut -d '=' -f2)
python src/bot/main.py
```

### Problema: "Unauthorized" o "401"

**Causa:** El token es inválido o fue revocado.

**Solución:**
1. Verificar que el token en `.env` es correcto (sin espacios extra)
2. Si copiaste mal, volver a @BotFather:
   - Envía `/mybots`
   - Selecciona tu bot
   - Presiona **API Token**
   - Copia nuevamente el token

### Problema: El bot no responde

**Posibles causas y soluciones:**

1. **Bot no está corriendo:**
   ```bash
   ps aux | grep "python src/bot/main.py"
   # Si no aparece, ejecutar: python src/bot/main.py
   ```

2. **Firewall bloqueando conexión:**
   ```bash
   # Probar conexión a Telegram API
   curl https://api.telegram.org/bot<TU_TOKEN>/getMe
   ```

3. **Red corporativa con proxy:**
   ```bash
   # Configurar proxy en requests (modificar api_service.py)
   proxies = {
       'http': 'http://proxy.empresa.com:8080',
       'https': 'http://proxy.empresa.com:8080',
   }
   response = requests.get(url, proxies=proxies)
   ```

### Problema: Comandos no aparecen al escribir /

**Causa:** Los comandos no se configuraron correctamente en @BotFather.

**Solución:**
1. Volver a @BotFather
2. `/mybots` → Seleccionar bot → **Edit Commands**
3. Reenviar la lista de comandos (ver Paso 2.2)
4. Reiniciar el cliente de Telegram

---

## 🔒 Seguridad y Mejores Prácticas

### 🔴 Crítico

1. **Nunca compartir el token:**
   - ❌ No publicar en GitHub
   - ❌ No compartir en Slack/Discord
   - ❌ No enviar por email sin cifrar

2. **Rotar el token si se compromete:**
   - En @BotFather: `/mybots` → Bot → **API Token** → **Revoke current token**
   - Actualizar `.env` con el nuevo token
   - Reiniciar el bot

3. **Configurar Whitelist:**
   ```bash
   # Solo usuarios autorizados pueden usar el bot
   WHITELIST_IDS='[123456789, 987654321, 111222333]'
   ```

### 🟡 Recomendaciones

1. **Usar variables de entorno en producción:**
   - No usar `.env` directamente
   - Usar Docker Secrets, AWS Secrets Manager, etc.

2. **Logs seguros:**
   - No loggear tokens
   - No loggear datos sensibles de usuarios

3. **Rate limiting:**
   - Implementar límite de mensajes por usuario
   - Prevenir abuso/spam

---

## 📚 Comandos Útiles de @BotFather

| Comando | Descripción |
|---------|-------------|
| `/mybots` | Ver y editar tus bots |
| `/newbot` | Crear nuevo bot |
| `/setname` | Cambiar nombre del bot |
| `/setdescription` | Cambiar descripción |
| `/setabouttext` | Cambiar "about" |
| `/setuserpic` | Cambiar foto de perfil |
| `/setcommands` | Configurar comandos |
| `/deletebot` | Eliminar bot (permanente) |
| `/revoke` | Revocar token actual |

---

## ✅ Checklist Final

- [ ] Bot creado en @BotFather
- [ ] Token guardado en `.env`
- [ ] Comandos configurados (/start, /crear, /finalizar, /ayuda)
- [ ] Descripción configurada
- [ ] About configurado
- [ ] Foto de perfil configurada (opcional)
- [ ] ADMIN_CHAT_ID obtenido y guardado
- [ ] WHITELIST_IDS configurado
- [ ] Bot probado localmente con `/start`
- [ ] Wizard de creación funcionando
- [ ] Finalizar tarea funcionando
- [ ] Logs sin errores críticos

---

## 📞 Soporte

**Documentación oficial de Telegram:**
- Bot API: https://core.telegram.org/bots/api
- BotFather: https://core.telegram.org/bots#botfather

**Contacto interno:**
- Equipo de Desarrollo: dev@grupogad.gob.ec
- Slack: #grupo-gad-support

---

**Última actualización:** 11 de octubre de 2025  
**Mantenedor:** Equipo de Desarrollo GRUPO_GAD

**Próximos pasos:**
- Ver: `docs/bot/TESTING_MANUAL_COMPLETO.md` para validar todas las funcionalidades
- Ver: `docs/bot/CONFIGURACION_ENTORNO.md` para configuración avanzada
