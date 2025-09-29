# PLAN DE DESPLIEGUE PERSONALIZADO - GRUPO_GAD

## 1. PREPARACIÓN PRE-DESPLIEGUE

### Checklist Completo de Verificación de Código

#### Validación de Código
```bash
# 1. Linting y formateo
ruff check src/ --fix
ruff format src/

# 2. Type checking
mypy src/ config/

# 3. Tests con coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=85

# 4. Security audit
pip-audit -r requirements.txt

# 5. Validar imports
python -c "from src.api.main import app; print('✅ App imports OK')"
```

#### Validación de Configuración
```bash
# 1. Verificar archivos críticos existen
test -f pyproject.toml && echo "✅ pyproject.toml"
test -f alembic.ini && echo "✅ alembic.ini" 
test -f docker/docker-compose.prod.yml && echo "✅ docker-compose.prod.yml"
test -f Caddyfile && echo "✅ Caddyfile"

# 2. Verificar estructura de directorios
ls -la src/api/ src/core/ config/ alembic/

# 3. Validar schema de base de datos
alembic check
```

### Configuraciones Específicas para Producción

#### Optimizaciones de Performance
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
keepalive = 120
timeout = 120
```

#### Configuración de Logging Producción
```python
# config/logging_prod.py
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}'
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/api.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
```

### Variables de Entorno para Producción

#### Template .env.production
```bash
# === CRÍTICAS (CAMBIAR OBLIGATORIAMENTE) ===
SECRET_KEY=tu_clave_secreta_32_caracteres_aqui_2024
DATABASE_URL=postgresql+asyncpg://gad_user:password_seguro@db:5432/gad_db

# === BASE DE DATOS ===
POSTGRES_SERVER=db
POSTGRES_USER=gad_user
POSTGRES_PASSWORD=password_muy_seguro_2024
POSTGRES_DB=gad_db
POSTGRES_PORT=5432

# === APLICACIÓN ===
PROJECT_NAME=GRUPO_GAD
PROJECT_VERSION=1.0.0
API_V1_STR=/api/v1
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === ENTORNO DE PRODUCCIÓN ===
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# === SEGURIDAD Y CORS ===
CORS_ALLOWED_ORIGINS=["https://tu-dominio.com","https://www.tu-dominio.com"]
CORS_ALLOW_CREDENTIALS=true
TRUSTED_PROXY_HOSTS=["localhost","127.0.0.1","172.18.0.1"]

# === LÍMITES Y PERFORMANCE ===
MAX_REQUEST_BODY_SIZE=10485760
WORKERS=4
MAX_CONNECTIONS=1000

# === SSL/TLS ===
FORCE_HTTPS=true
SECURE_COOKIES=true
```

### Scripts de Build Optimizados

#### Script de Build para Producción
```bash
#!/bin/bash
# scripts/build_production.sh
set -e

echo "🔨 Iniciando build de producción..."

# 1. Validar Python version
python_version=$(python3 --version | cut -d' ' -f2)
if [[ ! "$python_version" =~ ^3\.12 ]]; then
    echo "❌ Error: Se requiere Python 3.12+, encontrado: $python_version"
    exit 1
fi

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 3. Generar requirements.lock
echo "🔒 Generando requirements.lock..."
pip freeze > requirements.lock

# 4. Ejecutar tests
echo "🧪 Ejecutando tests..."
pytest --cov=src --cov-fail-under=70 -x

# 5. Linting
echo "🔍 Ejecutando linting..."
ruff check src/ --fix

# 6. Validar configuración
echo "⚙️ Validando configuración..."
python -c "from src.api.main import app; print('✅ Configuración válida')"

# 7. Build Docker image
echo "🐳 Building Docker image..."
docker build -f docker/Dockerfile.api -t grupo_gad_api:latest .

echo "✅ Build completado exitosamente"
```

### Archivos de Exclusión

#### .dockerignore optimizado
```
# Development files
.git
.gitignore
.env
.env.*
!.env.production

# Testing
tests/
pytest.ini
.coverage
htmlcov/

# Documentation
*.md
docs/
!README.md

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/

