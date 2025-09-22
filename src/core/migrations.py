# -*- coding: utf-8 -*-
"""
Utilidades para manejo de migraciones de Alembic.

Incluye comandos helper, validaciones y operaciones comunes
para el sistema de migraciones de GRUPO_GAD.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from src.core.logging import get_logger

# Logger para migraciones
migration_logger = get_logger("alembic.utils")


class MigrationManager:
    """
    Manager para operaciones de migración avanzadas.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.alembic_ini = self.project_root / "alembic.ini"
        self.versions_dir = self.project_root / "alembic" / "versions"
        
    def run_alembic_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Ejecuta un comando de Alembic de forma segura.
        
        Args:
            command: Lista con el comando y argumentos de Alembic
            
        Returns:
            Dict con resultado de la ejecución
        """
        # Usar directamente alembic sin poetry para evitar problemas de subprocess
        import sys
        python_path = sys.executable
        full_command = [python_path, "-m", "alembic"] + command
        
        migration_logger.info(
            f"Ejecutando comando Alembic: {' '.join(command)}",
            command=command,
            full_command=full_command
        )
        
        try:
            result = subprocess.run(
                full_command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                migration_logger.info(
                    f"Comando Alembic exitoso: {' '.join(command)}",
                    returncode=result.returncode,
                    stdout_lines=len(result.stdout.splitlines()) if result.stdout else 0
                )
                
                return {
                    "success": True,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
            else:
                migration_logger.error(
                    f"Comando Alembic falló: {' '.join(command)}",
                    returncode=result.returncode,
                    stderr=result.stderr[:500]  # Primeros 500 chars del error
                )
                
                return {
                    "success": False,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
                
        except subprocess.TimeoutExpired:
            migration_logger.error(
                f"Comando Alembic timeout: {' '.join(command)}",
                timeout_seconds=300
            )
            return {
                "success": False,
                "error": "timeout",
                "command": command
            }
        except Exception as e:
            migration_logger.error(
                f"Error ejecutando comando Alembic: {' '.join(command)}",
                error=e
            )
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def get_current_revision(self) -> Optional[str]:
        """
        Obtiene la revisión actual de la base de datos.
        
        Returns:
            String con la revisión actual o None si hay error
        """
        result = self.run_alembic_command(["current"])
        
        if result["success"] and result["stdout"]:
            # Extraer la revisión del output
            lines = result["stdout"].strip().split('\n')
            for line in lines:
                if line.strip() and not line.startswith("INFO"):
                    return line.strip().split()[0]
        
        return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de migraciones.
        
        Returns:
            Lista de diccionarios con información de migraciones
        """
        result = self.run_alembic_command(["history", "--verbose"])
        
        migrations = []
        if result["success"] and result["stdout"]:
            # Parse del output de history
            lines = result["stdout"].split('\n')
            current_migration = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith("Rev:"):
                    if current_migration:
                        migrations.append(current_migration)
                    current_migration = {"revision": line.split(":")[1].strip()}
                elif line.startswith("Parent:"):
                    current_migration["parent"] = line.split(":")[1].strip()
                elif line.startswith("Branch:"):
                    current_migration["branch"] = line.split(":")[1].strip()
                elif line.startswith("Path:"):
                    current_migration["path"] = line.split(":")[1].strip()
                elif line and not line.startswith("INFO"):
                    current_migration["description"] = line
            
            if current_migration:
                migrations.append(current_migration)
        
        return migrations
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Dict[str, Any]:
        """
        Crea una nueva migración.
        
        Args:
            message: Mensaje descriptivo para la migración
            autogenerate: Si usar autogenerate o crear migración vacía
            
        Returns:
            Dict con resultado de la operación
        """
        command = ["revision"]
        if autogenerate:
            command.append("--autogenerate")
        command.extend(["-m", message])
        
        migration_logger.info(
            f"Creando nueva migración: {message}",
            autogenerate=autogenerate
        )
        
        result = self.run_alembic_command(command)
        
        if result["success"]:
            # Extraer el ID de la nueva migración del output
            if result["stdout"]:
                lines = result["stdout"].split('\n')
                for line in lines:
                    if "Generating" in line and "revision ID" in line:
                        # Extract revision ID
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "ID" and i < len(parts) - 1:
                                revision_id = parts[i + 1]
                                result["revision_id"] = revision_id
                                break
            
            migration_logger.info(
                f"Migración creada exitosamente: {message}",
                revision_id=result.get("revision_id", "unknown")
            )
        
        return result
    
    def upgrade_database(self, revision: str = "head") -> Dict[str, Any]:
        """
        Actualiza la base de datos a una revisión específica.
        
        Args:
            revision: Revisión target (por defecto "head")
            
        Returns:
            Dict con resultado de la operación
        """
        migration_logger.info(
            f"Actualizando base de datos a revisión: {revision}"
        )
        
        result = self.run_alembic_command(["upgrade", revision])
        
        if result["success"]:
            migration_logger.info(
                f"Base de datos actualizada exitosamente a: {revision}"
            )
        
        return result
    
    def downgrade_database(self, revision: str) -> Dict[str, Any]:
        """
        Revierte la base de datos a una revisión anterior.
        
        Args:
            revision: Revisión a la cual revertir
            
        Returns:
            Dict con resultado de la operación
        """
        migration_logger.warning(
            f"Revirtiendo base de datos a revisión: {revision}"
        )
        
        result = self.run_alembic_command(["downgrade", revision])
        
        if result["success"]:
            migration_logger.info(
                f"Base de datos revertida exitosamente a: {revision}"
            )
        
        return result
    
    def validate_migrations(self) -> Dict[str, Any]:
        """
        Valida el estado de las migraciones.
        
        Returns:
            Dict con resultado de la validación
        """
        migration_logger.info("Iniciando validación de migraciones")
        
        validation_results = {
            "valid": True,
            "issues": [],
            "current_revision": None,
            "pending_migrations": [],
            "orphaned_files": []
        }
        
        # Obtener revisión actual
        current_rev = self.get_current_revision()
        validation_results["current_revision"] = current_rev
        
        # Check por migraciones pendientes
        result = self.run_alembic_command(["check"])
        if not result["success"]:
            validation_results["valid"] = False
            validation_results["issues"].append("Database is not up to date")
        
        # Check por archivos huérfanos en versions/
        if self.versions_dir.exists():
            version_files = list(self.versions_dir.glob("*.py"))
            version_files = [f for f in version_files if f.name != "__init__.py"]
            
            # Obtener migraciones conocidas por Alembic
            history = self.get_migration_history()
            known_revisions = {m.get("revision", "") for m in history}
            
            for version_file in version_files:
                # Extraer revision ID del nombre del archivo
                filename = version_file.name
                if "_" in filename:
                    file_revision = filename.split("_")[0]
                    if file_revision not in known_revisions:
                        validation_results["orphaned_files"].append(str(version_file))
                        validation_results["valid"] = False
        
        if validation_results["valid"]:
            migration_logger.info("Validación de migraciones exitosa")
        else:
            migration_logger.warning(
                "Se encontraron problemas en las migraciones",
                issues=validation_results["issues"],
                orphaned_files=validation_results["orphaned_files"]
            )
        
        return validation_results
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """
        Genera un reporte completo del estado de migraciones.
        
        Returns:
            Dict con reporte detallado
        """
        migration_logger.info("Generando reporte de migraciones")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_revision": self.get_current_revision(),
            "history": self.get_migration_history(),
            "validation": self.validate_migrations(),
            "stats": {
                "total_migrations": 0,
                "applied_migrations": 0,
                "pending_migrations": 0
            }
        }
        
        # Calcular estadísticas
        report["stats"]["total_migrations"] = len(report["history"])
        
        if report["current_revision"]:
            # Contar migraciones aplicadas (simplificado)
            report["stats"]["applied_migrations"] = len([
                m for m in report["history"] 
                if m.get("revision") == report["current_revision"]
            ])
        
        migration_logger.info(
            "Reporte de migraciones generado",
            total_migrations=report["stats"]["total_migrations"],
            current_revision=report["current_revision"]
        )
        
        return report


