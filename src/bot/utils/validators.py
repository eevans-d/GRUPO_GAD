# -*- coding: utf-8 -*-
"""
Validaciones y copy unificado para el sistema GRUPO_GAD.

Este módulo implementa Quick Win #3: Copy unificado
- Terminología consistente
- Límites de caracteres unificados
- Validaciones estandarizadas
"""

from typing import Tuple, Optional
from dataclasses import dataclass


# ==================== CONSTANTES DE COPY UNIFICADO ====================

class UnifiedCopy:
    """
    Terminología y copy unificado para todo el sistema.
    
    Quick Win #3: Elimina ambigüedad semántica en terminología.
    """
    
    # Roles y responsabilidades - TERMINOLOGÍA UNIFICADA
    DELEGADO_TERM = "Delegado"
    DELEGADO_DESC = "Supervisor que asigna y supervisa la tarea"
    
    ASIGNADOS_TERM = "Asignados"
    ASIGNADOS_DESC = "Efectivos que ejecutan la tarea en campo"
    
    # Límites de caracteres - UNIFICADOS
    MAX_CODIGO_LENGTH = 20
    MAX_TITULO_LENGTH = 100
    MIN_TITULO_LENGTH = 10
    MAX_DESCRIPCION_LENGTH = 500
    
    # Tipos de tarea - NOMENCLATURA OFICIAL
    TIPO_OPERATIVO = "OPERATIVO"
    TIPO_ADMINISTRATIVO = "ADMINISTRATIVO"
    TIPO_EMERGENCIA = "EMERGENCIA"
    
    # Mensajes de ayuda contextual
    HELP_DELEGADO = (
        f"*{DELEGADO_TERM}:* {DELEGADO_DESC}\n\n"
        "Responsabilidades:\n"
        "• Supervisar la ejecución de la tarea\n"
        "• Coordinar al equipo asignado\n"
        "• Reportar el progreso\n"
        "• Aprobar la finalización"
    )
    
    HELP_ASIGNADOS = (
        f"*{ASIGNADOS_TERM}:* {ASIGNADOS_DESC}\n\n"
        "Responsabilidades:\n"
        "• Ejecutar la tarea en campo\n"
        "• Reportar avances\n"
        "• Finalizar la tarea al completarla\n"
        "• Coordinar con el delegado"
    )
    
    # Labels para botones y mensajes
    BUTTON_CONFIRMAR = "Confirmar"
    BUTTON_EDITAR = "Editar"
    BUTTON_CANCELAR = "Cancelar"
    BUTTON_CONTINUAR = "Continuar"
    BUTTON_VOLVER = "Volver"


@dataclass
class ValidationResult:
    """
    Resultado de una validación con detalles específicos.
    """
    is_valid: bool
    error_message: Optional[str] = None
    suggestion: Optional[str] = None
    field_name: Optional[str] = None


