# Plan de Rotación de Secretos y Seguridad - GRUPO_GAD

Este documento define las políticas y procedimientos para la gestión segura de secretos, rotación de credenciales y auditorías de seguridad periódicas para el sistema GRUPO_GAD en producción.

## 1. Inventario de Secretos

### 1.1. Secretos de Base de Datos

| Secreto | Descripción | Rotación | Criticidad |
|---------|-------------|----------|------------|
| `POSTGRES_PASSWORD` | Contraseña del usuario principal de PostgreSQL | 90 días | Crítica |
| `POSTGRES_USER` | Usuario de la aplicación en PostgreSQL | Anual | Media |
| `DATABASE_URL` | URL completa de conexión a BD | Al rotar contraseña | Alta |

### 1.2. Secretos de API y JWT

| Secreto | Descripción | Rotación | Criticidad |
|---------|-------------|----------|------------|
| `SECRET_KEY` | Clave para firmar tokens JWT | 60 días | Crítica |
| `JWT_SECRET` | Clave alternativa para JWT | 60 días | Crítica |
| `API_KEY` | Clave de API para servicios externos | 90 días | Alta |

### 1.3. Secretos de Servicios Externos

| Secreto | Descripción | Rotación | Criticidad |
|---------|-------------|----------|------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | 180 días | Alta |
| `REDIS_PASSWORD` | Contraseña de Redis (si está habilitada) | 90 días | Media |
| `BACKUP_S3_ACCESS_KEY` | Clave de acceso a S3 para backups | 90 días | Alta |
| `BACKUP_S3_SECRET_KEY` | Clave secreta de S3 para backups | 90 días | Alta |

### 1.4. Secretos de Monitoreo

| Secreto | Descripción | Rotación | Criticidad |
|---------|-------------|----------|------------|
| `GRAFANA_ADMIN_PASSWORD` | Contraseña del admin de Grafana | 60 días | Alta |
| `PROMETHEUS_BASIC_AUTH` | Autenticación básica de Prometheus | 90 días | Media |
| `ALERTMANAGER_SECRET` | Secreto para webhook de alertas | 90 días | Media |

## 2. Procedimientos de Rotación

### 2.1. Rotación de Contraseñas de Base de Datos

```bash
#!/bin/bash
# Script: rotate_db_password.sh

# 1. Generar nueva contraseña segura
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Conectar a PostgreSQL y cambiar contraseña
export PGPASSWORD="$OLD_PASSWORD"
psql -h localhost -U postgres -c "ALTER USER grupogad_user PASSWORD '$NEW_PASSWORD';"

# 3. Actualizar variable de entorno
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASSWORD/" .env.production

# 4. Actualizar Docker secrets (si se usa Docker Swarm)
echo "$NEW_PASSWORD" | docker secret create postgres_password_v$(date +%Y%m%d) -

# 5. Reiniciar servicios que usan la BD
docker compose -f docker-compose.prod.yml restart api

# 6. Verificar conectividad
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncpg
import asyncio
async def test_connection():
    try:
        conn = await asyncpg.connect(database_url='$NEW_DATABASE_URL')
        await conn.close()
        print('✅ Conexión exitosa con nueva contraseña')
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
asyncio.run(test_connection())
"

# 7. Registrar rotación en logs de auditoría
echo "$(date): Database password rotated" >> /var/log/grupogad/security_audit.log
```

### 2.2. Rotación de Claves JWT

```bash
#!/bin/bash
# Script: rotate_jwt_secret.sh

# 1. Generar nueva clave secreta
NEW_SECRET=$(openssl rand -hex 64)

# 2. Actualizar variable de entorno
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env.production

# 3. Reiniciar API gradualmente (rolling restart)
docker compose -f docker-compose.prod.yml scale api=2
sleep 30
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml scale api=1

# 4. Invalidar tokens activos (opcional, según política)
# Este comando dependería de la implementación específica
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB

# 5. Notificar a usuarios sobre nueva autenticación
curl -X POST "$TELEGRAM_WEBHOOK" -d "JWT secrets rotated. Users may need to re-authenticate."
```

### 2.3. Rotación de Credenciales de S3

```bash
#!/bin/bash
# Script: rotate_s3_credentials.sh

# 1. Crear nuevas credenciales en AWS
aws iam create-access-key --user-name grupogad-backup-user

# 2. Extraer nuevas credenciales (almacenar temporalmente)
NEW_ACCESS_KEY=$(aws iam list-access-keys --user-name grupogad-backup-user --query 'AccessKeyMetadata[-1].AccessKeyId' --output text)

# 3. Actualizar variables de entorno
sed -i "s/BACKUP_S3_ACCESS_KEY=.*/BACKUP_S3_ACCESS_KEY=$NEW_ACCESS_KEY/" .env.production
sed -i "s/BACKUP_S3_SECRET_KEY=.*/BACKUP_S3_SECRET_KEY=$NEW_SECRET_KEY/" .env.production

# 4. Probar nuevo acceso con backup de prueba
docker compose -f docker-compose.prod.yml exec api python scripts/test_s3_backup.py

# 5. Eliminar credenciales antiguas
aws iam delete-access-key --user-name grupogad-backup-user --access-key-id "$OLD_ACCESS_KEY"
```

