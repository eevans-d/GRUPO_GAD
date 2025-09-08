#!/usr/bin/env python3
import json
import pathlib
import sys
import re
from typing import Set, List


def load_manifest() -> dict:
    manifest_path = pathlib.Path("docs/manifest.json")
    if not manifest_path.exists():
        print("⚠️ docs/manifest.json no encontrado — asumiendo allowlist vacía")
        return {}
    try:
        return json.loads(manifest_path.read_text())
    except Exception as e:
        print(f"❌ Error leyendo docs/manifest.json: {e}")
        return {}


def check_npm() -> bool:
    pkg_path = pathlib.Path("package.json")
    if not pkg_path.exists():
        # nothing to check
        return True

    manifest = load_manifest()
    try:
        pkg = json.loads(pkg_path.read_text())
    except Exception as e:
        print(f"❌ Error leyendo package.json: {e}")
        return False

    runtime_allow: Set[str] = set(
        manifest.get("dependencies", {}).get("allowlist", {}).get("npm", [])
    )
    dev_allow: Set[str] = set(
        manifest.get("dependencies", {}).get("dev_allowlist", {}).get("npm", [])
    )

    runtime_used: Set[str] = set(pkg.get("dependencies", {}).keys())
    dev_used: Set[str] = set(pkg.get("devDependencies", {}).keys())

    bad_runtime = sorted(list(runtime_used - runtime_allow))
    bad_dev = sorted(list(dev_used - dev_allow))

    if bad_runtime or bad_dev:
        print("❌ Dependencias npm fuera de allowlist:")
        if bad_runtime:
            print(f"  Runtime: {bad_runtime}")
        if bad_dev:
            print(f"  Dev: {bad_dev}")
        return False

    print("✓ Allowlist npm OK")
    return True


def parse_requirements_lines(lines: List[str]) -> List[str]:
    used = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=~!]", line)[0].split("[")[0].strip().lower()
        if name:
            used.append(name)
    return used


def check_python() -> bool:
    manifest = load_manifest()
    allow = set(
        p.lower()
        for p in manifest.get("dependencies", {}).get("allowlist", {}).get("pypi", [])
    )
    dev_allow = set(
        p.lower()
        for p in manifest.get("dependencies", {})
        .get("dev_allowlist", {})
        .get("pypi", [])
    )

    # Prefer pyproject.toml (poetry) if present
    pyproject = pathlib.Path("pyproject.toml")
    used = []
    if pyproject.exists():
        try:
            # extract simple dependency names from [tool.poetry.dependencies]
            # and group.dev
            content = pyproject.read_text()
            dep_section = False
            for line in content.splitlines():
                stripped_line = line.strip()
                if stripped_line == "[tool.poetry.dependencies]":
                    dep_section = True
                    continue
                if stripped_line.startswith("[tool.poetry.") and dep_section:
                    # end of dependencies section
                    dep_section = False
                if dep_section and stripped_line and not stripped_line.startswith("#"):
                    name = stripped_line.split("=")[0].strip()
                    if name and name != "python":
                        used.append(name.lower())

            # also check dev group
            dev_marker = "[tool.poetry.group.dev.dependencies]"
            if dev_marker in content:
                in_dev = False
                for line in content.splitlines():
                    stripped_line = line.strip()
                    if stripped_line == dev_marker:
                        in_dev = True
                        continue
                    if in_dev and stripped_line.startswith("["):
                        in_dev = False
                    if in_dev and stripped_line and not stripped_line.startswith("#"):
                        name = stripped_line.split("=")[0].strip()
                        if name:
                            used.append(name.lower())
        except Exception:
            # fallback to checking pyservice/requirements.txt
            used = []

    if not used:
        req_file = pathlib.Path("pyservice/requirements.txt")
        if req_file.exists():
            used = parse_requirements_lines(req_file.read_text().splitlines())
        else:
            # try root requirements.txt
            root_req = pathlib.Path("requirements.txt")
            if root_req.exists():
                used = parse_requirements_lines(root_req.read_text().splitlines())

    bad = [p for p in used if p not in allow and p not in dev_allow]
    if bad:
        print(f"❌ PyPI fuera de allowlist: {bad}")
        return False

    print("✓ Allowlist PyPI OK")
    return True


if __name__ == "__main__":
    npm_ok = check_npm()
    py_ok = check_python()
    sys.exit(0 if (npm_ok and py_ok) else 1)