class TaskValidator:
    """
    Validador centralizado para tareas con mensajes unificados.
    
    Quick Win #3: Validaciones estandarizadas con límites consistentes.
    """
    
    @staticmethod
    def validate_codigo(codigo: str) -> ValidationResult:
        """
        Valida código de tarea con límite unificado de 20 caracteres.
        
        Args:
            codigo: Código a validar
        
        Returns:
            ValidationResult con estado y mensaje específico
        
        Example:
            >>> validate_codigo("DEN-2024-001")
            ValidationResult(is_valid=True)
            
            >>> validate_codigo("CODIGO-MUY-LARGO-QUE-EXCEDE")
            ValidationResult(
                is_valid=False,
                error_message="El código excede el límite de 20 caracteres",
                suggestion="CODIGO-MUY-LARGO"
            )
        """
        codigo = codigo.strip()
        
        if not codigo:
            return ValidationResult(
                is_valid=False,
                error_message="El código no puede estar vacío",
                suggestion="Ejemplo: OPE-2025-001",
                field_name="Código"
            )
        
        if len(codigo) > UnifiedCopy.MAX_CODIGO_LENGTH:
            excess = len(codigo) - UnifiedCopy.MAX_CODIGO_LENGTH
            suggestion = codigo[:UnifiedCopy.MAX_CODIGO_LENGTH]
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"El código excede el límite de {UnifiedCopy.MAX_CODIGO_LENGTH} caracteres "
                    f"por {excess} caracteres"
                ),
                suggestion=suggestion,
                field_name="Código"
            )
        
        # Validar formato básico (sin espacios, caracteres especiales limitados)
        if ' ' in codigo:
            return ValidationResult(
                is_valid=False,
                error_message="El código no debe contener espacios",
                suggestion=codigo.replace(' ', '-'),
                field_name="Código"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_titulo(titulo: str) -> ValidationResult:
        """
        Valida título de tarea con límite unificado de 100 caracteres.
        
        Quick Win #3: Límite consistente de 100 caracteres para títulos.
        
        Args:
            titulo: Título a validar
        
        Returns:
            ValidationResult con estado y mensaje específico
        """
        titulo = titulo.strip()
        
        if not titulo:
            return ValidationResult(
                is_valid=False,
                error_message="El título no puede estar vacío",
                suggestion="Ejemplo: Reparar tubería principal edificio A",
                field_name="Título"
            )
        
        if len(titulo) < UnifiedCopy.MIN_TITULO_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"El título debe tener al menos {UnifiedCopy.MIN_TITULO_LENGTH} caracteres "
                    f"para ser descriptivo"
                ),
                suggestion="Añade más detalles sobre la tarea",
                field_name="Título"
            )
        
        if len(titulo) > UnifiedCopy.MAX_TITULO_LENGTH:
            excess = len(titulo) - UnifiedCopy.MAX_TITULO_LENGTH
            suggestion = titulo[:UnifiedCopy.MAX_TITULO_LENGTH].rstrip()
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"El título excede el límite de {UnifiedCopy.MAX_TITULO_LENGTH} caracteres "
                    f"por {excess} caracteres"
                ),
                suggestion=suggestion,
                field_name="Título"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_tipo(tipo: str) -> ValidationResult:
        """
        Valida tipo de tarea contra nomenclatura oficial.
        
        Args:
            tipo: Tipo de tarea
        
        Returns:
            ValidationResult con estado y mensaje
        """
        tipos_validos = [
            UnifiedCopy.TIPO_OPERATIVO,
            UnifiedCopy.TIPO_ADMINISTRATIVO,
            UnifiedCopy.TIPO_EMERGENCIA
        ]
        
        tipo_upper = tipo.upper().strip()
        
        if tipo_upper not in tipos_validos:
            return ValidationResult(
                is_valid=False,
                error_message=f"Tipo de tarea '{tipo}' no válido",
                suggestion=f"Tipos válidos: {', '.join(tipos_validos)}",
                field_name="Tipo"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_user_id(user_id: str) -> ValidationResult:
        """
        Valida ID de usuario.
        
        Args:
            user_id: ID de usuario a validar
        
        Returns:
            ValidationResult con estado
        """
        user_id = user_id.strip()
        
        if not user_id:
            return ValidationResult(
                is_valid=False,
                error_message="El ID de usuario no puede estar vacío",
                suggestion="Ejemplo: 101",
                field_name="ID de Usuario"
            )
        
        if not user_id.isdigit():
            return ValidationResult(
                is_valid=False,
                error_message="El ID de usuario debe ser numérico",
                suggestion="Usa solo números, ejemplo: 101",
                field_name="ID de Usuario"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_user_ids_list(user_ids_str: str) -> Tuple[ValidationResult, list[int]]:
        """
        Valida lista de IDs de usuario separados por comas.
        
        Args:
            user_ids_str: String con IDs separados por comas
        
        Returns:
            Tupla (ValidationResult, lista de IDs válidos)
        
        Example:
            >>> validate_user_ids_list("101, 102, 103")
            (ValidationResult(is_valid=True), [101, 102, 103])
            
            >>> validate_user_ids_list("101, abc, 103")
            (ValidationResult(is_valid=False, ...), [])
        """
        if not user_ids_str.strip():
            # Lista vacía es válida (asignados opcionales)
            return ValidationResult(is_valid=True), []
        
        parts = [p.strip() for p in user_ids_str.split(',')]
        valid_ids = []
        invalid_parts = []
        
        for part in parts:
            if part.isdigit():
                valid_ids.append(int(part))
            else:
                invalid_parts.append(part)
        
        if invalid_parts:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"IDs inválidos encontrados: {', '.join(invalid_parts)}"
                ),
                suggestion="Usa solo números separados por comas: 101, 102, 103",
                field_name="IDs de Asignados"
            ), []
        
        return ValidationResult(is_valid=True), valid_ids


