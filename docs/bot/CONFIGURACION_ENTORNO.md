# 🔧 Configuración de Entorno - Bot de Telegram GRUPO_GAD

## 📋 Información General

**Fecha de creación:** 11 de octubre de 2025  
**Autor:** Sistema de Documentación Automática  
**Versión del Bot:** 1.0.0  
**Propósito:** Documentar todas las variables de entorno y configuración necesarias para ejecutar el bot de Telegram.

---

## 🌐 Variables de Entorno Requeridas

### 1. Telegram Bot Configuration

| Variable | Tipo | Requerido | Ejemplo | Descripción |
|----------|------|-----------|---------|-------------|
| `TELEGRAM_TOKEN` | `str` | ✅ Sí | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` | Token del bot obtenido de @BotFather |
| `ADMIN_CHAT_ID` | `str` | ✅ Sí | `123456789` | Chat ID del administrador principal |
| `WHITELIST_IDS` | `List[int]` | ✅ Sí | `[123456789, 987654321]` | Array JSON de IDs de usuarios autorizados |
| `TELEGRAM_WEBHOOK_URL` | `str` | ❌ No | `https://example.com` | URL del webhook (opcional, para modo webhook) |
| `TELEGRAM_WEBHOOK_PATH` | `str` | ❌ No | `/webhook/telegram` | Path del webhook (default: `/webhook/telegram`) |
| `TELEGRAM_WEBHOOK_PORT` | `int` | ❌ No | `8000` | Puerto del webhook (default: 8000) |

#### 🔐 Obtener TELEGRAM_TOKEN

1. Buscar `@BotFather` en Telegram
2. Enviar `/newbot`
3. Seguir instrucciones para nombre y username
4. Copiar el token provisto (formato: `123456:ABC-DEF...`)
5. Guardar en `.env` como `TELEGRAM_TOKEN=<token>`

#### 👤 Obtener ADMIN_CHAT_ID

1. Buscar `@userinfobot` en Telegram
2. Enviar cualquier mensaje
3. Copiar tu `Id` (número que aparece)
4. Guardar en `.env` como `ADMIN_CHAT_ID=<id>`

### 2. API Configuration

