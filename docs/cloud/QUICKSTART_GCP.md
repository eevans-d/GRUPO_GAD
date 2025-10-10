# 🚀 GUÍA RÁPIDA: Migración a Google Cloud Platform

**Versión condensada del plan completo** | [Ver plan detallado →](./GOOGLE_CLOUD_MIGRATION_PLAN.md)

---

## ⚡ Inicio Rápido (5 minutos)

### 1. Requisitos Previos

```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Autenticar
gcloud auth login
gcloud config set project grupo-gad-prod
```

### 2. Crear Proyecto y Habilitar APIs

```bash
# Crear proyecto
gcloud projects create grupo-gad-prod --name="GRUPO GAD Producción"

# Habilitar APIs esenciales (todas en un comando)
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Configurar Billing

```bash
# Listar billing accounts
gcloud billing accounts list

# Vincular proyecto a billing account
gcloud billing projects link grupo-gad-prod \
  --billing-account=XXXXXX-XXXXXX-XXXXXX
```

---

## 📋 Fases de Migración (Timeline)

| Fase | Duración | Tareas Clave |
|------|----------|--------------|
| **1. Preparación** | 2-3 semanas | VPC, IAM, Secret Manager |
| **2. Base de Datos** | 1-2 semanas | Cloud SQL, migraciones |
| **3. Storage & Cache** | 3-5 días | Cloud Storage, Memorystore |
| **4. Deploy App** | 1 semana | Cloud Run, Dockerfile |
| **5. CI/CD** | 3-5 días | Cloud Build, triggers |
| **6. Load Balancer** | 2-3 días | HTTPS LB, SSL, DNS |
| **7. Monitoreo** | 3-5 días | Dashboards, alertas |
| **8. Optimización** | 2-3 semanas | CDN, autoscaling, armor |

**Total:** 7-10 semanas

---

## 💰 Costos Estimados Mensuales

| Escenario | Usuarios | Costo/Mes |
|-----------|----------|-----------|
| **Bajo** | < 100 | ~$121 |
| **Medio** | 500-1K | ~$1,292 |
| **Alto** | 5K+ | ~$5,902 |

💡 **Free Tier:** Cloud Run ofrece 2M requests/mes gratis

---

## 🏗️ Arquitectura Objetivo

```
Internet → Cloud CDN → Load Balancer (HTTPS)
                            ↓
                    Cloud Run (API)
                    ↙     ↓     ↘
          Cloud SQL   Memorystore   Secret Manager
                ↓
         Cloud Storage
```

### Servicios GCP Utilizados

- **Cloud Run** - API serverless (FastAPI)
- **Cloud SQL** - PostgreSQL 15 + PostGIS
- **Memorystore** - Redis 7.x cache
- **Cloud Storage** - Archivos estáticos y backups
- **Secret Manager** - Gestión de credenciales
- **Cloud Build** - CI/CD automatizado
- **Cloud Monitoring** - Logs y métricas

---

## 🚀 Deployment Rápido

### Opción 1: Script Automatizado

```bash
# Dar permisos de ejecución
chmod +x scripts/cloud/deploy_gcp.sh

# Ejecutar deployment
./scripts/cloud/deploy_gcp.sh v1.0.0
```

### Opción 2: Manual

```bash
# 1. Construir imagen
docker build -f docker/Dockerfile.cloudrun -t api:latest .

# 2. Tag para Artifact Registry
docker tag api:latest \
  us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest

# 3. Push
docker push us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest

# 4. Deploy a Cloud Run
gcloud run deploy grupo-gad-api \
  --image=us-central1-docker.pkg.dev/grupo-gad-prod/grupo-gad-images/api:latest \
  --region=us-central1 \
  --allow-unauthenticated
```

---

## 🔒 Seguridad Esencial

### Secretos en Secret Manager

```bash
# Crear secretos
echo -n "tu_secret_key_aqui" | gcloud secrets create SECRET_KEY --data-file=-
echo -n "tu_password_db" | gcloud secrets create POSTGRES_PASSWORD --data-file=-
echo -n "tu_token_telegram" | gcloud secrets create TELEGRAM_TOKEN --data-file=-

# Otorgar acceso a Cloud Run
gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member="serviceAccount:grupo-gad-api@grupo-gad-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Firewall Básico

