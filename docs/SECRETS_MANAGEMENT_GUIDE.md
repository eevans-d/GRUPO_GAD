# 🔐 Guía de Gestión de Secretos Gubernamental - GRUPO_GAD

## ⚠️ Principios de Seguridad

### **NUNCA**:
- ❌ Versionar archivos `.env` con valores reales
- ❌ Compartir secretos por email, chat o documentos
- ❌ Usar valores por defecto en producción
- ❌ Hardcodear secretos en código fuente
- ❌ Reutilizar secretos entre entornos

### **SIEMPRE**:
- ✅ Usar `.env.example` como plantilla
- ✅ Generar secretos aleatorios únicos
- ✅ Rotar secretos cada 90 días mínimo
- ✅ Usar gestores de secretos en producción
- ✅ Auditar accesos a secretos

---

## 🚀 Quick Start - Desarrollo Local

### 1. Crear archivo de configuración local

```bash
# Copiar plantilla
cp .env.example .env

# Editar con tus valores
nano .env  # o tu editor favorito
```

### 2. Generar secretos seguros

```bash
# JWT_SECRET_KEY (mínimo 32 caracteres)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# SECRET_KEY (mínimo 32 caracteres)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# POSTGRES_PASSWORD (16+ caracteres)
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(24))"
```

### 3. Configurar valores específicos

Editar `.env` y reemplazar todos los `CHANGEME_*`:

```bash
# Database
POSTGRES_PASSWORD=tu_password_seguro_aqui

# API Security
JWT_SECRET_KEY=tu_jwt_secret_key_generado_arriba
SECRET_KEY=tu_secret_key_generado_arriba

# Telegram (obtener de @BotFather)
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### 4. Validar configuración

```bash
# Verificar que no hay valores CHANGEME
grep -r "CHANGEME" .env && echo "⚠️ Aún hay valores CHANGEME" || echo "✅ Configuración OK"

# Verificar que .env no está en git
git status .env 2>/dev/null | grep "nothing to commit" && echo "✅ .env ignorado" || echo "⚠️ Verificar .gitignore"
```

---

## 🏛️ Staging y Producción

### Opción A: Docker Secrets (Recomendado para Docker Swarm)

```bash
# Inicializar swarm
docker swarm init

# Crear secrets desde archivos seguros
echo "tu_jwt_secret_aqui" | docker secret create jwt_secret_key -
echo "postgresql://..." | docker secret create database_url -
echo "tu_telegram_token" | docker secret create telegram_token -

# Deploy con secrets
docker stack deploy -c docker-compose.prod.yml grupo-gad
```

**docker-compose.prod.yml** con secrets:

```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/eevans-d/grupo_gad/api:v1.1.0
    secrets:
      - jwt_secret_key
      - database_url
      - telegram_token
    environment:
      ENVIRONMENT: production
      JWT_SECRET_KEY_FILE: /run/secrets/jwt_secret_key
      DATABASE_URL_FILE: /run/secrets/database_url
      TELEGRAM_TOKEN_FILE: /run/secrets/telegram_token

secrets:
  jwt_secret_key:
    external: true
  database_url:
    external: true
  telegram_token:
    external: true
```

### Opción B: Variables de Entorno Seguras (Kubernetes/Cloud)

```bash
# En Kubernetes con sealed-secrets
kubectl create secret generic grupo-gad-secrets \
  --from-literal=jwt-secret-key='tu_secret' \
  --from-literal=database-url='postgresql://...' \
  --from-literal=telegram-token='tu_token' \
  --dry-run=client -o yaml | kubeseal > sealed-secrets.yaml

# Aplicar
kubectl apply -f sealed-secrets.yaml
```

### Opción C: Gestores de Secretos Externos

#### HashiCorp Vault

```bash
# Escribir secretos
vault kv put secret/grupo-gad/production \
  jwt_secret_key="tu_secret" \
  database_url="postgresql://..." \
  telegram_token="tu_token"

# Leer en la aplicación
export VAULT_ADDR='https://vault.gobierno.gob'
export VAULT_TOKEN='tu_token_vault'
```

#### AWS Secrets Manager

```bash
# Crear secreto
aws secretsmanager create-secret \
  --name grupo-gad/production/jwt-secret \
  --secret-string "tu_secret_aqui"

