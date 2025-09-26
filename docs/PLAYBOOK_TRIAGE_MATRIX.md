# Playbook – Matriz de Triage (Alpha / Beta / Gamma)

Objetivo: Clasificar elementos pendientes en la fase final para decidir qué entra en el release inmediato sin debates prolongados.

## Criterios de Clasificación
| Nivel | Entra en Release | Criterios Objetivos | Ejemplos | Acción si no cumple |
|-------|------------------|---------------------|----------|---------------------|
| Alpha (Do or Die) | Siempre | Bloquea uso core / riesgo de datos / incumple legal / causa caída | Fix migración crítica, crash al iniciar, token inválido | Debe resolverse antes del Go/No-Go |
| Beta (High Impact) | Sí (si hay capacidad) | Mejora significativa UX / reduce riesgo operacional / visibilidad alta | Optimización de query lenta, mensaje de error claro | Si falta tiempo → pasa a Gamma |
| Gamma (Postpone) | No | No bloquea valor principal / optimización incremental / nice-to-have | Refactor estético, micro mejora de logs | Backlog v1.1 con fecha tentativa |

## Proceso de Triage Brutal
1. Listar todos los pendientes (issues, notas, TODOs).
2. Asignar criterio objetivo (no subjetivo) a cada ítem.
3. Marcar Alpha inmediatamente; agrupar Beta y Gamma.
4. Recalcular esfuerzo restante: si Beta > capacidad → mover algunos a Gamma.
5. Congelar lista final (scope freeze) y comunicar.

## Filtros de Verificación
- ¿El usuario no puede completar el flujo principal? → Alpha.
- ¿El problema degrada severamente performance bajo carga esperada? → Alpha/Beta.
- ¿La mejora solo acelera un flujo secundario? → Beta/Gamma.
- ¿Refactor sin impacto observable inmediato? → Gamma.

## Anti-Patrones
- Etiquetar demasiados Alpha → Indicador de mala planificación o criterio laxo.
- Mover Gamma a Beta sin datos (presión externa) → Bloquear.
- Reabrir scope tras freeze → Requiere aprobación explícita y justificación cuantificada.

## Salida Esperada
Documento/Ticket final con tablas separadas por nivel y esfuerzo estimado agregado.

---
Documento vivo – ajustar según retrospectivas.
