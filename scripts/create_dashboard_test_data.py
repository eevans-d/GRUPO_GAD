#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear datos de prueba para el dashboard.

Crea tareas georreferenciadas en Buenos Aires con diferentes prioridades
para demostrar la funcionalidad del mapa del dashboard.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.crud.crud_tarea import tarea as crud_tarea
from src.api.crud.crud_usuario import usuario as crud_usuario
from src.core.database import init_db, get_db_session
from src.schemas.tarea import TareaCreate
from src.shared.constants import TaskPriority, TaskStatus, TaskType
from config.settings import get_settings

# Coordenadas de Buenos Aires y alrededores
SAMPLE_LOCATIONS = [
    # Buenos Aires Centro
    (-34.6037, -58.3816, "Plaza de Mayo", TaskPriority.MEDIUM),
    (-34.6092, -58.3732, "Puerto Madero", TaskPriority.HIGH),
    (-34.5889, -58.3974, "Recoleta", TaskPriority.LOW),
    (-34.6158, -58.3731, "San Telmo", TaskPriority.MEDIUM),
    (-34.5493, -58.4582, "Belgrano", TaskPriority.LOW),
    
    # Operativos críticos
    (-34.6283, -58.3712, "La Boca - Emergencia", TaskPriority.CRITICAL),
    (-34.5836, -58.4425, "Palermo - Patrullaje", TaskPriority.HIGH),
    (-34.6472, -58.4642, "Barracas - Investigación", TaskPriority.URGENT),
    
    # Zona Sur
    (-34.7297, -58.2663, "Quilmes", TaskPriority.MEDIUM),
    (-34.8144, -58.2775, "Berazategui", TaskPriority.LOW),
    
    # Zona Norte  
    (-34.5019, -58.5161, "San Isidro", TaskPriority.HIGH),
    (-34.4613, -58.5361, "Tigre", TaskPriority.MEDIUM),
    
    # GBA Oeste
    (-34.6354, -58.5606, "Morón", TaskPriority.URGENT),
    (-34.7090, -58.7346, "Merlo", TaskPriority.LOW),
]

TASK_TEMPLATES = {
    TaskPriority.CRITICAL: [
        ("Emergencia en curso - Requiere intervención inmediata", TaskType.INTERVENCION),
        ("Operativo antidrogas - Allanamiento", TaskType.INVESTIGACION),
        ("Disturbios - Control de multitudes", TaskType.INTERVENCION),
    ],
    TaskPriority.URGENT: [
        ("Patrullaje nocturno zona conflictiva", TaskType.PATRULLAJE),
        ("Seguimiento sospechoso - Vigilancia", TaskType.VIGILANCIA),
        ("Operativo conjunto con fiscalía", TaskType.INVESTIGACION),
    ],
    TaskPriority.HIGH: [
        ("Control de tránsito en zona céntrica", TaskType.PATRULLAJE),
        ("Vigilancia de evento público", TaskType.VIGILANCIA),
        ("Relevamiento de seguridad", TaskType.ADMINISTRATIVA),
    ],
    TaskPriority.MEDIUM: [
        ("Ronda preventiva barrial", TaskType.PATRULLAJE),
        ("Atención al público - Comisaría", TaskType.ADMINISTRATIVA),
        ("Inspección de comercios", TaskType.ADMINISTRATIVA),
    ],
    TaskPriority.LOW: [
        ("Capacitación en normativas", TaskType.ENTRENAMIENTO),
        ("Mantenimiento de equipos", TaskType.ADMINISTRATIVA),
        ("Tareas administrativas", TaskType.ADMINISTRATIVA),
    ]
}


