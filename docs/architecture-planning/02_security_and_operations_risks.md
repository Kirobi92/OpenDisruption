# 02 — Security & Operations Risks

**Datum:** 2026-05-26 · **Quellen:** Security-Explore-Agent + direkte Reads
**Regel:** Alle Secret-Funde maskiert per `SECRET_FOUND(type=..., file=..., line=..., value=MASKED)`. **Niemals Klartext.**

## A) Secret-Inventar (alle maskiert)

```
SECRET_FOUND(type=mysql_root_password,    file=services/webshop/docker-compose.yml,            line=9,     value=MASKED)
SECRET_FOUND(type=mysql_user_password,    file=services/webshop/docker-compose.yml,            line=12,    value=MASKED)
SECRET_FOUND(type=mysql_user_password,    file=services/webshop/docker-compose.yml,            line=30,    value=MASKED)
SECRET_FOUND(type=db_url_with_password,   file=services/inventory/partdb/docker-compose.yml,   line=14,    value=MASKED)
SECRET_FOUND(type=mysql_user_password,    file=services/inventory/partdb/docker-compose.yml,   line=42,    value=MASKED)
SECRET_FOUND(type=mysql_root_password,    file=services/inventory/partdb/docker-compose.yml,   line=43,    value=MASKED)
SECRET_FOUND(type=default_admin_password, file=services/inventory/partdb/docker-compose.yml,   line=19,    value=MASKED)  # "changeme_partdb_admin"
SECRET_FOUND(type=inventree_user_password,file=services/3d-druck-pipeline/.env,                line=3,     value=MASKED)
SECRET_FOUND(type=inventree_api_token,    file=services/3d-druck-pipeline/.env,                line=4,     value=MASKED)
SECRET_FOUND(type=telegram_bot_token,     file=services/3d-druck-pipeline/.env,                line=14,    value=MASKED)
SECRET_FOUND(type=restic_repo_password,   file=.backup.env,                                    line=1,     value=MASKED)
SECRET_FOUND(type=woocommerce_consumer_key,    file=AGENT-ACTIVITY-LOG.md,                    line=69,    value=MASKED)
SECRET_FOUND(type=woocommerce_consumer_secret, file=AGENT-ACTIVITY-LOG.md,                    line=69,    value=MASKED)
SECRET_FOUND(type=inventree_api_token,    file=AGENT-ACTIVITY-LOG.md,                          line=67,    value=MASKED)
SECRET_FOUND(type=admin_password,         file=AGENT-ACTIVITY-LOG.md,                          line=52,    value=MASKED)  # InvenTree/WP admin
SECRET_FOUND(type=admin_password,         file=AGENT-ACTIVITY-LOG.md,                          line=67-68, value=MASKED)
```

**Summe:** ≥16 Klartext-Secrets in 5 Dateien.
**Anmerkung:** `KIROBI_OS_AUDIT.md` (68 KB / 1840 Zeilen) wurde aus Vorsicht nicht zeilenweise gegrept (Re-Exposure-Risiko); muss in Phase A separat hinter geschlossenen Türen geprüft werden.

## B) Risikomatrix

