# CONFIGURACIONES DE PRODUCCIÓN ESPECÍFICAS - GRUPO_GAD

## 1. VARIABLES DE ENTORNO COMPLETAS

### Lista Exhaustiva de Variables ENV

#### Variables Críticas (OBLIGATORIAS)
```bash
# === SEGURIDAD CRÍTICA ===
SECRET_KEY=tu_clave_secreta_minimo_32_caracteres_2024
# Propósito: Firma JWT tokens y encriptación de sesiones
# Generar con: openssl rand -hex 32

# === BASE DE DATOS ===
DATABASE_URL=postgresql+asyncpg://gad_user:password_seguro@db:5432/gad_db
# Propósito: Conexión principal a PostgreSQL
# Prioridad: 1. DATABASE_URL, 2. DB_URL (legacy), 3. Componentes POSTGRES_*
```

#### Variables de Base de Datos
```bash
POSTGRES_SERVER=db
# Propósito: Hostname del servidor PostgreSQL
# Valores: 'db' (Docker), 'localhost' (local), IP/hostname (remoto)

POSTGRES_USER=gad_user
# Propósito: Usuario de base de datos
# Recomendado: Crear usuario específico, no usar 'postgres'

POSTGRES_PASSWORD=password_muy_seguro_cambiar_2024
# Propósito: Contraseña del usuario de BD
# Requisitos: Mínimo 12 caracteres, incluir números y símbolos

POSTGRES_DB=gad_db
# Propósito: Nombre de la base de datos
# Nota: Debe existir antes del primer deploy

POSTGRES_PORT=5432
# Propósito: Puerto de conexión PostgreSQL
# Valor por defecto: 5432
```

#### Variables de Aplicación
```bash
PROJECT_NAME=GRUPO_GAD
# Propósito: Nombre mostrado en docs y logs
# Valor fijo para producción

PROJECT_VERSION=1.0.0
# Propósito: Versión de la aplicación
# Actualizar con cada release

API_V1_STR=/api/v1
# Propósito: Prefijo para todas las rutas de API
# No cambiar en producción (breaking change)

ACCESS_TOKEN_EXPIRE_MINUTES=30
# Propósito: Tiempo de vida de tokens JWT
# Balance entre seguridad y UX
```

#### Variables de Entorno y Debug
```bash
ENVIRONMENT=production
# Propósito: Configura comportamiento por entorno
# Valores: development, staging, production
# Afecta: logging, JWT validation, CORS

LOG_LEVEL=INFO
# Propósito: Nivel de logging
# Valores: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Producción: INFO o WARNING

DEBUG=false
# Propósito: Habilita modo debug de FastAPI
# SIEMPRE false en producción
```

#### Variables de Seguridad y CORS
```bash
CORS_ALLOWED_ORIGINS=["https://tu-dominio.com","https://www.tu-dominio.com"]
# Propósito: Orígenes permitidos para CORS
# Formato: Lista JSON de strings
# NUNCA usar "*" en producción

CORS_ALLOW_CREDENTIALS=true
# Propósito: Permitir cookies en requests CORS
# Requerido para autenticación con cookies HttpOnly

TRUSTED_PROXY_HOSTS=["localhost","127.0.0.1","172.18.0.1"]
# Propósito: IPs de proxies confiables para headers X-Forwarded-*
# Incluir: Load balancer, Reverse proxy, Container network
```

#### Variables de Performance y Límites
```bash
MAX_REQUEST_BODY_SIZE=10485760
# Propósito: Límite de tamaño de request body (bytes)
# Valor: 10MB por defecto
# Previene: Ataques DoS con requests grandes

WORKERS=4
# Propósito: Número de workers Gunicorn
# Cálculo: (2 x CPU cores) + 1
# Ajustar según recursos disponibles

MAX_CONNECTIONS=1000
# Propósito: Conexiones concurrentes por worker
# Balance entre memory usage y throughput
```

### Valores de Ejemplo Seguros

