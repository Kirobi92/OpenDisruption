# API-Katalog-Schema: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Schema für API-Einträge

Jede API im Katalog (integrations/APIS/) folgt diesem Schema:

```yaml
api:
  name: "API-Name"
  category: "ai|data|media|communication|productivity|iot|business"
  base_url: "https://api.example.com/v1"
  auth_type: "api_key|oauth2|bearer|none"
  cost: "free|freemium|paid"
  rate_limit: "X requests/minute"
  zone_compatible: ["PUBLIC", "WORKSPACE"]  # Keine FAMILY_PRIVATE/SACRED!
  
  endpoints:
    - name: "endpoint-name"
      path: "/endpoint"
      method: "GET|POST|PUT|DELETE"
      description: "Was tut dieser Endpoint"
      use_cases:
        - "Anwendungsfall 1"
        - "Anwendungsfall 2"
  
  kirobi_integration:
    agent: "agent-name"
    flowise_node: "custom-tool"
    config_file: "integrations/config/api-name.yaml"
  
  notes: "Wichtige Hinweise zur Nutzung"
```

## Pflichtfelder

- `name`: Eindeutiger Name
- `category`: Kategorie
- `base_url`: Basis-URL
- `auth_type`: Authentifizierungsart
- `cost`: Kostenmodell
- `zone_compatible`: Erlaubte Zonen (nie SACRED angeben)

## Kategorien

| Kategorie | Beschreibung | Beispiele |
|-----------|-------------|---------|
| `ai` | KI-Dienste | OpenAI, Anthropic, Groq |
| `data` | Datenquellen | Wikipedia, OpenStreetMap |
| `media` | Medien-Generierung | DALL-E, Suno, ElevenLabs |
| `communication` | Kommunikation | Slack, Teams |
| `productivity` | Produktivität | Notion, Google Calendar |
| `iot` | Internet of Things | Home Assistant, OpenHAB |
| `business` | Business | Enventa, SAP |
| `research` | Recherche | Arxiv, Semantic Scholar |
