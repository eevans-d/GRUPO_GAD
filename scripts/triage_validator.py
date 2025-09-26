#!/usr/bin/env python3
"""Valida el archivo triage JSON asegurando consistencia previa a un release.

Checks:
  - Estructura esperada: alpha/beta/gamma/metadata.
  - Cada item tiene id, titulo, criterio, estado.
  - Sin items Alpha con estado que no sea 'resuelto' si se usa bandera --require-alpha-resuelto.
  - Detecta duplicados de id entre categorías.
Uso:
  python scripts/triage_validator.py --file docs/triage_example.json
  python scripts/triage_validator.py --file docs/triage_example.json --require-alpha-resuelto
Exit codes:
  0 = válido
  1 = inválido
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set

REQUIRED_KEYS = {"alpha", "beta", "gamma", "metadata"}
ITEM_KEYS = {"id", "titulo", "criterio", "estado"}
ALLOWED_ESTADOS = {"pendiente", "en progreso", "diferido", "resuelto"}


def load(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def validate(data: Dict, require_alpha_resuelto: bool = False) -> List[str]:
    errors: List[str] = []
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"Faltan claves: {', '.join(sorted(missing))}")
        return errors
    ids: Set[str] = set()
    duplicate_ids: Set[str] = set()
    for bucket in ["alpha", "beta", "gamma"]:
        if not isinstance(data[bucket], list):
            errors.append(f"'{bucket}' debe ser lista")
            continue
        for idx, item in enumerate(data[bucket]):
            if not isinstance(item, dict):
                errors.append(f"Item no dict en {bucket}[{idx}]")
                continue
            missing_item = ITEM_KEYS - set(item.keys())
            if missing_item:
                errors.append(f"Faltan campos {missing_item} en {bucket}[{idx}]")
            estado = item.get("estado")
            if estado not in ALLOWED_ESTADOS:
                errors.append(f"Estado inválido '{estado}' en {bucket}[{idx}]")
            item_id = item.get("id")
            if item_id:
                if item_id in ids:
                    duplicate_ids.add(item_id)
                ids.add(item_id)
            if bucket == "alpha" and require_alpha_resuelto:
                if item.get("estado") != "resuelto":
                    errors.append(f"Alpha {item.get('id')} no está resuelto (estado={item.get('estado')})")
    if duplicate_ids:
        errors.append(f"IDs duplicados: {', '.join(sorted(duplicate_ids))}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validador de triage final")
    ap.add_argument("--file", required=True)
    ap.add_argument("--require-alpha-resuelto", action="store_true", help="Falla si algún Alpha no está resuelto")
    args = ap.parse_args()
    try:
        data = load(Path(args.file))
        errs = validate(data, args.require_alpha_resuelto)
        if errs:
            print("INVALIDO:")
            for e in errs:
                print(f" - {e}")
            return 1
        print("VALIDO")
        return 0
    except Exception as e:  # pragma: no cover
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