## 3. Automatización de Rotación

### 3.1. Configuración de Cron Jobs

```bash
# /etc/cron.d/grupogad-security

# Rotación semanal de logs de seguridad
0 2 * * 0 root /opt/grupogad/scripts/rotate_security_logs.sh

# Rotación mensual de contraseñas no críticas
0 3 1 * * deploy /opt/grupogad/scripts/rotate_monthly_secrets.sh

# Rotación bimestral de JWT secrets
0 3 1 */2 * deploy /opt/grupogad/scripts/rotate_jwt_secret.sh

# Rotación trimestral de credenciales críticas
0 3 1 */3 * deploy /opt/grupogad/scripts/rotate_critical_secrets.sh

# Auditoría semanal de seguridad
0 4 * * 1 deploy /opt/grupogad/scripts/security_audit.sh
```

### 3.2. Script de Rotación Automática

```python
#!/usr/bin/env python3
"""
Script de rotación automática de secretos
Ejecuta rotaciones basadas en la edad de los secretos
"""

import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List
import subprocess
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/grupogad/secret_rotation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecretRotationManager:
    def __init__(self, config_file: str = "/opt/grupogad/config/secret_rotation.json"):
        self.config_file = Path(config_file)
        self.state_file = Path("/opt/grupogad/data/secret_rotation_state.json")
        self.load_config()
        self.load_state()
    
    def load_config(self):
        """Cargar configuración de rotación"""
        default_config = {
            "secrets": {
                "database_password": {"days": 90, "script": "rotate_db_password.sh"},
                "jwt_secret": {"days": 60, "script": "rotate_jwt_secret.sh"},
                "api_keys": {"days": 90, "script": "rotate_api_keys.sh"},
                "s3_credentials": {"days": 90, "script": "rotate_s3_credentials.sh"}
            },
            "notification": {
                "webhook_url": os.getenv("SECURITY_WEBHOOK_URL"),
                "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN"),
                "telegram_chat_id": os.getenv("SECURITY_CHAT_ID")
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file) as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_state(self):
        """Cargar estado de última rotación"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {}
    
    def save_state(self):
        """Guardar estado de rotación"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def needs_rotation(self, secret_name: str) -> bool:
        """Verificar si un secreto necesita rotación"""
        if secret_name not in self.state:
            return True
        
        last_rotation = datetime.datetime.fromisoformat(self.state[secret_name]["last_rotation"])
        rotation_interval = datetime.timedelta(days=self.config["secrets"][secret_name]["days"])
        
        return datetime.datetime.now() - last_rotation > rotation_interval
    
    def rotate_secret(self, secret_name: str) -> bool:
        """Rotar un secreto específico"""
        try:
            script_name = self.config["secrets"][secret_name]["script"]
            script_path = f"/opt/grupogad/scripts/{script_name}"
            
            logger.info(f"Iniciando rotación de {secret_name}")
            
            result = subprocess.run([script_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.state[secret_name] = {
                    "last_rotation": datetime.datetime.now().isoformat(),
                    "status": "success"
                }
                logger.info(f"Rotación exitosa de {secret_name}")
                self.send_notification(f"✅ Rotación exitosa: {secret_name}")
                return True
            else:
                logger.error(f"Error en rotación de {secret_name}: {result.stderr}")
                self.send_notification(f"❌ Error en rotación: {secret_name}\n{result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción durante rotación de {secret_name}: {e}")
            self.send_notification(f"❌ Excepción en rotación: {secret_name}\n{str(e)}")
            return False
    
    def send_notification(self, message: str):
        """Enviar notificación de rotación"""
        try:
            webhook_url = self.config["notification"]["webhook_url"]
            if webhook_url:
                import requests
                requests.post(webhook_url, json={"text": message})
        except Exception as e:
            logger.warning(f"Error enviando notificación: {e}")
    
    def run_rotation_check(self):
        """Ejecutar verificación y rotación de secretos"""
        logger.info("Iniciando verificación de rotación de secretos")
        
        rotations_needed = []
        for secret_name in self.config["secrets"]:
            if self.needs_rotation(secret_name):
                rotations_needed.append(secret_name)
        
        if not rotations_needed:
            logger.info("No se necesitan rotaciones en este momento")
            return
        
        logger.info(f"Secretos que necesitan rotación: {rotations_needed}")
        
        success_count = 0
        for secret_name in rotations_needed:
            if self.rotate_secret(secret_name):
                success_count += 1
        
        self.save_state()
        
        summary = f"Rotación completada: {success_count}/{len(rotations_needed)} exitosas"
        logger.info(summary)
        self.send_notification(summary)

if __name__ == "__main__":
    manager = SecretRotationManager()
    manager.run_rotation_check()
```

