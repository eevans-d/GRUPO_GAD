#!/usr/bin/env bash
# ----------------------------------------------------------------
# Nombre: setup_production_server.sh
# Descripción: Script para configuración inicial de un servidor de producción
# Autor: GRUPO_GAD
# Fecha: 2025-10-07
# Versión: 1.0
# ----------------------------------------------------------------

# Función para imprimir mensajes con formato
print_section() {
    echo ""
    echo "======================================================================"
    echo "    $1"
    echo "======================================================================"
}

print_step() {
    echo "➤ $1"
}

print_success() {
    echo "✓ $1"
}

print_error() {
    echo "✗ $1"
}

# Comprobar que el script se ejecuta como root o con sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root o con sudo"
    exit 1
fi

# Comprobar la distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        print_error "Este script está diseñado para Ubuntu, pero se detectó: $ID"
        exit 1
    fi
    
    if [ "$VERSION_ID" != "22.04" ] && [ "$VERSION_ID" != "20.04" ]; then
        print_error "Se recomienda Ubuntu 22.04 LTS, pero se detectó: $VERSION_ID"
        read -p "¿Deseas continuar de todos modos? (s/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
else
    print_error "No se pudo determinar la distribución del sistema operativo"
    exit 1
fi

# Configurar variables
DEPLOY_USER="deploy"
APP_DIR="/opt/grupogad"
BACKUP_DIR="${APP_DIR}/backups"
LOGS_DIR="${APP_DIR}/logs"
DATA_DIR="${APP_DIR}/data"

print_section "INICIANDO CONFIGURACIÓN DEL SERVIDOR DE PRODUCCIÓN - GRUPO_GAD"
echo "Fecha: $(date)"
echo "Sistema: $PRETTY_NAME"
echo ""

# 1. Actualizar el sistema
print_section "1. Actualización del Sistema"
print_step "Actualizando lista de paquetes..."
apt update
if [ $? -ne 0 ]; then
    print_error "Error al actualizar la lista de paquetes"
    exit 1
fi

print_step "Actualizando paquetes instalados..."
apt upgrade -y
if [ $? -ne 0 ]; then
    print_error "Error al actualizar los paquetes"
    exit 1
fi

print_step "Instalando paquetes esenciales..."
apt install -y curl wget git htop vim tmux fail2ban unzip
if [ $? -ne 0 ]; then
    print_error "Error al instalar paquetes esenciales"
    exit 1
fi
print_success "Sistema actualizado correctamente"

# 2. Configurar zona horaria
print_section "2. Configuración de Zona Horaria"
print_step "Configurando zona horaria a UTC..."
timedatectl set-timezone UTC
print_success "Zona horaria configurada: $(timedatectl | grep "Time zone")"

# 3. Configurar firewall
print_section "3. Configuración del Firewall (UFW)"
print_step "Instalando UFW..."
apt install -y ufw
if [ $? -ne 0 ]; then
    print_error "Error al instalar UFW"
    exit 1
fi

print_step "Configurando reglas de firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

print_step "Habilitando firewall..."
echo "y" | ufw enable
print_success "Firewall configurado correctamente. Estado:"
ufw status

# 4. Configurar Fail2ban
print_section "4. Configuración de Fail2ban"
print_step "Configurando Fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl restart fail2ban
systemctl enable fail2ban
print_success "Fail2ban configurado y activado"

# 5. Crear usuario para el despliegue
print_section "5. Creación de Usuario para Despliegue"
print_step "Verificando si el usuario ${DEPLOY_USER} existe..."
if id "$DEPLOY_USER" &>/dev/null; then
    print_success "El usuario ${DEPLOY_USER} ya existe"
