#!/usr/bin/env python3
"""
GitHub Secrets Configuration Reference
Script para verificar y validar secrets configurados en GitHub

Uso:
    python3 verify_secrets.py
    
Este script es una referencia de qué secrets espera el CI/CD
"""

# ============================================================================
# GITHUB SECRETS CONFIGURATION REFERENCE
# ============================================================================
# 
# Este archivo documenta todos los secrets que deben configurarse en:
# https://github.com/eevans-d/GRUPO_GAD/settings/secrets/actions
#
# Total: 15 secrets (13 requeridos + 2 opcionales)
# ============================================================================

REQUIRED_SECRETS = {
    # ========== SERVIDOR ==========
    "SSH_PRIVATE_KEY": {
        "description": "Clave privada SSH para acceder al servidor",
        "type": "Private Key (RSA format)",
        "format": "-----BEGIN RSA PRIVATE KEY-----\n[content]\n-----END RSA PRIVATE KEY-----",
        "how_to_get": "cat ~/.ssh/id_rsa",
        "required": True,
        "tier": "Tier 1",
    },
    "SERVER_HOST": {
        "description": "IP o dominio del servidor de producción",
        "type": "IP Address or Domain",
        "format": "192.168.1.100 o prod.example.com",
        "how_to_get": "ssh user@server 'hostname -I'",
        "required": True,
        "tier": "Tier 1",
    },
    "SERVER_USERNAME": {
        "description": "Usuario SSH para acceder al servidor",
        "type": "Username",
        "format": "ubuntu, ec2-user, admin, root",
        "how_to_get": "whoami",
        "required": True,
        "tier": "Tier 1",
    },

    # ========== APLICACIÓN ==========
    "SECRET_KEY": {
        "description": "Clave secreta para JWT y encriptación",
        "type": "Random string",
        "format": "32+ caracteres aleatorios",
        "how_to_get": "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"",
        "required": True,
        "tier": "Tier 1",
    },

    # ========== DATABASE ==========
    "DATABASE_URL": {
        "description": "URL de conexión a PostgreSQL en producción",
        "type": "PostgreSQL Connection String",
        "format": "postgresql://user:password@host:5432/database",
        "how_to_get": "psql -U postgres -h localhost -c \"SELECT current_database();\"",
        "required": True,
        "tier": "Tier 2",
    },
    "POSTGRES_USER": {
        "description": "Usuario de PostgreSQL",
        "type": "Username",
        "format": "app_user, postgres, grupogad_user",
        "how_to_get": "psql -U postgres -l",
        "required": True,
        "tier": "Tier 2",
    },
    "POSTGRES_PASSWORD": {
        "description": "Contraseña de PostgreSQL",
        "type": "Password",
        "format": "16+ caracteres, incluir símbolos especiales",
        "how_to_get": "openssl rand -base64 20",
        "required": True,
        "tier": "Tier 2",
    },
    "POSTGRES_DB": {
        "description": "Nombre de base de datos",
        "type": "Database name",
        "format": "app_db, grupogad_prod, production",
        "how_to_get": "psql -U postgres -l | grep database_name",
        "required": True,
        "tier": "Tier 2",
    },

    # ========== REDIS ==========
    "REDIS_URL": {
        "description": "URL de conexión a Redis en producción",
        "type": "Redis Connection String",
        "format": "redis://host:6379 o redis://:password@host:6379",
        "how_to_get": "redis-cli -h localhost PING",
        "required": True,
        "tier": "Tier 3",
    },

    # ========== DOCKER REGISTRY ==========
    "DOCKER_USERNAME": {
        "description": "Usuario de Docker Registry (DockerHub, ECR, etc.)",
        "type": "Username",
        "format": "tu_usuario_dockerhub o aws_account_id (ECR)",
        "how_to_get": "docker logout && docker login",
        "required": True,
        "tier": "Tier 3",
    },
    "DOCKER_PASSWORD": {
        "description": "Token/contraseña de Docker Registry",
        "type": "Access Token or Password",
        "format": "Token de DockerHub o AWS ECR token",
        "how_to_get": "https://hub.docker.com/settings/security",
        "required": True,
        "tier": "Tier 3",
    },

    # ========== BACKUPS ==========
    "BACKUP_ACCESS_KEY": {
        "description": "Access key para almacenamiento de backups (AWS S3)",
        "type": "AWS Access Key ID",
        "format": "AKIA... (20 caracteres típicamente)",
        "how_to_get": "AWS IAM → Users → Security credentials",
        "required": True,
        "tier": "Tier 4",
    },
    "BACKUP_SECRET_KEY": {
        "description": "Secret key para almacenamiento de backups (AWS S3)",
        "type": "AWS Secret Access Key",
        "format": "Contraseña larga aleatoria",
        "how_to_get": "AWS IAM → Users → Security credentials",
        "required": True,
        "tier": "Tier 4",
    },
}

