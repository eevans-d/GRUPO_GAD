# Índice de Documentación - GRUPO_GAD

## 1. Base del Proyecto
- `README.md`: Guía general, instalación, despliegue.
- `pyproject.toml`: Configuración de dependencias y herramientas.

## 2. Backend & Core
- `WEBSOCKET_SYSTEM_STATUS.md`: Estado y diseño del subsistema WebSocket.
- `docs/PROMETHEUS_METRICAS_DISENO.md`: Diseño propuesto de métricas.
- `docs/COBERTURA_NOTAS.md`: Notas sobre cobertura y módulos selectivos.

## 3. Playbook de Finalización
- `docs/PLAYBOOK_FINALIZACION.md`: Marco principal.
- `docs/PLAYBOOK_TRIAGE_MATRIX.md`: Matriz de triage Alpha/Beta/Gamma.
- `docs/PLAYBOOK_RISK_SCORE_TEMPLATE.md`: Plantilla de cálculo de riesgo.
- `docs/PLAYBOOK_ROLLBACK_RUNBOOK.md`: Runbook de rollback (<10 min).
- `docs/CHECKLIST_PRE_DEPLOY.md`: Checklist pre-despliegue.

Utilidades:
- `scripts/risk_score_calculator.py`: Calcula RISK_SCORE desde JSON/YAML.
- Ejemplos: `docs/risk_score_example.json`, `docs/risk_score_example.yaml`.
- Nueva plantilla triage: `docs/triage_example.json`.

## 4. Seguridad y Operaciones
- (Pendiente) Documentos de hardening y pipeline (futuros).

## 5. Próximos Artefactos (Sugeridos)
- Plantillas para incident reviews.
- Índice de decisiones de arquitectura.

---
Documento vivo. Actualizar al añadir nuevos artefactos.
