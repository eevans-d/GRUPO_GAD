# -*- coding: utf-8 -*-
"""
Sistema de mensajes de error específicos con CTAs claras.

Este módulo implementa Quick Win #2: Mensajes de error específicos
con guidance clara y contexto útil para el usuario.
"""

from typing import Optional
from loguru import logger

from src.bot.utils.emojis import StatusEmojis, ActionEmojis, GeneralEmojis


class ErrorCategory:
    """Categorías de errores para clasificación."""
    VALIDATION = "validation"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    API_ERROR = "api_error"
    NETWORK = "network"
    USER_INPUT = "user_input"
    SYSTEM = "system"


class ErrorMessages:
    """
    Sistema centralizado de mensajes de error con CTAs específicas.
    
    Quick Win #2: Reemplazar mensajes genéricos por mensajes detallados
    con calls-to-action claras.
    """
    
    @staticmethod
    def format_validation_error(
        field: str,
        value: Optional[str],
        issue: str,
        suggestion: str = "",
        max_length: Optional[int] = None
    ) -> str:
        """
        Error de validación con detalles específicos y sugerencias.
        
        Args:
            field: Campo que falló la validación
            value: Valor ingresado (se trunca si es muy largo)
            issue: Descripción específica del problema
            suggestion: Sugerencia concreta de corrección
            max_length: Longitud máxima esperada
        
        Returns:
            Mensaje formateado con contexto y CTA
        
        Example:
            >>> format_validation_error(
            ...     field="Código",
            ...     value="DEN-2024-001-EXTRA-MUY-LARGO",
            ...     issue="El código excede el límite de 20 caracteres",
            ...     suggestion="DEN-2024-001-EXTRA",
            ...     max_length=20
            ... )
        """
        message = (
            f"{StatusEmojis.WARNING} *Error de validación: {field}*\n\n"
            f"*Problema:* {issue}\n\n"
        )
        
        if value:
            display_value = value[:50] + "..." if len(value) > 50 else value
            message += f"*Tu entrada:* `{display_value}`\n"
            if max_length:
                message += f"*Longitud:* {len(value)} caracteres (máximo: {max_length})\n\n"
        
        if suggestion:
            message += (
                f"{GeneralEmojis.HELP} *Sugerencia:*\n"
                f"`{suggestion}`\n\n"
            )
        
        message += (
            f"{ActionEmojis.REFRESH} *Qué hacer:*\n"
            f"• Corrige el valor según las indicaciones\n"
            f"• Vuelve a intentar con el formato correcto\n"
            f"• Usa {ActionEmojis.CANCEL} /cancelar si necesitas empezar de nuevo"
        )
        
        return message
    
    @staticmethod
    def format_not_found_error(
        resource: str,
        identifier: Optional[str] = None,
        suggestions: Optional[list[str]] = None
    ) -> str:
        """
        Error de recurso no encontrado con alternativas.
        
        Args:
            resource: Tipo de recurso (Usuario, Tarea, etc.)
            identifier: Identificador buscado
            suggestions: Lista de sugerencias o alternativas
        
        Returns:
            Mensaje formateado con opciones de recuperación
        
        Example:
            >>> format_not_found_error(
            ...     resource="Usuario",
            ...     identifier="ID 999",
            ...     suggestions=["Verifica el ID", "Busca en lista de efectivos"]
            ... )
        """
        message = (
            f"{StatusEmojis.ERROR} *{resource} no encontrado*\n\n"
        )
        
        if identifier:
            message += f"No se encontró: `{identifier}`\n\n"
        
        message += (
            f"{GeneralEmojis.HELP} *Posibles causas:*\n"
            f"• El {resource.lower()} no existe en el sistema\n"
            f"• El identificador es incorrecto\n"
            f"• Fue eliminado recientemente\n"
            f"• No tienes permisos para verlo\n\n"
        )
        
        if suggestions:
            message += f"{ActionEmojis.FORWARD} *Qué hacer:*\n"
            for suggestion in suggestions:
                message += f"• {suggestion}\n"
        else:
            message += (
                f"{ActionEmojis.FORWARD} *Qué hacer:*\n"
                f"• Verifica el identificador\n"
                f"• Consulta la lista de recursos disponibles\n"
                f"• Contacta al administrador si crees que es un error\n"
            )
        
        message += f"\n{ActionEmojis.BACK} Volver al menú: /start"
        
        return message
    
    @staticmethod
    def format_permission_error(
        action: str,
        required_role: Optional[str] = None,
        current_role: Optional[str] = None
    ) -> str:
        """
        Error de permisos con información de roles.
        
        Args:
            action: Acción que se intentó realizar
            required_role: Rol requerido
            current_role: Rol actual del usuario
        
        Returns:
            Mensaje con explicación de permisos y CTA
        
        Example:
            >>> format_permission_error(
            ...     action="crear tareas de emergencia",
            ...     required_role="Supervisor",
            ...     current_role="Operador"
            ... )
        """
        message = (
            f"{StatusEmojis.WARNING} *Acceso denegado*\n\n"
            f"No tienes permisos para {action}.\n\n"
        )
        
        if current_role and required_role:
            message += (
                f"{GeneralEmojis.KEY} *Información de permisos:*\n"
                f"• Tu rol actual: *{current_role}*\n"
                f"• Rol requerido: *{required_role}*\n\n"
            )
        
        message += (
            f"{GeneralEmojis.HELP} *¿Por qué?*\n"
            f"Esta acción está restringida a usuarios con permisos especiales "
            f"para mantener la seguridad del sistema.\n\n"
            f"{ActionEmojis.FORWARD} *¿Necesitas acceso?*\n"
            f"• Contacta a tu supervisor\n"
            f"• Solicita elevación de permisos al administrador\n"
            f"• Verifica que estés usando la cuenta correcta\n\n"
            f"{GeneralEmojis.PHONE} *Soporte:* Contacta al administrador del sistema\n"
            f"{ActionEmojis.BACK} Volver al menú: /start"
        )
        
        return message
    
    @staticmethod
    def format_api_error(
        operation: str,
        error_code: Optional[str] = None,
        technical_details: Optional[str] = None,
        retry_possible: bool = True
    ) -> str:
        """
        Error de API con contexto técnico y opciones de recovery.
        
        Args:
            operation: Operación que se estaba realizando
            error_code: Código de error HTTP o interno
            technical_details: Detalles técnicos (opcional)
            retry_possible: Si el usuario puede reintentar
        
        Returns:
            Mensaje con diagnóstico y pasos de recovery
        
        Example:
            >>> format_api_error(
            ...     operation="crear tarea",
            ...     error_code="500",
            ...     retry_possible=True
            ... )
        """
        message = (
            f"{StatusEmojis.ERROR} *Error al {operation}*\n\n"
            f"No pudimos completar la operación debido a un problema técnico.\n\n"
        )
        
        if error_code:
            message += f"{GeneralEmojis.SETTINGS} *Código de error:* `{error_code}`\n"
        
        if technical_details:
            details = technical_details[:100] + "..." if len(technical_details) > 100 else technical_details
            message += f"*Detalles:* {details}\n"
        
        message += "\n"
        
        if retry_possible:
            message += (
                f"{ActionEmojis.REFRESH} *Qué hacer:*\n"
                f"1. Espera unos segundos e intenta nuevamente\n"
                f"2. Verifica tu conexión a internet\n"
                f"3. Si el problema persiste, usa /start para reiniciar\n"
                f"4. Contacta al soporte técnico si el error continúa\n\n"
            )
        else:
            message += (
                f"{ActionEmojis.FORWARD} *Qué hacer:*\n"
                f"• Este error requiere atención del administrador\n"
                f"• Contacta al soporte técnico con el código de error\n"
                f"• No intentes repetir la operación por ahora\n\n"
            )
        
        message += (
            f"{StatusEmojis.INFO} *Nota:* Este error ha sido reportado automáticamente "
            f"al equipo técnico.\n\n"
            f"{ActionEmojis.BACK} Volver al menú: /start"
        )
        
        return message
    
    @staticmethod
    def format_network_error(retry_count: int = 0) -> str:
        """
        Error de conexión de red.
        
        Args:
            retry_count: Número de reintentos realizados
        
        Returns:
            Mensaje con troubleshooting de red
        """
        message = (
            f"{StatusEmojis.WARNING} *Problema de conexión*\n\n"
            f"No pudimos conectar con el servidor.\n\n"
        )
        
        if retry_count > 0:
            message += f"*Intentos realizados:* {retry_count}\n\n"
        
        message += (
            f"{GeneralEmojis.HELP} *Posibles causas:*\n"
            f"• Problema temporal de conexión a internet\n"
            f"• El servidor está en mantenimiento\n"
            f"• Tu red está bloqueando la conexión\n\n"
            f"{ActionEmojis.REFRESH} *Qué hacer:*\n"
            f"1. Verifica tu conexión WiFi o datos móviles\n"
            f"2. Espera 30 segundos e intenta nuevamente\n"
            f"3. Si persiste, contacta al soporte técnico\n\n"
            f"{StatusEmojis.INFO} *Estado:* Reintentaremos automáticamente en breve\n\n"
            f"{ActionEmojis.BACK} Volver al menú: /start"
        )
        
        return message
    
    @staticmethod
    def format_user_input_error(
        expected: str,
        received: Optional[str] = None,
        examples: Optional[list[str]] = None
    ) -> str:
        """
        Error de formato de entrada de usuario.
        
        Args:
            expected: Descripción de lo esperado
            received: Lo que se recibió
            examples: Lista de ejemplos válidos
        
        Returns:
            Mensaje educativo con ejemplos
        
        Example:
            >>> format_user_input_error(
            ...     expected="ID de usuario numérico",
            ...     received="abc123",
            ...     examples=["101", "205", "999"]
            ... )
        """
        message = (
            f"{StatusEmojis.WARNING} *Formato de entrada incorrecto*\n\n"
            f"*Se esperaba:* {expected}\n"
        )
        
        if received:
            message += f"*Se recibió:* `{received}`\n\n"
        
        if examples:
            message += f"{GeneralEmojis.HELP} *Ejemplos válidos:*\n"
            for example in examples[:3]:  # Máximo 3 ejemplos
                message += f"• `{example}`\n"
            message += "\n"
        
        message += (
            f"{ActionEmojis.REFRESH} *Intenta nuevamente:*\n"
            f"• Revisa el formato esperado\n"
            f"• Usa uno de los ejemplos como guía\n"
            f"• Asegúrate de no incluir espacios extras\n\n"
            f"{ActionEmojis.CANCEL} Cancelar: /cancelar"
        )
        
        return message
    
    @staticmethod
    def get_generic_error(context: str = "operación") -> str:
        """
        Error genérico cuando no se tiene más contexto.
        
        Args:
            context: Contexto de la operación
        
        Returns:
            Mensaje genérico pero útil
        """
        return (
            f"{StatusEmojis.ERROR} *Error inesperado*\n\n"
            f"Ocurrió un problema al procesar tu {context}.\n\n"
            f"{ActionEmojis.REFRESH} *Qué hacer:*\n"
            f"1. Intenta nuevamente en unos segundos\n"
            f"2. Si el error persiste, usa /start para reiniciar\n"
            f"3. Contacta al soporte si el problema continúa\n\n"
            f"{StatusEmojis.INFO} *Nota:* Este error ha sido registrado automáticamente.\n\n"
            f"{ActionEmojis.BACK} Volver al menú: /start"
        )