# En la aplicación, configurar IAM role y SDK de AWS
```

---

## 🔄 Rotación de Secretos

### Calendario Gubernamental Recomendado

| Secreto | Frecuencia | Impacto |
|---------|-----------|---------|
| JWT_SECRET_KEY | 90 días | Alto - Invalida sesiones |
| DATABASE_PASSWORD | 90 días | Crítico - Requiere restart |
| TELEGRAM_TOKEN | 180 días | Medio - Revocar desde @BotFather |
| REDIS_PASSWORD | 90 días | Bajo - Restart servicios |

### Procedimiento de Rotación

```bash
# 1. Generar nuevo secreto
NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. En staging: actualizar y validar
echo $NEW_JWT_SECRET | docker secret create jwt_secret_key_v2 -
docker service update --secret-rm jwt_secret_key --secret-add jwt_secret_key_v2 grupo-gad_api

# 3. Validar funcionamiento (15 minutos)
curl -f https://staging.grupo-gad.gob.cl/health || echo "Fallo - rollback"

# 4. Si OK, aplicar en producción con mantenimiento programado
# 5. Auditar y documentar rotación

# 6. Eliminar secreto antiguo después de 7 días
docker secret rm jwt_secret_key
```

---

## 📊 Auditoría y Compliance

### Verificación Pre-Despliegue

```bash
# Ejecutar checklist de seguridad
./scripts/security_checklist.sh

# Debe pasar:
# ✅ Sin secretos hardcoded en código
# ✅ .env no versionado
# ✅ Secretos de producción en gestor externo
# ✅ Longitud mínima de secretos validada
# ✅ Rotación programada documentada
```

### Logging de Acceso a Secretos

```python
# En config/settings.py
import logging
from datetime import datetime

logger = logging.getLogger("security.secrets")

def load_secret(secret_name: str) -> str:
    """Carga secreto con auditoría."""
    logger.info(
        f"Secret accessed: {secret_name}",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "component": "settings_loader",
            "environment": os.getenv("ENVIRONMENT"),
            "secret_name": secret_name  # No loggear el valor
        }
    )
    # Cargar secreto...
    return secret_value
```

---

## 🚨 Respuesta a Incidentes

### Si un Secreto se Compromete

1. **Inmediato (< 5 minutos)**:
   ```bash
   # Revocar secreto comprometido
   docker service update --env-rm JWT_SECRET_KEY grupo-gad_api
   
   # Detener servicio si es crítico
   docker service scale grupo-gad_api=0
   ```

2. **Mitigación (< 30 minutos)**:
   - Generar nuevo secreto
   - Actualizar en gestor de secretos
   - Restart servicios con nuevo secreto
   - Validar operación normal

3. **Post-Mortem (< 24 horas)**:
   - Documentar cómo ocurrió la exposición
   - Identificar datos/sesiones afectadas
   - Notificar según protocolo gubernamental
   - Implementar controles preventivos

---

## ✅ Checklist Final Gubernamental

### Desarrollo Local
- [ ] `.env` creado desde `.env.example`
- [ ] Todos los `CHANGEME_*` reemplazados
- [ ] Secretos generados aleatoriamente
- [ ] `.env` en `.gitignore`
- [ ] Validación de configuración pasada

### Staging
- [ ] Secretos en gestor externo (Vault/Secrets Manager)
- [ ] `ENVIRONMENT=staging` configurado
- [ ] CORS restrictivo configurado
- [ ] Rate limiting habilitado
- [ ] Logging de auditoría activo
- [ ] Monitoreo de acceso a secretos

### Producción
- [ ] `ENVIRONMENT=production` configurado
- [ ] Todos los secretos rotados antes de Go-Live
- [ ] Gestión de secretos con alta disponibilidad
- [ ] Plan de rotación documentado (90 días)
- [ ] Procedimiento de respuesta a incidentes
- [ ] Auditoría de compliance gubernamental aprobada
- [ ] Backup seguro de secretos (encrypted)
- [ ] Equipo on-call capacitado

---

## 📚 Referencias

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [HashiCorp Vault Best Practices](https://developer.hashicorp.com/vault/tutorials/recommended-patterns/pattern-centralized-secrets)
- Políticas de Seguridad Gubernamental (interno)

---

## 🆘 Contacto de Seguridad

- **Equipo de Seguridad**: security@grupo-gad.gob
- **Incident Response**: +XX XXX XXX XXX (24/7)
- **Escalación**: ciso@grupo-gad.gob

**Última actualización**: 2025-10-03  
**Versión**: 1.1.0