async def create_test_tasks():
    """Crear tareas de prueba georreferenciadas."""
    settings = get_settings()
    db_url = settings.assemble_db_url()
    
    if not db_url:
        print("❌ Error: No se pudo determinar la URL de la base de datos")
        print("Configura DATABASE_URL o las variables POSTGRES_*")
        return False
    
    print("🔌 Conectando a la base de datos...")
    init_db(db_url)
    
    async for session in get_db_session():
        try:
            # Obtener un usuario admin para asignar las tareas
            admin_user = await crud_usuario.get_by_email(session, email="admin@grupogad.com")
            
            if not admin_user:
                print("❌ Error: No se encontró usuario admin@grupogad.com")
                print("Crea primero un usuario administrador")
                return False
            
            print(f"👤 Usando usuario: {admin_user.email} (ID: {admin_user.id})")
            
            tasks_created = 0
            
            for i, (lat, lng, location, priority) in enumerate(SAMPLE_LOCATIONS, 1):
                # Seleccionar una plantilla de tarea según la prioridad
                templates = TASK_TEMPLATES[priority]
                template_idx = (i - 1) % len(templates)
                title_template, task_type = templates[template_idx]
                
                # Crear código único de tarea
                codigo = f"GAD-{datetime.now().year}-{i:04d}"
                
                # Título descriptivo con ubicación
                titulo = f"{title_template} - {location}"
                
                # Descripción detallada
                descripcion = (
                    f"Tarea asignada en {location} "
                    f"(Lat: {lat:.4f}, Lng: {lng:.4f}). "
                    f"Prioridad: {priority.name}. "
                    f"Generada automáticamente para pruebas del dashboard."
                )
                
                # Fechas de programación (algunas ya iniciadas, otras futuras)
                base_time = datetime.now()
                if i % 3 == 0:  # 33% ya en curso
                    inicio = base_time - timedelta(hours=i % 12)
                    fin = base_time + timedelta(hours=2 + i % 6)
                    estado = TaskStatus.IN_PROGRESS
                elif i % 4 == 0:  # 25% programadas para el futuro
                    inicio = base_time + timedelta(hours=1 + i % 24)
                    fin = inicio + timedelta(hours=3 + i % 8)
                    estado = TaskStatus.PROGRAMMED
                else:  # Resto inmediatas
                    inicio = base_time
                    fin = base_time + timedelta(hours=4 + i % 6)
                    estado = TaskStatus.PROGRAMMED
                
                # Crear la tarea
                tarea_data = TareaCreate(
                    codigo=codigo,
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo=task_type,
                    prioridad=priority,
                    inicio_programado=inicio,
                    fin_programado=fin,
                    delegado_usuario_id=admin_user.id,
                    creado_por_usuario_id=admin_user.id,
                    efectivos_asignados=[],
                )
                
                # Crear en la base de datos
                new_task = await crud_tarea.create(session, obj_in=tarea_data)
                
                # Asignar ubicación (no está en el schema de creación)
                new_task.ubicacion_lat = lat
                new_task.ubicacion_lon = lng
                new_task.ubicacion_descripcion = location
                new_task.estado = estado
                
                await session.commit()
                await session.refresh(new_task)
                
                tasks_created += 1
                priority_emoji = {
                    TaskPriority.CRITICAL: "🚨",
                    TaskPriority.URGENT: "⚠️",
                    TaskPriority.HIGH: "🔴",
                    TaskPriority.MEDIUM: "🟡",
                    TaskPriority.LOW: "🟢",
                }
                
                print(f"✅ {priority_emoji[priority]} {codigo}: {titulo[:60]}...")
            
            await session.commit()
            print(f"\n🎉 Creadas {tasks_created} tareas de prueba exitosamente!")
            print("📍 Ubicaciones distribuidas en Buenos Aires y GBA")
            print(f"🗂️ Prioridades: {sum(1 for _, _, _, p in SAMPLE_LOCATIONS if p == TaskPriority.CRITICAL)} críticas, "
                  f"{sum(1 for _, _, _, p in SAMPLE_LOCATIONS if p == TaskPriority.URGENT)} urgentes, "
                  f"{sum(1 for _, _, _, p in SAMPLE_LOCATIONS if p == TaskPriority.HIGH)} altas, "
                  f"{sum(1 for _, _, _, p in SAMPLE_LOCATIONS if p == TaskPriority.MEDIUM)} medias, "
                  f"{sum(1 for _, _, _, p in SAMPLE_LOCATIONS if p == TaskPriority.LOW)} bajas")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creando tareas: {e}")
            await session.rollback()
            return False


async def main():
    """Función principal."""
    print("🚔 GRUPO_GAD - Creador de datos de prueba para dashboard")
    print("=" * 60)
    
    try:
        success = await create_test_tasks()
        if success:
            print("\n🎯 ¡Listo! Ahora puedes:")
            print("   1. Iniciar la API: poetry run uvicorn src.api.main:app --reload")
            print("   2. Acceder al dashboard: http://localhost:8000/dashboard")
            print("   3. Ver las tareas en el mapa interactivo")
            print("   4. Las emergencias aparecerán en rojo 🚨")
        else:
            print("\n❌ Error en la creación de datos de prueba")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())