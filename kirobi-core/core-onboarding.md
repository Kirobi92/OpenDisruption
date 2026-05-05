# Onboarding: Kirobi / Disruptive OS

**Zone:** WORKSPACE | **Version:** 1.0

---

## Willkommen bei Kirobi!

Dieses Dokument führt neue Nutzer durch die erste Einrichtung und erklärt, wie das System am effektivsten genutzt werden kann.

---

## Schritt 1: System starten

```bash
# .env konfigurieren
cp .env.example .env
nano .env  # Passwörter und Ports anpassen

# System initialisieren
make init

# Alle Services starten
make up

# Status prüfen
make status
```

## Schritt 2: Erste Modelle herunterladen

```bash
make pull-models
# Lädt llama3.1:8b, nomic-embed-text und mistral:7b herunter
# Dauer: 10-30 Minuten je nach Internetverbindung
```

## Schritt 3: Open WebUI einrichten

1. Öffne http://localhost:3000
2. Erstelle einen Admin-Account
3. Gehe zu Settings → Models → Wähle llama3.1:8b
4. Teste mit einer einfachen Frage

## Schritt 4: Ersten Inhalt ingesten

```bash
# Lege eine Datei in sources/inbox/ ab
cp /path/to/dokument.pdf sources/inbox/

# Hermes Extractor wird automatisch ausgelöst (wenn konfiguriert)
# Oder manuell: kirobi-core anweisen zu ingesten
```

## Schritt 5: Kirobi kennenlernen

Empfohlene erste Fragen in Open WebUI:
- "Kirobi, erkläre mir deine Architektur"
- "Was sind deine Kernprinzipien?"
- "Welche Agenten stehen zur Verfügung?"
- "Wie verarbeite ich eine neue Datei?"

---

## Häufige Anfänger-Fehler

1. **Passwörter nicht ändern**: Die Standard-Passwörter aus `.env.example` sind unsicher!
2. **Große Modelle zu früh**: Starte mit 8B-Modellen, dann skaliere hoch
3. **SACRED-Zone vergessen**: Definiere klare Grenzen was in SACRED gehört
4. **Kein Backup**: Richte Backup ein bevor du wichtige Daten speicherst