```bash
# Permitir health checks de Load Balancer
gcloud compute firewall-rules create allow-health-checks \
  --network=default \
  --action=ALLOW \
  --direction=INGRESS \
  --source-ranges=130.211.0.0/22,35.191.0.0/16 \
  --rules=tcp:8080
```

---

## 📊 Monitoreo Básico

### Ver Logs en Tiempo Real

```bash
# Logs de Cloud Run
gcloud run services logs read grupo-gad-api \
  --region=us-central1 \
  --limit=50 \
  --format=json

# Logs de Cloud SQL
gcloud sql operations list --instance=grupo-gad-db
```

### Dashboards Esenciales

1. **Cloud Console** → Monitoring → Dashboards
2. Seleccionar "Cloud Run" y "Cloud SQL"
3. Crear alertas para:
   - Error rate > 5%
   - Response time > 1s
   - Database CPU > 80%

---

## 🔄 CI/CD con Cloud Build

### Configurar Trigger de GitHub

```bash
# Conectar repositorio
gcloud builds connections create github grupo-gad-github \
  --region=us-central1

# Crear trigger para main branch
gcloud builds triggers create github \
  --name="deploy-production" \
  --repo-name=GRUPO_GAD \
  --repo-owner=eevans-d \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

### Archivo cloudbuild.yaml

Ya está incluido en el repositorio. Pipeline automático:
1. ✅ Tests unitarios
2. 🔍 Linters y type checks
3. 🔒 Security audit
4. 🐳 Build Docker image
5. 📦 Push a Artifact Registry
6. 🚀 Deploy a Cloud Run
7. 🧪 Smoke tests

---

## ⚠️ Troubleshooting Común

### Error: Permission Denied

```bash
# Verificar service account tiene permisos
gcloud projects get-iam-policy grupo-gad-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:grupo-gad-api@*"
```

### Error: Cloud SQL Connection Failed

```bash
# Verificar Cloud SQL Proxy
./cloud_sql_proxy -instances=grupo-gad-prod:us-central1:grupo-gad-db=tcp:5432

# Probar conexión
psql "host=127.0.0.1 port=5432 dbname=gad_db user=gad_user"
```

### Error: Out of Memory en Cloud Run

```bash
# Aumentar memoria
gcloud run services update grupo-gad-api \
  --region=us-central1 \
  --memory=8Gi
```

---

## 📚 Recursos Útiles

### Documentación Oficial

- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)

### Comandos Útiles

```bash
# Ver todos los servicios desplegados
gcloud run services list --region=us-central1

# Describir servicio específico
gcloud run services describe grupo-gad-api --region=us-central1

# Ver métricas de CPU/Memoria
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision"'

# Estimar costos
gcloud alpha billing budgets list
```

---

## ✅ Checklist de Producción

### Pre-Deployment

- [ ] Cuenta GCP con billing configurado
- [ ] Dominio registrado y acceso a DNS
- [ ] Backup completo de base de datos local
- [ ] Secretos exportados a Secret Manager
- [ ] VPC y networking configurados

### Post-Deployment

- [ ] Health checks pasando
- [ ] DNS apuntando a Load Balancer
- [ ] SSL certificado activo
- [ ] Monitoreo y alertas configurados
- [ ] Backup automático funcionando
- [ ] Smoke tests exitosos
- [ ] Documentación actualizada

---

## 🆘 Soporte

### Plan de Rollback Rápido

```bash
# 1. Redirigir tráfico a versión anterior
gcloud run services update-traffic grupo-gad-api \
  --to-revisions=REVISION_ANTERIOR=100

# 2. O pausar completamente el servicio
gcloud run services update grupo-gad-api \
  --no-traffic
```

### Contactos

- **Documentación completa:** `docs/cloud/GOOGLE_CLOUD_MIGRATION_PLAN.md`
- **Scripts de utilidad:** `scripts/cloud/`
- **GCP Support:** https://cloud.google.com/support

---

**⚡ Siguiente paso:** Revisar el [Plan Completo de Migración](./GOOGLE_CLOUD_MIGRATION_PLAN.md) para detalles técnicos exhaustivos.

---

*Actualizado: 10 de Octubre, 2025*  
*Versión: 1.0.0*