OPTIONAL_SECRETS = {
    # ========== OPCIONAL: DNS & MONITOREO ==========
    "CLOUDFLARE_TOKEN": {
        "description": "Token de Cloudflare para DNS/certificados",
        "type": "API Token",
        "format": "Token desde Cloudflare dashboard",
        "how_to_get": "https://dash.cloudflare.com/profile/api-tokens",
        "required": False,
        "tier": "Tier 4",
    },
    "MONITORING_TOKEN": {
        "description": "Token para servicio de monitoreo (DataDog, New Relic, etc.)",
        "type": "API Token",
        "format": "Token desde plataforma de monitoreo",
        "how_to_get": "Dashboard del servicio → API Tokens",
        "required": False,
        "tier": "Tier 4",
    },
}

# Merge all secrets
ALL_SECRETS = {**REQUIRED_SECRETS, **OPTIONAL_SECRETS}

# ============================================================================
# VERIFICACIÓN Y VALIDACIÓN
# ============================================================================

def validate_secrets():
    """
    Verifica que todos los secrets requeridos estén disponibles
    """
    import os
    from typing import Dict, List
    
    print("🔐 GitHub Secrets Configuration Verification")
    print("=" * 70)
    
    missing: List[str] = []
    found: List[str] = []
    
    print("\n📋 Verificando secrets requeridos...\n")
    
    for secret_name, secret_info in REQUIRED_SECRETS.items():
        # Nota: En CI/CD, estos secrets NO estarán disponibles localmente
        # Este script es solo para referencia
        print(f"  [{secret_name}]")
        print(f"    Description: {secret_info['description']}")
        print(f"    Type: {secret_info['type']}")
        print(f"    Tier: {secret_info['tier']}")
        print(f"    ⚠️  Status: NOT CHECKED (Solo disponible en GitHub UI)")
        print()
    
    print("\n" + "=" * 70)
    print(f"✅ Total secrets requeridos: {len(REQUIRED_SECRETS)}")
    print(f"⏳ Total secrets opcionales: {len(OPTIONAL_SECRETS)}")
    print(f"📊 Total secrets: {len(ALL_SECRETS)}")

def print_secrets_table():
    """Imprime tabla de referencia de todos los secrets"""
    
    print("\n🔑 SECRETS REFERENCE TABLE")
    print("=" * 100)
    print(f"{'Secret Name':<25} {'Type':<20} {'Tier':<8} {'Required':<10}")
    print("=" * 100)
    
    for secret_name in sorted(ALL_SECRETS.keys()):
        info = ALL_SECRETS[secret_name]
        required = "✅ Yes" if info['required'] else "⏳ Optional"
        print(f"{secret_name:<25} {info['type']:<20} {info['tier']:<8} {required:<10}")
    
    print("=" * 100)

def generate_github_actions_secrets():
    """
    Genera un template para GitHub Actions workflow
    Muestra qué secrets espera cada job
    """
    
    template = """
# GitHub Actions Workflow - Secrets Usage Reference
# ================================================

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # Acceso al servidor
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts

      # Conectar a base de datos
      - name: Setup Database
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
        run: |
          psql "${{ secrets.DATABASE_URL }}" -c "\\dt"

      # Redis
      - name: Setup Redis
        env:
          REDIS_URL: ${{ secrets.REDIS_URL }}
        run: |
          redis-cli -u "${{ secrets.REDIS_URL }}" PING

      # Docker Registry
      - name: Login to Docker Registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

      # Secrets para aplicación
      - name: Configure Application
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
        run: |
          echo "SECRET_KEY configured"

      # Backups
      - name: Configure Backups
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.BACKUP_ACCESS_KEY }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.BACKUP_SECRET_KEY }}
        run: |
          aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
          aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY

      # Opcionales: Monitoreo y DNS
      - name: Configure Optional Services
        env:
          CLOUDFLARE_TOKEN: ${{ secrets.CLOUDFLARE_TOKEN }}
          MONITORING_TOKEN: ${{ secrets.MONITORING_TOKEN }}
        if: ${{ env.CLOUDFLARE_TOKEN != '' }}
        run: |
          echo "Optional services configured"
"""
    
    print(template)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "validate":
            validate_secrets()
        elif command == "table":
            print_secrets_table()
        elif command == "workflow":
            generate_github_actions_secrets()
        else:
            print(f"Comando desconocido: {command}")
            print("Comandos disponibles: validate, table, workflow")
    else:
        # Mostrar todo por defecto
        validate_secrets()
        print_secrets_table()
        print("\n💡 Para ver el template de workflow, ejecuta: python3 verify_secrets.py workflow")