#### Template .env.production Completo
```bash
# =====================================================
# GRUPO_GAD - CONFIGURACIÓN DE PRODUCCIÓN
# =====================================================
# ⚠️  NUNCA commitear este archivo con valores reales
# =====================================================

# === SEGURIDAD CRÍTICA (CAMBIAR OBLIGATORIAMENTE) ===
SECRET_KEY=generar_con_openssl_rand_hex_32_aqui
DATABASE_URL=postgresql+asyncpg://gad_user:password_aqui@db:5432/gad_db

# === BASE DE DATOS ===
POSTGRES_SERVER=db
POSTGRES_USER=gad_user
POSTGRES_PASSWORD=password_seguro_cambiar_2024
POSTGRES_DB=gad_db
POSTGRES_PORT=5432

# === APLICACIÓN ===
PROJECT_NAME=GRUPO_GAD
PROJECT_VERSION=1.0.0
API_V1_STR=/api/v1
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === ENTORNO ===
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# === SEGURIDAD Y CORS ===
CORS_ALLOWED_ORIGINS=["https://tu-dominio.com","https://www.tu-dominio.com","https://api.tu-dominio.com"]
CORS_ALLOW_CREDENTIALS=true
TRUSTED_PROXY_HOSTS=["localhost","127.0.0.1","172.18.0.1","10.0.0.0/8"]

# === PERFORMANCE ===
MAX_REQUEST_BODY_SIZE=10485760
WORKERS=4
MAX_CONNECTIONS=1000

# === SSL/TLS (Opcional) ===
FORCE_HTTPS=true
SECURE_COOKIES=true
HSTS_MAX_AGE=31536000

# === MONITOREO (Opcional) ===
ENABLE_METRICS=true
METRICS_PATH=/metrics
HEALTH_CHECK_PATH=/api/v1/health

# === WEBSOCKETS (Opcional) ===
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_MESSAGE_MAX_SIZE=1048576
```

### Variables Específicas por Entorno

#### Development
```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./dev.db
LOG_LEVEL=DEBUG
CORS_ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/gad_staging
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=["https://staging.tu-dominio.com"]
```

#### Production
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/gad_prod
LOG_LEVEL=WARNING
CORS_ALLOWED_ORIGINS=["https://tu-dominio.com"]
```

## 2. CONFIGURACIÓN DE BASE DE DATOS

### Connection String para Producción
```python
# Configuración optimizada para producción
DATABASE_CONFIG = {
    # Connection string con parámetros de optimización
    "url": "postgresql+asyncpg://user:pass@host:5432/db?ssl=require&pool_size=20&max_overflow=0",
    
    # Configuración de pool de conexiones
    "pool_size": 20,          # Conexiones en pool
    "max_overflow": 10,       # Conexiones adicionales permitidas
    "pool_timeout": 30,       # Timeout para obtener conexión
    "pool_recycle": 3600,     # Reciclar conexiones cada hora
    "pool_pre_ping": True,    # Verificar conexiones antes de usar
}
```

### Configuración de Connection Pooling
```python
# src/core/database.py - Configuración de producción
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Engine con configuración optimizada
async_engine = create_async_engine(
    DATABASE_URL,
    # Pool settings para producción
    pool_size=20,              # Conexiones permanentes
    max_overflow=10,           # Conexiones adicionales bajo load
    pool_timeout=30,           # Timeout para obtener conexión (segundos)
    pool_recycle=3600,         # Reciclar conexiones cada hora
    pool_pre_ping=True,        # Health check antes de usar conexión
    
    # Async settings
    echo=False,                # No logging SQL en producción
    future=True,               # SQLAlchemy 2.0 style
    
    # Connection arguments
    connect_args={
        "ssl": "require",      # Forzar SSL
        "command_timeout": 60, # Timeout para comandos
        "server_settings": {
            "jit": "off",      # Disable JIT para predictabilidad
        },
    },
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
```

### Migrations para Producción
```python
# alembic/env.py - Configuración de producción
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Configuración para producción
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Configuración específica para producción
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    # Configuración de conexión para migrations
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pool para migrations
        future=True,
    )

    async def do_run_migrations(connection: Connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Para SQLite compatibility en tests
        )

        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(do_run_migrations_with_connection(connectable))
