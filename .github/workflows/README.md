---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# .github/workflows/

GitHub Actions CI-Pipelines für das OpenDisruption-Repository. Laufen bei Push auf `main` und bei Pull Requests.

## Workflows

### ci.yml — Haupt-CI

Läuft bei jedem Push auf `main` und bei Pull Requests.

Schritte:
1. Python 3.11 einrichten
2. `pytest tests/unit -q` — kirobi_core Unit-Tests
3. `python -m kirobi_core doctor` — Offline-Systemcheck
4. `docker compose config --quiet` — Compose-Validierung
5. `make integration-test` — Vollständiger Integrations-Check (Shell-Lint, FastAPI py_compile, PWA-Manifest)

### install-test.yml — Installer-Validierung

Läuft nur bei Änderungen an `install.sh`, `infra/scripts/`, `config/templates/` oder dem Workflow selbst.

Jobs:
- `shellcheck` — Shell-Lint für `install.sh` und alle `infra/scripts/*.sh`
- `installer-help` — `--version` und `--help` smoke test
- `installer-dry-run` — Dry-Run-Matrix über alle Profile: `auto`, `minimal`, `cpu`, `nvidia`, `amd`
- `detect-and-validate` — System-Erkennung und `.env`-Validierung
- `backup-update-dry` — `backup.sh` und `update.sh` im Dry-Run-Modus

## Lokale Entsprechung

```bash
make integration-test          # CI-äquivalenter Check lokal
python -m pytest tests/unit -q # Unit-Tests
docker compose config --quiet  # Compose-Validierung
```
