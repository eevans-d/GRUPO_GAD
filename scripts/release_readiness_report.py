#!/usr/bin/env python3
"""Genera un reporte consolidado (Markdown) de readiness usando:
 - risk_score_example.(json|yaml)
 - triage_example.json

Salida por stdout; puede redirigirse a docs/release_readiness_report.md

Uso:
  python scripts/release_readiness_report.py \
      --risk-file docs/risk_score_example.json \
      --triage-file docs/triage_example.json > docs/release_readiness_report.md
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

RISK_WEIGHTS = {
    "impacto_usuario": 0.30,
    "complejidad_tecnica": 0.20,
    "superficie_seguridad": 0.15,
    "reversibilidad": 0.15,
    "dependencias_externas": 0.10,
    "madurez_pruebas": 0.10,
}


def load_any(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("pyyaml requerido para YAML")
        return yaml.safe_load(text)  # type: ignore
    return json.loads(text)


def compute_risk(data: Dict[str, Any]) -> float:
    total = 0.0
    for k, w in RISK_WEIGHTS.items():
        v = data.get(k)
        if v is None:
            raise ValueError(f"Falta dimensión {k}")
        total += float(v) * w
    return round(total, 2)


def classify(score: float) -> str:
    if score >= 4.0:
        return "ALTO (Modo C)"
    if score >= 2.5:
        return "MEDIO (Modo B)"
    return "BAJO (Modo A)"


def summarize_triage(data: Dict[str, Any]) -> Dict[str, int]:
    return {k: len(data.get(k, [])) for k in ["alpha", "beta", "gamma"]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generador de reporte readiness")
    ap.add_argument("--risk-file", required=True)
    ap.add_argument("--triage-file", required=True)
    args = ap.parse_args()
    risk = load_any(Path(args.risk_file))
    triage = load_any(Path(args.triage_file))
    score = compute_risk(risk)
    triage_counts = summarize_triage(triage)
    alpha_ok = all(item.get("estado") == "resuelto" for item in triage.get("alpha", []))
    # ETA heurística: número de Beta pendientes * 0.5 días (ejemplo)
    beta_pendientes = sum(1 for i in triage.get("beta", []) if i.get("estado") != "resuelto")
    eta_dias = round(beta_pendientes * 0.5, 1)
    print(f"# Release Readiness Report\n")
    print(f"## Resumen de Riesgo\n")
    print(f"Score de Riesgo: **{score}** — {classify(score)}\n")
    print(f"## Triage Actual\n")
    print(f"Alpha: {triage_counts['alpha']} | Beta: {triage_counts['beta']} | Gamma: {triage_counts['gamma']}\n")
    print(f"Alpha todos resueltos: {'Sí' if alpha_ok else 'No'}\n")
    print(f"ETA (heurística) para Beta pendientes: ~{eta_dias} días\n")
    print("### Pendientes Alpha\n")
    if triage_counts['alpha'] == 0:
        print("(Ninguno)\n")
    else:
        for item in triage.get("alpha", []):
            print(f"- {item['id']}: {item['titulo']} (estado={item['estado']})")
        print()
    print("### Pendientes Beta (no resueltos)\n")
    for item in triage.get("beta", []):
        if item.get("estado") != "resuelto":
            print(f"- {item['id']}: {item['titulo']} (estado={item['estado']})")
    print()
    print("## Recomendación Modo Operativo\n")
    recommendation = classify(score)
    if not alpha_ok:
        print("Aún existen Alpha no resueltos → bloquear Go/No-Go.\n")
    else:
        print(f"Proceder con pipeline de liberación en modo {recommendation}.\n")
    print("## Notas\n")
    print("Este reporte es generado automáticamente. Ajustar heurísticas según histórico real.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
