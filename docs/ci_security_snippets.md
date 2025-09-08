# CI security snippets

Ejemplos recomendados para GitHub Actions: exportar dependencias y ejecutar `pip-audit`, `gitleaks` y `pre-commit`.

Job `security` (ejemplo):

```yaml
name: Security checks
on:
  workflow_dispatch: {}

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: |
          python -m pip install --upgrade pip
          pip install poetry
      - name: Export requirements
        run: poetry export -f requirements.txt -o requirements.txt --without-hashes
      - name: Run pip-audit
        run: pip-audit -r requirements.txt || true
      - name: Run gitleaks (if installed)
        run: gitleaks detect --source . --report-path gitleaks-report.json || true
      - name: Run pre-commit
        run: |
          pip install pre-commit
          pre-commit run --all-files || true
```

Job `test` (snippet con secrets inyectados):

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: pytest -q
```

Ajustar según la política de la organización (por ejemplo, fallar el job security en función de severidad).
