---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/routing – Modell-Routing

Konfigurationen und Dokumentation für die intelligente Modell-Auswahl im Kirobi-Ökosystem. Das Routing entscheidet automatisch, welches Modell für eine gegebene Aufgabe, Priorität und Ressourcenlage am besten geeignet ist.

## Zweck

Nicht jede Aufgabe braucht das stärkste Modell. Routing optimiert den Trade-off zwischen Qualität, Geschwindigkeit und Ressourcenverbrauch: Einfache Klassifizierungen gehen an kleine, schnelle Modelle – komplexe Reasoning-Aufgaben an große Modelle oder Cloud-Fallbacks.

## Routing-Logik

```
Aufgabe eingehend
    │
    ├─ prefer_fast=true  →  kleinstes verfügbares Modell (z. B. llama3.2:3b)
    │
    ├─ Aufgabentyp=code  →  qwen2.5-coder:7b (oder :32b bei Komplexität)
    │
    ├─ Aufgabentyp=embed →  nomic-embed-text
    │
    ├─ Standard          →  llama3.1:8b (primary)
    │                       llama3.1:70b (fallback, wenn GPU verfügbar)
    │
    └─ Kein lokales Modell verfügbar  →  Cloud-Fallback (nur WORKSPACE/PUBLIC)
```

## Konfiguration

Der Model-Routing-Service (`services/model-routing/`) liest verfügbare Modelle beim Start von Ollama und wählt dynamisch aus:

```env
MODEL_PRIMARY=llama3.1:8b
MODEL_FALLBACK=llama3.1:70b
MODEL_FAST=llama3.2:3b
MODEL_CODING=qwen2.5-coder:7b
MODEL_EMBED=nomic-embed-text
```

## Testen

```bash
# Unit-Tests für Routing-Logik (vollständig gemockt)
python -m pytest tests/unit/test_model_routing_service.py -v

# Verfügbare Modelle anzeigen
python -m kirobi_core registry
```

## Verwandte Verzeichnisse

- `services/model-routing/` – FastAPI-Service-Implementierung
- `models/local/` – Lokal verfügbare Ollama-Modelle
- `models/cloud/` – Cloud-Fallback-Konfigurationen
- `models/coding/` – Code-spezialisierte Modelle