```

### Seeds y Data Inicial
```python
# scripts/seed_production_data.py
import asyncio
from src.core.database import get_db_session
from src.api.crud.crud_usuario import usuario as crud_usuario
from src.schemas.usuario import UsuarioCreate

async def seed_initial_data():
    """Crear datos iniciales para producción"""
    async with get_db_session() as db:
        # Crear usuario admin si no existe
        admin_email = "admin@grupogad.com"
        admin = await crud_usuario.get_by_email(db, admin_email)
        
        if not admin:
            admin_data = UsuarioCreate(
                email=admin_email,
                full_name="Administrador Sistema",
                password="cambiar_en_primer_login_2024",
                is_active=True,
                is_superuser=True,
            )
            admin = await crud_usuario.create(db, obj_in=admin_data)
            print(f"✅ Usuario admin creado: {admin.email}")
        
        # Crear roles básicos si no existen
        # ... más seeds según necesidades
        
        await db.commit()
        print("✅ Datos iniciales creados")

if __name__ == "__main__":
    asyncio.run(seed_initial_data())
```

### Configuración de Backup Automático
```bash
#!/bin/bash
# scripts/backup_db.sh
set -e

# Variables
BACKUP_DIR="/app/backups"
DB_NAME="gad_db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Comprimir
gzip $BACKUP_FILE

# Limpiar backups antiguos (mantener 7 días)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "✅ Backup completado: ${BACKUP_FILE}.gz"
```

## 3. CONFIGURACIÓN DE SEGURIDAD

### CORS Setup Específico
```python
# src/api/main.py - Configuración CORS para producción
from starlette.middleware.cors import CORSMiddleware

# CORS configuración específica para GRUPO_GAD
cors_origins = [
    "https://grupogad.com",
    "https://www.grupogad.com",
    "https://api.grupogad.com",
    "https://admin.grupogad.com",
]

# En producción, solo orígenes específicos
if settings.ENVIRONMENT == "production":
    cors_origins = settings.CORS_ALLOWED_ORIGINS
