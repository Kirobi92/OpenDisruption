---
zone: WORKSPACE
type: canon-master
document: api-catalog-master
version: 1.0
created_at: 2024-01-01
reviewed_by: kirobi-architect
---

# Canon: API-Katalog

## Interne APIs

### Kirobi Core API
- **URL:** http://localhost:8000/api/v1
- **Auth:** Bearer Token aus .env
- **Docs:** http://localhost:8000/docs

### Flowise API
- **URL:** http://localhost:3001/api/v1
- **Auth:** FLOWISE_USERNAME/PASSWORD
- **Flows:** GET /chatflow

### Qdrant API
- **URL:** http://localhost:6333
- **Auth:** Keine (nur lokales Netzwerk)
- **Docs:** http://localhost:6333/dashboard

### Ollama API
- **URL:** http://localhost:11434/api
- **Auth:** Keine (nur lokales Netzwerk)
- **Modelle:** GET /api/tags

## Externe APIs (Optional)

### OpenAI (Cloud - nur PUBLIC Zone)
- **Bedingung:** Nur für PUBLIC-Zone-Inhalte
- **Key:** OPENAI_API_KEY in .env

### Microsoft 365 (Optional)
- **Client-ID:** M365_CLIENT_ID in .env
- **Scope:** Kalender, Aufgaben, E-Mail

## API-Sicherheits-Regeln

1. Interne APIs nie öffentlich exponieren
2. Externe APIs nie mit FAMILY/SACRED-Inhalten aufrufen
3. API-Keys rotieren alle 90 Tage
4. Rate-Limiting für alle APIs aktivieren
