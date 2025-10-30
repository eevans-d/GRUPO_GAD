# -*- coding: utf-8 -*-
"""
Sistema de instrumentación UX para métricas críticas.

Este módulo implementa Quick Win #5: Instrumentación UX Básica
- Métricas de abandono de wizard (objetivo <10%)
- Latencia P95 por paso (objetivo <800ms)
- Tasa de confirmaciones erróneas (objetivo <2%)
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics


class MetricType(Enum):
    """Tipos de métricas UX."""
    WIZARD_START = "wizard_start"
    WIZARD_COMPLETE = "wizard_complete"
    WIZARD_ABANDON = "wizard_abandon"
    STEP_LATENCY = "step_latency"
    CONFIRMATION_ERROR = "confirmation_error"
    VALIDATION_ERROR = "validation_error"
    USER_ERROR = "user_error"


@dataclass
class UXMetricEvent:
    """
    Evento de métrica UX con contexto.
    
    Quick Win #5: Instrumentación básica para métricas críticas.
    """
    metric_type: MetricType
    user_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Contexto del evento
    wizard_type: Optional[str] = None  # "crear" o "finalizar"
    step: Optional[int] = None  # Paso del wizard (1-6)
    latency_ms: Optional[float] = None  # Latencia en milisegundos
    error_type: Optional[str] = None  # Tipo de error
    error_field: Optional[str] = None  # Campo con error
    
    # Metadata adicional
    metadata: Dict = field(default_factory=dict)


class UXMetricsCollector:
    """
    Recolector de métricas UX con análisis en tiempo real.
    
    Quick Win #5: Tracking de métricas críticas de experiencia.
    """
    
    def __init__(self) -> None:
        self._events: List[UXMetricEvent] = []
        self._wizard_sessions: Dict[int, Dict[str, Any]] = {}  # user_id -> session data
    
    # ==================== WIZARD LIFECYCLE ====================
    
    def track_wizard_start(
        self, 
        user_id: int, 
        wizard_type: str = "crear"
    ) -> None:
        """
        Registra inicio de wizard.
        
        Args:
            user_id: ID de usuario
            wizard_type: Tipo de wizard
        """
        event = UXMetricEvent(
            metric_type=MetricType.WIZARD_START,
            user_id=user_id,
            wizard_type=wizard_type
        )
        self._events.append(event)
        
        # Iniciar tracking de sesión
        self._wizard_sessions[user_id] = {
            'started_at': datetime.now(),
            'wizard_type': wizard_type,
            'steps_completed': 0,
            'errors_count': 0,
            'step_latencies': []
        }
    
    def track_wizard_complete(
        self, 
        user_id: int,
        total_time_ms: Optional[float] = None
    ) -> None:
        """
        Registra completación exitosa de wizard.
        
        Args:
            user_id: ID de usuario
            total_time_ms: Tiempo total en milisegundos
        """
        event = UXMetricEvent(
            metric_type=MetricType.WIZARD_COMPLETE,
            user_id=user_id,
            latency_ms=total_time_ms
        )
        
        if user_id in self._wizard_sessions:
            session = self._wizard_sessions[user_id]
            event.wizard_type = session.get('wizard_type')
            event.metadata = {
                'total_steps': session.get('steps_completed', 0),
                'total_errors': session.get('errors_count', 0)
            }
            
            # Calcular tiempo si no se proporcionó
            if total_time_ms is None and 'started_at' in session:
                elapsed = datetime.now() - session['started_at']
                event.latency_ms = elapsed.total_seconds() * 1000
        
        self._events.append(event)
        
        # Limpiar sesión
        if user_id in self._wizard_sessions:
            del self._wizard_sessions[user_id]
    
    def track_wizard_abandon(
        self, 
        user_id: int,
        step: Optional[int] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Registra abandono de wizard.
        
        Quick Win #5: Métrica clave - objetivo <10% abandono.
        
        Args:
            user_id: ID de usuario
            step: Paso donde abandonó
            reason: Razón del abandono (opcional)
        """
        event = UXMetricEvent(
            metric_type=MetricType.WIZARD_ABANDON,
            user_id=user_id,
            step=step
        )
        
        if user_id in self._wizard_sessions:
            session = self._wizard_sessions[user_id]
            event.wizard_type = session.get('wizard_type')
            
            # Calcular tiempo hasta abandono
            if 'started_at' in session:
                elapsed = datetime.now() - session['started_at']
                event.latency_ms = elapsed.total_seconds() * 1000
            
            event.metadata = {
                'steps_completed': session.get('steps_completed', 0),
                'errors_before_abandon': session.get('errors_count', 0),
                'reason': reason
            }
        
        self._events.append(event)
        
        # Limpiar sesión
        if user_id in self._wizard_sessions:
            del self._wizard_sessions[user_id]
    
    # ==================== STEP TRACKING ====================
    
    def track_step_start(self, user_id: int, step: int) -> None:
        """
        Marca inicio de un paso del wizard.
        
        Args:
            user_id: ID de usuario
            step: Número de paso (1-6)
        """
        if user_id in self._wizard_sessions:
            self._wizard_sessions[user_id][f'step_{step}_start'] = datetime.now()
    
    def track_step_complete(self, user_id: int, step: int) -> None:
        """
        Registra completación de un paso con latencia.
        
        Quick Win #5: Latencia P95 por paso (objetivo <800ms).
        
        Args:
            user_id: ID de usuario
            step: Número de paso (1-6)
        """
        if user_id not in self._wizard_sessions:
            return
        
        session = self._wizard_sessions[user_id]
        start_key = f'step_{step}_start'
        
        if start_key in session:
            start_time = session[start_key]
            elapsed = datetime.now() - start_time
            latency_ms = elapsed.total_seconds() * 1000
            
            # Registrar evento de latencia
            event = UXMetricEvent(
                metric_type=MetricType.STEP_LATENCY,
                user_id=user_id,
                wizard_type=session.get('wizard_type'),
                step=step,
                latency_ms=latency_ms
            )
            self._events.append(event)
            
            # Actualizar sesión
            session['steps_completed'] = step
            if 'step_latencies' not in session:
                session['step_latencies'] = []
            session['step_latencies'].append(latency_ms)
    
    # ==================== ERROR TRACKING ====================
    
    def track_validation_error(
        self, 
        user_id: int,
        field: str,
        error_type: str,
        step: Optional[int] = None
    ) -> None:
        """
        Registra error de validación.
        
        Args:
            user_id: ID de usuario
            field: Campo con error
            error_type: Tipo de error
            step: Paso donde ocurrió
        """
        event = UXMetricEvent(
            metric_type=MetricType.VALIDATION_ERROR,
            user_id=user_id,
            step=step,
            error_type=error_type,
            error_field=field
        )
        self._events.append(event)
        
        # Incrementar contador de errores en sesión
        if user_id in self._wizard_sessions:
            self._wizard_sessions[user_id]['errors_count'] = \
                self._wizard_sessions[user_id].get('errors_count', 0) + 1
    
    def track_confirmation_error(
        self, 
        user_id: int,
        error_details: Optional[str] = None
    ) -> None:
        """
        Registra error en confirmación.
        
        Quick Win #5: Tasa de confirmaciones erróneas (objetivo <2%).
        
        Args:
            user_id: ID de usuario
            error_details: Detalles del error
        """
        event = UXMetricEvent(
            metric_type=MetricType.CONFIRMATION_ERROR,
            user_id=user_id,
            metadata={'details': error_details}
        )
        
        if user_id in self._wizard_sessions:
            event.wizard_type = self._wizard_sessions[user_id].get('wizard_type')
        
        self._events.append(event)
    
    # ==================== ANALYTICS ====================
    
    def get_wizard_abandonment_rate(
        self, 
        wizard_type: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> float:
        """
        Calcula tasa de abandono de wizard.
        
        Quick Win #5: Métrica objetivo <10%.
        
        Args:
            wizard_type: Filtrar por tipo de wizard
            time_window_hours: Ventana de tiempo en horas
        
        Returns:
            Tasa de abandono (0.0 a 1.0)
        """
        events = self._filter_events(
            time_window_hours=time_window_hours,
            wizard_type=wizard_type
        )
        
        starts = sum(1 for e in events if e.metric_type == MetricType.WIZARD_START)
        completes = sum(1 for e in events if e.metric_type == MetricType.WIZARD_COMPLETE)
        
        if starts == 0:
            return 0.0
        
        abandonment_rate = 1 - (completes / starts)
        return max(0.0, min(1.0, abandonment_rate))
    
    def get_step_latency_p95(
        self, 
        step: Optional[int] = None,
        time_window_hours: Optional[int] = None
    ) -> float:
        """
        Calcula latencia P95 por paso.
        
        Quick Win #5: Objetivo <800ms.
        
        Args:
            step: Filtrar por paso específico
            time_window_hours: Ventana de tiempo
        
        Returns:
            Latencia P95 en milisegundos
        """
        events = self._filter_events(
            metric_type=MetricType.STEP_LATENCY,
            time_window_hours=time_window_hours
        )
        
        if step is not None:
            events = [e for e in events if e.step == step]
        
        latencies = [e.latency_ms for e in events if e.latency_ms is not None]
        
        if not latencies:
            return 0.0
        
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        return latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
    
    def get_confirmation_error_rate(
        self,
        time_window_hours: Optional[int] = None
    ) -> float:
        """
        Calcula tasa de errores en confirmación.
        
        Quick Win #5: Objetivo <2%.
        
        Args:
            time_window_hours: Ventana de tiempo
        
        Returns:
            Tasa de error (0.0 a 1.0)
        """
        events = self._filter_events(time_window_hours=time_window_hours)
        
        completes = sum(1 for e in events if e.metric_type == MetricType.WIZARD_COMPLETE)
        errors = sum(1 for e in events if e.metric_type == MetricType.CONFIRMATION_ERROR)
        
        total = completes + errors
        if total == 0:
            return 0.0
        
        return errors / total
    
    def get_error_breakdown(
        self,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Obtiene breakdown de errores por campo.
        
        Args:
            time_window_hours: Ventana de tiempo
        
        Returns:
            Diccionario campo -> contador
        """
        events = self._filter_events(
            metric_type=MetricType.VALIDATION_ERROR,
            time_window_hours=time_window_hours
        )
        
        breakdown = {}
        for event in events:
            if event.error_field:
                breakdown[event.error_field] = breakdown.get(event.error_field, 0) + 1
        
        return breakdown
    
    def get_metrics_summary(self) -> Dict[str, any]:
        """
        Obtiene resumen de todas las métricas UX.
        
        Quick Win #5: Dashboard de métricas críticas.
        
        Returns:
            Diccionario con métricas principales
        """
        # Últimas 24 horas
        abandonment = self.get_wizard_abandonment_rate(time_window_hours=24)
        latency_p95 = self.get_step_latency_p95(time_window_hours=24)
        confirmation_errors = self.get_confirmation_error_rate(time_window_hours=24)
        error_breakdown = self.get_error_breakdown(time_window_hours=24)
        
        # Calcular promedios
        events_24h = self._filter_events(time_window_hours=24)
        latency_events = [e for e in events_24h if e.metric_type == MetricType.STEP_LATENCY and e.latency_ms]
        
        avg_latency = 0.0
        if latency_events:
            avg_latency = statistics.mean([e.latency_ms for e in latency_events])
        
        return {
            'abandonment_rate': {
                'value': abandonment,
                'percentage': abandonment * 100,
                'target': 10.0,
                'meets_target': abandonment * 100 < 10.0
            },
            'latency_p95_ms': {
                'value': latency_p95,
                'target': 800.0,
                'meets_target': latency_p95 < 800.0
            },
            'latency_avg_ms': {
                'value': avg_latency
            },
            'confirmation_error_rate': {
                'value': confirmation_errors,
                'percentage': confirmation_errors * 100,
                'target': 2.0,
                'meets_target': confirmation_errors * 100 < 2.0
            },
            'error_breakdown': error_breakdown,
            'total_events_24h': len(events_24h)
        }
    
    # ==================== HELPERS ====================
    
    def _filter_events(
        self,
        metric_type: Optional[MetricType] = None,
        wizard_type: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> List[UXMetricEvent]:
        """Filtra eventos por criterios."""
        filtered = self._events
        
        if metric_type:
            filtered = [e for e in filtered if e.metric_type == metric_type]
        
        if wizard_type:
            filtered = [e for e in filtered if e.wizard_type == wizard_type]
        
        if time_window_hours:
            cutoff = datetime.now() - timedelta(hours=time_window_hours)
            filtered = [e for e in filtered if e.timestamp >= cutoff]
        
        return filtered
    
    def clear_old_events(self, days_to_keep: int = 7) -> int:
        """
        Limpia eventos antiguos.
        
        Args:
            days_to_keep: Días de eventos a mantener
        
        Returns:
            Número de eventos eliminados
        """
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        initial_count = len(self._events)
        self._events = [e for e in self._events if e.timestamp >= cutoff]
        return initial_count - len(self._events)


# Instancia global del collector
ux_metrics = UXMetricsCollector()


# Helper functions para uso fácil
def track_wizard_start(user_id: int, wizard_type: str = "crear") -> None:
    """Shortcut para tracking de inicio de wizard."""
    ux_metrics.track_wizard_start(user_id, wizard_type)


def track_wizard_complete(user_id: int) -> None:
    """Shortcut para tracking de completación."""
    ux_metrics.track_wizard_complete(user_id)


def track_wizard_abandon(user_id: int, step: Optional[int] = None) -> None:
    """Shortcut para tracking de abandono."""
    ux_metrics.track_wizard_abandon(user_id, step)


# Tests
if __name__ == "__main__":
    print("=== Tests de Instrumentación UX ===\n")
    
    # Simular sesión exitosa
    user1 = 1001
    ux_metrics.track_wizard_start(user1, "crear")
    ux_metrics.track_step_start(user1, 1)
    ux_metrics.track_step_complete(user1, 1)
    ux_metrics.track_step_start(user1, 2)
    ux_metrics.track_step_complete(user1, 2)
    ux_metrics.track_wizard_complete(user1)
    
    # Simular abandono
    user2 = 1002
    ux_metrics.track_wizard_start(user2, "crear")
    ux_metrics.track_step_start(user2, 1)
    ux_metrics.track_step_complete(user2, 1)
    ux_metrics.track_wizard_abandon(user2, step=2)
    
    # Obtener métricas
    summary = ux_metrics.get_metrics_summary()
    
    print("=== Resumen de Métricas UX ===\n")
    print(f"Abandono: {summary['abandonment_rate']['percentage']:.1f}% "
          f"(Objetivo: {summary['abandonment_rate']['target']}%)")
    print(f"  ✓ Cumple objetivo" if summary['abandonment_rate']['meets_target'] else f"  ✗ No cumple objetivo")
    
    print(f"\nLatencia P95: {summary['latency_p95_ms']['value']:.0f}ms "
          f"(Objetivo: {summary['latency_p95_ms']['target']}ms)")
    print(f"  ✓ Cumple objetivo" if summary['latency_p95_ms']['meets_target'] else f"  ✗ No cumple objetivo")
    
    print(f"\nErrores confirmación: {summary['confirmation_error_rate']['percentage']:.1f}% "
          f"(Objetivo: {summary['confirmation_error_rate']['target']}%)")
    print(f"  ✓ Cumple objetivo" if summary['confirmation_error_rate']['meets_target'] else f"  ✗ No cumple objetivo")
