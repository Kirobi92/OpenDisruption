---
zone: WORKSPACE
created_by: github-copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# MVP E2E Proof

Stand: **2026-05-09**

## Ergebnis

OpenDisruption ist jetzt als **lokales, showbares, nutzbares Fullstack-MVP** belegbar:

- lokaler Auth-/Session-Flow funktioniert,
- `WORKSPACE` Upload → Suche → Chat funktioniert,
- `FAMILY_PRIVATE` braucht explizite lokale Freigabe,
- `SACRED` wird hart verweigert,
- Dashboard + Operator-Surface laufen erreichbar auf `localhost:3003`.

## In dieser Umgebung bewiesen

### Repo-/Build-Beweis

```bash
make integration-test
```

Ergebnis: **grün** (`369 passed` + Compose/Script/PWA-Checks).

### Live-Stack-Beweis

Folgende HTTP-Surfaces liefen lokal:

- `http://localhost:8002/health` (`auth`)
- `http://localhost:8003/health` (`api`)
- `http://localhost:8004/health` (`embeddings`)
- `http://localhost:8006/health` (`retrieval`)
- `http://localhost:8007/health` (`ingest`)
- `http://localhost:8010/health` (`analytics`)
- `http://localhost:3002` (`web`)
- `http://localhost:3003` (`dashboard`)

### Kern-Journeys

1. **Auth / Session**
   - `POST /register`
   - `POST /login`
   - `GET /me`
   - `GET /me/permissions`
   - `POST /change-password`
   - `POST /logout`
   - alter Token danach auf `GET /me` → `401`

2. **WORKSPACE**
   - `POST /uploads/text` → `201`
   - `POST /rag/search` mit Workspace-Marker → Treffer vorhanden
   - `POST /conversations`
   - `POST /conversations/{id}/messages` → Assistant-Antwort vorhanden
   - `POST /ingest/text` → Job `completed`

3. **FAMILY_PRIVATE**
   - Upload ohne Freigabe → `403`
   - Upload mit `human_approved=true` + `approval_note` → `201`
   - Suche ohne Freigabe → `403`
   - Suche mit Freigabe → Treffer vorhanden
   - Default-/ALL-Suche leakt den privaten Marker **nicht**

4. **SACRED**
   - `POST /uploads/text` mit `zone=SACRED` → `403`
   - `POST /rag/search` mit `zone=SACRED` → `403`

5. **Dashboard / Operator**
   - `GET /dashboard/activity` → Aktivitätsfeed vorhanden
   - `GET /control/status` → Human-Gate-Zonen + Operator-Summary vorhanden
   - `http://localhost:3003` → Dashboard-HTML erreichbar

## Relevante Fixes aus diesem Proof-Lauf

- Dashboard-Build repariert (`RecentActivity`-Typ ergänzt).
- Auth prüft jetzt Session-Existenz auch bei geschützten Endpunkten; Logout invalidiert die Session tatsächlich.
- API toleriert ältere `supervisor_tasks`-Schemas ohne `last_error`.
- Interne Service-URLs normalisieren Docker-interne Ports korrekt (`embeddings` / `retrieval`).

## Verbleibende Einschränkungen

- **Host-Node fehlt** in dieser Umgebung; `npm run build` konnte lokal nicht direkt ausgeführt werden. Die dockerisierten Web-/Dashboard-Surfaces wurden aber erfolgreich gebaut und über HTTP verifiziert.
- **Host-Python hat keine FastAPI-Test-Extras**; service-spezifische Unit-Tests wie `tests/unit/test_auth_service.py` laufen lokal nicht ohne zusätzliche Dependencies. Der verifizierte Repo-Gate bleibt `make integration-test`.
- **Qdrant-Compose-Healthcheck ist aktuell falsch-negativ** (Compose nutzt `curl`, das im Upstream-Image fehlt). Qdrant antwortet dennoch auf `/collections`; dadurch mussten abhängige Container nach dem Rebuild einmalig gestartet werden.
- Bei älteren lokalen Volumes kann `uploads_data` root-owned sein. Falls Uploads mit `PermissionError` scheitern, einmalig:

```bash
docker exec -u 0 kirobi-api sh -lc 'chown -R 1000:1000 /data/uploads'
```

## Demo-Start

```bash
make integration-test
docker compose up -d auth api embeddings ingest retrieval analytics web dashboard
```

Wenn Compose wegen des bekannten Qdrant-Healthchecks abhängige Container nur als `Created` belässt:

```bash
docker start kirobi-api kirobi-embeddings kirobi-ingest kirobi-retrieval kirobi-web kirobi-dashboard
```

Dann:

- PWA: `http://localhost:3002`
- Dashboard: `http://localhost:3003`
