---
zone: WORKSPACE
created_by: kirobi-coder
created_at: 2026-05-07
reviewed_by: pending
version: 1.0
---

# services/analytics-service/

**Verantwortlich:** kirobi-coder  
**Status:** Implementiert  
**Port:** 8010

## Zweck

Event-Tracking und Nutzungsstatistiken für das OpenDisruption-Ökosystem.
Speichert strukturierte Analytics-Events in PostgreSQL und stellt aggregierte
Statistiken über Zonen-Nutzung, Modell-Verwendung und tägliche Aktivität bereit.

## Technologie

- Python 3.11+ / FastAPI
- asyncpg (async PostgreSQL)
- Pydantic v2
- uvicorn[standard]

## API-Endpoints

| Methode | Pfad            | Beschreibung                                      |
|---------|-----------------|---------------------------------------------------|
| GET     | `/health`       | DB-Konnektivitäts-Check                           |
| POST    | `/events`       | Event tracken (`event_type`, `user_id`, `zone`, `metadata`) |
| GET     | `/events`       | Events abfragen (Filter: `event_type`, `zone`, `user_id`, `limit`, `offset`) |
| GET     | `/stats/daily`  | Tages-Statistiken (Events/Typ, aktive User, Zonen) |
| GET     | `/stats/zones`  | Lese/Schreib-Counts pro Zone                      |
| GET     | `/stats/models` | Ollama-Modell-Nutzung aus der `messages`-Tabelle  |

## DB-Schema

```sql
CREATE TABLE analytics_events (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    user_id     TEXT,
    zone        TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Indizes auf `event_type`, `created_at DESC` und `user_id`.

## Umgebungsvariablen

| Variable            | Standard    | Beschreibung              |
|---------------------|-------------|---------------------------|
| `POSTGRES_USER`     | `kirobi`    | DB-Benutzername           |
| `POSTGRES_PASSWORD` | `changeme`  | DB-Passwort               |
| `POSTGRES_HOST`     | `postgres`  | DB-Hostname               |
| `POSTGRES_PORT`     | `5432`      | DB-Port                   |
| `POSTGRES_DB`       | `kirobi`    | Datenbankname             |
| `KIROBI_PUBLIC_ORIGINS` | *(leer)* | Komma-getrennte CORS-Origins; leer = LAN-Regex |

## Lokaler Start

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8010 --reload
```

## Docker

```bash
docker build -t kirobi-analytics .
docker run -p 8010:8010 --env-file ../../.env kirobi-analytics
```

## Sicherheitshinweise

- CORS: kein `allow_origins=["*"]` mit Credentials — identisches Regex-Pattern wie `auth`/`api`
- Keine SACRED- oder FAMILY_PRIVATE-Daten in `metadata` speichern (Caller-Verantwortung)
- Parametrisierte Queries durchgehend (`$1, $2, ...`)
- Non-root User `kirobi` (UID 1001) im Container