def log_error(
    category: str,
    message: str,
    user_id: Optional[int] = None,
    context: Optional[dict] = None
) -> None:
    """
    Registra errores con contexto estructurado.
    
    Args:
        category: Categoría del error (de ErrorCategory)
        message: Mensaje de error
        user_id: ID del usuario afectado
        context: Contexto adicional del error
    """
    logger.bind(
        error_category=category,
        user_id=user_id,
        context=context or {}
    ).error(message)


# Ejemplos de uso documentados
if __name__ == "__main__":
    # Ejemplo 1: Error de validación de código
    print(ErrorMessages.format_validation_error(
        field="Código de tarea",
        value="DEN-2024-001-ADICIONAL-EXTRA",
        issue="El código excede el límite de 20 caracteres",
        suggestion="DEN-2024-001",
        max_length=20
    ))
    
    print("\n" + "="*50 + "\n")
    
    # Ejemplo 2: Usuario no encontrado
    print(ErrorMessages.format_not_found_error(
        resource="Usuario",
        identifier="ID 999",
        suggestions=[
            "Verifica el número de ID",
            "Busca en la lista de efectivos disponibles",
            "Confirma que el usuario esté activo"
        ]
    ))
    
    print("\n" + "="*50 + "\n")
    
    # Ejemplo 3: Error de permisos
    print(ErrorMessages.format_permission_error(
        action="crear tareas de emergencia",
        required_role="Supervisor",
        current_role="Operador"
    ))
