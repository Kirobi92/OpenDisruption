---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/coding – Code-Modelle

Konfigurationen und Dokumentation für code-spezialisierte Modelle im Kirobi-Ökosystem. Diese Modelle werden vom `kirobi-coder`-Agent und dem KeyCodi-Orchestrator für Code-Generierung, Refactoring, Debugging und Code-Review genutzt.

## Zweck

Code-Modelle sind auf Programmieraufgaben optimiert: Sie verstehen Syntax, kennen Bibliotheken und können kontextbezogene Code-Vorschläge machen. Sie ergänzen General-Purpose-Modelle dort, wo Präzision bei Code entscheidend ist.

## Verfügbare Modelle

| Modell | Anbieter | Stärken | Ressourcen |
|--------|----------|---------|-----------|
| `qwen2.5-coder:7b` | Alibaba / lokal via Ollama | Python, TypeScript, schnell | ~5 GB VRAM |
| `qwen2.5-coder:32b` | Alibaba / lokal via Ollama | Komplexe Aufgaben, hohe Qualität | ~20 GB VRAM |
| `deepseek-coder-v2` | DeepSeek / lokal | Code-Reasoning, Debugging | ~8 GB VRAM |
| `codellama:13b` | Meta / lokal | Bewährt, breite Sprachunterstützung | ~8 GB VRAM |
| `github-copilot/*` | Cloud (OpenCode) | Integration in Editor-Workflow | API, nur WORKSPACE |

## Modell-Auswahl

- **Schnelle Autovervollständigung / kleine Aufgaben:** `qwen2.5-coder:7b`
- **Komplexe Refactorings / Architektur-Entscheidungen:** `qwen2.5-coder:32b`
- **Debugging und Fehleranalyse:** `deepseek-coder-v2`
- **Cloud-Fallback (nur WORKSPACE-Daten):** `github-copilot` via OpenCode

## Konfiguration

Das Model-Routing wählt automatisch das passende Modell basierend auf Aufgabentyp und verfügbaren Ressourcen:

```bash
# Verfügbare Modelle prüfen
python -m kirobi_core registry

# Modell-Routing testen
python -m pytest tests/unit/test_model_routing_service.py -v
```

## Verwandte Verzeichnisse

- `models/routing/` – Routing-Logik für Modell-Auswahl
- `services/model-routing/` – Model-Routing-Service
- `models/local/` – Alle lokal via Ollama laufenden Modelle