# Development tools
.vscode/
.idea/
.ruff_cache/
.mypy_cache/

# Logs
logs/
*.log

# Temporary files
tmp/
temp/
.tmp/
```

## 2. ESTRATEGIA DE HOSTING PARA ARGENTINA

### Recomendación Específica: Railway

#### Justificación Técnica
1. **Latencia**: Servidores en región US-West con CDN global (< 200ms desde Argentina)
2. **Base de Datos**: PostgreSQL managed incluido con PostGIS
3. **Docker Native**: Deploy directo desde repo GitHub
4. **Auto-scaling**: Escalado automático basado en CPU/memoria
5. **Monitoreo**: Métricas y logs integrados
6. **SSL**: Certificados automáticos Let's Encrypt
7. **Pricing**: Competitive para Argentina, facturación en USD

#### Alternativas Consideradas
- **Render**: Buena opción, menor performance DB
- **Fly.io**: Excelente latencia, configuración más compleja
- **DigitalOcean App Platform**: Más caro, mejor para empresas
- **Vercel**: No soporta WebSockets long-running

### Configuración Paso a Paso en Railway

#### 1. Setup Inicial
```bash
# Instalar Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Crear proyecto
railway init grupo-gad
```

#### 2. Configuración de Servicios
```yaml
# railway.json
{
  "deploy": {
    "buildCommand": "pip install -r requirements.txt",
    "startCommand": "scripts/start.sh",
    "healthcheckPath": "/api/v1/health",
    "healthcheckTimeout": 300
  }
}
```

#### 3. Variables de Entorno Railway
```bash
# Configurar variables críticas
railway variables set SECRET_KEY=tu_clave_secreta_32_chars
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO

# Database automática (Railway provee)
# POSTGRES_URL se auto-configura
```

#### 4. Deploy Configuration
```dockerfile
# railway.dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Start command
CMD ["scripts/start.sh"]
```

### Costos Estimados Mensuales (USD)

#### Railway Pricing (2024)
- **Hobby Plan**: $5/mes
  - 512MB RAM, 1 vCPU
  - PostgreSQL incluida (1GB)
  - SSL certificado automático
  - 100GB transferencia
  
- **Pro Plan**: $20/mes (recomendado)
  - 2GB RAM, 2 vCPU
  - PostgreSQL (8GB)
  - Métricas avanzadas
  - 500GB transferencia

#### Costos Adicionales Estimados
- **Dominio custom**: $12/año (.com)
- **Monitoring extra**: $0 (incluido)
- **Backups**: $5/mes (recomendado)

**Total mensual estimado**: $25-30 USD

### Límites Plan Gratuito y Cuándo Upgrader

#### Plan Hobby ($5/mes) - Límites
- 512MB RAM (suficiente para inicio)
- 1 vCPU (puede ser lento con >50 usuarios)
- 1GB PostgreSQL (suficiente para MVP)
- Sin métricas avanzadas

#### Señales para Upgrade a Pro
- **Performance**: Response time > 2 segundos consistente
- **Memoria**: Uso > 80% por más de 24h
- **Base de datos**: Uso > 800MB
- **Usuarios concurrentes**: > 50 usuarios activos
- **Necesidad de métricas**: Para debugging avanzado

## 3. PROCESO DE DESPLIEGUE DETALLADO

### Comandos Git Exactos

#### Preparación del Deploy
```bash
# 1. Crear rama de deploy
git checkout -b deploy/production-v1.0.0
git push -u origin deploy/production-v1.0.0

# 2. Validar que todo esté commitado
git status
git diff --cached

# 3. Tag de versión
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0
```

### Configuración de Repositorio para Auto-Deploy

#### GitHub Actions para Railway
```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main, master]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=70
      
      - name: Deploy to Railway
        uses: railway-app/railway-action@v1
        with:
          service: ${{ secrets.RAILWAY_SERVICE_ID }}
          token: ${{ secrets.RAILWAY_TOKEN }}
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Pasos Manuales Necesarios