else:
    # En desarrollo, permitir localhost
    cors_origins.extend([
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### Rate Limiting
```python
# src/api/middleware/rate_limiting.py
import time
from collections import defaultdict
from typing import Dict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Número de requests permitidas
        self.period = period  # Período en segundos
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = request.client.host
        if hasattr(request.state, "forwarded_for"):
            client_ip = request.state.forwarded_for
        
        # Limpiar requests antiguos
        now = time.time()
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
        
        # Verificar límite
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )
        
        # Registrar request actual
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response

# Aplicar en main.py
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
```

### Validación de Inputs
```python
# src/api/middleware/input_validation.py
import re
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class InputValidationMiddleware(BaseHTTPMiddleware):
    # Patrones maliciosos comunes
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;|\\;)|(\\|)|(\\|\\|))",
        r"(\\*|\\?|\\{|\\}|\\[|\\]|\\(|\\)|\\||\\\\|\\+|\\.|\\^|\\$)",
        r"(exec|execute|sp_|xp_)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Validar query parameters
        query_string = str(request.url.query)
        if self._contains_malicious_pattern(query_string):
            raise HTTPException(
                status_code=400,
                detail="Invalid characters in request"
            )
        
        response = await call_next(request)
        return response
    
    def _contains_malicious_pattern(self, text: str) -> bool:
        text_lower = text.lower()
        
        # Verificar patrones SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Verificar patrones XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
```

### Headers de Seguridad
```python
# src/api/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Headers de seguridad para producción
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self';"
            )
        
        # Ocultar información del servidor
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
```

### Configuración de Autenticación/Autorización
```python
# src/api/services/auth.py - Configuración JWT para producción
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

class AuthService:
    def __init__(self):
        # Configuración más estricta para producción
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12 if settings.ENVIRONMENT == "production" else 10
        )
        
        # Configuración JWT
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        
        # Agregar claims de seguridad
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.PROJECT_NAME,  # Issuer
            "aud": "api",                  # Audience
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="api",
                issuer=settings.PROJECT_NAME,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            return payload
        except JWTError:
            return None
```

## 4. OPTIMIZACIÓN DE PERFORMANCE

### Configuración de Caching
```python
# src/core/cache.py - Redis cache para producción
import redis.asyncio as redis
from typing import Optional, Any
import json
import pickle

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # Para permitir pickle
            max_connections=20,
        )
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
        serialize: str = "json"
    ) -> bool:
        """Guardar en cache con serialización automática"""
        try:
            if serialize == "json":
                serialized_value = json.dumps(value)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            await self.redis.set(key, serialized_value, ex=expire)
            return True
        except Exception:
            return False
    
    async def get(self, key: str, serialize: str = "json") -> Optional[Any]:
        """Obtener del cache con deserialización automática"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            if serialize == "json":
                return json.loads(value)
            elif serialize == "pickle":
                return pickle.loads(value)
            else:
                return value.decode("utf-8")
        except Exception:
            return None
    
    async def delete(self, key: str) -> bool:
        """Eliminar del cache"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            return False

# Instancia global
cache_service = CacheService()
```

### Compression y Minification
```python
# src/api/middleware/compression.py
import gzip
import io
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class GzipMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, minimum_size: int = 1000):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Solo comprimir si el cliente acepta gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Solo comprimir responses grandes
        content = b""
        async for chunk in response.body_iterator:
            content += chunk
        
        if len(content) < self.minimum_size:
            return Response(
                content=content,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type,
            )
        
        # Comprimir contenido
        compressed = gzip.compress(content)
        
        # Crear response comprimida
        response.headers["content-encoding"] = "gzip"
        response.headers["content-length"] = str(len(compressed))
        
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.media_type,
        )
```

### Optimización de Static Assets
```python
# src/api/main.py - Configuración de archivos estáticos
from fastapi.staticfiles import StaticFiles

# Montar archivos estáticos con headers de cache
class CachedStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def file_response(
        self,
        full_path,
        stat_result=None,
        method="GET",
        request_headers=None,
    ):
        response = super().file_response(
            full_path, stat_result, method, request_headers
        )
        
        # Agregar headers de cache para producción
        if settings.ENVIRONMENT == "production":
            # Cache por 1 año para assets con hash
            if any(ext in str(full_path) for ext in [".js", ".css", ".png", ".jpg", ".ico"]):
                response.headers["cache-control"] = "public, max-age=31536000, immutable"
            # Cache por 1 hora para otros archivos
            else:
                response.headers["cache-control"] = "public, max-age=3600"
        
        return response

# Montar archivos estáticos con cache
app.mount("/static", CachedStaticFiles(directory="dashboard/static"), name="static")
```

### CDN Configuration
```python
# config/cdn.py - Configuración CDN para producción
class CDNConfig:
    """Configuración CDN para assets estáticos"""
    
    # URLs base para diferentes tipos de assets
    CDN_URLS = {
        "production": {
            "static": "https://cdn.grupogad.com/static",
            "images": "https://cdn.grupogad.com/images",
            "docs": "https://cdn.grupogad.com/docs",
        },
        "staging": {
            "static": "https://staging-cdn.grupogad.com/static",
            "images": "https://staging-cdn.grupogad.com/images",
            "docs": "https://staging-cdn.grupogad.com/docs",
        },
        "development": {
            "static": "/static",
            "images": "/static/images",
            "docs": "/static/docs",
        }
    }
    
    @classmethod
    def get_asset_url(cls, asset_type: str, filename: str) -> str:
        """Obtener URL completa para un asset"""
        base_url = cls.CDN_URLS[settings.ENVIRONMENT][asset_type]
        return f"{base_url}/{filename}"
```

### Database Query Optimization
```python
# src/api/crud/base.py - Optimizaciones de queries
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional

class CRUDBase:
    def __init__(self, model):
        self.model = model
    
    async def get_multi_optimized(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        prefetch_related: List[str] = None,
    ) -> List[Any]:
        """Query optimizada con prefetch de relaciones"""
        query = select(self.model)
        
        # Aplicar eager loading para evitar N+1 queries
        if prefetch_related:
            for relation in prefetch_related:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_cache(
        self,
        db: AsyncSession,
        id: Any,
        cache_key: str = None,
        cache_expire: int = 3600,
    ) -> Optional[Any]:
        """Get con cache automático"""
        if not cache_key:
            cache_key = f"{self.model.__name__}:{id}"
        
        # Intentar obtener del cache
        cached_result = await cache_service.get(cache_key, serialize="pickle")
        if cached_result:
            return cached_result
        
        # Si no está en cache, obtener de BD
        result = await self.get(db, id=id)
        if result:
            # Guardar en cache
            await cache_service.set(cache_key, result, expire=cache_expire, serialize="pickle")
        
        return result
```

## 5. ARCHIVOS DE CONFIGURACIÓN COMPLETOS

### Dockerfile Optimizado
```dockerfile
# docker/Dockerfile.api
FROM python:3.12-slim as base

# Configurar variables de build
ARG BUILD_ENV=production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Crear directorios
WORKDIR /app
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Instalar dependencias Python
COPY requirements.lock .
RUN pip install -r requirements.lock

# Copiar código de aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["scripts/start.sh"]
```

### Docker Compose Producción
```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.3-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_network

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
    env_file:
      - ../.env.production
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - app_logs:/app/logs
      - app_uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app_network

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ../Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - api
    networks:
      - app_network

volumes:
  postgres_data:
  redis_data:
  app_logs:
  app_uploads:
  caddy_data:
  caddy_config:

networks:
  app_network:
    driver: bridge
```

### Configuración Gunicorn
```python
# gunicorn.conf.py
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.environ.get("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeouts
timeout = 120
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "grupo_gad_api"

# Server mechanics
daemon = False
pidfile = "/app/logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = "/tmp"

# SSL (si es necesario)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### Scripts de Package.json Optimizados
```bash
#!/bin/bash
# scripts/start.sh
set -e

echo "🚀 Iniciando GRUPO_GAD API..."

# Aplicar migraciones
echo "📊 Aplicando migraciones de base de datos..."
alembic upgrade head

# Crear datos iniciales si es necesario
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🌱 Verificando datos iniciales..."
    python scripts/seed_production_data.py
fi

# Calcular workers automáticamente
if [ -z "$WORKERS" ]; then
    WORKERS=$(($(nproc) * 2 + 1))
    export WORKERS
fi

echo "⚙️  Configuración:"
echo "  - Entorno: $ENVIRONMENT"
echo "  - Workers: $WORKERS"
echo "  - Log Level: $LOG_LEVEL"

# Iniciar aplicación
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Iniciando en modo producción con Gunicorn..."
    exec gunicorn src.api.main:app -c gunicorn.conf.py
else
    echo "🔧 Iniciando en modo desarrollo con Uvicorn..."
    exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
fi
```

### Configuración CI/CD Básica
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=70
      
      - name: Run linting
        run: |
          ruff check src/
          mypy src/ config/

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: docker/Dockerfile.api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to production
        run: |
          echo "🚀 Deploying to production..."
          # Aquí iría la lógica específica de deploy
          # Por ejemplo, actualizar Railway, K8s, etc.
```

## 6. CONFIGURACIÓN ESPECÍFICA DE IA/AGENTES

### Variables de Entorno para APIs de IA
```bash
# === APIs EXTERNAS ===
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# === TIMEOUTS Y RATE LIMITS ===
AI_REQUEST_TIMEOUT=30
AI_MAX_REQUESTS_PER_MINUTE=60
AI_MAX_CONCURRENT_REQUESTS=5

# === WEBSOCKETS ===
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_MESSAGE_MAX_SIZE=1048576
WS_CONNECTION_TIMEOUT=300
```

### Configuración de Timeouts y Rate Limits
```python
# src/core/ai_client.py
import asyncio
import aiohttp
from typing import Optional, Dict, Any
import time
from collections import deque

class AIClientService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.timeout = aiohttp.ClientTimeout(total=settings.AI_REQUEST_TIMEOUT)
        
        # Rate limiting
        self.max_requests_per_minute = settings.AI_MAX_REQUESTS_PER_MINUTE
        self.request_times = deque()
        
        # Semáforo para limitar requests concurrentes
        self.semaphore = asyncio.Semaphore(settings.AI_MAX_CONCURRENT_REQUESTS)
    
    async def _check_rate_limit(self):
        """Verificar y aplicar rate limiting"""
        now = time.time()
        
        # Limpiar requests antiguos (más de 1 minuto)
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Si hemos alcanzado el límite, esperar
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            await asyncio.sleep(sleep_time)
        
        # Registrar este request
        self.request_times.append(now)
    
    async def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """Generar respuesta con IA con manejo de errores y timeouts"""
        
        async with self.semaphore:  # Limitar concurrencia
            await self._check_rate_limit()  # Aplicar rate limiting
            
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens or settings.OPENAI_MAX_TOKENS,
                        "temperature": temperature or settings.OPENAI_TEMPERATURE,
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    }
                    
                    async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        json=payload,
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        else:
                            # Log error para debugging
                            error_text = await response.text()
                            logger.error(f"AI API error: {response.status} - {error_text}")
                            return None
                            
            except asyncio.TimeoutError:
                logger.error("AI API request timeout")
                return None
            except Exception as e:
                logger.error(f"AI API error: {str(e)}")
                return None

# Instancia global
ai_service = AIClientService()
```

### Manejo de Errores de APIs Externas
```python
# src/core/fallback_service.py
from typing import Optional, Callable, Any
import asyncio

class FallbackService:
    """Servicio para manejar fallbacks cuando APIs externas fallan"""
    
    def __init__(self):
        self.fallback_responses = {
            "ai_unavailable": "El servicio de IA no está disponible temporalmente. Intente más tarde.",
            "processing_error": "Ocurrió un error procesando su solicitud. Intente nuevamente.",
            "timeout_error": "La solicitud tardó demasiado tiempo. Intente con una consulta más corta.",
        }
    
    async def with_fallback(
        self,
        primary_func: Callable,
        fallback_response: str,
        *args,
        **kwargs
    ) -> Any:
        """Ejecutar función con fallback automático"""
        try:
            result = await primary_func(*args, **kwargs)
            if result is not None:
                return result
            else:
                return {"error": True, "message": fallback_response}
        except Exception as e:
            logger.error(f"Primary function failed: {str(e)}")
            return {"error": True, "message": fallback_response}
    
    async def ai_with_fallback(self, prompt: str) -> dict:
        """Wrapper para AI con fallback"""
        return await self.with_fallback(
            ai_service.generate_response,
            self.fallback_responses["ai_unavailable"],
            prompt
        )

# Instancia global
fallback_service = FallbackService()
```

### Configuración de Fallbacks
```python
# src/api/routers/ai.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.core.ai_client import ai_service
from src.core.fallback_service import fallback_service

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat")
async def chat_endpoint(
    message: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """Endpoint de chat con IA con fallbacks"""
    
    # Usar servicio con fallback
    response = await fallback_service.ai_with_fallback(message)
    
    # Si hay error, usar respuesta fallback
    if isinstance(response, dict) and response.get("error"):
        background_tasks.add_task(log_ai_failure, message, response["message"])
        return {
            "response": response["message"],
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    return {
        "response": response,
        "source": "ai",
        "timestamp": datetime.utcnow().isoformat(),
    }

async def log_ai_failure(message: str, error: str):
    """Log fallback usage para monitoreo"""
    logger.warning(
        "AI fallback used",
        extra={
            "user_message": message[:100],  # Solo primeros 100 chars
            "fallback_reason": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
```

Esta configuración proporciona un sistema robusto y production-ready para el proyecto GRUPO_GAD, con todas las optimizaciones de seguridad, performance y manejo de errores necesarias para un despliegue exitoso.