# -*- coding: utf-8 -*-
"""
Sistema de estados del wizard para control de flujo y atajos.

Este módulo implementa Quick Win #4: Control de atajos
- Deshabilitar comandos texto libre durante wizard
- Estados sensibles para prevenir acciones involuntarias
- Control de flujo seguro
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


class WizardState(Enum):
    """
    Estados del wizard de creación de tareas.
    
    Quick Win #4: Estados sensibles que controlan qué comandos están permitidos.
    """
    IDLE = "idle"  # Sin wizard activo - todos los comandos permitidos
    SELECTING_TYPE = "selecting_type"  # Paso 1: Seleccionando tipo
    ENTERING_CODE = "entering_code"  # Paso 2: Ingresando código
    ENTERING_TITLE = "entering_title"  # Paso 3: Ingresando título
    SELECTING_DELEGADO = "selecting_delegado"  # Paso 4: Seleccionando delegado
    SELECTING_ASIGNADOS = "selecting_asignados"  # Paso 5: Seleccionando asignados
    CONFIRMING = "confirming"  # Paso 6: Confirmando datos
    PROCESSING = "processing"  # Procesando creación (bloqueado)


class FinalizarWizardState(Enum):
    """Estados del wizard de finalización de tareas."""
    IDLE = "idle"
    SELECTING_TASK = "selecting_task"
    ENTERING_NOTES = "entering_notes"
    CONFIRMING = "confirming"
    PROCESSING = "processing"


@dataclass
class WizardSession:
    """
    Sesión de wizard con control de estado y datos.
    
    Quick Win #4: Sesión que mantiene estado y previene acciones involuntarias.
    """
    state: WizardState = WizardState.IDLE
    data: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Control de atajos
    shortcuts_enabled: bool = True
    text_commands_allowed: bool = True
    
    def update_activity(self) -> None:
        """Actualiza timestamp de última actividad."""
        self.last_activity = datetime.now()
    
    def is_active(self) -> bool:
        """Verifica si el wizard está activo (no IDLE)."""
        return self.state != WizardState.IDLE
    
    def is_processing(self) -> bool:
        """Verifica si está en estado de procesamiento (bloqueado)."""
        return self.state == WizardState.PROCESSING
    
    def allow_command(self, command: str) -> bool:
        """
        Verifica si un comando está permitido en el estado actual.
        
        Quick Win #4: Deshabilita comandos durante wizard/confirmaciones.
        
        Args:
            command: Comando a verificar (ej: "/start", "/help")
        
        Returns:
            True si el comando está permitido
        """
        # Comandos siempre permitidos
        always_allowed = ["/cancelar", "/ayuda", "/help"]
        if command in always_allowed:
            return True
        
        # Si no hay wizard activo, todo está permitido
        if not self.is_active():
            return True
        
        # Si está procesando, solo cancelar y ayuda
        if self.is_processing():
            return False
        
        # Si está confirmando, bloquear otros comandos
        if self.state == WizardState.CONFIRMING:
            return False
        
        # En otros estados del wizard, permitir solo ciertos comandos
        return command in ["/cancelar", "/ayuda"]
    
    def allow_text_input(self) -> bool:
        """
        Verifica si se permite entrada de texto libre.
        
        Quick Win #4: Control de atajos tipo "listo + código".
        
        Returns:
            True si se permite entrada de texto
        """
        if not self.is_active():
            return False  # Sin wizard activo, ignorar texto libre
        
        # Estados que esperan entrada de texto
        text_input_states = [
            WizardState.ENTERING_CODE,
            WizardState.ENTERING_TITLE,
            WizardState.SELECTING_DELEGADO,
            WizardState.SELECTING_ASIGNADOS
        ]
        
        return self.state in text_input_states
    
    def allow_callback(self) -> bool:
        """
        Verifica si se permiten callbacks de botones.
        
        Returns:
            True si se permiten callbacks
        """
        # No permitir callbacks mientras procesa
        if self.is_processing():
            return False
        
        return True


class WizardSessionManager:
    """
    Gestor de sesiones de wizard por usuario.
    
    Quick Win #4: Gestión centralizada de estados por usuario.
    """
    
    def __init__(self) -> None:
        self._sessions: Dict[int, WizardSession] = {}
    
    def get_session(self, user_id: int) -> WizardSession:
        """
        Obtiene o crea sesión de wizard para un usuario.
        
        Args:
            user_id: ID de usuario de Telegram
        
        Returns:
            Sesión de wizard del usuario
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = WizardSession()
        
        self._sessions[user_id].update_activity()
        return self._sessions[user_id]
    
    def start_wizard(self, user_id: int, wizard_type: str = "crear") -> WizardSession:
        """
        Inicia un nuevo wizard para el usuario.
        
        Args:
            user_id: ID de usuario
            wizard_type: Tipo de wizard ("crear" o "finalizar")
        
        Returns:
            Sesión de wizard iniciada
        """
        session = WizardSession()
        session.data['wizard_type'] = wizard_type
        
        if wizard_type == "crear":
            session.state = WizardState.SELECTING_TYPE
        
        self._sessions[user_id] = session
        return session
    
    def cancel_wizard(self, user_id: int) -> None:
        """
        Cancela y limpia el wizard del usuario.
        
        Args:
            user_id: ID de usuario
        """
        if user_id in self._sessions:
            self._sessions[user_id] = WizardSession()  # Reset a IDLE
    
    def advance_state(
        self, 
        user_id: int, 
        next_state: WizardState,
        data: Optional[Dict[str, Any]] = None
    ) -> WizardSession:
        """
        Avanza el wizard al siguiente estado.
        
        Args:
            user_id: ID de usuario
            next_state: Siguiente estado
            data: Datos a agregar a la sesión
        
        Returns:
            Sesión actualizada
        """
        session = self.get_session(user_id)
        session.state = next_state
        
        if data:
            session.data.update(data)
        
        session.update_activity()
        return session
    
    def set_processing(self, user_id: int, processing: bool = True) -> None:
        """
        Marca sesión como procesando (bloqueada).
        
        Quick Win #4: Bloquea acciones durante procesamiento.
        
        Args:
            user_id: ID de usuario
            processing: True para bloquear, False para desbloquear
        """
        session = self.get_session(user_id)
        if processing:
            session.state = WizardState.PROCESSING
        session.update_activity()
    
    def cleanup_old_sessions(self, max_age_minutes: int = 30) -> int:
        """
        Limpia sesiones inactivas.
        
        Args:
            max_age_minutes: Edad máxima en minutos
        
        Returns:
            Número de sesiones limpiadas
        """
        now = datetime.now()
        to_remove = []
        
        for user_id, session in self._sessions.items():
            age = (now - session.last_activity).total_seconds() / 60
            if age > max_age_minutes and session.state != WizardState.PROCESSING:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self._sessions[user_id]
        
        return len(to_remove)
    
    def get_active_sessions_count(self) -> int:
        """
        Obtiene número de sesiones activas.
        
        Returns:
            Número de wizards activos
        """
        return sum(1 for s in self._sessions.values() if s.is_active())


