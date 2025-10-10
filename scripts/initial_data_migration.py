#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Migración Inicial de Datos para GRUPO_GAD
--------------------------------------------------
Este script realiza la migración inicial de datos necesarios para el entorno de producción.
Garantiza que los datos básicos estén disponibles antes de que la aplicación esté en producción.

Uso:
    python initial_data_migration.py [--env ENV_FILE] [--dry-run]

Opciones:
    --env ENV_FILE     Archivo de variables de entorno (por defecto: .env.production)
    --dry-run          Ejecutar sin realizar cambios reales en la base de datos
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

try:
    from dotenv import load_dotenv
    from sqlalchemy import Column, MetaData, Table, create_engine, select
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("Error: Dependencias faltantes. Ejecute: pip install sqlalchemy python-dotenv")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('initial_data_migration')

# Directorios y archivos
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "migration"
RESULTS_DIR = BASE_DIR / "logs" / "migration"

# Asegurar que los directorios existen
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Clases para representar datos
class MigrationTask:
    """Representa una tarea de migración con su dependencia y prioridad."""
    
    def __init__(self, name: str, description: str, dependencies: Optional[List[str]] = None, 
                 priority: int = 100, sql_file: Optional[str] = None, 
                 csv_file: Optional[str] = None, table_name: Optional[str] = None):
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.priority = priority
        self.sql_file = sql_file
        self.csv_file = csv_file
        self.table_name = table_name
        self.completed = False
        self.start_time = None
        self.end_time = None
        self.error = None

    def __repr__(self):
        return f"MigrationTask({self.name}, priority={self.priority}, completed={self.completed})"
    
    @property
    def duration(self) -> Optional[float]:
        """Duración de la tarea en segundos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict:
        """Convierte la tarea a un diccionario para informes."""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "completed": self.completed,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "error": str(self.error) if self.error else None,
        }


class MigrationResult:
    """Almacena los resultados de la migración."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tasks = {}  # name -> MigrationTask
        
    def add_task(self, task: MigrationTask):
        """Añade una tarea al resultado."""
        self.tasks[task.name] = task
        
    def complete_task(self, task_name: str, success: bool = True, error: Optional[Exception] = None):
        """Marca una tarea como completada."""
        if task_name not in self.tasks:
            logger.warning(f"Intentando completar tarea desconocida: {task_name}")
            return
            
        task = self.tasks[task_name]
        task.completed = success
        task.end_time = datetime.now()
        
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
            task.error = error
            
    def start_task(self, task_name: str):
        """Marca una tarea como iniciada."""
        if task_name not in self.tasks:
            logger.warning(f"Intentando iniciar tarea desconocida: {task_name}")
            return
            
        task = self.tasks[task_name]
        task.start_time = datetime.now()
        
    def finalize(self):
        """Finaliza el resultado de la migración."""
        self.end_time = datetime.now()
        
    @property
    def duration(self) -> float:
        """Duración total de la migración en segundos."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
        
    @property
    def success(self) -> bool:
        """Indica si la migración fue exitosa."""
        return self.tasks_failed == 0
        
    def to_dict(self) -> Dict:
        """Convierte el resultado a un diccionario para informes."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success": self.success,
            "tasks": {name: task.to_dict() for name, task in self.tasks.items()}
        }
        
    def save_report(self, filename: Optional[str] = None):
        """Guarda un informe de la migración en formato JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"migration_report_{timestamp}.json"
            
        filepath = RESULTS_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
        logger.info(f"Informe de migración guardado en: {filepath}")
        return filepath


# Funciones principales
async def get_db_engine(db_url: str) -> AsyncEngine:
    """Crea y devuelve un motor de base de datos asíncrono."""
    try:
        engine = create_async_engine(db_url)
        # Verificar conexión
        async with engine.connect() as conn:
            await conn.execute(select(1))
        return engine
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        raise


async def execute_sql_file(engine: AsyncEngine, sql_file: Path, dry_run: bool = False) -> None:
    """Ejecuta un archivo SQL en la base de datos."""
    if not sql_file.exists():
        raise FileNotFoundError(f"Archivo SQL no encontrado: {sql_file}")
    
    sql_content = sql_file.read_text(encoding='utf-8')
    if not sql_content.strip():
        logger.warning(f"Archivo SQL vacío: {sql_file}")
        return
    
    # Dividir en sentencias SQL individuales
    statements = sql_content.split(';')
    statements = [stmt.strip() for stmt in statements if stmt.strip()]
    
    logger.info(f"Ejecutando {len(statements)} sentencias SQL de {sql_file.name}")
    
    if dry_run:
        logger.info("[SIMULACIÓN] No se ejecutarán sentencias SQL")
        return
        
    async with engine.begin() as conn:
        for stmt in statements:
            # Usar text() para ejecutar SQL crudo
            from sqlalchemy import text
            await conn.execute(text(stmt))


async def import_csv_data(engine: AsyncEngine, table_name: str, csv_file: Path, 
                          dry_run: bool = False) -> int:
    """Importa datos desde un archivo CSV a una tabla de la base de datos."""
    if not csv_file.exists():
        raise FileNotFoundError(f"Archivo CSV no encontrado: {csv_file}")
    
    # Leer datos CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        logger.warning(f"Archivo CSV vacío o mal formateado: {csv_file}")
        return 0
    
    logger.info(f"Importando {len(rows)} filas a tabla '{table_name}' desde {csv_file.name}")
    
    if dry_run:
        logger.info(f"[SIMULACIÓN] No se importarán datos a la tabla {table_name}")
        return len(rows)
    
    # Obtener metadatos de la tabla
    async with engine.connect() as conn:
        metadata = MetaData()
        await conn.run_sync(lambda sync_conn: metadata.reflect(sync_conn, only=[table_name]))
        
        if table_name not in metadata.tables:
            raise ValueError(f"La tabla '{table_name}' no existe en la base de datos")
            
        table = metadata.tables[table_name]
        
        # Insertar datos
        async with conn.begin():
            for row in rows:
                # Filtrar solo columnas existentes en la tabla
                valid_columns = {col: val for col, val in row.items() if col in table.columns}
                await conn.execute(table.insert().values(**valid_columns))
    
    return len(rows)


def define_migration_tasks() -> List[MigrationTask]:
    """Define las tareas de migración inicial."""
    return [
        MigrationTask(
            name="roles_base",
            description="Crear roles básicos del sistema",
            priority=10,
            sql_file="roles_base.sql",
            table_name="roles"
        ),
        MigrationTask(
            name="permisos_base",
            description="Crear permisos básicos del sistema",
            priority=20,
            dependencies=["roles_base"],
            sql_file="permisos_base.sql",
            table_name="permisos"
        ),
        MigrationTask(
            name="rol_permisos",
            description="Asignar permisos a roles",
            priority=30,
            dependencies=["roles_base", "permisos_base"],
            sql_file="rol_permisos.sql",
            table_name="rol_permisos"
        ),
        MigrationTask(
            name="configuraciones",
            description="Configuraciones iniciales del sistema",
            priority=40,
            sql_file="configuraciones.sql",
            table_name="configuraciones"
        ),
        MigrationTask(
            name="usuario_admin",
            description="Crear usuario administrador",
            priority=50,
            dependencies=["roles_base"],
            sql_file="usuario_admin.sql",
            table_name="usuarios"
        ),
        MigrationTask(
            name="categorias_base",
            description="Categorías iniciales",
            priority=60,
            csv_file="categorias.csv",
            table_name="categorias"
        ),
        MigrationTask(
            name="estados_base",
            description="Estados de entidades",
            priority=70,
            csv_file="estados.csv",
            table_name="estados"
        ),
    ]


def sort_tasks_by_dependency(tasks: List[MigrationTask]) -> List[MigrationTask]:
    """Ordena las tareas por dependencias (ordenación topológica)."""
    # Crear un diccionario de tareas por nombre para búsqueda rápida
    tasks_dict = {task.name: task for task in tasks}
    
    # Verificar que todas las dependencias existen
    for task in tasks:
        for dep in task.dependencies:
            if dep not in tasks_dict:
                logger.warning(f"La tarea '{task.name}' depende de '{dep}', pero esta no existe")
    
    # Implementar ordenación topológica
    result = []
    visited = set()
    temp_visited = set()
    
    def visit(task_name: str):
        if task_name in temp_visited:
            raise ValueError(f"Dependencia cíclica detectada con tarea: {task_name}")
        
        if task_name in visited:
            return
            
        if task_name not in tasks_dict:
            logger.warning(f"Dependencia '{task_name}' no encontrada en las tareas")
            return
            
        temp_visited.add(task_name)
        
        task = tasks_dict[task_name]
        for dep in task.dependencies:
            if dep in tasks_dict:
                visit(dep)
        
        temp_visited.remove(task_name)
        visited.add(task_name)
        result.append(task)
    
    # Visitar todas las tareas
    # Primero ordenar por prioridad para resolver empates
    priority_sorted = sorted(tasks, key=lambda t: t.priority)
    for task in priority_sorted:
        if task.name not in visited:
            visit(task.name)
    
    return result


async def execute_migration_task(engine: AsyncEngine, task: MigrationTask, 
                                dry_run: bool) -> None:
    """Ejecuta una tarea de migración específica."""
    logger.info(f"Ejecutando tarea: {task.name} - {task.description}")
    
    if task.sql_file:
        sql_path = DATA_DIR / task.sql_file
        await execute_sql_file(engine, sql_path, dry_run)
    
    if task.csv_file and task.table_name:
        csv_path = DATA_DIR / task.csv_file
        await import_csv_data(engine, task.table_name, csv_path, dry_run)
    elif task.csv_file and not task.table_name:
        logger.warning(f"Tarea {task.name} tiene csv_file pero no table_name, saltando importación CSV")


async def run_migration(db_url: str, dry_run: bool = False) -> MigrationResult:
    """Ejecuta la migración inicial completa."""
    logger.info("Iniciando migración de datos inicial")
    if dry_run:
        logger.info("MODO SIMULACIÓN: No se realizarán cambios reales en la base de datos")
    
    result = MigrationResult()
    
    try:
        # Obtener motor de base de datos
        engine = await get_db_engine(db_url)
        
        # Definir y ordenar tareas
        tasks = define_migration_tasks()
        for task in tasks:
            result.add_task(task)
            
        ordered_tasks = sort_tasks_by_dependency(tasks)
        
        # Ejecutar tareas en orden
        for task in ordered_tasks:
            result.start_task(task.name)
            try:
                await execute_migration_task(engine, task, dry_run)
                result.complete_task(task.name, success=True)
                logger.info(f"✅ Tarea completada: {task.name}")
            except Exception as e:
                logger.error(f"❌ Error en tarea {task.name}: {e}")
                result.complete_task(task.name, success=False, error=e)
                # Si es una tarea crítica, abortar
                if task.priority < 50:
                    logger.critical("Abortando migración debido a un error en una tarea crítica")
                    break
    except Exception as e:
        logger.critical(f"Error fatal durante la migración: {e}")
    finally:
        result.finalize()
        
    # Generar informe
    success_count = result.tasks_completed
    total_tasks = len(result.tasks)
    logger.info(f"Migración completada: {success_count}/{total_tasks} tareas exitosas")
    
    if result.tasks_failed > 0:
        logger.warning(f"⚠️ {result.tasks_failed} tareas fallaron durante la migración")
        
    # Guardar informe
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"migration_report_{timestamp}.json"
    result.save_report(report_filename)
    
    return result


def parse_args():
    """Analiza los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Migración inicial de datos para GRUPO_GAD")
    parser.add_argument('--env', default='.env.production',
                      help="Archivo de variables de entorno (por defecto: .env.production)")
    parser.add_argument('--dry-run', action='store_true',
                      help="Ejecutar sin realizar cambios reales en la base de datos")
    return parser.parse_args()


