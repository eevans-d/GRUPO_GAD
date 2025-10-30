#!/usr/bin/env python3
"""
Sistema de Verificación Final Automática - Protocolo de Testing Coverage
================================================================

Este script implementa la verificación final obligatoria antes de completar 
cualquier análisis de testing coverage, según el protocolo establecido.

Funcionalidades:
- Lee el plan de investigación como documento vivo
- Verifica que todas las tareas estén marcadas como completadas [x]
- Genera reporte de verificación detallado
- Valida adherencia al 100% del protocolo de flujo de trabajo

Uso:
    python 01_verificacion_final_automatica.py

Autor: MiniMax Agent - Sistema de Análisis Testing Coverage
Fecha: 29 de octubre de 2025
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class VerificadorProtocoloTesting:
    """Clase principal para verificación de adherencia al protocolo de testing coverage."""
    
    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.tareas_pendientes = []
        self.tareas_completadas = 0
        self.total_tareas = 0
        self.errores_protocolo = []
        self.warning_protocolo = []
        
    def leer_plan(self) -> str:
        """Lee el contenido del plan de investigación."""
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            self.errores_protocolo.append(f"PLAN NO ENCONTRADO: {self.plan_path}")
            return ""
        except Exception as e:
            self.errores_protocolo.append(f"ERROR AL LEER PLAN: {e}")
            return ""
    
    def extraer_tareas_del_plan(self, contenido: str) -> Dict[str, bool]:
        """Extrae todas las tareas del plan y su estado de completitud."""
        tareas = {}
        
        # Patrón para buscar tareas marcadas [x] o [ ]
        patron_tarea = r'- \[([x ])\]\s+(.+?)(?=\n|\r|$)'
        
        # Buscar todas las tareas
        matches = re.findall(patron_tarea, contenido, re.MULTILINE)
        
        for estado, descripcion in matches:
            estado_completado = estado.strip() == 'x'
            descripcion_limpia = descripcion.strip()
            
            # Crear ID único para la tarea
            tarea_id = self._generar_id_tarea(descripcion_limpia)
            tareas[tarea_id] = {
                'descripcion': descripcion_limpia,
                'completada': estado_completado,
                'original': f"[{estado}] {descripcion_limpia}"
            }
            
            if estado_completado:
                self.tareas_completadas += 1
            else:
                self.tareas_pendientes.append(descripcion_limpia)
            
            self.total_tareas += 1
        
        return tareas
    
    def _generar_id_tarea(self, descripcion: str) -> str:
        """Genera un ID único para una tarea basado en su descripción."""
        # Tomar las primeras palabras significativas
        palabras = descripcion.split()[:4]
        id_base = "_".join([p.strip() for p in palabras if len(p.strip()) > 2])
        return id_base.lower().replace(':', '').replace('/', '_')
    
    def verificar_adherencia_flujo(self, tareas: Dict[str, bool]) -> Tuple[bool, List[str]]:
        """Verifica que el flujo de trabajo se haya seguido correctamente."""
        violaciones_flujo = []
        
        # Verificar que el documento principal fue completado
        doc_principal_encontrado = any(
            'documento principal' in desc.lower() and datos['completada']
            for desc, datos in tareas.items()
        )
        if not doc_principal_encontrado:
            violaciones_flujo.append("CRÍTICO: Documento principal no marcado como completado")
        
        # Verificar que el análisis de gaps críticos está presente
        gaps_criticos_encontrados = sum(
            1 for desc, datos in tareas.items() 
            if 'gap' in desc.lower() and datos['completada']
        )
        if gaps_criticos_encontrados < 3:
            violaciones_flujo.append(f"WARNING: Solo {gaps_criticos_encontrados} análisis de gaps críticos completados (mínimo 3)")
        
        # Verificar que el roadmap está presente
        roadmap_encontrado = any(
            'roadmap' in desc.lower() and datos['completada']
            for desc, datos in tareas.items()
        )
        if not roadmap_encontrado:
            violaciones_flujo.append("CRÍTICO: Roadmap no marcado como completado")
        
        # Verificar que se completó el benchmarking
        benchmarking_encontrado = any(
            'benchmarking' in desc.lower() and datos['completada']
            for desc, datos in tareas.items()
        )
        if not benchmarking_encontrado:
            violaciones_flujo.append("CRÍTICO: Benchmarking contra estándares no completado")
        
        adherencia_completa = len(violaciones_flujo) == 0
        return adherencia_completa, violaciones_flujo
    
    def calcular_porcentaje_completitud(self) -> float:
        """Calcula el porcentaje de tareas completadas."""
        if self.total_tareas == 0:
            return 0.0
        return (self.tareas_completadas / self.total_tareas) * 100
    
    def validar_estado_final(self) -> Dict[str, any]:
        """Valida el estado final y determina si la tarea puede completarse."""
        estado_final = {
            'puede_completarse': False,
            'porcentaje_completitud': 0.0,
            'errores_criticos': [],
            'warnings': [],
            'recomendaciones': []
        }
        
        # Calcular completitud
        completitud = self.calcular_porcentaje_completitud()
        estado_final['porcentaje_completitud'] = completitud
        
        # Verificar errores críticos
        if self.errores_protocolo:
            estado_final['errores_criticos'].extend(self.errores_protocolo)
            estado_final['puede_completarse'] = False
        
        # Verificar tareas pendientes
        if self.tareas_pendientes:
            estado_final['errores_criticos'].append(
                f"TAREAS PENDIENTES: {len(self.tareas_pendientes)} tareas sin completar"
            )
            estado_final['warnings'].extend(
                [f"- {tarea}" for tarea in self.tareas_pendientes[:10]]  # Solo primeros 10
            )
            if len(self.tareas_pendientes) > 10:
                estado_final['warnings'].append(f"... y {len(self.tareas_pendientes) - 10} más")
        
        # Determinar si puede completarse
        if (not self.errores_protocolo and 
            not self.tareas_pendientes and 
            completitud >= 100.0):
            estado_final['puede_completarse'] = True
        else:
            estado_final['recomendaciones'].append(
                "Acción requerida: Completar todas las tareas pendientes antes de finalizar"
            )
        
        return estado_final
    
    def generar_reporte_verificacion(self, tareas: Dict[str, bool]) -> str:
        """Genera un reporte detallado de la verificación."""
        adherencia, violaciones = self.verificar_adherencia_flujo(tareas)
        estado = self.validar_estado_final()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        reporte = f"""
