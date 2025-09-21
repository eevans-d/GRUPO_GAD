Title: chore: guardrails env fixes (ignore .env.production, env.example, settings fix)

Description:
This PR groups several low-risk changes that improve developer safety and make the repository easier to run locally:

- Add `.env.example` with placeholders and ensure `.env.production` is ignored.
- Annotate `env_files` in `config/settings.py` to satisfy Pydantic (ClassVar).
- Add `src/core/auth.py` shim to restore previously expected imports used by the dashboard router.
- Add `scripts/rotate_secrets.sh` (documentation) and `scripts/prepare_repo_backup.sh` + `scripts/perform_history_cleanup.sh` to help rotating secrets and cleaning the Git history safely.

Testing / QA:

1. Run tests locally with virtualenv active:

   ```bash
   PYTHONPATH=. .venv/bin/pytest -q
   ```

2. Validate that the app starts (dev) after copying `.env.example` to `.env` and filling values.

3. Review `docs/GUARDRAILS_REGISTRY.md` for the recorded steps and notes.

Checklist:
- [x] Add `.env.example` and ignore `.env.production`
- [x] Patch `config/settings.py` (ClassVar)
- [x] Add `src/core/auth.py` shim
- [x] Add helper scripts for secrets rotation and history cleanup (documental)

Notes:
- This PR intentionally does not remove secrets from git history; that is a separate destructive operation and must be coordinated.