class CopyFormatter:
    """
    Formateadores de texto con terminología unificada.
    """
    
    @staticmethod
    def format_delegado_label(nombre: Optional[str] = None) -> str:
        """
        Formatea etiqueta de delegado con terminología unificada.
        
        Args:
            nombre: Nombre del delegado (opcional)
        
        Returns:
            String formateado
        """
        if nombre:
            return f"{UnifiedCopy.DELEGADO_TERM}: {nombre}"
        return UnifiedCopy.DELEGADO_TERM
    
    @staticmethod
    def format_asignados_label(count: int = 0, nombres: Optional[list[str]] = None) -> str:
        """
        Formatea etiqueta de asignados con terminología unificada.
        
        Args:
            count: Número de asignados
            nombres: Lista de nombres (opcional)
        
        Returns:
            String formateado
        """
        if nombres:
            if len(nombres) <= 3:
                return f"{UnifiedCopy.ASIGNADOS_TERM}: {', '.join(nombres)}"
            else:
                return f"{UnifiedCopy.ASIGNADOS_TERM}: {', '.join(nombres[:3])} y {len(nombres) - 3} más"
        
        if count == 0:
            return f"{UnifiedCopy.ASIGNADOS_TERM}: Ninguno"
        elif count == 1:
            return f"{UnifiedCopy.ASIGNADOS_TERM}: 1 persona"
        else:
            return f"{UnifiedCopy.ASIGNADOS_TERM}: {count} personas"
    
    @staticmethod
    def format_character_counter(current: int, max_length: int) -> str:
        """
        Formatea contador de caracteres.
        
        Args:
            current: Caracteres actuales
            max_length: Longitud máxima
        
        Returns:
            String formateado con indicador visual
        """
        remaining = max_length - current
        
        if remaining < 0:
            return f"📊 Caracteres: {current}/{max_length} (⚠️ {abs(remaining)} de más)"
        elif remaining < 10:
            return f"📊 Caracteres: {current}/{max_length} (⚠️ Quedan {remaining})"
        else:
            return f"📊 Caracteres: {current}/{max_length}"


# Tests de validación
if __name__ == "__main__":
    print("=== Tests de Validación ===\n")
    
    # Test 1: Código válido
    result = TaskValidator.validate_codigo("OPE-2025-001")
    print(f"Código válido: {result.is_valid}")
    
    # Test 2: Código muy largo
    result = TaskValidator.validate_codigo("CODIGO-DEMASIADO-LARGO-EXCEDE-LIMITE")
    print(f"\nCódigo largo:")
    print(f"  Válido: {result.is_valid}")
    print(f"  Error: {result.error_message}")
    print(f"  Sugerencia: {result.suggestion}")
    
    # Test 3: Título válido
    result = TaskValidator.validate_titulo("Reparar tubería principal edificio A")
    print(f"\nTítulo válido: {result.is_valid}")
    
    # Test 4: Título muy largo (>100 chars)
    long_title = "Este es un título extremadamente largo que definitivamente excede los 100 caracteres permitidos para títulos de tareas"
    result = TaskValidator.validate_titulo(long_title)
    print(f"\nTítulo largo:")
    print(f"  Válido: {result.is_valid}")
    print(f"  Error: {result.error_message}")
    print(f"  Sugerencia: {result.suggestion[:50]}...")
    
    # Test 5: IDs de usuario
    result, ids = TaskValidator.validate_user_ids_list("101, 102, 103")
    print(f"\nIDs válidos: {result.is_valid}, IDs: {ids}")
    
    result, ids = TaskValidator.validate_user_ids_list("101, abc, 103")
    print(f"IDs con error: {result.is_valid}, Error: {result.error_message}")
    
    # Test 6: Formateo de labels
    print(f"\n=== Labels Unificados ===")
    print(CopyFormatter.format_delegado_label("Juan Pérez"))
    print(CopyFormatter.format_asignados_label(count=3))
    print(CopyFormatter.format_character_counter(85, 100))
    print(CopyFormatter.format_character_counter(105, 100))
