#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación de Quick Wins implementados.

Ejecuta tests de verificación para todos los módulos nuevos.
"""

import sys
from pathlib import Path

# Añadir path del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_validadores():
    """Test módulo de validadores."""
    print("="*60)
    print("TEST 1: VALIDADORES (Quick Win #3)")
    print("="*60)
    
    from src.bot.utils.validators import TaskValidator, UnifiedCopy
    
    # Test 1.1: Código válido
    result = TaskValidator.validate_codigo("OPE-2025-001")
    assert result.is_valid, "Código válido debería pasar"
    print("✅ Validación de código válido: PASS")
    
    # Test 1.2: Código muy largo
    result = TaskValidator.validate_codigo("CODIGO-DEMASIADO-LARGO-EXCEDE")
    assert not result.is_valid, "Código largo debería fallar"
    assert "20 caracteres" in result.error_message
    print("✅ Validación de código largo: PASS")
    
    # Test 1.3: Título válido
    result = TaskValidator.validate_titulo("Reparar tubería principal")
    assert result.is_valid, "Título válido debería pasar"
    print("✅ Validación de título válido: PASS")
    
    # Test 1.4: Título muy largo
    long_title = "A" * 150
    result = TaskValidator.validate_titulo(long_title)
    assert not result.is_valid, "Título largo debería fallar"
    assert "100 caracteres" in result.error_message
    print("✅ Validación de título largo: PASS")
    
    # Test 1.5: Terminología unificada
    assert UnifiedCopy.DELEGADO_TERM == "Delegado"
    assert UnifiedCopy.ASIGNADOS_TERM == "Asignados"
    assert UnifiedCopy.MAX_CODIGO_LENGTH == 20
    assert UnifiedCopy.MAX_TITULO_LENGTH == 100
    print("✅ Constantes de copy unificado: PASS")
    
    print("\n✅ MÓDULO VALIDADORES: TODOS LOS TESTS PASARON\n")


def test_wizard_state():
    """Test módulo de estados del wizard."""
    print("="*60)
    print("TEST 2: CONTROL DE ESTADOS (Quick Win #4)")
    print("="*60)
    
    from src.bot.utils.wizard_state import (
        wizard_manager, WizardState, can_execute_command, can_process_text_input
    )
    
    user_id = 99999  # Usuario de test
    
    # Test 2.1: Iniciar wizard
    wizard_manager.start_wizard(user_id, "crear")
    session = wizard_manager.get_session(user_id)
    assert session.is_active(), "Wizard debería estar activo"
    print("✅ Inicio de wizard: PASS")
    
    # Test 2.2: Comandos bloqueados
    assert not can_execute_command(user_id, "/start"), "/start debería estar bloqueado"
    assert can_execute_command(user_id, "/cancelar"), "/cancelar debería estar permitido"
    print("✅ Control de comandos: PASS")
    
    # Test 2.3: Entrada de texto según estado
    wizard_manager.advance_state(user_id, WizardState.ENTERING_CODE)
    assert can_process_text_input(user_id), "Debería permitir texto en ENTERING_CODE"
    print("✅ Control de entrada de texto: PASS")
    
    # Test 2.4: Estado confirmación
    wizard_manager.advance_state(user_id, WizardState.CONFIRMING)
    assert not can_execute_command(user_id, "/start"), "Comandos bloqueados en CONFIRMING"
    assert not can_process_text_input(user_id), "Texto bloqueado en CONFIRMING"
    print("✅ Estado de confirmación: PASS")
    
    # Test 2.5: Cancelar wizard
    wizard_manager.cancel_wizard(user_id)
    session = wizard_manager.get_session(user_id)
    assert not session.is_active(), "Wizard debería estar inactivo"
    print("✅ Cancelación de wizard: PASS")
    
    print("\n✅ MÓDULO WIZARD STATE: TODOS LOS TESTS PASARON\n")


def test_ux_metrics():
    """Test módulo de métricas UX."""
    print("="*60)
    print("TEST 3: INSTRUMENTACIÓN UX (Quick Win #5)")
    print("="*60)
    
    from src.bot.utils.ux_metrics import ux_metrics
    
    user_test = 88888
    
    # Test 3.1: Tracking de wizard
    ux_metrics.track_wizard_start(user_test, "crear")
    ux_metrics.track_step_start(user_test, 1)
    ux_metrics.track_step_complete(user_test, 1)
    ux_metrics.track_wizard_complete(user_test)
    print("✅ Tracking de wizard completo: PASS")
    
    # Test 3.2: Tracking de abandono
    user_test2 = 88889
    ux_metrics.track_wizard_start(user_test2, "crear")
    ux_metrics.track_wizard_abandon(user_test2, step=2)
    print("✅ Tracking de abandono: PASS")
    
    # Test 3.3: Métricas summary
    summary = ux_metrics.get_metrics_summary()
    assert 'abandonment_rate' in summary
    assert 'latency_p95_ms' in summary
    assert 'confirmation_error_rate' in summary
    print("✅ Generación de resumen: PASS")
    
    # Test 3.4: Estructura de métricas
    assert 'value' in summary['abandonment_rate']
    assert 'target' in summary['abandonment_rate']
    assert 'meets_target' in summary['abandonment_rate']
    print("✅ Estructura de métricas: PASS")
    
    print("\n✅ MÓDULO UX METRICS: TODOS LOS TESTS PASARON\n")


def test_error_messages():
    """Test módulo de mensajes de error."""
    print("="*60)
    print("TEST 4: MENSAJES DE ERROR (Quick Win #2)")
    print("="*60)
    
    from src.bot.utils.error_messages import ErrorMessages
    
    # Test 4.1: Error de validación
    msg = ErrorMessages.format_validation_error(
        field="Código",
        value="DEMASIADO-LARGO",
        issue="Excede límite",
        suggestion="CORRECTO"
    )
    assert "Código" in msg
    assert "DEMASIADO-LARGO" in msg
    assert "CORRECTO" in msg
    print("✅ Error de validación: PASS")
    
    # Test 4.2: Recurso no encontrado
    msg = ErrorMessages.format_not_found_error(
        resource="Usuario",
        identifier="ID 999",
        suggestions=["Verifica el ID", "Busca en lista"]
    )
    assert "Usuario" in msg
    assert "ID 999" in msg
    print("✅ Error de recurso no encontrado: PASS")
    
    # Test 4.3: Error de permisos
    msg = ErrorMessages.format_permission_error(
        action="eliminar tareas",
        required_role="Admin",
        current_role="Usuario"
    )
    assert "Acceso denegado" in msg
    assert "Admin" in msg
    print("✅ Error de permisos: PASS")
    
    # Test 4.4: Error de API
    msg = ErrorMessages.format_api_error(
        operation="crear tarea",
        error_code="500",
        retry_possible=True
    )
    assert "crear tarea" in msg
    assert "500" in msg
    print("✅ Error de API: PASS")
    
    print("\n✅ MÓDULO ERROR MESSAGES: TODOS LOS TESTS PASARON\n")


def test_confirmations():
    """Test módulo de confirmaciones."""
    print("="*60)
    print("TEST 5: CONFIRMACIONES (Quick Win #1)")
    print("="*60)
    
    from src.bot.utils.confirmations import (
        ConfirmationFormatter, ConfirmationPattern, ConfirmationHelper
    )
    
    # Test 5.1: Confirmación de tarea
    task_data = {
        'codigo': 'OPE-2025-001',
        'titulo': 'Tarea de prueba',
        'tipo': 'OPERATIVO',
        'delegado_id': 101,
        'asignados': [201, 202]
    }
    msg = ConfirmationFormatter.format_task_confirmation(task_data)
    assert 'OPE-2025-001' in msg
    assert 'Tarea de prueba' in msg
    assert 'Delegado' in msg
    assert 'Asignados' in msg
    print("✅ Formato de confirmación de tarea: PASS")
    
    # Test 5.2: Teclado estándar
    keyboard = ConfirmationPattern.standard_confirmation("crear")
    assert keyboard.inline_keyboard is not None
    assert len(keyboard.inline_keyboard) >= 2
    print("✅ Teclado de confirmación estándar: PASS")
    
    # Test 5.3: Confirmación destructiva
    keyboard = ConfirmationPattern.destructive_confirmation("eliminar", "123")
    assert keyboard.inline_keyboard is not None
    print("✅ Confirmación destructiva: PASS")
    
    # Test 5.4: Helper de confirmación
    assert ConfirmationHelper.should_show_confirmation("crear")
    assert ConfirmationHelper.should_show_confirmation("eliminar")
    print("✅ Helper de confirmación: PASS")
    
    print("\n✅ MÓDULO CONFIRMATIONS: TODOS LOS TESTS PASARON\n")


def main():
    """Ejecuta todos los tests de validación."""
    print("\n" + "="*60)
    print("VALIDACIÓN DE QUICK WINS - FASE 1")
    print("Sistema GRUPO_GAD")
    print("="*60 + "\n")
    
    try:
        test_validadores()
        test_wizard_state()
        test_ux_metrics()
        test_error_messages()
        test_confirmations()
        
        print("="*60)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("="*60)
        print("\n🎉 Los 5 Quick Wins están correctamente implementados:")
        print("  ✅ #1: Confirmaciones consistentes")
        print("  ✅ #2: Mensajes de error específicos")
        print("  ✅ #3: Copy unificado")
        print("  ✅ #4: Control de atajos")
        print("  ✅ #5: Instrumentación UX\n")
        print("📊 Sistema listo para despliegue en staging\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {str(e)}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
