# Runbook — Phase 6: install.sh + Doku-Polish

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/MULTI-AGENT-ARCHITECTURE.md` §6 (Phasen-Zusammenfassung)
**Milestones:** `keycodi/MILESTONES.md` § Phase 6

---

## Vorbedingungen

- Phase 4 ist `🟢 done`. Phase 5 ist `🟢 done` **oder** offiziell übersprungen (Sven Option B).

## Schritte

### 1. `install.sh`

Repo-lokales Skript (`./install.sh`), das `infra/scripts/bootstrap.sh` umhüllt. Das ist die gewählte Option: komfortabel (ein lokaler Befehl) und sicher (kein Remote-Pipe, Dry-Run als Default).

- Default-Modus: `--dry-run`. Skript zeigt nur, was es täte, führt nichts aus.
- `--apply` ist explizit erforderlich, um zu installieren.
- Niemals `curl … | bash` empfehlen.
- Falls Sven später explizit ein gehostetes Skript wünscht: Checksum-Verifizierung (`sha256sum -c install.sh.sha256`) wird Pflicht; dieses ist ein separater PR und braucht ADR.

### 2. Phasen-Integration

`install.sh` ruft `bootstrap.sh` plus optionale Subkommandos:

```
./install.sh --dry-run                 # default
./install.sh --apply                   # full install
./install.sh --apply --profile kidi    # plus ContextDB
./install.sh --apply --profile agents  # plus agent skeletons
./install.sh --apply --profile telegram # only after Sven sign-off
./install.sh --apply --profile webui    # Caddy edge for LAN/Tailscale access
```

### 3. Sicherheits-Checks im Installer

- Prüft `git status --porcelain` — Abbruch bei dirty tree, außer mit `--allow-dirty`.
- Prüft `.env` Existenz; wenn fehlend, kopiert `.env.example` und warnt zu Token-Befüllung.
- Prüft `KIROBI_BIND_HOST`; wenn `0.0.0.0`, fragt explizit nach.
- Prüft `KIROBI_PROXY_BIND_HOST`; wenn nicht `0.0.0.0` und `KIROBI_ACCESS_MODE=lan-tailscale`, warnt es, dass LAN/Tailscale nicht erreichbar ist.
- Prüft bei `--profile telegram`, dass alle `KIROBI_TELEGRAM_*_TOKEN_FILE`- und `KIROBI_TELEGRAM_CHANNEL_ID_FILE`-Pfade existieren.
- Schreibt eine Pre-Install-Snapshot der wichtigsten Dirs (`canon/`, `experiences/`) gemäß bestehender Backup-Konvention.

### 4. Docs

- `README.md`: Abschnitt „Installation (lokal)" mit Verweis auf `install.sh --dry-run`.
- `BENUTZERHANDBUCH.md`: Kapitel „Erste Schritte mit KEYBRODI/KeyCodi".
- `QUICK-REFERENCE.md`: Befehlsliste für die neuen Phasen-Targets (`make test-kidi`, `make agent-*`, `make obsidian-*`).
- `CHANGELOG.md`: Eintrag für das Roll-up der Phasen 0–6.
- `docs/agent/*.md`: Update auf den tatsächlichen Stand.

### 5. Tests

- `tests/integration/test_install_dry_run.py` — `./install.sh --dry-run` läuft fehlerfrei in einem frischen Clone (CI-Job).
- `tests/integration/test_no_secrets_in_repo.py` — Grep auf `*token*`, `*secret*`, `*key*`-Pattern in tracked files.

### 6. Repo-Polish

- Alle `🟡 IN PROGRESS`-Marker auf `🟢 done` setzen.
- `keycodi/MILESTONES.md` Status-Zeile final.
- `keycodi/learnings/` und `keycodi/decisions/` Indizes aktualisiert.
- Vault-MOCs final regenerieren.

## Definition of Done

`./install.sh --dry-run` grün auf frischem Clone. Doku konsistent. CI grün. CHANGELOG-Eintrag vorhanden.

## Übergang

Nach `🟢 done`: KeyCodi triggert Handoff-Prozess, falls noch nicht erfolgt (`HANDOFF-TO-KEYBRODI.md`). Roll-up-PR mit allen Phasen wird gemerged. Roadmap-Status: 🟢 done.
