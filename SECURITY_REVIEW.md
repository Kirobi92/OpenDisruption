---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
classification: WORKSPACE
status: ACTIVE
---

# SECURITY_REVIEW.md — OpenDisruption

Verdichtetes Sicherheitsaudit, basierend auf `scope-security-quality` (explore agent, 249 s)
und direkter Code-Inspektion.

## Score: 35 / 100 (F)

## 1. Top-3 KRITISCH (heute beheben)

### CRIT-1 — Network Exposure (5 Services auf `0.0.0.0`)
**Pfad:** `services/{api,auth,model-routing,media-processing,video-generation}/main.py` Endezeile.
**Verletzung:** CLAUDE.md §2 (Local-First), AGENTS.md (`KIROBI_BIND_HOST=127.0.0.1`).
**Fix:**
```diff
- uvicorn.run(app, host="0.0.0.0", port=PORT)
+ uvicorn.run(app, host=os.getenv("BIND_HOST", "127.0.0.1"), port=PORT)
```
*Anmerkung:* Im Compose ist Port-Binding bereits via `${KIROBI_BIND_HOST:-127.0.0.1}:port:port`
auf 127.0.0.1 beschränkt — uvicorn-Bind ist „nur" defense-in-depth. Trotzdem sofort fixen.

### CRIT-2 — Unauthenticated Endpoints
**Pfade:**
- `services/model-routing/main.py` — alle Routen ohne `Depends(get_current_user)`
- `services/personal-agents/app/main.py` — alle `/{subject}/*` ohne Auth
- `services/nutzi/` — alle Endpoints offen

**Reproduktion:**
```bash
curl http://127.0.0.1:8009/models           # 200 OK ohne Token
curl http://127.0.0.1:8017/sineo/profile    # 200 OK ohne Token
```

**Fix:** Shared dependency in `kirobi_core/auth_deps.py` einführen, in jedem Service via
`Depends(verify_jwt)` (Token gegen `auth:8002/me` validieren).

### CRIT-3 — CORS-Wildcard ohne Credentials-Restriction
**Pfade:**
- `services/model-routing/main.py:109`
- `services/personal-agents/app/main.py`
- `services/nutzi/app/main.py`