| ID | Risiko | Fundstelle | Evidenz | Auswirkung | Wahrscheinlichkeit | Kritikalität | Sofortmaßnahme | Zielmaßnahme | Aufwand | Empfehlung |
|---|---|---|---|---|---|---|---|---|---|---|
| SEC-001 | MySQL Root-PW Klartext | `services/webshop/docker-compose.yml:9` | SECRET_FOUND | DB-Übernahme Webshop | HOCH | **CRITICAL** | PW rotieren, Compose auf `${MYSQL_ROOT_PASSWORD}` umstellen | Secrets-File `.env` außerhalb Repo, chmod 600 | S | rotieren+abstrahieren |
| SEC-002 | MySQL User-PW Klartext (2x) | `services/webshop/docker-compose.yml:12,30` | SECRET_FOUND | DB-/WP-Zugriff | HOCH | **CRITICAL** | dito | dito | S | dito |
| SEC-003 | Part-DB DB-URL mit PW | `services/inventory/partdb/docker-compose.yml:14,42,43` | SECRET_FOUND | DB-Übernahme Part-DB | MITTEL | **HIGH** | PW rotieren, `${DATABASE_URL}` | Secrets-File | S | rotieren+abstrahieren |
| SEC-004 | Default-Admin-PW Part-DB | `services/inventory/partdb/docker-compose.yml:19` | `changeme_partdb_admin` | Admin-Übernahme bei Start | MITTEL | **HIGH** | PW im Compose entfernen, bei First-Run interaktiv | env-Variable | XS | ersetzen |
| SEC-005 | InvenTree-User-PW im Repo | `services/3d-druck-pipeline/.env:3` | SECRET_FOUND | ERP-Übernahme | HOCH | **CRITICAL** | PW sofort ändern + 2FA aktivieren | .env aus Repo entfernen, `.gitignore` | XS | sofort |
| SEC-006 | InvenTree-API-Token im Repo | `services/3d-druck-pipeline/.env:4` + `AGENT-ACTIVITY-LOG.md:67` | SECRET_FOUND | ERP-API-Zugriff | HOCH | **CRITICAL** | Token revoken + neu | Token-Manager | XS | sofort |
| SEC-007 | Telegram-Bot-Token im Repo | `services/3d-druck-pipeline/.env:14` | SECRET_FOUND | Bot-Hijack | HOCH | **CRITICAL** | Token via @BotFather revoken | Secrets-File | XS | sofort |
| SEC-008 | WooCommerce Consumer-Key+Secret in Logdatei | `AGENT-ACTIVITY-LOG.md:69` | SECRET_FOUND | Shop-API-Übernahme | HOCH | **CRITICAL** | Keys in WC Admin regenerieren | Audit-Logs nie ins Repo | S | sofort |
| SEC-009 | Restic-Repo-PW im Repo | `.backup.env:1` | SECRET_FOUND | Backup-Decryption | MITTEL | **HIGH** | PW rotieren + neues Restic-Repo, alten Repo verschlüsselt archivieren | Secrets-File außerhalb Repo, `chmod 600` | S | rotieren |
| SEC-010 | Audit-Datei enthält Klartext-Credentials | `AGENT-ACTIVITY-LOG.md` (mehrfach), evtl. `KIROBI_OS_AUDIT.md` | s.o. | persistente Leaks; einmal getrackt schwer zu entfernen | HOCH | **CRITICAL** | Datei aus Repo entfernen, archivieren in `/Datenspeicher/OpenDisruption-Data/secrets/quarantine/` (chmod 600) | Policy: Audits enthalten nur maskierte Werte | S | quarantänieren |
| SEC-011 | Live-MySQL-Volume im Repo + `root:root` | `data/webshop-mysql/` (101 MB) | `ls -la data` | DB-Korruption, Permission-Probleme | HOCH | **CRITICAL** | Webshop stoppen → DB-Dump → Volume nach `/Datenspeicher/OpenDisruption-Data/luki?/labs/webshop/mysql/` migrieren | Named Docker-Volume; `data/` aus Repo löschen | M | migrieren |
| SEC-012 | Live-WordPress-Volume im Repo | `data/webshop-wordpress/` (174 MB) | dito | dito | HOCH | **CRITICAL** | dito | dito | M | migrieren |
| SEC-013 | 10 GB Qdrant-Index im Repo (DUPLICATE) | `services/qdrant/` | du -sh | Repo-Bloat, Konflikt mit aktivem Qdrant in `Systembetrieb-und-Indizes/qdrant/` | MITTEL | **HIGH** | Verifikation, ob aktiv. Wenn nicht → in `/Datenspeicher/OpenDisruption-Data/archive/qdrant-legacy/` verschieben | aktiver Qdrant einzig in Systembetrieb mit Volume | M | konsolidieren |
| SEC-014 | 6.9 GB Open-WebUI-Runtime im Repo, kein Compose | `services/open-webui/` | du, fehlende compose.yml | nicht reproduzierbar; `.webui_secret_key` exponiert | HOCH | **HIGH** | Service nach klarer Domäne (LABS) verschieben, Compose nachziehen oder Service stilllegen | Labs-Stack mit Compose+Volume | M | rekonstruieren oder stilllegen |
| SEC-015 | Caddy auf `0.0.0.0:80` ohne HTTPS, ohne globale Auth | `services/caddy/Caddyfile` + `docker-compose.yml` | reverse_proxy lines | MITM im LAN; offene Routen zu Admin-UIs | MITTEL | **HIGH** | mindestens `basicauth` für `/mission`, `/flowise`, `/webui`, `/3dbar`, `/luki`; Caddy nur an Tailscale-IP binden | `auto_https on` mit lokaler CA oder LE-DNS-01; alle Admin-Routen hinter Auth | M | härten |
| SEC-016 | Kirobi-PWA bindet `0.0.0.0:4300` | `kirobi-pwa.service:14` | HOST=0.0.0.0 | LAN-Exposition Privat-PWA | MITTEL | **HIGH** | `HOST=127.0.0.1`; Zugriff via Caddy/Tailscale | nur Loopback + Reverse Proxy | XS | umstellen |
| SEC-017 | Mehrere Service-Compose binden `0.0.0.0:*` | webshop:9001/3307, partdb:8200, homebox:8201, website:8080, caddy:80 | compose | Direkter Bypass des Reverse-Proxy | MITTEL | **MEDIUM** | Bindings auf `127.0.0.1:` oder Docker-Internal-Netz; ausschließlich Caddy nach außen | Docker-Netzwerkmodell mit `internal: true` | M | konsolidieren |
| SEC-018 | `data/` root-owned (Mount-Permission-Drift) | `data/` (root:root) | ls -la | Container-Restart-Failure, manuelle Reparatur nötig | MITTEL | **MEDIUM** | UID/GID-Plan dokumentieren, `chown` korrekt setzen | Volumes statt Bind-Mounts | S | bereinigen |
| SEC-019 | Compose-Stacks ohne Healthcheck/Restart | webshop, hermes-agent, caddy, website, homebox | compose-Reviews | Zombie-Container | MITTEL | **MEDIUM** | minimale Healthchecks ergänzen (mysqladmin, curl /health) | Healthcheck-Pflicht | S | ergänzen |
| SEC-020 | Compose ohne versionierte Bilder (`:latest`) | webshop (`wordpress:latest`, `mysql:8.0`), inventory (`:latest`) | compose | unvorhergesehene Upgrades, Supply-Chain | MITTEL | **MEDIUM** | Tags pinnen + Digest | Renovate/Dependabot | S | pinnen |
| SEC-021 | Audit-/Logfiles im Tree | `logs/backup.log`, `services/flowise/logs/`, `hermes-agent/logs/` | ls | sensible Operationen logged | NIEDRIG | **MEDIUM** | nach `/Datenspeicher/OpenDisruption-Data/shared/logs/` migrieren | zentrales Log-Verzeichnis + Rotation | S | umlagern |
| SEC-022 | SQLite-DBs im Repo | `services/flowise/data/database.sqlite`, `services/open-webui/data/webui.db` | find | Personen-/Konversationsdaten persistent | HOCH | **HIGH** | DBs aus Repo entfernen, in Daten-Verzeichnis migrieren | Volume-only | S | migrieren |
| SEC-023 | `node_modules/`, `.opencode/`, `__pycache__/` im Tree | Root + diverse | du, find | Bloat, Vuln-Scans erschwert | NIEDRIG | **MEDIUM** | löschen + (sobald Git existiert) `.gitignore` ergänzen | Build-Artefakte nie versionieren | XS | aufräumen |
| SEC-024 | `geplante_ERP-eNVenta…pdf` doppelt (Root + `Nutzeisen Prozessanalyse/`) | ls | identische SHA wahrscheinlich | Verwirrung, Drift | NIEDRIG | **LOW** | Root-Kopie löschen | LUKI-MVP-Quelle nur in `products/luki/source-docs/` | XS | dedupe |
| SEC-025 | Kein Git-Repo + keine Branch-Strategie | git rev-parse fail | – | kein Rollback, kein Audit-Trail | HOCH | **HIGH** | externer Snapshot vor Phase A; danach Git init in Ziel-Repo-Skelett | Monorepo mit Git, Pre-Commit-Hooks (TruffleHog/GitGuardian) | M | aufbauen |
| SEC-026 | Backup-Restore-Test nicht dokumentiert | – | Abwesenheit | Backup unzuverlässig | MITTEL | **HIGH** | Restic-Restore-Probelauf in Sandkasten | Wöchentlicher automatisierter Restore-Test | M | aufbauen |
| SEC-027 | Parallel-Codebase `/Datenspeicher/home-migration/OpenDisruption` (Symlink `~/OpenDisruption`) | ls -la | – | Drift, doppelte Wahrheit | MITTEL | **MEDIUM** | Inhalts-Diff (Phase B), dann ARCHIVE | nur ein Wahrheits-Tree | S | konsolidieren |
| SEC-028 | Hermes-Agent ~7.2 GB im Tree (vermutlich `.venv` + Caches) | du | – | Repo-Bloat, schwer zu sichern | NIEDRIG | **MEDIUM** | `.venv`, `__pycache__`, `image_cache/`, `audio_cache/` identifizieren und auslagern | klare Trennung Source vs. Runtime | M | aufräumen |

