# Fallback-Strategien: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Modell-Fallbacks

| Primär | Fallback 1 | Fallback 2 | Notfall |
|--------|-----------|-----------|---------|
| llama3.1:70b | llama3.1:8b | phi3.5:3.8b | Cloud (PUBLIC only) |
| deepseek-r1:32b | llama3.1:70b | llama3.1:8b | Cloud (PUBLIC only) |
| qwen2.5-coder:32b | qwen2.5-coder:7b | llama3.1:8b | Cloud (PUBLIC only) |
| bge-m3 | nomic-embed-text | mxbai-embed-large | – |

## Service-Fallbacks

| Service | Fallback | Beschreibung |
|---------|---------|-------------|
| Qdrant down | Keyword-Suche in Markdown | Einfache grep-basierte Suche |
| PostgreSQL down | JSON-Flat-Files | Temporärer lokaler Speicher |
| Flowise down | Direkte API-Calls | Manuelle Agenten-Trigger |
| Open WebUI down | CLI-Interface | Terminal-basiertes Interface |

## Inhaltliche Fallbacks

| Situation | Fallback |
|-----------|---------|
| Keine relevanten Qdrant-Ergebnisse | Kirobi-Core Allgemeinwissen |
| Canon-Dokument nicht aktuell | Hinweis auf Aktualisierungsbedarf |
| Halluzinations-Risiko erkannt | Antwort mit `[UNSICHER – bitte verifizieren]` markieren |
| Zonenverletzungs-Versuch | Ablehnung + Logging + ggf. Alarm |

## Kommunikations-Fallbacks

Wenn Kirobi eine Aufgabe nicht erfüllen kann:
1. Klar kommunizieren: "Das liegt außerhalb meiner aktuellen Fähigkeiten"
2. Alternative vorschlagen wenn möglich
3. In `experiences/learnings/agent-errors.md` dokumentieren
4. Bei wiederkehrendem Muster: Verbesserungsvorschlag an kirobi-architect
