# Playbook – Plantilla de Risk Score

Objetivo: Determinar rápidamente el riesgo compuesto de un release para calibrar rigor (modo A/B/C) y gates.

## Dimensiones y Ponderaciones Sugeridas
| Dimensión | Descripción | Escala (1–5) | Peso | Ejemplo 5 (alto) | Ejemplo 1 (bajo) |
|-----------|------------|--------------|------|------------------|------------------|
| Impacto en Usuario | Afecta flujo core o ingresos | 1–5 | 0.30 | Checkout crítico | Página secundaria |
| Complejidad Técnica | Número de componentes tocados | 1–5 | 0.20 | Cambios multi-servicio | Cambio aislado |
| Superficie de Seguridad | Incrementa vectores de ataque | 1–5 | 0.15 | Nuevo endpoint público | Cambio interno |
| Reversibilidad | Dificultad del rollback | 1–5 | 0.15 | Migración irreversible | Feature flag simple |
| Dependencias Externas | Servicios/terceros involucrados | 1–5 | 0.10 | Integración con pasarela | Sin dependencias |
| Madurez de Pruebas | Cobertura + tests críticos | 1–5 | 0.10 | Cobertura <30% sin tests e2e | Cobertura >80% |

Fórmula: `RISK_SCORE = Σ(escala * peso)` → Normalizado a 1–5.

## Interpretación
| Score | Clasificación | Modo Sugerido | Acciones Adicionales |
|-------|---------------|---------------|----------------------|
| 4.0 – 5.0 | Alto | C | Revisiones extras + prueba de rollback + canary |
| 2.5 – 3.9 | Medio | B | Gates estándar + monitoreo |
| 1.0 – 2.4 | Bajo | A | Fast lane + foco en feedback |

## Ejemplo Relleno
| Dimensión | Escala | Peso | Contribución |
|-----------|--------|------|--------------|
| Impacto en Usuario | 4 | 0.30 | 1.20 |
| Complejidad Técnica | 3 | 0.20 | 0.60 |
| Superficie de Seguridad | 2 | 0.15 | 0.30 |
| Reversibilidad | 4 | 0.15 | 0.60 |
| Dependencias Externas | 2 | 0.10 | 0.20 |
| Madurez de Pruebas | 3 | 0.10 | 0.30 |
| TOTAL |  |  | 3.20 (Modo B) |

## Uso Operativo
1. Completar tabla en sesión corta (≤10 min) con equipo core.
2. Registrar score y fecha en changelog / ticket.
3. Ajustar modo operativo si score cambia >0.5 tras nuevos hallazgos.

## Anti-Patrones
- Inflar valores para frenar despliegue sin argumento técnico.
- Minimizar riesgos por presión externa.
- Omitir revisión cuando el scope cambia.

---
Actualizar pesos tras 2–3 iteraciones si no correlacionan con incidentes reales.