**Fix-Pattern (übernehmen aus `services/ingest/main.py:195-221`):**
```python
def _cors_kwargs() -> dict:
    return {
        "allow_origin_regex": r"^https?://(localhost|127\.0\.0\.1|"
                              r"[a-zA-Z0-9-]+\.local|10\.\d+|192\.168|"
                              r"172\.(1[6-9]|2\d|3[01])\.\d+)(:\d+)?$"
    }

app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## 2. HIGH-Findings (Sprint 1)

| # | Befund | Pfad | Fix-Skizze |
|---|---|---|---|
| H-1 | JWT-Secret-Fallback `"CHANGEME-in-production-..."` | `services/auth/main.py:31` | Fail-fast wenn nicht gesetzt |
| H-2 | Postgres-Pass-Fallback `"changeme"` | `services/{api,auth,telegram}/main.py` | Fail-fast oder explizite Pflicht |
| H-3 | Personal-agents schreibt FAMILY_PRIVATE in Datenspeicher ohne Auth-Check | `services/personal-agents/app/main.py` | JWT + `username==subject`-Check |
| H-4 | Telegram-Bot ohne Rate-Limit | `services/telegram/main.py` | SlowAPI middleware (10 req/min/user) |
| H-5 | Backup-Skript nie restore-getestet | `infra/scripts/backup.sh` | Test-Restore in CI |

## 3. MEDIUM-Findings (Sprint 2)

| # | Befund | Pfad | Fix |
|---|---|---|---|
| M-1 | Bare `except Exception:` swallowed errors | `services/ingest/main.py:465,522,599,601,621` | Specific exceptions + log |
| M-2 | Path.suffix ohne volles Sanitizing für Uploads | `services/ingest/main.py:561` | `_safe_upload_path()` mit Whitelist |
| M-3 | Keine Rate Limits | alle Services | SlowAPI als shared middleware |
| M-4 | Sensitive Daten in Logs (DB-URL inkl. Passwort wird teils geloggt) | mehrere | Redact in `kirobi_core/logging_config.py` |
| M-5 | `.env` Datei existiert (RW-Mount-Risk in einigen Volumes) | Repo-Root | Bestätigt im `.gitignore`, dennoch Audit-Trail prüfen |
| M-6 | Keine Memory-Limits | `docker-compose.yml` | `deploy.resources.limits` setzen |
| M-7 | Hermes filesystem-MCP deckt nicht `/Datenspeicher/` ab | `services/hermes-runtime/config/cli-config.yaml` | Pfad ergänzen (siehe TD-031) |

## 4. LOW-Findings

| # | Befund | Empfehlung |
|---|---|---|
| L-1 | Magic numbers (Timeouts, Limits) | Nach `constants.py` |
| L-2 | Tiefe Nesting in `services/api/create_message()` | Guard clauses |
| L-3 | SQL als raw strings | mid-term: SQLAlchemy oder asyncpg-Statements zentralisieren |
| L-4 | Healthcheck nur `{"status": "ok"}` | + `timestamp`, `db_latency_ms`, `version` |
| L-5 | Unused imports vermutet | `vulture` durchlaufen lassen |

## 5. Was bereits gut ist ✅

- `.env` ist im `.gitignore` (`/home/sven/OpenDisruption/.gitignore`)
- `.env.example` enthält keine echten Werte
- Caddy als alleiniger LAN-Edge (per `KIROBI_PROXY_BIND_HOST`)
- SACRED-Zone wird in `services/retrieval/` als HTTP 403 erzwungen, ohne Override
- `services/ingest/` hat sauberes CORS-Pattern (Vorbild)
- `auth` macht User-Bootstrap idempotent + speichert nur Bcrypt-Hashes

## 6. Endpoint-Auth-Matrix

| Service | Health | Daten-Routen | Schreib-Routen |
|---|---|---|---|
| auth | 🟢 öffentlich | 🟢 (`/login` öffentlich; `/me` JWT) | 🟢 (`/users` admin) |
| api | 🟢 öffentlich | 🟡 partial (manche Routen prüfen User, andere nicht) | 🟡 |
| retrieval | 🟢 öffentlich | 🟢 zone-enforced | n/a |
| ingest | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| embeddings | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| model-routing | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| personal-agents | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| nutzi | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| analytics-service | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| image/music/video-generation | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| media-processing | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| voice-processing | 🟢 öffentlich | 🔴 ohne Auth | 🔴 ohne Auth |
| telegram | (intern) | – | Bot prüft `TELEGRAM_ALLOWED_USER_IDS` ✅ |

## 7. Sofort-Patches (Quick Wins)

→ siehe `IMPLEMENTATION_ROADMAP.md` Phase 0/1 für ausführbare Diffs.

## 8. Sicherheits-Pflicht-Checkliste vor jedem Release

- [ ] `pip-audit` über alle `requirements.txt`
- [ ] `npm audit --audit-level=high` über alle `package.json`
- [ ] `docker scan` über alle gebauten Images
- [ ] `bash infra/scripts/validate-env.sh` muss exit `0` liefern
- [ ] Zone-Test (geplant): `pytest tests/integration/test_zones.py`
- [ ] Alle 16 Backend-Services: `curl /health` muss `200` zurückgeben
- [ ] `git log -p .env*` (Sicherstellen kein Secret-Leak)

## 9. Threat-Modell-Zusammenfassung (aus THREAT-MODEL.md, gekürzt)

| Bedrohung | Mitigation heute | Status |
|---|---|---|
| Cloud-Daten-Leak (PII to OpenAI etc.) | Local-First, Ollama default | ✅ |
| Prompt-Injection via RAG | Anti-Halluzination Prompts (personal-agents v2 ✅) | 🟡 |
| Path-Traversal Upload | Whitelist nötig | 🔴 |
| JWT-Replay | Kurze TTL, Token-Rotation | 🟡 |
| LAN-Snooping | 127.0.0.1 + Caddy | 🟡 (5 Services brechen aus) |
| Backup-Diebstahl | `archive/snapshots/` mit `chmod 600` | 🟡 (manuell) |
| Supply-Chain (npm/pip) | Pin + Audit | 🔴 |