def main():
    """Punto de entrada principal."""
    args = parse_args()
    
    # Cargar variables de entorno
    env_path = Path(args.env)
    if not env_path.exists():
        logger.warning(f"Archivo de entorno {env_path} no encontrado. Usando variables de entorno del sistema.")
    else:
        load_dotenv(env_path)
    
    # Obtener URL de la base de datos
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    if not db_url:
        # Intentar construir desde componentes
        components = {
            "user": os.environ.get("POSTGRES_USER"),
            "password": os.environ.get("POSTGRES_PASSWORD"),
            "host": os.environ.get("POSTGRES_HOST", "localhost"),
            "port": os.environ.get("POSTGRES_PORT", "5432"),
            "db": os.environ.get("POSTGRES_DB"),
        }
        
        if all(components.values()):
            db_url = f"postgresql+asyncpg://{components['user']}:{components['password']}@{components['host']}:{components['port']}/{components['db']}"
        else:
            logger.error("No se pudo determinar la URL de la base de datos. Configure DATABASE_URL o los componentes POSTGRES_*")
            sys.exit(1)
    
    # Asegurarse de que usamos el driver asyncpg
    if not db_url.startswith("postgresql+asyncpg://"):
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            logger.error("La URL de la base de datos debe usar el esquema postgresql:// o postgresql+asyncpg://")
            sys.exit(1)
    
    # Ejecutar la migración
    try:
        result = asyncio.run(run_migration(db_url, args.dry_run))
        
        # Mostrar resumen
        if result.success:
            logger.info("✅ Migración completada correctamente")
            sys.exit(0)
        else:
            logger.error(f"❌ Migración completada con errores: {result.tasks_failed} tareas fallaron")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Migración interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()