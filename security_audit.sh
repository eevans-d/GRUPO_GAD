#!/bin/bash
set -e

echo "🔍 Security and Health Audit"
echo "============================"

EXIT_CODE=0

echo -n "Checking environment variables... "
poetry run python - << 'PYCODE' || EXIT_CODE=1
import os, sys
required = ['SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET_KEY']
missing = [v for v in required if not os.getenv(v)]
if missing:
    print('❌ Missing:', ', '.join(missing))
    sys.exit(1)
print('✅')
PYCODE

echo -n "Checking Poetry configuration... "
if poetry check &>/dev/null; then echo "✅"; else echo "❌"; EXIT_CODE=1; fi

echo -n "Checking for vulnerabilities... "
poetry export -f requirements.txt --output /tmp/req.txt --without-hashes >/dev/null 2>&1 || true
if poetry run pip-audit -r /tmp/req.txt -f json -o audit_report.json >/dev/null 2>&1; then echo "✅"; else echo "⚠️ Review audit_report.json"; fi

echo -n "Checking code security... "
if poetry run bandit -r src/ -f json -o bandit_report.json >/dev/null 2>&1; then echo "✅"; else echo "⚠️ Check bandit_report.json"; fi

echo -n "Testing basic imports... "
if poetry run python -c "from src.app.core.config import settings" >/dev/null 2>&1; then echo "✅"; else echo "❌"; EXIT_CODE=1; fi

exit $EXIT_CODE
