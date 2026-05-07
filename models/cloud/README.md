---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/cloud – Cloud-Modell-Konfigurationen

Konfigurationen für Cloud-basierte KI-Modelle, die als optionaler Fallback oder für spezifische Aufgaben genutzt werden. **Wichtig:** Cloud-Modelle dürfen ausschließlich mit `PUBLIC`- oder explizit genehmigten `WORKSPACE`-Daten verwendet werden.

## Zweck

Cloud-Modelle ergänzen das lokale Ollama-Setup dort, wo lokale Ressourcen nicht ausreichen oder spezialisierte Fähigkeiten benötigt werden. Sie sind **nicht** der Standard – Kirobi ist Local-First.

## Verfügbare Cloud-Modelle

| Modell | Anbieter | Einsatz | Zonen-Limit |
|--------|----------|---------|-------------|
| `gpt-4o` | OpenAI | Komplexe Reasoning-Aufgaben | PUBLIC, WORKSPACE (mit Genehmigung) |
| `claude-3-5-sonnet` | Anthropic | Lange Kontexte, Analyse | PUBLIC, WORKSPACE (mit Genehmigung) |
| `gemini-1.5-pro` | Google | Multimodal, große Dokumente | PUBLIC, WORKSPACE (mit Genehmigung) |
| `github-copilot/*` | GitHub/Microsoft | Code-Aufgaben via OpenCode | WORKSPACE (mit Genehmigung) |
| `perplexity-sonar` | Perplexity | Web-Recherche | PUBLIC |

## Zonen-Enforcement

```
FAMILY_PRIVATE  →  ❌ NIEMALS an Cloud-APIs
SACRED          →  ❌ NIEMALS an Cloud-APIs
WORKSPACE       →  ⚠️  Nur mit expliziter Genehmigung von Sven
PUBLIC          →  ✅  Erlaubt
```

## Konfiguration

Cloud-API-Keys gehören ausschließlich in `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...
```

## Wann Cloud-Modelle verwenden?

- Lokale GPU-Ressourcen sind erschöpft (OOM)
- Aufgabe erfordert sehr langen Kontext (>100k Token)
- Spezialisierte Fähigkeiten nicht lokal verfügbar
- Immer: Datensensitivität prüfen, Genehmigung einholen

## Verwandte Verzeichnisse

- `models/local/` – Bevorzugte lokale Modelle via Ollama
- `models/routing/` – Automatische Modell-Auswahl inkl. Cloud-Fallback
- `integrations/` – API-Integrations-Dokumentation
