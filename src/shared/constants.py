# -*- coding: utf-8 -*-
"""
Constantes globales del sistema GRUPO_GAD.
"""

from enum import Enum
from typing import Dict, List


# === NIVELES DE USUARIO ===
class UserLevel(int, Enum):
    """Niveles de autorización de usuarios."""
    LEVEL_1 = 1  # Efectivo básico
    LEVEL_2 = 2  # Supervisor
    LEVEL_3 = 3  # Administrador


# === ESTADOS DE TAREAS ===
class TaskStatus(str, Enum):
    """Estados posibles de una tarea."""
    PROGRAMMED = "programada"
    IN_PROGRESS = "en_curso"
    COMPLETED = "finalizada"
    CANCELLED = "cancelada"
    PAUSED = "pausada"


# === ESTADOS DE DISPONIBILIDAD ===
class AvailabilityStatus(str, Enum):
    """Estados de disponibilidad de efectivos."""
    AVAILABLE = "disponible"
    ON_TASK = "en_tarea"
    OFF_DUTY = "fuera_servicio"
    UNAVAILABLE = "no_disponible"


# === PRIORIDADES DE TAREAS ===
class TaskPriority(int, Enum):
    """Niveles de prioridad de tareas."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


# === TIPOS DE TAREAS ===
class TaskType(str, Enum):
    """Tipos de tareas."""
    PATRULLAJE = "patrullaje"
    INVESTIGACION = "investigacion"
    VIGILANCIA = "vigilancia"
    INTERVENCION = "intervencion"
    ADMINISTRATIVA = "administrativa"
    ENTRENAMIENTO = "entrenamiento"



# === PERMISOS POR NIVEL ===
PERMISSIONS_MATRIX: Dict[UserLevel, List[str]] = {
    UserLevel.LEVEL_1: [
        "view_assigned_tasks",
        "update_task_status",
        "send_task_updates"
    ],
    UserLevel.LEVEL_2: [
        "view_assigned_tasks",
        "update_task_status",
        "send_task_updates",
        "create_tasks",
        "assign_tasks",
        "view_team_metrics"
    ],
    UserLevel.LEVEL_3: [
        "view_all_tasks",
        "create_tasks",
        "assign_tasks",
        "modify_tasks",
        "delete_tasks",
        "manage_users",
        "view_system_metrics",
        "configure_system"
    ]
}


# === CONFIGURACIÓN DE SEGURIDAD ===
SECURITY_CONFIG = {
    "jwt_algorithm": "HS256",
    "jwt_access_token_expires": 1800,  # 30 minutos
    "password_min_length": 8,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30
}


# === CONFIGURACIÓN DE CACHE ===
CACHE_CONFIG = {
    "default_ttl": 300,  # 5 minutos
    "user_ttl": 1800,    # 30 minutos
    "task_ttl": 600,     # 10 minutos
    "metrics_ttl": 3600  # 1 hora
}
