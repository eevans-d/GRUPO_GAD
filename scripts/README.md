# Scripts Utilitarios

| Script | Propósito | Impacto Runtime |
|--------|-----------|-----------------|
| `risk_score_calculator.py` | Calcula RISK_SCORE desde JSON/YAML | Ninguno |
| `triage_validator.py` | Valida estructura y estados de triage | Ninguno |
| `release_readiness_report.py` | Genera reporte Markdown consolidado | Ninguno |

Ejemplos:
```bash
python scripts/triage_validator.py --file docs/triage_example.json
python scripts/triage_validator.py --file docs/triage_example.json --require-alpha-resuelto
python scripts/release_readiness_report.py --risk-file docs/risk_score_example.json --triage-file docs/triage_example.json > docs/release_readiness_report.md
```

Todos los scripts son compatibles con el modo "Barco Anclado" (solo documentación y soporte de decisión).
