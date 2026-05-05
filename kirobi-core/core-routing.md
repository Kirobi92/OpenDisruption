# Routing-Logik: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Routing-Entscheidungsbaum

### Schritt 1: Anfrage-Klassifizierung

| Anfrage-Typ | Routing-Ziel | Modell |
|------------|-------------|--------|
| Code schreiben | kirobi-coder | qwen2.5-coder:32b |
| System planen | kirobi-architect | deepseek-r1:32b |
| Infra/Docker | kirobi-ops | llama3.1:8b |
| Überwachung | kirobi-observer | mistral:7b |
| Daten ingesten | hermes-extractor | mistral:7b |
| Familie/Mediation | samira-heart-agent | llama3.1:8b |
| Creator/Sineo | sineo-creator-coach | llama3.1:8b |
| Web-Recherche | research-crew | Perplexica |
| Kreative Aufgabe | creative-agent | llama3.1:70b |
| Sprach-Input | voice-agent | Whisper |
| Business/Enterprise | enterprise-agent | llama3.1:70b |
| Allgemein/Komplex | kirobi-core (direkt) | llama3.1:70b |

### Schritt 2: Modell-Auswahl

```
Ist die Aufgabe zeitkritisch (< 5 Sek)?
  → Ja: phi3.5:3.8b oder llama3.1:8b
  → Nein:
    Benötigt es komplexes Reasoning?
      → Ja: deepseek-r1:32b
      → Nein:
        Ist es Code?
          → Ja: qwen2.5-coder:32b oder :7b
          → Nein: llama3.1:70b (Standard für wichtige Aufgaben)
```

### Schritt 3: Zonen-Check

Bevor jeder Routing-Entscheidung:
1. Zone der Anfrage bestimmen
2. Zone mit ZONE-POLICY-MATRIX prüfen
3. Wenn Zone-Verletzung: Ablehnen und Human-in-Loop

---

## Fallback-Routing

| Primary | Fallback | Grund |
|---------|---------|-------|
| llama3.1:70b | llama3.1:8b | Zu langsam / VRAM |
| deepseek-r1:32b | llama3.1:70b | Modell nicht verfügbar |
| qwen2.5-coder:32b | qwen2.5-coder:7b | VRAM begrenzt |
| Cloud-API | lokales Modell | Netzwerk-Problem |