| Variable | Tipo | Requerido | Default | Descripción |
|----------|------|-----------|---------|-------------|
| `API_V1_STR` | `str` | ❌ No | `/api/v1` | Prefijo de la API REST |
| `SECRET_KEY` | `str` | ✅ Sí | - | Clave secreta para JWT (mín. 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | ❌ No | `30` | Tiempo de expiración de tokens JWT |

### 3. Database Configuration

| Variable | Tipo | Requerido | Default | Descripción |
|----------|------|-----------|---------|-------------|
| `DATABASE_URL` | `str` | ✅ Sí* | - | URL completa de conexión PostgreSQL |
| `POSTGRES_USER` | `str` | ✅ Sí* | - | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `str` | ✅ Sí* | - | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `str` | ✅ Sí* | - | Nombre de la base de datos |
| `POSTGRES_SERVER` | `str` | ❌ No | `db` | Host del servidor PostgreSQL |
| `POSTGRES_PORT` | `int` | ❌ No | `5432` | Puerto de PostgreSQL |

\* **Nota:** Puedes proveer `DATABASE_URL` completo **O** las variables individuales `POSTGRES_*`. Si provees ambos, `DATABASE_URL` tiene prioridad.

**Formato de DATABASE_URL:**
```
postgresql+asyncpg://usuario:password@host:5432/nombre_db
```

### 4. General Configuration

| Variable | Tipo | Requerido | Default | Descripción |
|----------|------|-----------|---------|-------------|
| `ENVIRONMENT` | `str` | ❌ No | `development` | Entorno de ejecución (`development`, `staging`, `production`) |
| `PROJECT_NAME` | `str` | ❌ No | `GRUPO_GAD` | Nombre del proyecto |
| `PROJECT_VERSION` | `str` | ❌ No | `1.0.0` | Versión del proyecto |
| `DEBUG` | `bool` | ❌ No | `False` | Habilitar modo debug |
| `LOG_LEVEL` | `str` | ❌ No | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `TZ` | `str` | ❌ No | `UTC` | Zona horaria |

---

## 📁 Archivo `.env` de Ejemplo

```bash
# ======================================================================
# GRUPO_GAD - Bot de Telegram - Configuración Local
# ======================================================================

# ------------------------------------------------------------------
# GENERAL
# ------------------------------------------------------------------
ENVIRONMENT=development
LOG_LEVEL=INFO
TZ=America/Guayaquil
PROJECT_NAME=GRUPO_GAD
PROJECT_VERSION=1.0.0
DEBUG=False

# ------------------------------------------------------------------
# TELEGRAM BOT
# ------------------------------------------------------------------
# Obtener de @BotFather
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Obtener de @userinfobot
ADMIN_CHAT_ID=123456789

# Lista de IDs autorizados (formato JSON array)
WHITELIST_IDS='[123456789, 987654321]'

# Webhook (opcional, si no se usa polling)
# TELEGRAM_WEBHOOK_URL=https://mi-servidor.com
# TELEGRAM_WEBHOOK_PATH=/webhook/telegram
# TELEGRAM_WEBHOOK_PORT=8000

# ------------------------------------------------------------------
# API
# ------------------------------------------------------------------
API_V1_STR=/api/v1
SECRET_KEY=CHANGEME_RANDOM_SECRET_KEY_MIN_32_CHARS_SECURE
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------
# Opción 1: URL completa (recomendado)
DATABASE_URL=postgresql+asyncpg://gad_user:secure_password@localhost:5432/grupo_gad_dev

# Opción 2: Variables individuales (alternativo)
# POSTGRES_USER=gad_user
# POSTGRES_PASSWORD=secure_password
# POSTGRES_DB=grupo_gad_dev
# POSTGRES_SERVER=localhost
# POSTGRES_PORT=5432

# ------------------------------------------------------------------
# REDIS (opcional para caching)
# ------------------------------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=

# ------------------------------------------------------------------
# RATE LIMITING
# ------------------------------------------------------------------
RATE_LIMITING_ENABLED=true
```

---

## 🐳 Configuración con Docker Compose

Si ejecutas el bot con Docker Compose, puedes usar el siguiente servicio:

```yaml
version: '3.8'

services:
  bot:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
    container_name: grupogad_bot
    env_file:
      - .env
    environment:
      # Sobrescribir variables si es necesario
      POSTGRES_SERVER: db
      REDIS_HOST: redis
    depends_on:
      - db
      - redis
      - api
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - grupogad_network

  db:
    image: postgis/postgis:15-3.3
    container_name: grupogad_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - grupogad_network

  redis:
    image: redis:7-alpine
    container_name: grupogad_redis
    ports:
      - "6379:6379"
    networks:
      - grupogad_network

networks:
  grupogad_network:
    driver: bridge

volumes:
  postgres_data:
```

---

## 🔍 Validación de Configuración

### Script de Validación

Puedes usar este script Python para validar tu configuración:

```python
#!/usr/bin/env python3
"""
Script de validación de configuración del bot.
Ejecutar: python scripts/validate_config.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def validate_config() -> bool:
    """Valida que todas las configuraciones críticas estén presentes."""
    errors = []
    
    # Validar Telegram
    if not settings.TELEGRAM_TOKEN:
        errors.append("❌ TELEGRAM_TOKEN no está configurado")
    else:
        print(f"✅ TELEGRAM_TOKEN: {settings.TELEGRAM_TOKEN[:10]}...")
    
    if not settings.ADMIN_CHAT_ID:
        errors.append("❌ ADMIN_CHAT_ID no está configurado")
    else:
        print(f"✅ ADMIN_CHAT_ID: {settings.ADMIN_CHAT_ID}")
    
    if not settings.WHITELIST_IDS or len(settings.WHITELIST_IDS) == 0:
        errors.append("⚠️  WHITELIST_IDS está vacío (advertencia)")
    else:
        print(f"✅ WHITELIST_IDS: {len(settings.WHITELIST_IDS)} usuarios autorizados")
    
    # Validar Database
    db_url = settings.assemble_db_url()
    if not db_url:
        errors.append("❌ DATABASE_URL o POSTGRES_* no están configurados correctamente")
    else:
        # Ocultar password en la salida
        safe_url = db_url.split('@')[1] if '@' in db_url else db_url
        print(f"✅ DATABASE_URL: ...@{safe_url}")
    
    # Validar API
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        errors.append("❌ SECRET_KEY debe tener al menos 32 caracteres")
    else:
        print(f"✅ SECRET_KEY: {len(settings.SECRET_KEY)} caracteres")
    
    # Mostrar errores
    if errors:
        print("\n🚨 ERRORES DE CONFIGURACIÓN:")
        for error in errors:
            print(f"   {error}")
        return False
    
    print("\n✅ Configuración válida!")
    return True


if __name__ == "__main__":
    is_valid = validate_config()
    sys.exit(0 if is_valid else 1)
```

### Comando Manual de Validación

```bash
# Validar que las variables están cargadas
python -c "from config.settings import settings; print('✅ Token:', settings.TELEGRAM_TOKEN[:10] if settings.TELEGRAM_TOKEN else '❌ NO CONFIGURADO')"
```

---

## 🔄 Prioridad de Carga de Variables

El sistema carga las variables en el siguiente orden de prioridad (mayor a menor):

1. **Variables de entorno del sistema** (exportadas en el shell)
2. **Archivo `.env`** en el directorio raíz
3. **Valores por defecto** en `config/settings.py`

**Ejemplo:**
```bash
# Archivo .env
DATABASE_URL=postgresql://...

# Al ejecutar, esta variable sobrescribe .env
export DATABASE_URL=postgresql://otra_db
python src/bot/main.py  # Usará postgresql://otra_db
```

---

## 📊 Dependencias de Configuración

```
┌─────────────────────────────────────────────────────────┐
│                  config/settings.py                      │
│                  (Settings Class)                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│ src/bot/      │         │ src/api/     │
│ main.py       │         │ main.py      │
│               │         │              │
│ • token       │         │ • db_url     │
│ • admin_id    │         │ • secret_key │
│ • whitelist   │         │ • cors       │
└───────────────┘         └──────────────┘
```

---

## ⚠️ Consideraciones de Seguridad

### 🔴 CRÍTICO - Producción

1. **Nunca** versionar el archivo `.env` con valores reales
2. **Nunca** compartir `TELEGRAM_TOKEN` públicamente
3. **Rotar** `SECRET_KEY` y `JWT_SECRET_KEY` cada 90 días
4. **Usar** gestores de secretos en producción:
   - Docker Secrets
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
5. **Configurar** `ENVIRONMENT=production` en producción para habilitar seguridad completa

### 🟡 ADVERTENCIA - Desarrollo

1. Usar contraseñas fuertes incluso en desarrollo
2. No usar tokens de producción en desarrollo
3. Mantener `.env.example` actualizado sin valores reales

---

## 🛠️ Troubleshooting

### Error: "TELEGRAM_TOKEN debe estar definida"

**Causa:** La variable `TELEGRAM_TOKEN` no está configurada.

**Solución:**
```bash
# 1. Verificar que existe en .env
grep TELEGRAM_TOKEN .env

# 2. Si no existe, obtener de @BotFather y agregar
echo "TELEGRAM_TOKEN=tu_token_aqui" >> .env

# 3. Si existe pero no se carga, verificar permisos
ls -la .env

# 4. Verificar carga manual
export TELEGRAM_TOKEN=tu_token
python src/bot/main.py
```

### Error: "Can't connect to database"

**Causa:** La URL de base de datos es incorrecta o el servidor no está disponible.

**Solución:**
```bash
# 1. Verificar que PostgreSQL está corriendo
docker ps | grep postgres
# o
sudo systemctl status postgresql

# 2. Probar conexión manualmente
psql -h localhost -p 5432 -U gad_user -d grupo_gad_dev

# 3. Verificar variables
python -c "from config.settings import settings; print(settings.assemble_db_url())"

# 4. Si usas Docker, verificar network
docker network inspect grupogad_network
```

### Error: "ModuleNotFoundError"

**Causa:** Dependencias no instaladas.

**Solución:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# o con Poetry
poetry install

# Verificar instalación
pip list | grep telegram
```

---

## 📚 Referencias

- **Configuración principal:** `config/settings.py`
- **Ejemplo de entorno:** `.env.example`
- **Docker Compose:** `docker-compose.yml`, `docker/Dockerfile.bot`
- **Documentación Telegram Bot API:** https://core.telegram.org/bots/api
- **Pydantic Settings:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

## ✅ Checklist de Configuración Inicial

- [ ] Copiar `.env.example` a `.env`
- [ ] Obtener `TELEGRAM_TOKEN` de @BotFather
- [ ] Obtener `ADMIN_CHAT_ID` de @userinfobot
- [ ] Configurar `WHITELIST_IDS` con IDs autorizados
- [ ] Generar `SECRET_KEY` de 32+ caracteres
- [ ] Configurar `DATABASE_URL` o variables `POSTGRES_*`
- [ ] Ajustar `ENVIRONMENT` según contexto (dev/prod)
- [ ] Configurar zona horaria `TZ` (ejemplo: `America/Guayaquil`)
- [ ] Ejecutar script de validación
- [ ] Probar conexión a base de datos
- [ ] Probar inicio del bot

---

**Última actualización:** 11 de octubre de 2025  
**Mantenedor:** Equipo de Desarrollo GRUPO_GAD
