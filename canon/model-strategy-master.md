---
zone: WORKSPACE
type: canon-master
document: model-strategy-master
version: 1.0
created_at: 2024-01-01
reviewed_by: kirobi-architect
---

# Canon: Modell-Strategie

## Modell-Hierarchie

### Tier 1: Standard-Modelle (Lokal)
Für alltägliche Aufgaben, kein Internet erforderlich.

| Modell | Stärken | Use-Case |
|--------|---------|---------|
| llama3.1:8b | Ausgewogen, schnell | Routing, einfache Tasks |
| mistral:7b | Instruktionen | Task-Ausführung |
| qwen2.5:7b | Mehrsprachig | Deutsch-Inhalte |

### Tier 2: Spezialisten-Modelle (Lokal)
Für spezifische Aufgaben.

| Modell | Stärken | Use-Case |
|--------|---------|---------|
| llama3.1:70b | Reasoning | Komplexe Analyse |
| deepseek-coder:7b | Code | Code-Generierung |
| llava:13b | Vision | Bild-Analyse |

### Tier 3: Embedding-Modelle
| Modell | Dimensionen | Use-Case |
|--------|------------|---------|
| nomic-embed-text | 768 | Standard-Deutsch |
| bge-m3 | 1024 | Hochwertige Multi-lingual |

## Modell-Auswahl-Strategie

```
Einfache Frage → llama3.1:8b
Technische Analyse → llama3.1:70b
Code-Aufgabe → qwen2.5-coder
Bild-Aufgabe → llava
Embedding → nomic-embed-text (Standard) / bge-m3 (Qualität)
```

## VRAM-Budget

| Szenario | VRAM-Bedarf |
|----------|------------|
| Nur 8b-Modelle | 8-12 GB |
| 8b + 70b gleichzeitig | 40-50 GB |
| Produktiv (4090) | 24 GB – 1-2 Modelle aktiv |