def create_initial_migration():
    """
    Crea la migración inicial del proyecto si no existe.
    """
    manager = MigrationManager()
    
    migration_logger.info("Verificando necesidad de migración inicial")
    
    # Verificar si ya hay migraciones
    history = manager.get_migration_history()
    if history:
        migration_logger.info(
            f"Ya existen {len(history)} migraciones, saltando creación inicial"
        )
        return {"success": True, "skipped": True, "reason": "migrations_exist"}
    
    # Crear migración inicial
    result = manager.create_migration(
        "Migración inicial de GRUPO_GAD",
        autogenerate=True
    )
    
    if result["success"]:
        migration_logger.info("Migración inicial creada exitosamente")
        
        # Aplicar la migración inmediatamente
        upgrade_result = manager.upgrade_database()
        if upgrade_result["success"]:
            migration_logger.info("Migración inicial aplicada exitosamente")
        else:
            migration_logger.error("Error aplicando migración inicial")
            return upgrade_result
    
    return result


async def main():
    """
    Función principal para testing de utilidades.
    """
    manager = MigrationManager()
    
    # Generar reporte
    report = manager.generate_migration_report()
    
    print("\n📊 REPORTE DE MIGRACIONES")
    print("=" * 50)
    print(f"🕐 Timestamp: {report['timestamp']}")
    print(f"📋 Revisión actual: {report['current_revision'] or 'None'}")
    print(f"📈 Total migraciones: {report['stats']['total_migrations']}")
    print(f"✅ Validación: {'OK' if report['validation']['valid'] else 'ISSUES'}")
    
    if not report['validation']['valid']:
        print("\n⚠️  PROBLEMAS ENCONTRADOS:")
        for issue in report['validation']['issues']:
            print(f"   - {issue}")


if __name__ == "__main__":
    asyncio.run(main())