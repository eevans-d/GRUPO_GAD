#!/usr/bin/env python3
"""CLI simple para calcular RISK_SCORE a partir de un archivo JSON o YAML.

Uso:
    python scripts/risk_score_calculator.py --file risk_input.json
    python scripts/risk_score_calculator.py --file risk_input.yaml

Formato esperado (claves con escala 1..5):
{
  "impacto_usuario": 4,
  "complejidad_tecnica": 3,
  "superficie_seguridad": 2,
  "reversibilidad": 4,
  "dependencias_externas": 2,
  "madurez_pruebas": 3
}

El peso de cada dimensión proviene de `PLAYBOOK_RISK_SCORE_TEMPLATE.md`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - yaml es opcional
    yaml = None  # type: ignore

WEIGHTS = {
    "impacto_usuario": 0.30,
    "complejidad_tecnica": 0.20,
    "superficie_seguridad": 0.15,
    "reversibilidad": 0.15,
    "dependencias_externas": 0.10,
    "madurez_pruebas": 0.10,
}


def load_data(path: Path) -> Dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML no instalado. Instala 'pyyaml' para usar archivos YAML.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):  # pragma: no cover - validación defensiva
        raise ValueError("El archivo debe contener un objeto JSON/YAML de nivel superior")
    return data  # type: ignore


def compute_score(values: Dict[str, int]) -> float:
    total = 0.0
    missing = []
    for key, weight in WEIGHTS.items():
        if key not in values:
            missing.append(key)
            continue
        scale = values[key]
        if not isinstance(scale, (int, float)):
            raise TypeError(f"Valor no numérico para {key}: {scale}")
        if scale < 1 or scale > 5:
            raise ValueError(f"Escala fuera de rango (1..5) en {key}: {scale}")
        total += scale * weight
    if missing:
        raise ValueError(f"Faltan dimensiones obligatorias: {', '.join(missing)}")
    return round(total, 2)


def classify(score: float) -> str:
    if score >= 4.0:
        return "ALTO (Modo C sugerido)"
    if score >= 2.5:
        return "MEDIO (Modo B sugerido)"
    return "BAJO (Modo A sugerido)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculadora de risk score Playbook")
    parser.add_argument("--file", required=True, help="Ruta a archivo JSON/YAML con las dimensiones")
    args = parser.parse_args()
    path = Path(args.file)
    try:
        data = load_data(path)
        score = compute_score(data)
        print(json.dumps({
            "score": score,
            "clasificacion": classify(score),
            "modo_sugerido": classify(score).split()[1].strip("()")[:1],
            "detalles": {
                k: {
                    "valor": data[k], 
                    "peso": WEIGHTS[k], 
                    "contribucion": round(data[k]*WEIGHTS[k], 2)
                } 
                for k in WEIGHTS
            }
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:  # pragma: no cover - CLI path
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
