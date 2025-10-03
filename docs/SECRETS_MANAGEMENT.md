# 🔐 Gestión Segura de Secretos - GRUPO_GAD

## Guía Gubernamental para Manejo de Credenciales

### ⚠️ Principios de Seguridad

1. **NUNCA** versionar secretos en el repositorio
2. **NUNCA** hardcodear credenciales en docker-compose.yml
3. **SIEMPRE** usar variables de entorno o Docker Secrets
4. **ROTAR** secretos regularmente según políticas gubernamentales

---

## 📋 Configuración por Entorno

### **Desarrollo Local**

```bash
# 1. Copiar template
cp .env.example .env

# 2. Editar .env con valores reales
nano .env

# 3. Asegurar que .env está en .gitignore
echo ".env" >> .gitignore

# 4. Ejecutar con docker-compose
docker-compose up -d
```

**Secretos necesarios:**
- `JWT_SECRET_KEY`: Mínimo 32 caracteres aleatorios
- `DATABASE_URL`: URL completa de PostgreSQL
- `TELEGRAM_TOKEN`: Token de @BotFather
- `SECRET_KEY`: Clave secreta de la aplicación

### **Staging/Producción con Docker Secrets**

```bash
# 1. Inicializar Docker Swarm (si no está activo)
docker swarm init

# 2. Crear secrets desde archivos o stdin
echo "tu-jwt-secret-key-super-seguro-min-32-chars" | docker secret create jwt_secret_key -
echo "postgresql://user:pass@db:5432/grupo_gad" | docker secret create database_url -
echo "tu-telegram-token-aqui" | docker secret create telegram_token -
echo "tu-secret-key-aqui" | docker secret create app_secret_key -

# 3. Desplegar stack con docker-compose.prod.yml
docker stack deploy -c docker-compose.prod.yml grupo-gad

# 4. Verificar secrets cargados
docker secret ls
```

### **Producción con Gestores de Secretos**

#### **AWS Secrets Manager**
```bash
# Instalar AWS CLI y configurar
aws secretsmanager create-secret \
  --name grupo-gad/jwt-secret \
  --secret-string "tu-jwt-secret-key"

# Recuperar en runtime
export JWT_SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id grupo-gad/jwt-secret \
  --query SecretString \
  --output text)
```

#### **HashiCorp Vault**
```bash
# Guardar secret
vault kv put secret/grupo-gad/jwt jwt_secret_key="tu-jwt-secret"

# Recuperar en runtime
export JWT_SECRET_KEY=$(vault kv get -field=jwt_secret_key secret/grupo-gad/jwt)
```

---

## 🔄 Rotación de Secretos

### **Calendario de Rotación Gubernamental**

| Secreto | Frecuencia | Prioridad |
|---------|-----------|-----------|
| JWT_SECRET_KEY | 90 días | ALTA |
| DATABASE_URL (password) | 60 días | CRÍTICA |
| TELEGRAM_TOKEN | 180 días | MEDIA |
| SECRET_KEY | 90 días | ALTA |

### **Procedimiento de Rotación**

```bash
# 1. Generar nuevo secret
NEW_JWT=$(openssl rand -base64 48)

# 2. Actualizar en gestor de secrets
docker secret create jwt_secret_key_v2 <(echo "$NEW_JWT")

# 3. Actualizar servicio para usar nuevo secret
docker service update \
  --secret-rm jwt_secret_key \
  --secret-add source=jwt_secret_key_v2,target=jwt_secret_key \
  grupo-gad_api

# 4. Validar funcionamiento
curl -f https://grupo-gad.gob.cl/health/government

# 5. Eliminar secret antiguo (después de validar)
docker secret rm jwt_secret_key
```

---

## ✅ Checklist de Seguridad

### **Pre-Despliegue**
- [ ] `.env` en `.gitignore`
- [ ] `.env.example` sin valores reales
- [ ] `docker-compose.yml` usa `${VARIABLES}`
- [ ] Secrets no hardcoded en código fuente
- [ ] JWT_SECRET_KEY ≥ 32 caracteres
- [ ] DATABASE_URL con password fuerte

### **Producción**
- [ ] Docker Secrets configurado
- [ ] O gestor de secrets externo (Vault/AWS)
- [ ] Rotación automática programada
- [ ] Auditoría de acceso a secrets habilitada
- [ ] Backup encriptado de secrets
- [ ] Documentación de recuperación ante desastres

---

## 🚨 Respuesta a Incidentes

### **Si un Secret se Compromete:**

1. **Inmediato (< 5 minutos):**
   ```bash
   # Rotar secret comprometido
   docker service update --force grupo-gad_api
   ```

2. **Corto Plazo (< 1 hora):**
   - Generar nuevo secret
   - Desplegar con nuevo secret
   - Invalidar tokens JWT antiguos
   - Revisar logs de acceso

3. **Seguimiento (< 24 horas):**
   - Análisis forense
   - Notificar a stakeholders
   - Actualizar procedimientos
   - Post-mortem documentado

---

## 📚 Recursos Adicionales

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [12 Factor App - Config](https://12factor.net/config)

---

## 🏛️ Compliance Gubernamental

Este sistema de gestión de secretos cumple con:
- ✅ Estándares de seguridad gubernamental
- ✅ Principio de privilegio mínimo
- ✅ Auditoría completa de accesos
- ✅ Rotación periódica obligatoria
- ✅ Encriptación en reposo y tránsito

**Última actualización:** 2025-10-03  
**Revisión:** Seguridad Gubernamental GRUPO_GAD