else
    print_step "Creando usuario ${DEPLOY_USER}..."
    adduser --disabled-password --gecos "" $DEPLOY_USER
    usermod -aG sudo $DEPLOY_USER
    print_success "Usuario ${DEPLOY_USER} creado"
    
    print_step "Configurando directorio SSH..."
    mkdir -p /home/$DEPLOY_USER/.ssh
    chmod 700 /home/$DEPLOY_USER/.ssh
    touch /home/$DEPLOY_USER/.ssh/authorized_keys
    chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
    chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
    
    echo ""
    echo "IMPORTANTE: Añade tu clave SSH pública al archivo authorized_keys:"
    echo ""
    echo "  echo 'TU_CLAVE_PUBLICA_SSH' >> /home/${DEPLOY_USER}/.ssh/authorized_keys"
    echo ""
fi

# 6. Configurar SSH seguro
print_section "6. Configuración de SSH"
print_step "Endureciendo configuración de SSH..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
print_success "SSH configurado con seguridad mejorada"

# 7. Instalar Docker
print_section "7. Instalación de Docker"
print_step "Comprobando si Docker ya está instalado..."
if command -v docker &> /dev/null; then
    print_success "Docker ya está instalado: $(docker --version)"
else
    print_step "Desinstalando versiones antiguas si existen..."
    apt remove -y docker docker-engine docker.io containerd runc

    print_step "Instalando dependencias..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common

    print_step "Añadiendo clave GPG oficial de Docker..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    print_step "Añadiendo repositorio de Docker..."
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    print_step "Actualizando paquetes e instalando Docker..."
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    print_step "Iniciando y habilitando Docker..."
    systemctl start docker
    systemctl enable docker

    print_step "Añadiendo usuario ${DEPLOY_USER} al grupo Docker..."
    usermod -aG docker $DEPLOY_USER

    print_success "Docker instalado correctamente: $(docker --version)"
    print_success "Docker Compose instalado: $(docker compose version)"
fi

# 8. Crear estructura de directorios
print_section "8. Configuración del Sistema de Archivos"
print_step "Creando estructura de directorios..."
mkdir -p $APP_DIR
mkdir -p $BACKUP_DIR
mkdir -p $LOGS_DIR
mkdir -p $DATA_DIR
mkdir -p ${APP_DIR}/ssl

# Asignar permisos
chown -R $DEPLOY_USER:$DEPLOY_USER $APP_DIR
print_success "Estructura de directorios creada en ${APP_DIR}"

# 9. Configurar logrotate
print_section "9. Configuración de Rotación de Logs"
print_step "Configurando logrotate para la aplicación..."
cat > /etc/logrotate.d/grupogad << EOF
${LOGS_DIR}/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ${DEPLOY_USER} ${DEPLOY_USER}
}
EOF
print_success "Configuración de logrotate creada"

# 10. Instalar herramientas adicionales de monitoreo
print_section "10. Configuración de Monitoreo Básico"
print_step "Instalando Prometheus Node Exporter..."
apt install -y prometheus-node-exporter
systemctl start prometheus-node-exporter
systemctl enable prometheus-node-exporter
print_success "Prometheus Node Exporter instalado y activado"

# 11. Resumen final
print_section "11. Verificación Final"
echo "Espacio en disco:"
df -h
echo ""

echo "Memoria disponible:"
free -m
echo ""

echo "Estado de servicios críticos:"
systemctl status docker --no-pager | head -n 5
systemctl status ssh --no-pager | head -n 5
systemctl status fail2ban --no-pager | head -n 5
echo ""

print_section "CONFIGURACIÓN DEL SERVIDOR COMPLETADA"
echo ""
echo "Próximos pasos:"
echo "1. Añade tu clave SSH pública al usuario ${DEPLOY_USER} si aún no lo has hecho"
echo "2. Configura los registros DNS para apuntar a este servidor"
echo "3. Clona el repositorio GRUPO_GAD en ${APP_DIR}"
echo "4. Copia .env.production.example a .env.production y configura los valores"
echo "5. Despliega la aplicación según la guía DEPLOYMENT_GUIDE.md"
echo ""
echo "Documentación relacionada:"
echo "- docs/DEPLOYMENT_GUIDE.md"
echo "- docs/BACKUP_RESTORE_STRATEGY.md"
echo "- docs/CI_CD_GUIDE.md"
echo "- CHECKLIST_PRODUCCION.md"
echo ""
echo "¡Servidor listo para el despliegue!"