#### Configuración Inicial de Base de Datos
```bash
# 1. Acceder a Railway dashboard
# 2. Obtener DATABASE_URL desde variables
export DATABASE_URL="postgresql://..."

# 3. Ejecutar migraciones iniciales
alembic upgrade head

# 4. Crear usuario admin inicial (script personalizado)
python scripts/create_admin_user.py
```

### Configuración de Dominio Personalizado

#### En Railway Dashboard
1. Ir a **Settings** → **Domains**
2. Agregar dominio: `tu-dominio.com`
3. Agregar CNAME record en tu DNS:
   ```
   CNAME: www.tu-dominio.com → xxx.railway.app
   ```
4. Esperar propagación DNS (5-30 minutos)

#### Verificación SSL
```bash
# Verificar certificado SSL
curl -I https://tu-dominio.com/api/v1/health
# Debe retornar 200 con headers SSL válidos
```

### Setup de Base de Datos en Producción

#### Script de Inicialización
```python
# scripts/init_production_db.py
import asyncio
from src.core.database import get_db_session
from src.api.crud.crud_usuario import usuario as crud_usuario
from src.schemas.usuario import UsuarioCreate

async def init_admin_user():
    async with get_db_session() as db:
        # Verificar si ya existe admin
        admin = await crud_usuario.get_by_email(db, "admin@grupogad.com")
        if not admin:
            admin_create = UsuarioCreate(
                email="admin@grupogad.com",
                full_name="Administrador",
                password="password_temporal_cambiar"
            )
            admin = await crud_usuario.create(db, obj_in=admin_create)
            print(f"✅ Usuario admin creado: {admin.email}")
        else:
            print("✅ Usuario admin ya existe")

if __name__ == "__main__":
    asyncio.run(init_admin_user())
```

## 4. VERIFICACIÓN POST-DESPLIEGUE

### URLs y Endpoints para Testear
```bash
# 1. Health check básico
curl https://tu-dominio.com/api/v1/health

# 2. API documentation
curl https://tu-dominio.com/docs

# 3. Authentication endpoint
curl -X POST https://tu-dominio.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@grupogad.com","password":"test"}'

# 4. WebSocket endpoint (usar wscat)
wscat -c wss://tu-dominio.com/ws/connect

# 5. Métricas
curl https://tu-dominio.com/metrics
```

### Comandos de Verificación
```bash
# Verificación de servicios Railway
railway status

# Logs en tiempo real
railway logs

# Conexión a base de datos
railway connect postgres
```

### Logs Críticos a Revisar
1. **Startup logs**: Verificar que todos los servicios inicien
2. **Database logs**: Confirmar conexión exitosa
3. **WebSocket logs**: Verificar sistema de eventos
4. **Authentication logs**: Validar JWT funcionando
5. **Health check logs**: Confirmar endpoints responden

### Tests de Funcionalidad Básicos
```python
# tests/production_smoke_test.py
import httpx
import pytest

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://tu-dominio.com/api/v1/health")
        assert response.status_code == 200

@pytest.mark.asyncio  
async def test_docs_accessible():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://tu-dominio.com/docs")
        assert response.status_code == 200
```

## 5. ROLLBACK Y RECOVERY

### Cómo Hacer Rollback
```bash
# 1. Rollback a versión anterior en Railway
railway rollback --to-deployment <deployment-id>

# 2. O rollback via Git
git revert HEAD
git push origin main

# 3. Database rollback (si necesario)
alembic downgrade -1
```

### Backup de Configuraciones
```bash
# Backup de variables de entorno
railway variables > backup_env_$(date +%Y%m%d).txt

# Backup de base de datos (automático en Railway)
# También manual:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Recovery Plan Básico
1. **Verificar el problema**: Logs + métricas
2. **Rollback de aplicación**: Railway dashboard o CLI
3. **Rollback de DB** (si es necesario): Alembic downgrade
4. **Verificar funcionamiento**: Smoke tests
5. **Comunicar status**: A stakeholders
6. **Post-mortem**: Documentar causa y solución

Este plan proporciona una guía completa y ejecutable para el despliegue seguro y confiable del proyecto GRUPO_GAD en producción.