## C) Top-5 kritische Risiken

1. **SEC-001/002** — Webshop-MySQL-Passwörter im Repo + Live-Volume `root:root` im Repo (SEC-011/012). Doppelt kritisch: Code + Daten gleichzeitig kompromittierbar.
2. **SEC-005/006/007** — InvenTree-User-PW, InvenTree-API-Token und Telegram-Bot-Token im selben `.env` (3d-druck-pipeline).
3. **SEC-008/010** — `AGENT-ACTIVITY-LOG.md` und vermutlich `KIROBI_OS_AUDIT.md` mit operativen Klartext-Credentials.
4. **SEC-015/016/017** — Netzwerk-Exposition: Caddy ohne HTTPS/Auth, Kirobi-PWA und mehrere Service-Compose auf `0.0.0.0`.
5. **SEC-025/026** — Kein Git + kein dokumentierter Restore-Test = kein zuverlässiges Rollback bei Fehlern.

## D) Quick-Wins (Aufwand XS/S, Kritikalität HIGH+)

| ID | Maßnahme | Aufwand |
|---|---|---|
| SEC-005, SEC-006, SEC-007 | InvenTree-PW + Token + Telegram-Token sofort rotieren | XS |
| SEC-008 | WooCommerce API-Keys regenerieren | XS |
| SEC-009 | Restic-Repo-PW rotieren + neues Repo | S |
| SEC-016 | Kirobi-PWA auf `HOST=127.0.0.1` | XS |
| SEC-010 | `AGENT-ACTIVITY-LOG.md` aus Tree in `…OpenDisruption-Data/secrets/quarantine/` (chmod 600) verschieben | S |
| SEC-024 | Root-PDF-Duplikat löschen | XS |
| SEC-023 | `node_modules/`, `.opencode/` aufräumen | XS |
| SEC-004 | Part-DB Default-Admin-PW im Compose entfernen | XS |

## E) Hinweis zur Reihenfolge

- Quick-Wins werden in **Phase A — Safety Baseline** (Phasenplan A) gebündelt.
- Volumen-Migrationen (SEC-011/012/013/014/022) gehören in **Phase C — Shared Infra Normalisierung**, weil sie Stack-Downtime erfordern.
- Git-Init + Pre-Commit-Hooks (SEC-025) gehören in **Phase B — Repository Skeleton**.
