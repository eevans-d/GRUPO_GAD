# 🌐 PLAN MAESTRO DE MIGRACIÓN A GOOGLE CLOUD PLATFORM

**Proyecto:** GRUPO_GAD - Sistema de Gestión de Tareas Policial  
**Fecha:** 10 de Octubre, 2025  
**Versión:** 1.0.0  
**Estado:** 📋 PLANIFICACIÓN

---

## 📑 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura Objetivo en GCP](#2-arquitectura-objetivo-en-gcp)
3. [Análisis de Costos Estimados](#3-análisis-de-costos-estimados)
4. [Plan de Migración por Fases](#4-plan-de-migración-por-fases)
5. [Configuración Detallada de Servicios](#5-configuración-detallada-de-servicios)
6. [Seguridad y Compliance](#6-seguridad-y-compliance)
7. [Monitoreo y Observabilidad](#7-monitoreo-y-observabilidad)
8. [Disaster Recovery y Backups](#8-disaster-recovery-y-backups)
9. [Checklist de Preparación](#9-checklist-de-preparación)
10. [Documentación de Rollback](#10-documentación-de-rollback)

---

## 1. RESUMEN EJECUTIVO

### 🎯 Objetivos de la Migración

- **Alta Disponibilidad:** 99.95% SLA para servicios críticos
- **Escalabilidad Automática:** Soportar desde 10 hasta 10,000+ usuarios concurrentes
- **Seguridad Avanzada:** Cumplir con estándares de protección de datos sensibles
- **Reducción de Costos:** Optimización mediante arquitectura serverless y managed services
- **Geo-redundancia:** Datos replicados en múltiples regiones

### 📊 Estado Actual vs Objetivo

| Componente | Estado Actual | Estado Objetivo GCP |
|------------|---------------|---------------------|
| **API** | Docker local | Cloud Run (serverless) |
| **Base de Datos** | PostgreSQL local | Cloud SQL PostgreSQL + PostGIS |
| **Cache** | Redis local | Memorystore Redis |
| **Storage** | Sistema de archivos | Cloud Storage + CDN |
| **Secrets** | .env files | Secret Manager |
| **CI/CD** | GitHub Actions básico | Cloud Build + Artifact Registry |
| **Monitoreo** | Prometheus local | Cloud Monitoring + Logging |
| **Backup** | Scripts manuales | Automated snapshots + Cloud Storage |

### ⏱️ Timeline Estimado

- **Fase 1 (Preparación):** 2-3 semanas
- **Fase 2 (Infraestructura Base):** 1-2 semanas
- **Fase 3 (Migración Datos):** 1 semana
- **Fase 4 (Deployment):** 1 semana
- **Fase 5 (Optimización):** 2-3 semanas
- **TOTAL:** 7-10 semanas

---

## 2. ARQUITECTURA OBJETIVO EN GCP

### 🏗️ Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │  Cloud   │ ◄── SSL/TLS Automático
                    │   CDN    │ ◄── DDoS Protection
                    └────┬─────┘
                         │
              ┌──────────▼──────────┐
              │  Cloud Load         │ ◄── Global Load Balancer
              │  Balancer (HTTPS)   │ ◄── Health Checks
              └──────────┬──────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌─────▼─────┐   ┌─────▼─────┐
   │ Cloud   │     │  Cloud    │   │  Cloud    │
   │  Run    │────►│  Run      │──►│  Run      │
   │ (API 1) │     │  (API 2)  │   │  (API N)  │
   └────┬────┘     └─────┬─────┘   └─────┬─────┘
        │                │               │
        └────────────────┼───────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌─────▼─────┐   ┌─────▼─────┐
   │ Cloud   │     │Memorystore│   │  Secret   │
   │   SQL   │     │  (Redis)  │   │  Manager  │
   │(PostGIS)│     └───────────┘   └───────────┘
   └────┬────┘
        │
   ┌────▼────┐
   │ Cloud   │ ◄── Backups Automáticos
   │ Storage │ ◄── Logs, Archivos, Backups
   └─────────┘

   ┌──────────────────────────────────┐
   │  Cloud Monitoring & Logging      │
   │  - Logs Explorer                 │
   │  - Metrics Dashboard             │
   │  - Alerting Policies             │
   └──────────────────────────────────┘
```

### 🔧 Servicios GCP Seleccionados

#### **Compute & Runtime**

1. **Cloud Run** (API FastAPI)
   - Serverless, auto-escala 0→N instancias
   - Pago por uso (requests + CPU time)
   - Compatible con contenedores Docker existentes
   - Integración nativa con Secret Manager

2. **Cloud Functions** (Tareas asíncronas)
   - Procesar webhooks de Telegram
   - Ejecutar jobs de mantenimiento
   - Procesamiento de eventos

#### **Data & Storage**

3. **Cloud SQL for PostgreSQL**
   - Versión: PostgreSQL 15
   - Extensión PostGIS habilitada
   - Alta disponibilidad (HA) con failover automático
   - Backups automáticos diarios + point-in-time recovery

4. **Memorystore for Redis**
   - Cache de sesiones y datos frecuentes
   - Replicación automática
   - Versión: Redis 7.x

5. **Cloud Storage**
   - Archivos estáticos (dashboard, assets)
   - Logs a largo plazo
   - Backups de base de datos
   - Versionado habilitado

#### **Networking & Security**

6. **Cloud Load Balancing**
   - Global HTTPS Load Balancer
   - SSL/TLS con certificados gestionados
   - Health checks automáticos

7. **Cloud CDN**
   - Cache global para contenido estático
   - Reduce latencia para usuarios remotos

8. **Secret Manager**
   - Gestión segura de credenciales
   - Rotación automática de secretos
   - Integración con IAM

9. **VPC (Virtual Private Cloud)**
   - Red privada aislada
   - Firewall rules estrictas
   - Cloud NAT para salidas controladas

#### **Operations & CI/CD**

10. **Cloud Build**
    - CI/CD pipeline nativo
    - Builds automáticos desde GitHub
    - Integración con Artifact Registry

11. **Artifact Registry**
    - Repositorio privado de imágenes Docker
    - Escaneo de vulnerabilidades

12. **Cloud Monitoring & Logging**
    - Logs centralizados
    - Métricas personalizadas
    - Alertas y dashboards

---

## 3. ANÁLISIS DE COSTOS ESTIMADOS

### 💰 Costos Mensuales Proyectados (USD)

#### **Escenario: Tráfico Bajo** (< 100 usuarios activos)

| Servicio | Configuración | Costo Mensual |
|----------|---------------|---------------|
| Cloud Run (API) | 2 vCPU, 4GB RAM, 100K req/mes | $25 - $50 |
| Cloud SQL (PostgreSQL) | db-f1-micro (1 vCPU, 3.75 GB) | $26 |
| Memorystore (Redis) | Basic, 1GB | $34 |
| Cloud Storage | 50GB estándar + 10GB logs | $2 |
| Cloud Load Balancer | 1 regla, 500GB egress | $23 |
| Secret Manager | 10 secretos, 1000 accesos | $0.60 |
| Cloud Monitoring | Logs + métricas básicas | $10 |
| **TOTAL MENSUAL** | | **~$121/mes** |

#### **Escenario: Tráfico Medio** (500-1000 usuarios activos)

| Servicio | Configuración | Costo Mensual |
|----------|---------------|---------------|
| Cloud Run (API) | 4 vCPU, 8GB RAM, 1M req/mes | $180 - $250 |
| Cloud SQL (PostgreSQL) | db-n1-standard-2 (2 vCPU, 7.5 GB) + HA | $320 |
| Memorystore (Redis) | Standard (HA), 5GB | $260 |
| Cloud Storage | 200GB estándar + 50GB logs | $6 |
| Cloud Load Balancer | 1 regla, 2TB egress | $140 |
| Cloud CDN | 1TB tráfico | $85 |
| Secret Manager | 50 secretos, 10K accesos | $1 |
| Cloud Monitoring | Logs avanzados + métricas | $50 |
| **TOTAL MENSUAL** | | **~$1,292/mes** |

#### **Escenario: Tráfico Alto** (5000+ usuarios activos)

| Servicio | Configuración | Costo Mensual |
|----------|---------------|---------------|
| Cloud Run (API) | 8 vCPU, 16GB RAM, 10M req/mes | $850 - $1,200 |
| Cloud SQL (PostgreSQL) | db-n1-standard-8 (8 vCPU, 30 GB) + HA | $1,280 |
| Memorystore (Redis) | Standard (HA), 20GB | $970 |
| Cloud Storage | 1TB estándar + 200GB logs | $25 |
| Cloud Load Balancer | 3 reglas, 10TB egress | $980 |
| Cloud CDN | 5TB tráfico | $395 |
| Secret Manager | 100 secretos, 100K accesos | $2 |
| Cloud Monitoring | Logs + métricas completas | $200 |
| **TOTAL MENSUAL** | | **~$5,902/mes** |

### 🎁 Opciones de Ahorro

1. **Committed Use Discounts:** Ahorro del 20-30% con compromiso de 1-3 años
2. **Sustained Use Discounts:** Descuentos automáticos por uso continuo
3. **Free Tier:**
   - Cloud Run: 2M requests/mes gratis
   - Cloud Storage: 5GB gratis/mes
   - Cloud Build: 120 build-minutes/día gratis

---

## 4. PLAN DE MIGRACIÓN POR FASES

### 📅 FASE 1: PREPARACIÓN Y CONFIGURACIÓN INICIAL

**Duración:** 2-3 semanas  
**Prioridad:** 🔴 CRÍTICA

#### **1.1. Crear Proyecto GCP y Configuración Inicial**

```bash
# 1. Crear proyecto
gcloud projects create grupo-gad-prod \
  --name="GRUPO GAD Producción" \
  --set-as-default

# 2. Habilitar APIs necesarias
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  compute.googleapis.com

# 3. Configurar billing
gcloud beta billing projects link grupo-gad-prod \
  --billing-account=XXXXXX-XXXXXX-XXXXXX

# 4. Crear service accounts
gcloud iam service-accounts create grupo-gad-api \
  --display-name="API Service Account"

gcloud iam service-accounts create grupo-gad-ci \
  --display-name="CI/CD Service Account"
```

#### **1.2. Configurar VPC y Networking**

```bash
# 1. Crear VPC personalizada
gcloud compute networks create grupo-gad-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=regional

# 2. Crear subnets por región
gcloud compute networks subnets create grupo-gad-subnet-us \
  --network=grupo-gad-vpc \
  --region=us-central1 \
  --range=10.0.0.0/24 \
  --enable-private-ip-google-access

gcloud compute networks subnets create grupo-gad-subnet-eu \
  --network=grupo-gad-vpc \
  --region=europe-west1 \
  --range=10.1.0.0/24 \
  --enable-private-ip-google-access

# 3. Configurar Cloud NAT (para salidas controladas)
gcloud compute routers create grupo-gad-router \
  --network=grupo-gad-vpc \
  --region=us-central1

gcloud compute routers nats create grupo-gad-nat \
  --router=grupo-gad-router \
  --region=us-central1 \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges

# 4. Configurar Firewall Rules
gcloud compute firewall-rules create allow-health-checks \
  --network=grupo-gad-vpc \
  --action=ALLOW \
  --direction=INGRESS \
  --source-ranges=130.211.0.0/22,35.191.0.0/16 \
  --rules=tcp:8000

gcloud compute firewall-rules create allow-internal \
  --network=grupo-gad-vpc \
  --action=ALLOW \
  --direction=INGRESS \
  --source-ranges=10.0.0.0/8 \
  --rules=all
```

#### **1.3. Migrar Secretos a Secret Manager**

```bash
# Secretos críticos del proyecto
SECRETS=(
  "SECRET_KEY"
  "POSTGRES_PASSWORD"
  "TELEGRAM_TOKEN"
  "REDIS_PASSWORD"
)

# Crear secretos en Secret Manager
for secret in "${SECRETS[@]}"; do
  echo -n "Valor para $secret: " && read -s value
  echo -n "$value" | gcloud secrets create $secret \
    --data-file=- \
    --replication-policy="automatic"
  echo ""
done

# Otorgar acceso a service account
for secret in "${SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

#### **1.4. Configurar Artifact Registry**

```bash
# Crear repositorio para imágenes Docker
gcloud artifacts repositories create grupo-gad-images \
  --repository-format=docker \
  --location=us-central1 \
  --description="GRUPO GAD Docker images"

# Configurar autenticación Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Crear repositorio para Python packages (opcional)
gcloud artifacts repositories create grupo-gad-python \
  --repository-format=python \
  --location=us-central1 \
  --description="GRUPO GAD Python packages"
```

---

### 📅 FASE 2: INFRAESTRUCTURA BASE DE DATOS

**Duración:** 1-2 semanas  
**Prioridad:** 🔴 CRÍTICA

#### **2.1. Crear Cloud SQL Instance**

```bash
# 1. Crear instancia PostgreSQL con PostGIS
gcloud sql instances create grupo-gad-db \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-2 \
  --region=us-central1 \
  --network=grupo-gad-vpc \
  --no-assign-ip \
  --database-flags=cloudsql.enable_pgaudit=on,cloudsql_iam_authentication=on \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --enable-point-in-time-recovery \
  --retained-backups-count=30 \
  --retained-transaction-log-days=7

# 2. Configurar alta disponibilidad (opcional, aumenta costo)
gcloud sql instances patch grupo-gad-db \
  --availability-type=REGIONAL

# 3. Crear base de datos
gcloud sql databases create gad_db \
  --instance=grupo-gad-db \
  --charset=UTF8

# 4. Crear usuario de aplicación
gcloud sql users create gad_user \
  --instance=grupo-gad-db \
  --password=$(openssl rand -base64 32)

# 5. Habilitar extensión PostGIS
gcloud sql connect grupo-gad-db --user=postgres
```

```sql
-- Dentro de psql
\c gad_db
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verificar instalación
SELECT PostGIS_version();
```

#### **2.2. Configurar Cloud SQL Proxy (para desarrollo local)**

```bash
# Descargar Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Ejecutar proxy local (para migraciones)
./cloud_sql_proxy -instances=grupo-gad-prod:us-central1:grupo-gad-db=tcp:5432 &
```

#### **2.3. Migrar Schema con Alembic**

```bash
# 1. Actualizar DATABASE_URL en .env.production
export DATABASE_URL="postgresql+asyncpg://gad_user:PASSWORD@/gad_db?host=/cloudsql/grupo-gad-prod:us-central1:grupo-gad-db"

# 2. Ejecutar migraciones
cd /home/eevan/ProyectosIA/GRUPO_GAD
python -m alembic upgrade head

# 3. Verificar tablas creadas
gcloud sql connect grupo-gad-db --user=gad_user --database=gad_db
```

```sql
-- Verificar schema
\dt
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

---

### 📅 FASE 3: STORAGE Y CACHE

**Duración:** 3-5 días  
**Prioridad:** 🟡 ALTA

#### **3.1. Configurar Cloud Storage**

```bash
# 1. Crear buckets
gsutil mb -c STANDARD -l us-central1 gs://grupo-gad-static/
gsutil mb -c STANDARD -l us-central1 gs://grupo-gad-backups/
gsutil mb -c NEARLINE -l us-central1 gs://grupo-gad-logs-archive/

# 2. Configurar lifecycle policies (auto-delete logs antiguos)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["logs/"]
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
        "condition": {
          "age": 30,
          "matchesPrefix": ["backups/"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://grupo-gad-logs-archive/

# 3. Configurar CORS para dashboard
cat > cors.json << EOF
[
  {
    "origin": ["https://grupogad.example.com"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://grupo-gad-static/

# 4. Hacer público el contenido estático
gsutil iam ch allUsers:objectViewer gs://grupo-gad-static/

# 5. Subir archivos estáticos
gsutil -m cp -r dashboard/static/* gs://grupo-gad-static/static/
```

#### **3.2. Configurar Memorystore (Redis)**

```bash
# 1. Crear instancia Redis
gcloud redis instances create grupo-gad-cache \
  --size=5 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --network=grupo-gad-vpc \
  --tier=STANDARD_HA \
  --enable-auth

# 2. Obtener información de conexión
gcloud redis instances describe grupo-gad-cache \
  --region=us-central1 \
  --format="get(host,port,authString)"

# 3. Guardar AUTH_STRING en Secret Manager
gcloud secrets create REDIS_PASSWORD \
  --data-file=<(gcloud redis instances describe grupo-gad-cache \
    --region=us-central1 \
    --format="get(authString)")
```

---

### 📅 FASE 4: DESPLIEGUE DE APLICACIÓN

**Duración:** 1 semana  
**Prioridad:** 🔴 CRÍTICA

#### **4.1. Preparar Dockerfile para Cloud Run**

Crear archivo `Dockerfile.cloudrun`:

```dockerfile
# Dockerfile.cloudrun
FROM python:3.11-slim

# Variables de build
ARG ENVIRONMENT=production
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
RUN useradd -m -u 1000 appuser

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Exponer puerto (Cloud Run usa PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Comando de inicio con Gunicorn + Uvicorn workers
CMD exec gunicorn src.api.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind :8080 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
```

#### **4.2. Construir y Pushear Imagen**

```bash
# 1. Construir imagen localmente
docker build -f Dockerfile.cloudrun -t grupo-gad-api:latest .

# 2. Tag para Artifact Registry
docker tag grupo-gad-api:latest \
  us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:v1.0.0

docker tag grupo-gad-api:latest \
  us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest

# 3. Push a Artifact Registry
docker push us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:v1.0.0
docker push us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest
```

#### **4.3. Desplegar a Cloud Run**

```bash
# 1. Obtener connection name de Cloud SQL
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe grupo-gad-db \
  --format='get(connectionName)')

# 2. Obtener IP de Redis
REDIS_HOST=$(gcloud redis instances describe grupo-gad-cache \
  --region=us-central1 \
  --format='get(host)')

# 3. Desplegar servicio
gcloud run deploy grupo-gad-api \
  --image=us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest \
  --platform=managed \
  --region=us-central1 \
  --service-account=grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com \
  --set-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
  --vpc-connector=grupo-gad-connector \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=10 \
  --cpu=2 \
  --memory=4Gi \
  --timeout=300 \
  --concurrency=80 \
  --port=8080 \
  --set-env-vars="ENVIRONMENT=production,PROJECT_NAME=GRUPO_GAD,API_V1_STR=/api/v1" \
  --set-env-vars="POSTGRES_SERVER=/cloudsql/$INSTANCE_CONNECTION_NAME,POSTGRES_DB=gad_db,POSTGRES_USER=gad_user,POSTGRES_PORT=5432" \
  --set-env-vars="REDIS_HOST=$REDIS_HOST,REDIS_PORT=6379" \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,REDIS_PASSWORD=REDIS_PASSWORD:latest,TELEGRAM_TOKEN=TELEGRAM_TOKEN:latest"

# 4. Obtener URL del servicio
gcloud run services describe grupo-gad-api \
  --region=us-central1 \
  --format='get(status.url)'
```

#### **4.4. Configurar VPC Connector (para acceso a Redis)**

```bash
# Crear VPC Serverless Connector
gcloud compute networks vpc-access connectors create grupo-gad-connector \
  --network=grupo-gad-vpc \
  --region=us-central1 \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=10
```

---

### 📅 FASE 5: CI/CD CON CLOUD BUILD

**Duración:** 3-5 días  
**Prioridad:** 🟡 ALTA

#### **5.1. Crear Configuración de Cloud Build**

Crear archivo `cloudbuild.yaml`:

```yaml
# cloudbuild.yaml
steps:
  # Step 1: Run tests
  - name: 'python:3.11-slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        python -m pytest -q --cov=src --cov-report=term-missing
    id: 'run-tests'

  # Step 2: Security scan
  - name: 'python:3.11-slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install pip-audit safety
        pip-audit -r requirements.txt
    id: 'security-scan'
    waitFor: ['-']

  # Step 3: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'Dockerfile.cloudrun'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api:$COMMIT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api:latest'
      - '.'
    id: 'build-image'
    waitFor: ['run-tests', 'security-scan']

  # Step 4: Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api'
    id: 'push-image'
    waitFor: ['build-image']

  # Step 5: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'grupo-gad-api'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
    id: 'deploy-cloudrun'
    waitFor: ['push-image']

  # Step 6: Run smoke tests
  - name: 'gcr.io/cloud-builders/curl'
    args:
      - '-f'
      - 'https://grupo-gad-api-XXXXX-uc.a.run.app/api/v1/health'
    id: 'smoke-test'
    waitFor: ['deploy-cloudrun']

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'N1_HIGHCPU_8'

timeout: '1800s'

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api:$COMMIT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/grupo-gad-images/api:latest'
```

#### **5.2. Configurar Trigger de GitHub**

```bash
# 1. Conectar repositorio GitHub
gcloud builds connections create github grupo-gad-github \
  --region=us-central1

# 2. Crear trigger para push a main
gcloud builds triggers create github \
  --name="deploy-production" \
  --region=us-central1 \
  --repo-name=GRUPO_GAD \
  --repo-owner=eevans-d \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml

# 3. Crear trigger para PRs (solo tests)
gcloud builds triggers create github \
  --name="test-pull-requests" \
  --region=us-central1 \
  --repo-name=GRUPO_GAD \
  --repo-owner=eevans-d \
  --pull-request-pattern="^.*$" \
  --build-config=cloudbuild.test.yaml
```

---

### 📅 FASE 6: LOAD BALANCER Y SSL

**Duración:** 2-3 días  
**Prioridad:** 🟡 ALTA

#### **6.1. Configurar HTTPS Load Balancer**

```bash
# 1. Reservar IP estática
gcloud compute addresses create grupo-gad-ip \
  --global

# 2. Crear NEG (Network Endpoint Group) para Cloud Run
gcloud compute network-endpoint-groups create grupo-gad-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=grupo-gad-api

# 3. Crear backend service
gcloud compute backend-services create grupo-gad-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

# 4. Añadir NEG al backend
gcloud compute backend-services add-backend grupo-gad-backend \
  --global \
  --network-endpoint-group=grupo-gad-neg \
  --network-endpoint-group-region=us-central1

# 5. Crear URL map
gcloud compute url-maps create grupo-gad-lb \
  --default-service=grupo-gad-backend

# 6. Crear certificado SSL gestionado
gcloud compute ssl-certificates create grupo-gad-cert \
  --domains=api.grupogad.com,grupogad.com

# 7. Crear HTTPS proxy
gcloud compute target-https-proxies create grupo-gad-https-proxy \
  --url-map=grupo-gad-lb \
  --ssl-certificates=grupo-gad-cert

# 8. Crear forwarding rule
gcloud compute forwarding-rules create grupo-gad-https-rule \
  --global \
  --target-https-proxy=grupo-gad-https-proxy \
  --address=grupo-gad-ip \
  --ports=443

# 9. (Opcional) Redirigir HTTP a HTTPS
gcloud compute url-maps import grupo-gad-lb \
  --global \
  --source=/dev/stdin <<EOF
name: grupo-gad-lb
defaultService: https://www.googleapis.com/compute/v1/projects/grupo-gad-prod/global/backendServices/grupo-gad-backend
hostRules:
- hosts:
  - '*'
  pathMatcher: path-matcher-1
pathMatchers:
- name: path-matcher-1
  defaultService: https://www.googleapis.com/compute/v1/projects/grupo-gad-prod/global/backendServices/grupo-gad-backend
EOF
```

#### **6.2. Configurar DNS**

```bash
# Obtener IP estática asignada
IP_ADDRESS=$(gcloud compute addresses describe grupo-gad-ip \
  --global \
  --format="get(address)")

echo "Configurar estos registros DNS:"
echo "A    grupogad.com           -> $IP_ADDRESS"
echo "A    api.grupogad.com       -> $IP_ADDRESS"
echo "AAAA grupogad.com           -> (IPv6 si aplica)"
```

---

### 📅 FASE 7: MONITOREO Y ALERTAS

**Duración:** 3-5 días  
**Prioridad:** 🟡 ALTA

#### **7.1. Configurar Cloud Monitoring Dashboard**

```bash
# Crear dashboard personalizado
gcloud monitoring dashboards create --config-from-file=- <<EOF
{
  "displayName": "GRUPO GAD - Production Monitoring",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "API Request Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"grupo-gad-api\" AND metric.type=\"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "API Response Time (p95)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"grupo-gad-api\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_DELTA",
                    "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud SQL CPU Utilization",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloudsql_database\" AND resource.labels.database_id=~\".*grupo-gad-db\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Redis Memory Usage",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"grupo-gad-cache\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF
```

#### **7.2. Configurar Alertas Críticas**

```bash
# Alerta: API con alta tasa de errores
gcloud alpha monitoring policies create --notification-channels=CHANNEL_ID --config-from-file=- <<EOF
{
  "displayName": "GRUPO GAD - High Error Rate",
  "conditions": [{
    "displayName": "Error rate > 5%",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"grupo-gad-api\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_RATE"
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.05,
      "duration": "300s"
    }
  }],
  "combiner": "OR",
  "enabled": true
}
EOF

# Alerta: Cloud SQL alto uso de CPU
gcloud alpha monitoring policies create --notification-channels=CHANNEL_ID --config-from-file=- <<EOF
{
  "displayName": "GRUPO GAD - High Database CPU",
  "conditions": [{
    "displayName": "CPU > 80%",
    "conditionThreshold": {
      "filter": "resource.type=\"cloudsql_database\" AND resource.labels.database_id=~\".*grupo-gad-db\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_MEAN"
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.8,
      "duration": "600s"
    }
  }],
  "combiner": "OR",
  "enabled": true
}
EOF

# Alerta: Redis memoria casi llena
gcloud alpha monitoring policies create --notification-channels=CHANNEL_ID --config-from-file=- <<EOF
{
  "displayName": "GRUPO GAD - Redis Memory High",
  "conditions": [{
    "displayName": "Memory > 90%",
    "conditionThreshold": {
      "filter": "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"grupo-gad-cache\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\"",
      "aggregations": [{
        "alignmentPeriod": "300s",
        "perSeriesAligner": "ALIGN_MEAN"
      }],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.9,
      "duration": "300s"
    }
  }],
  "combiner": "OR",
  "enabled": true
}
EOF
```

#### **7.3. Configurar Log-Based Metrics**

```bash
# Crear metric para errores de autenticación
gcloud logging metrics create auth_failures \
  --description="Failed authentication attempts" \
  --log-filter='resource.type="cloud_run_revision"
    resource.labels.service_name="grupo-gad-api"
    jsonPayload.level="ERROR"
    jsonPayload.message=~"Authentication failed"'

# Crear metric para slow queries
gcloud logging metrics create slow_queries \
  --description="Database queries taking > 1s" \
  --log-filter='resource.type="cloudsql_database"
    jsonPayload.message=~"duration: [1-9][0-9]{3,}"'
```

---

### 📅 FASE 8: OPTIMIZACIÓN Y SCALING

**Duración:** 2-3 semanas  
**Prioridad:** 🟢 MEDIA

#### **8.1. Implementar Cloud CDN**

```bash
# Habilitar Cloud CDN en backend service
gcloud compute backend-services update grupo-gad-backend \
  --global \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400 \
  --client-ttl=3600

# Configurar cache key policy
gcloud compute backend-services update grupo-gad-backend \
  --global \
  --cache-key-include-protocol \
  --cache-key-include-host \
  --cache-key-include-query-string \
  --cache-key-query-string-whitelist="page,limit"
```

#### **8.2. Configurar Autoscaling Avanzado**

```bash
# Actualizar configuración de Cloud Run con autoscaling
gcloud run services update grupo-gad-api \
  --region=us-central1 \
  --min-instances=2 \
  --max-instances=100 \
  --cpu-throttling \
  --concurrency=80 \
  --cpu=2 \
  --memory=4Gi \
  --timeout=300 \
  --execution-environment=gen2
```

#### **8.3. Implementar Cloud Armor (DDoS Protection)**

```bash
# Crear security policy
gcloud compute security-policies create grupo-gad-security \
  --description="Security policy for GRUPO GAD"

# Regla: Rate limiting (max 100 req/min por IP)
gcloud compute security-policies rules create 1000 \
  --security-policy=grupo-gad-security \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP

# Regla: Bloquear países específicos (ejemplo)
gcloud compute security-policies rules create 2000 \
  --security-policy=grupo-gad-security \
  --action=deny-403 \
  --expression="origin.region_code in ['CN', 'RU']"

# Regla: Permitir todo lo demás
gcloud compute security-policies rules create 2147483647 \
  --security-policy=grupo-gad-security \
  --action=allow

# Aplicar policy al backend
gcloud compute backend-services update grupo-gad-backend \
  --global \
  --security-policy=grupo-gad-security
```

---

## 5. CONFIGURACIÓN DETALLADA DE SERVICIOS

### 🔧 Archivo de Configuración: `.env.gcp`

```bash
# ================================================
# GRUPO_GAD - Google Cloud Platform Configuration
# ================================================

# === PROYECTO GCP ===
GCP_PROJECT_ID=grupo-gad-prod
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# === ENVIRONMENT ===
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME=GRUPO_GAD
PROJECT_VERSION=1.0.0
API_V1_STR=/api/v1

# === BASE DE DATOS (Cloud SQL) ===
# Connection via Unix socket
POSTGRES_SERVER=/cloudsql/grupo-gad-prod:us-central1:grupo-gad-db
POSTGRES_USER=gad_user
POSTGRES_DB=gad_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://gad_user:PASSWORD@/gad_db?host=/cloudsql/grupo-gad-prod:us-central1:grupo-gad-db

# Pool de conexiones optimizado para Cloud Run
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# === REDIS (Memorystore) ===
REDIS_HOST=10.0.0.3
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD se obtiene de Secret Manager

# === STORAGE (Cloud Storage) ===
STORAGE_BUCKET=grupo-gad-static
BACKUP_BUCKET=grupo-gad-backups
LOGS_BUCKET=grupo-gad-logs-archive

# === SECRETOS (Secret Manager) ===
# Los secretos se inyectan automáticamente por Cloud Run
# No incluir valores aquí, solo referencias
SECRET_KEY=projects/grupo-gad-prod/secrets/SECRET_KEY/versions/latest
TELEGRAM_TOKEN=projects/grupo-gad-prod/secrets/TELEGRAM_TOKEN/versions/latest

# === LOGGING & MONITORING ===
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_METRICS=true
METRICS_PORT=9090

# === SECURITY ===
CORS_ALLOWED_ORIGINS=https://grupogad.com,https://api.grupogad.com
TRUSTED_PROXIES=169.254.1.1
ACCESS_TOKEN_EXPIRE_MINUTES=60

# === PERFORMANCE ===
MAX_WORKERS=4
WORKER_TIMEOUT=120
KEEP_ALIVE=5
```

### 🐍 Actualización de `config/settings.py` para GCP

```python
# config/settings.py - Actualización para GCP
import os
from typing import Optional
from google.cloud import secretmanager
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # === PROYECTO ===
    PROJECT_NAME: str = "GRUPO_GAD"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # === GCP ===
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: str = "us-central1"
    
    # === BASE DE DATOS ===
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str  # Se carga desde Secret Manager
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # === REDIS ===
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # === STORAGE ===
    STORAGE_BUCKET: str = "grupo-gad-static"
    BACKUP_BUCKET: str = "grupo-gad-backups"
    
    # === SECRETS ===
    SECRET_KEY: str
    TELEGRAM_TOKEN: str
    
    model_config = {
        "env_file": ".env.gcp",
        "case_sensitive": False,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Cargar secretos desde Secret Manager si estamos en GCP
        if self.GCP_PROJECT_ID and self.ENVIRONMENT == "production":
            self._load_secrets_from_gcp()
    
    def _load_secrets_from_gcp(self):
        """Cargar secretos desde Google Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            
            secrets = {
                "SECRET_KEY": "SECRET_KEY",
                "POSTGRES_PASSWORD": "POSTGRES_PASSWORD",
                "REDIS_PASSWORD": "REDIS_PASSWORD",
                "TELEGRAM_TOKEN": "TELEGRAM_TOKEN",
            }
            
            for attr, secret_name in secrets.items():
                if not getattr(self, attr, None):
                    secret_path = f"projects/{self.GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
                    try:
                        response = client.access_secret_version(request={"name": secret_path})
                        setattr(self, attr, response.payload.data.decode("UTF-8"))
                    except Exception as e:
                        print(f"Warning: Could not load {secret_name}: {e}")
        except Exception as e:
            print(f"Warning: Secret Manager not available: {e}")

def get_settings() -> Settings:
    """Obtener instancia de Settings (con caché)."""
    return Settings()
```

---

## 6. SEGURIDAD Y COMPLIANCE

### 🔒 Checklist de Seguridad

#### **6.1. IAM y Permisos**

```bash
# Service Account para API
gcloud iam service-accounts create grupo-gad-api \
  --display-name="API Service Account"

# Permisos mínimos necesarios
gcloud projects add-iam-policy-binding grupo-gad-prod \
  --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding grupo-gad-prod \
  --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding grupo-gad-prod \
  --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding grupo-gad-prod \
  --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

#### **6.2. Secret Rotation Policy**

```bash
# Configurar rotación automática de secretos
gcloud secrets update SECRET_KEY \
  --rotation-period="2592000s" \
  --next-rotation-time="2025-11-10T00:00:00Z"

# Cloud Function para rotación (ejemplo)
# Ver docs/cloud/secret_rotation_function.py
```

#### **6.3. Auditoría de Accesos**

```bash
# Habilitar Cloud Audit Logs
gcloud logging sinks create audit-sink \
  storage.googleapis.com/grupo-gad-audit-logs \
  --log-filter='protoPayload.serviceName="cloudsql.googleapis.com" OR protoPayload.serviceName="secretmanager.googleapis.com"'
```

---

## 7. MONITOREO Y OBSERVABILIDAD

### 📊 KPIs y Métricas Clave

| Métrica | Target | Alerta en |
|---------|--------|-----------|
| **Uptime** | 99.95% | < 99.9% |
| **Response Time (p95)** | < 200ms | > 500ms |
| **Error Rate** | < 0.1% | > 1% |
| **Database Connections** | < 80% pool | > 90% |
| **Redis Memory** | < 80% | > 90% |
| **Cloud Run CPU** | < 60% | > 80% |
| **API Latency (p99)** | < 1s | > 2s |

### 📈 Dashboards Recomendados

1. **Dashboard Ejecutivo:** Vista de alto nivel (uptime, usuarios, errores)
2. **Dashboard Técnico:** Métricas detalladas (latencias, queries, cache hits)
3. **Dashboard de Costos:** Tracking de gastos por servicio
4. **Dashboard de Seguridad:** Intentos de autenticación fallidos, rate limits

---

## 8. DISASTER RECOVERY Y BACKUPS

### 💾 Estrategia de Backups

#### **Automated Backups**

```bash
# Cloud SQL: Backups automáticos configurados en creación
# - Daily automated backups (retained 30 days)
# - Point-in-time recovery (7 days)
# - On-demand backups before major changes

# Crear backup manual antes de cambios críticos
gcloud sql backups create \
  --instance=grupo-gad-db \
  --description="Pre-migration backup"

# Exportar backup a Cloud Storage
gcloud sql export sql grupo-gad-db \
  gs://grupo-gad-backups/manual-backup-$(date +%Y%m%d).sql.gz \
  --database=gad_db
```

#### **Disaster Recovery Plan**

**RPO (Recovery Point Objective):** 1 hora  
**RTO (Recovery Time Objective):** 4 horas

**Procedimiento de Recuperación:**

```bash
# 1. Crear nueva instancia desde backup
gcloud sql instances restore-backup grupo-gad-db \
  --backup-id=BACKUP_ID

# O restaurar desde export
gcloud sql import sql grupo-gad-db-new \
  gs://grupo-gad-backups/manual-backup-YYYYMMDD.sql.gz \
  --database=gad_db

# 2. Actualizar Cloud Run para apuntar a nueva instancia
gcloud run services update grupo-gad-api \
  --region=us-central1 \
  --set-cloudsql-instances=grupo-gad-prod:us-central1:grupo-gad-db-new

# 3. Verificar funcionalidad
curl -f https://api.grupogad.com/api/v1/health

# 4. Monitorear logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

---

## 9. CHECKLIST DE PREPARACIÓN

### ✅ Pre-Migración

- [ ] Cuenta GCP creada con billing habilitado
- [ ] Dominio registrado y acceso a DNS
- [ ] Backup completo de base de datos local
- [ ] Exportar todos los secretos a Secret Manager
- [ ] Actualizar Dockerfile para Cloud Run
- [ ] Crear repositorio en Artifact Registry
- [ ] Configurar VPC y networking
- [ ] Documentar arquitectura actual

### ✅ Durante Migración

- [ ] Crear Cloud SQL instance
- [ ] Migrar schema con Alembic
- [ ] Importar datos de producción
- [ ] Configurar Memorystore Redis
- [ ] Desplegar aplicación a Cloud Run
- [ ] Configurar Load Balancer y SSL
- [ ] Configurar DNS
- [ ] Ejecutar smoke tests

### ✅ Post-Migración

- [ ] Monitorear métricas por 7 días
- [ ] Configurar alertas críticas
- [ ] Documentar troubleshooting común
- [ ] Entrenar equipo en herramientas GCP
- [ ] Optimizar costos
- [ ] Realizar test de carga
- [ ] Validar disaster recovery plan

---

## 10. DOCUMENTACIÓN DE ROLLBACK

### ⏮️ Plan de Rollback Rápido

En caso de problemas críticos durante la migración:

```bash
# 1. Redirigir DNS a infraestructura anterior
# (Cambiar A record en proveedor DNS)

# 2. Pausar Cloud Run
gcloud run services update grupo-gad-api \
  --region=us-central1 \
  --no-traffic

# 3. Exportar datos recientes desde Cloud SQL
gcloud sql export sql grupo-gad-db \
  gs://grupo-gad-backups/rollback-$(date +%Y%m%d-%H%M%S).sql.gz \
  --database=gad_db

# 4. Restaurar en infraestructura anterior
# (Seguir procedimiento de restore local)

# 5. Notificar stakeholders
```

### 🚨 Criterios para Activar Rollback

- Error rate > 10% por más de 5 minutos
- Downtime completo > 15 minutos
- Pérdida de datos detectada
- Problemas de seguridad críticos
- Costos > 200% del estimado

---

## 📚 RECURSOS ADICIONALES

### Documentación GCP

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Quickstart](https://cloud.google.com/build/docs/quickstart-build)

### Scripts de Utilidad

Ver carpeta `docs/cloud/scripts/`:
- `deploy.sh` - Script de deployment automatizado
- `rollback.sh` - Script de rollback rápido
- `migrate_data.py` - Migración de datos
- `health_check.sh` - Verificación post-deployment

### Contactos de Soporte

- **GCP Support:** https://cloud.google.com/support
- **Tier:** Standard / Premium (recomendado para producción)
- **24/7 Phone Support:** Incluido en Premium tier

---

## 📋 PRÓXIMOS PASOS

### Inmediatos (Esta Semana)

1. ✅ Revisar y aprobar este plan con stakeholders
2. ⏳ Crear cuenta GCP y configurar billing
3. ⏳ Registrar dominio o configurar subdominio
4. ⏳ Exportar backup completo de base de datos actual

### Corto Plazo (Próximas 2 Semanas)

1. Ejecutar Fase 1 (Preparación y Configuración)
2. Ejecutar Fase 2 (Infraestructura Base de Datos)
3. Realizar pruebas de conectividad

### Mediano Plazo (1 Mes)

1. Completar Fases 3-5 (Storage, Deploy, CI/CD)
2. Configurar monitoreo completo
3. Realizar migration dry-run

### Largo Plazo (2-3 Meses)

1. Optimización de costos
2. Implementación de multi-región
3. Disaster recovery drills
4. Performance tuning avanzado

---

## ✍️ APROBACIONES

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Project Lead | | | |
| DevOps Engineer | | | |
| Security Officer | | | |
| Finance Approver | | | |

---

**Documento creado por:** GitHub Copilot  
**Fecha:** 10 de Octubre, 2025  
**Versión:** 1.0.0  
**Próxima revisión:** Semanal durante migración

---

**🚀 GRUPO_GAD → Google Cloud Platform Migration**