================================================================================
VERIFICACIÓN FINAL AUTOMÁTICA - PROTOCOLO TESTING COVERAGE
================================================================================

Fecha de verificación: {timestamp}
Archivo analizado: {self.plan_path}

RESUMEN EJECUTIVO:
------------------
✅ Tareas completadas: {self.tareas_completadas}
❌ Tareas pendientes: {len(self.tareas_pendientes)}
📊 Total de tareas: {self.total_tareas}
🎯 Porcentaje completitud: {estado['porcentaje_completitud']:.1f}%

ESTADO DE ADHERENCIA AL FLUJO:
------------------------------
✅ Adherencia al flujo: {"COMPLETA" if adherencia else "INCOMPLETA"}
{"✅" if adherencia else "❌"} Protocolo seguido correctamente: {adherencia}

{"" if adherencia else "❌ VIOLACIONES DEL FLUJO DETECTADAS:"}
{chr(10).join(f"  - {violacion}" for violacion in violaciones) if not adherencia else ""}

ERRORES CRÍTICOS:
-----------------
{chr(10).join(f"❌ {error}" for error in estado['errores_criticos']) if estado['errores_criticos'] else "✅ No hay errores críticos"}

WARNINGS:
---------
{chr(10).join(f"⚠️  {warning}" for warning in estado['warnings']) if estado['warnings'] else "✅ No hay warnings"}

RECOMENDACIONES:
----------------
{chr(10).join(f"💡 {rec}" for rec in estado['recomendaciones']) if estado['recomendaciones'] else "✅ No hay recomendaciones adicionales"}

VALIDACIÓN FINAL:
-----------------
{'✅' if estado['puede_completarse'] else '❌'} TAREA PUEDE COMPLETARSE: {estado['puede_completarse']}

{'🎉 PROTOCOLO CUMPLIDO AL 100% - TAREA LISTA PARA FINALIZAR' if estado['puede_completarse'] else 
 '🚫 PROTOCOLO INCOMPLETO - SE REQUIEREN ACCIONES ANTES DE FINALIZAR'}

================================================================================
VERIFICACIÓN AUTOMÁTICA COMPLETADA
================================================================================
"""
        return reporte
    
    def ejecutar_verificacion_completa(self) -> Dict[str, any]:
        """Ejecuta la verificación completa del protocolo."""
        print("🔍 Iniciando verificación automática del protocolo...")
        
        # Leer el plan
        contenido = self.leer_plan()
        if not contenido:
            return {
                'exito': False,
                'error': "No se pudo leer el plan de investigación",
                'reporte': "ERROR: Plan no encontrado o no legible"
            }
        
        # Extraer tareas
        print("📋 Extrayendo tareas del plan...")
        tareas = self.extraer_tareas_del_plan(contenido)
        print(f"✅ {len(tareas)} tareas identificadas en el plan")
        
        # Generar reporte
        print("📊 Generando reporte de verificación...")
        reporte = self.generar_reporte_verificacion(tareas)
        
        # Validar estado
        estado = self.validar_estado_final()
        
        print("✅ Verificación automática completada")
        
        return {
            'exito': True,
            'tareas': tareas,
            'reporte': reporte,
            'estado': estado,
            'tareas_completadas': self.tareas_completadas,
            'total_tareas': self.total_tareas,
            'pendientes': len(self.tareas_pendientes)
        }


def main():
    """Función principal del verificador automático."""
    print("🔧 SISTEMA DE VERIFICACIÓN FINAL AUTOMÁTICA")
    print("=" * 60)
    
    # Ruta del plan de investigación
    plan_path = "01_coverage_analysis_plan.md"
    
    # Crear verificador
    verificador = VerificadorProtocoloTesting(plan_path)
    
    # Ejecutar verificación completa
    resultado = verificador.ejecutar_verificacion_completa()
    
    # Mostrar reporte
    print("\n" + resultado['reporte'])
    
    # Determinar acción
    if resultado['exito'] and resultado['estado']['puede_completarse']:
        print("🎉 VERIFICACIÓN EXITOSA - PROTOCOLO CUMPLIDO AL 100%")
        print("✅ La tarea puede finalizarse con confianza")
        return 0
    else:
        print("🚫 VERIFICACIÓN FALLIDA - PROTOCOLO INCOMPLETO")
        print("❌ Acciones requeridas antes de finalizar")
        return 1


if __name__ == "__main__":
    sys.exit(main())