## 4. Auditorías de Seguridad

### 4.1. Checklist de Auditoría Semanal

```bash
#!/bin/bash
# Script: weekly_security_audit.sh

AUDIT_LOG="/var/log/grupogad/security_audit.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Iniciando auditoría semanal de seguridad" >> $AUDIT_LOG

# 1. Verificar permisos de archivos críticos
echo "[$DATE] Verificando permisos de archivos" >> $AUDIT_LOG
find /opt/grupogad -name "*.env*" -exec ls -la {} \; >> $AUDIT_LOG
find /opt/grupogad -name "*.key" -exec ls -la {} \; >> $AUDIT_LOG

# 2. Verificar usuarios con acceso sudo
echo "[$DATE] Usuarios con acceso sudo:" >> $AUDIT_LOG
getent group sudo >> $AUDIT_LOG

# 3. Verificar conexiones de red activas
echo "[$DATE] Conexiones de red activas:" >> $AUDIT_LOG
netstat -tulpn >> $AUDIT_LOG

# 4. Verificar logs de intentos de login fallidos
echo "[$DATE] Intentos de login fallidos:" >> $AUDIT_LOG
grep "Failed password" /var/log/auth.log | tail -10 >> $AUDIT_LOG

# 5. Verificar actualizaciones de seguridad pendientes
echo "[$DATE] Actualizaciones de seguridad pendientes:" >> $AUDIT_LOG
apt list --upgradable | grep -i security >> $AUDIT_LOG

# 6. Verificar integridad de archivos críticos
echo "[$DATE] Verificando integridad de archivos" >> $AUDIT_LOG
md5sum /opt/grupogad/.env.production >> $AUDIT_LOG
md5sum /opt/grupogad/docker-compose.prod.yml >> $AUDIT_LOG

# 7. Verificar certificados SSL próximos a expirar
echo "[$DATE] Verificando expiración de certificados SSL" >> $AUDIT_LOG
docker compose -f /opt/grupogad/docker-compose.prod.yml exec caddy caddy list-certificates

echo "[$DATE] Auditoría semanal completada" >> $AUDIT_LOG
```

### 4.2. Auditoría de Dependencias

```bash
#!/bin/bash
# Script: dependency_security_audit.sh

echo "Auditando dependencias de Python..."
pip-audit --desc --format=json --output=/var/log/grupogad/pip_audit.json

echo "Auditando imágenes Docker..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v /opt/grupogad:/tmp/grupogad \
  aquasec/trivy:latest image grupogad_api:latest \
  --format json --output /var/log/grupogad/trivy_audit.json

echo "Verificando configuración de Docker..."
docker-bench-security > /var/log/grupogad/docker_bench.txt
```

## 5. Políticas de Seguridad

### 5.1. Política de Contraseñas

- **Longitud mínima:** 16 caracteres para contraseñas de servicios
- **Complejidad:** Combinación de letras, números y símbolos especiales
- **Generación:** Usar generadores criptográficamente seguros (openssl, /dev/urandom)
- **Almacenamiento:** Nunca en texto plano, usar gestores de secretos
- **Rotación:** Según tabla de criticidad (60-180 días)

### 5.2. Política de Acceso

- **Principio de menor privilegio:** Acceso mínimo necesario
- **Autenticación multifactor:** Obligatoria para acceso administrativo
- **Segregación de roles:** Separar usuarios de aplicación y administración
- **Auditoría de acceso:** Log de todos los accesos y cambios

### 5.3. Política de Monitoreo

- **Alertas de seguridad:** Inmediatas para eventos críticos
- **Logs de auditoría:** Retención mínima de 1 año
- **Revisión regular:** Análisis semanal de logs de seguridad
- **Respuesta a incidentes:** Procedimientos documentados

## 6. Plan de Respuesta a Incidentes

### 6.1. Compromiso de Credenciales

1. **Detección:** Alert automático o reporte manual
2. **Contención:** Rotación inmediata de credenciales afectadas
3. **Evaluación:** Análisis del alcance del compromiso
4. **Erradicación:** Cierre de vectores de ataque
5. **Recuperación:** Restauración de servicios normales
6. **Lecciones aprendidas:** Documentación y mejoras

### 6.2. Contactos de Emergencia

| Rol | Contacto | Escalado |
|-----|----------|----------|
| DevOps Principal | +34-XXX-XXX-XXX | Inmediato |
| Administrador de Sistemas | +34-XXX-XXX-XXX | 15 minutos |
| Responsable de Seguridad | +34-XXX-XXX-XXX | 30 minutos |
| Gerencia IT | +34-XXX-XXX-XXX | 1 hora |

---

## Referencias

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)