# Instancia global del gestor
wizard_manager = WizardSessionManager()


def get_wizard_state(user_id: int) -> WizardState:
    """
    Obtiene estado actual del wizard del usuario.
    
    Args:
        user_id: ID de usuario
    
    Returns:
        Estado actual del wizard
    """
    return wizard_manager.get_session(user_id).state


def is_wizard_active(user_id: int) -> bool:
    """
    Verifica si el usuario tiene un wizard activo.
    
    Args:
        user_id: ID de usuario
    
    Returns:
        True si hay wizard activo
    """
    return wizard_manager.get_session(user_id).is_active()


def can_execute_command(user_id: int, command: str) -> bool:
    """
    Verifica si un comando puede ejecutarse.
    
    Quick Win #4: Control centralizado de comandos.
    
    Args:
        user_id: ID de usuario
        command: Comando a verificar
    
    Returns:
        True si el comando está permitido
    """
    return wizard_manager.get_session(user_id).allow_command(command)


def can_process_text_input(user_id: int) -> bool:
    """
    Verifica si se debe procesar entrada de texto libre.
    
    Quick Win #4: Previene "listo + código" durante confirmaciones.
    
    Args:
        user_id: ID de usuario
    
    Returns:
        True si se permite texto libre
    """
    return wizard_manager.get_session(user_id).allow_text_input()


# Tests y ejemplos
if __name__ == "__main__":
    print("=== Tests de Control de Estados ===\n")
    
    # Test 1: Crear sesión
    user_id = 12345
    session = wizard_manager.start_wizard(user_id, "crear")
    print(f"Wizard iniciado: Estado = {session.state}")
    print(f"¿Wizard activo? {session.is_active()}")
    
    # Test 2: Verificar comandos permitidos
    print(f"\n=== Comandos Permitidos ===")
    print(f"/start permitido: {session.allow_command('/start')}")
    print(f"/cancelar permitido: {session.allow_command('/cancelar')}")
    print(f"/ayuda permitido: {session.allow_command('/ayuda')}")
    
    # Test 3: Avanzar a ingreso de código
    wizard_manager.advance_state(user_id, WizardState.ENTERING_CODE)
    session = wizard_manager.get_session(user_id)
    print(f"\nEstado avanzado: {session.state}")
    print(f"¿Permite texto? {session.allow_text_input()}")
    
    # Test 4: Pasar a confirmación
    wizard_manager.advance_state(user_id, WizardState.CONFIRMING)
    session = wizard_manager.get_session(user_id)
    print(f"\nEn confirmación: {session.state}")
    print(f"/start permitido: {session.allow_command('/start')}")
    print(f"¿Permite texto? {session.allow_text_input()}")
    
    # Test 5: Procesar
    wizard_manager.set_processing(user_id, True)
    session = wizard_manager.get_session(user_id)
    print(f"\nProcesando: {session.is_processing()}")
    print(f"¿Permite callbacks? {session.allow_callback()}")
    
    # Test 6: Cancelar
    wizard_manager.cancel_wizard(user_id)
    session = wizard_manager.get_session(user_id)
    print(f"\nDespués de cancelar: {session.state}")
    print(f"¿Wizard activo? {session.is_active()}")
    
    # Test 7: Sesiones activas
    print(f"\nSesiones activas: {wizard_manager.get_active_sessions_count()}")
