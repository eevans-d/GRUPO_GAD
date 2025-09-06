#!/usr/bin/env python3
import json, pathlib, sys, re

def check_npm():
    if not pathlib.Path("package.json").exists():
        return True
    
    manifest = json.loads(pathlib.Path("docs/manifest.json").read_text())
    pkg = json.loads(pathlib.Path("package.json").read_text())
    
    runtime_allow = set(manifest.get("dependencies", {}).get("allowlist", {}).get("npm", []))
    dev_allow = set(manifest.get("dependencies", {}).get("dev_allowlist", {}).get("npm", []))
    
    runtime_used = set(pkg.get("dependencies", {}).keys())
    dev_used = set(pkg.get("devDependencies", {}).keys())
    
    bad_runtime = runtime_used - runtime_allow
    bad_dev = dev_used - dev_allow
    
    if bad_runtime or bad_dev:
        print(f"❌ Dependencias fuera de allowlist:")
        if bad_runtime: print(f"  Runtime: {list(bad_runtime)}")
        if bad_dev: print(f"  Dev: {list(bad_dev)}")
        return False
    
    print("✓ Allowlist npm OK")
    return True

def check_python():
    req_file = pathlib.Path("pyservice/requirements.txt")
    if not req_file.exists():
        return True
        
    manifest = json.loads(pathlib.Path("docs/manifest.json").read_text())
    allow = set(p.lower() for p in manifest.get("dependencies", {}).get("allowlist", {}).get("pypi", []))
    
    used = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name = re.split(r"[<>=~!]", line)[0].split("[")[0].strip().lower()
            if name: used.append(name)
    
    bad = [p for p in used if p not in allow]
    if bad:
        print(f"❌ PyPI fuera de allowlist: {bad}")
        return False
    
    print("✓ Allowlist PyPI OK")
    return True

if __name__ == "__main__":
    npm_ok = check_npm()
    py_ok = check_python()
    sys.exit(0 if (npm_ok and py_ok) else 1)
