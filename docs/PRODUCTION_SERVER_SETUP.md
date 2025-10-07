# Configuración del Servidor de Producción - GRUPO_GAD

Este documento detalla paso a paso la configuración de un servidor para el despliegue en producción de GRUPO_GAD.

## 1. Requisitos del Servidor

**Configuración mínima recomendada:**
- **Sistema Operativo:** Ubuntu 22.04 LTS
- **CPU:** 4 vCPUs
- **RAM:** 8 GB
- **Almacenamiento:** 50 GB SSD
- **Red:** Conectividad pública con IP estática
- **Puertos necesarios:** 22 (SSH), 80 (HTTP), 443 (HTTPS)

## 2. Instalación Base

### 2.1 Actualizar el Sistema

```bash
# Actualizar la lista de paquetes
sudo apt update

# Actualizar los paquetes instalados
sudo apt upgrade -y

# Instalar paquetes esenciales
sudo apt install -y curl wget git htop vim tmux fail2ban unzip
```

### 2.2 Configurar Zona Horaria

```bash
# Configurar a UTC o tu zona horaria preferida
sudo timedatectl set-timezone UTC
```

### 2.3 Configurar Firewall (UFW)

```bash
# Instalar UFW si no está presente
sudo apt install -y ufw

# Configuración básica
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH (restringir si es posible a IPs conocidas)
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Habilitar firewall
sudo ufw enable
```

### 2.4 Configurar Fail2ban

```bash
# Fail2ban ya debería estar instalado, ahora configuramos
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Editar configuración según sea necesario
sudo vim /etc/fail2ban/jail.local

# Reiniciar servicio
sudo systemctl restart fail2ban
```

### 2.5 Configurar Usuario y Acceso SSH

```bash
# Crear usuario para el despliegue
sudo adduser deploy
sudo usermod -aG sudo deploy

# Configurar SSH para el nuevo usuario
sudo su - deploy
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Añadir tu clave pública al archivo authorized_keys
echo "TU_CLAVE_PUBLICA_SSH" >> ~/.ssh/authorized_keys

# Volver a tu usuario
exit

# Configurar SSH para más seguridad
sudo vim /etc/ssh/sshd_config
```

Cambios recomendados en `sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```

Reiniciar SSH:
```bash
sudo systemctl restart sshd
```

## 3. Instalación de Docker y Docker Compose

### 3.1 Instalar Docker

```bash
# Desinstalar versiones antiguas si existen
sudo apt remove docker docker-engine docker.io containerd runc

# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Añadir clave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Añadir repositorio de Docker
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Actualizar paquetes e instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Iniciar y habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Añadir usuario al grupo Docker (no necesario si se ejecuta todo como root)
sudo usermod -aG docker deploy
```

### 3.2 Instalar Docker Compose

```bash
# Instalar Docker Compose directamente
sudo apt install -y docker-compose-plugin

# Verificar instalación
docker compose version
```

## 4. Configuración del Sistema de Archivos

### 4.1 Crear Estructura de Directorios

```bash
# Crear directorio principal de la aplicación
sudo mkdir -p /opt/grupogad
sudo chown deploy:deploy /opt/grupogad

# Crear directorios para datos persistentes
mkdir -p /opt/grupogad/data
mkdir -p /opt/grupogad/backups
mkdir -p /opt/grupogad/logs
mkdir -p /opt/grupogad/ssl
```

### 4.2 Configurar Montaje para Backups (Opcional)

Si utilizas un volumen separado para backups:

```bash
# Montar el volumen para backups (ejemplo con un volumen adicional)
sudo mount /dev/sdb1 /opt/grupogad/backups
```

## 5. Configuración de DNS

Asegúrate de configurar los registros DNS para apuntar a la IP del servidor:

1. Registros A para dominio principal y subdominio www:
   ```
   tudominio.com.       IN A      IP.DEL.SERVIDOR
   www.tudominio.com.   IN A      IP.DEL.SERVIDOR
   ```

2. Configurar registros SPF, DKIM y DMARC si se usará envío de correos.

## 6. Preparación para Despliegue

### 6.1 Clonar Repositorio

```bash
# Cambiar al directorio de la aplicación
cd /opt/grupogad

# Clonar el repositorio
git clone https://github.com/eevans-d/GRUPO_GAD.git .
```

### 6.2 Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.production.example .env.production

# Editar el archivo con valores reales
vim .env.production
```

### 6.3 Configurar Dominios en Caddyfile

```bash
# Editar Caddyfile para usar el dominio real
vim Caddyfile
```

Cambiar la configuración para usar tu dominio:
```
tudominio.com {
    # Resto de la configuración...
}
```

## 7. Monitoreo y Alertas

### 7.1 Configurar Monitoreo Básico

```bash
# Instalar Prometheus Node Exporter para métricas del sistema
sudo apt install -y prometheus-node-exporter

# Iniciar y habilitar el servicio
sudo systemctl start prometheus-node-exporter
sudo systemctl enable prometheus-node-exporter
```

### 7.2 Configurar Rotación de Logs

```bash
# Instalar logrotate si no está presente
sudo apt install -y logrotate

# Crear configuración de rotación de logs
sudo vim /etc/logrotate.d/grupogad
```

Contenido de la configuración:
```
/opt/grupogad/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
}
```

## 8. Seguridad Adicional

### 8.1 Configurar Copias de Seguridad Programadas

```bash
# Añadir cron job para ejecutar backups
(crontab -l ; echo "0 1 * * * cd /opt/grupogad && make backup >> /opt/grupogad/logs/backup.log 2>&1") | crontab -
```

### 8.2 Verificación de Integridad de Archivos (Opcional)

```bash
# Instalar aide
sudo apt install -y aide

# Inicializar la base de datos AIDE
sudo aideinit

# Mover la base de datos inicial a su ubicación final
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Configurar verificaciones diarias
sudo cp /usr/share/aide/config/aide.conf /etc/aide/aide.conf
```

## 9. Verificación Final

```bash
# Verificar estado del sistema
df -h
free -m
htop

# Verificar conectividad
curl -I http://localhost:80

# Verificar Docker
docker info
docker compose version

# Verificar permisos
ls -la /opt/grupogad
```

## Próximos Pasos

Una vez completada esta configuración, procede con:

1. **Despliegue inicial** siguiendo la [Guía de Despliegue](DEPLOYMENT_GUIDE.md)
2. **Verificación post-despliegue** usando el [Checklist de Producción](../CHECKLIST_PRODUCCION.md)

---

**Documentación relacionada:**
- [Guía de Despliegue](DEPLOYMENT_GUIDE.md)
- [Estrategia de Backup y Restauración](BACKUP_RESTORE_STRATEGY.md)
- [Guía de CI/CD](CI_CD_GUIDE.md)