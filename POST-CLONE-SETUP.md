# 🎉 Post-Clone Setup Guide – Heute Abend Ready!

**Version:** 1.1
**Ziel:** Von Clone bis zum ersten natürlichen Family-Gespräch in unter 30 Minuten
**Datum:** 2026-05-05

---

## ⚡ Tonight Clone & Run – Local-First Kickstart (kein Docker nötig)

Wenn du zuerst nur sehen willst, dass das Repo *jetzt* auf einem frischen
Linux-Rechner läuft – ohne Ollama, ohne GPU, ohne Compose-Stack – nutze den
neuen Python-Core (`kirobi_core`). Er nutzt ausschließlich die Python-
Standardbibliothek und braucht weder `pip install` noch Internet.

```bash
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption

# 1. Health-Check, .env anlegen, Repo scannen
make bootstrap

# 2. Geführtes Onboarding-Interview (CLI, Antworten landen in .kirobi/)
make interview

# 3. Eine autonome Iteration im Dry-Run (Report nach .kirobi/reports/)
make autonomous-once

# 4. Backlog ansehen (priorisierte Tasks als JSON)
make backlog LIMIT=5

# 5. Tests ausführen
make test
```

Alle obigen Befehle sind **dry-run-by-default**, schreiben keine sensiblen
Daten in die Cloud und respektieren die fünf Sicherheitszonen aus
`CLAUDE.md`. Die Audit-Spur landet in `kirobi-core/core-events.log`.

Die volle Container-Variante mit Ollama, Qdrant, Open WebUI und Voice
findest du weiter unten unter „Schnellstart (TL;DR)".

---

## 🚀 Schnellstart (TL;DR)

```bash
# 1. Repository klonen
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption

# 2. GPU optimieren
chmod +x infra/scripts/detect-gpu.sh
./infra/scripts/detect-gpu.sh

# 3. System initialisieren
make init

# 4. Starten!
make up

# 5. Family Interview starten
make start-interview
```

**Das war's! 🎊 Kirobi ist jetzt live und bereit für Gespräche.**

---

## 📋 Detaillierte Anleitung

### Schritt 1: System-Voraussetzungen prüfen

#### Hardware (Minimum)
- ✅ Pop!_OS 22.04+ (oder Ubuntu 22.04+)
- ✅ NVIDIA GPU mit mindestens 8GB VRAM (empfohlen: 16GB+)
- ✅ 32 GB RAM
- ✅ 500 GB freier SSD-Speicher
- ✅ Mikrofon (für Voice-Interaction)

#### Software
- ✅ Docker & Docker Compose v2+
- ✅ NVIDIA Drivers (wird automatisch geprüft)
- ✅ Git

#### Installation der Dependencies (falls noch nicht vorhanden)

```bash
# Docker installieren (falls nötig)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Neu anmelden oder:
newgrp docker

# Docker Compose v2 prüfen
docker compose version

# NVIDIA Drivers (Pop!_OS)
sudo apt install system76-cuda-latest system76-cudnn-11.8
```

---

### Schritt 2: Repository klonen

```bash
cd ~
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption
```

---

### Schritt 3: GPU-Erkennung und Optimierung

Dieser Schritt ist **kritisch** für optimale Voice-Performance:

```bash
chmod +x infra/scripts/detect-gpu.sh
./infra/scripts/detect-gpu.sh
```

**Das Script macht:**
- ✅ Erkennt NVIDIA GPU und zeigt Specs
- ✅ Prüft CUDA Installation
- ✅ Installiert NVIDIA Container Toolkit (falls nötig)
- ✅ Optimiert `.env` für deine GPU
- ✅ Empfiehlt passende Modelle basierend auf VRAM

**Erwartete Ausgabe:**
```
╔════════════════════════════════════════════════════════════╗
║     Kirobi GPU Detection & Optimization                    ║
╚════════════════════════════════════════════════════════════╝

→ Detecting NVIDIA GPU...
  ✓ NVIDIA GPU detected:
    GPU: NVIDIA GeForce RTX 4090
    Memory: 24576 MB
    Driver: 535.183.01

  ✓ CUDA Version: 12.1
  ✓ NVIDIA Container Runtime detected
  ✓ GPU accessible from Docker containers

→ Model recommendations based on GPU memory:
  Available GPU Memory: 24GB

  Excellent! Your GPU can handle all models:
    - Whisper large-v3 (recommended)
    - llama3.1:70b for supervisor
    - Multiple models simultaneously
```

---

### Schritt 4: System initialisieren

```bash
make init
```

**Das passiert hier:**
- Erstellt `.env` aus `.env.example`
- Initialisiert Verzeichnisstruktur
- Lädt Docker Images herunter
- Bereitet Services vor

**Dauer:** ~5-10 Minuten (abhängig von Internet-Geschwindigkeit)

---

### Schritt 5: Konfiguration anpassen (optional)

Die `.env` Datei ist bereits GPU-optimiert. Optionale Anpassungen:

```bash
nano .env
```

**Wichtige Einstellungen:**

```env
# Voice Settings (bereits optimiert durch detect-gpu.sh)
WHISPER_MODEL=large-v3          # oder 'medium', 'turbo'
WHISPER_DEVICE=cuda             # GPU-beschleunigt
WHISPER_COMPUTE_TYPE=float16    # oder 'int8' für weniger VRAM
VOICE_LANGUAGE=de               # Deutsch

# Supervisor Model
SUPERVISOR_MODEL=llama3.1:70b   # oder llama3.1:8b für weniger VRAM

# Ports (Standard sollte passen)
OPENWEBUI_PORT=3000
FLOWISE_PORT=3001
VOICE_PORT=8001
```

---

### Schritt 6: System starten

```bash
make up
```

**Das startet:**
- 🐘 PostgreSQL (Datenbank)
- 🔮 Qdrant (Vector DB)
- 🦙 Ollama (Lokale LLMs mit GPU)
- 🌐 Open WebUI (Chat-Interface)
- 🔄 Flowise (Workflow-Orchestrierung)
- 🎙️ Voice Processing Service (Whisper + Piper TTS)
- 🤖 Kirobi Supervisor (Autonomer Agent)

**Dauer:** ~2-3 Minuten

**Prüfe den Status:**
```bash
make status
```

**Erwartete Ausgabe:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Kirobi / Disruptive OS – System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAME                    STATUS      PORTS
kirobi-ollama           Up          11434
kirobi-postgres         Up          5432
kirobi-qdrant           Up          6333, 6334
kirobi-open-webui       Up          3000
kirobi-flowise          Up          3001
kirobi-voice-processing Up          8001
kirobi-supervisor       Up
```

---

### Schritt 7: Modelle herunterladen

```bash
make pull-models
```

Das lädt die benötigten Ollama-Modelle herunter:
- llama3.1:70b (oder 8b je nach GPU)
- qwen2.5-coder:32b
- mistral:7b
- deepseek-r1:32b

**Dauer:** ~15-30 Minuten (einmalig, große Downloads)

**Tipp:** Lass das im Hintergrund laufen und fahre parallel fort!

---

### Schritt 8: Voice Interface testen

Bevor du mit dem Family Interview startest, teste die Voice-Funktionalität:

```bash
make voice-test
```

**Das testet:**
- ✅ Text-to-Speech (TTS mit Piper)
- ✅ Piper Voice Model (Deutsch)

**Für Speech-to-Text Test (mit Mikrofon):**
```bash
docker compose exec voice-processing python3 voice_interface.py --test-stt
```

Sprich etwas ins Mikrofon nach dem Prompt. Wenn die Transkription korrekt ist, funktioniert alles! 🎉

---

### Schritt 9: Family Interview starten! 🎊

**Dies ist der Moment!** Starte dein erstes natürliches Gespräch mit Kirobi:

```bash
make start-interview
```

**Du wirst gefragt:**
```
╔════════════════════════════════════════════════════════════╗
║        Kirobi Family Interview - Willkommen!               ║
╚════════════════════════════════════════════════════════════╝

Mit wem soll das Interview geführt werden? (Sven/Samira/Sineo):
```

Gib deinen Namen ein (z.B. `Sven`) und drücke Enter.

**Kirobi begrüßt dich warm und das Gespräch beginnt!**

---

## 🎤 Was passiert im Interview?

### Kirobi wird:
- **Warm begrüßen** und den Kontext erklären
- **Aktiv zuhören** und intelligente Folgefragen stellen
- **Natürlich fließend** sprechen (nicht wie ein Fragebogen)
- **Emotionen erkennen** und empathisch reagieren
- **Tief nachfragen** um wirklich zu verstehen

### Themen, die natürlich erforscht werden:
1. **Vision & Träume** – Wo willst du in 1, 3, 5 Jahren sein?
2. **Werte & Prinzipien** – Was ist dir wirklich wichtig?
3. **Alltag & Rhythmen** – Wie sieht dein Tag aus?
4. **Herausforderungen** – Wo brauchst du Unterstützung?
5. **SACRED Grenzen** – Was ist streng privat?
6. **Familie & Beziehungen** – Wie funktioniert eure Dynamik?
7. **Business & Projekte** – Was treibt dich beruflich?
8. **Kreativität** – Wie drückst du dich aus?
9. **Wie Kirobi helfen soll** – Wie stellst du dir die Zusammenarbeit vor?
10. **Tech-Präferenzen** – Voice oder Text? Formal oder casual?

### Das Gespräch ist:
- ❤️ Empathisch und respektvoll
- 🧠 Intelligent und kontextbewusst
- 🔄 Iterativ (kann jederzeit pausiert/fortgesetzt werden)
- 🔒 Absolut privat (FAMILY_PRIVATE zone, keine Cloud)

---

## 🎛️ Wichtige Kommandos

### System-Status
```bash
make status          # Zeigt alle Services
make logs            # Live-Logs aller Services
make voice-logs      # Nur Voice Service
make supervisor-logs # Nur Supervisor
```

### Voice & Interview
```bash
make voice-test      # Voice testen
make start-interview # Interview starten
make voice-restart   # Voice Services neu starten
```

### Wartung
```bash
make restart         # Alle Services neu starten
make down            # Services stoppen
make backup          # Backup erstellen
```

---

## 🔧 Troubleshooting

### Problem: "GPU not accessible from Docker"

**Lösung:**
```bash
sudo systemctl restart docker
./infra/scripts/detect-gpu.sh
make up
```

### Problem: "Voice service not responding"

**Lösung:**
```bash
make voice-logs  # Prüfe Logs
make voice-restart
```

### Problem: "Whisper model download failed"

**Lösung:**
```bash
docker compose exec voice-processing bash
cd /models/piper
# Manuell herunterladen
```

### Problem: "Out of GPU memory"

**Lösung:**
1. Prüfe GPU-Auslastung: `watch -n 1 nvidia-smi`
2. Nutze kleinere Modelle in `.env`:
   ```env
   WHISPER_MODEL=medium
   WHISPER_COMPUTE_TYPE=int8
   SUPERVISOR_MODEL=llama3.1:8b
   ```
3. System neu starten: `make restart`

### Problem: "Microphone not detected"

**Lösung:**
```bash
# Prüfe verfügbare Audio-Devices
arecord -l

# Teste Mikrofonaufnahme
arecord -d 5 test.wav
aplay test.wav
```

---

## 🌟 Was kommt als Nächstes?

Nach dem ersten Interview wird Kirobi **autonom weiterarbeiten**:

### Sofort nach dem Interview:
1. **Erstellt persönliche Profile** in `/canon/family/`
2. **Speichert Erkenntnisse** in `/experiences/family/interviews/`
3. **Aktualisiert Agenten-Prompts** basierend auf deinen Präferenzen
4. **Priorisiert Tasks** für die Familienunterstützung
5. **Läuft 24/7** im Hintergrund und entwickelt sich weiter

### Du kannst:
- **Jederzeit weitersprechen:** `make start-interview`
- **Mit anderen Familienmitgliedern Interviews führen**
- **Open WebUI nutzen:** http://localhost:3000
- **Flowise Workflows erstellen:** http://localhost:3001
- **System beobachten:** `make supervisor-logs`

---

## 📊 System-Übersicht

### Services & Ports
| Service | Port | Zweck |
|---------|------|-------|
| Open WebUI | 3000 | Chat-Interface |
| Flowise | 3001 | Workflow-Builder |
| Ollama | 11434 | LLM API |
| Qdrant | 6333 | Vector Search |
| PostgreSQL | 5432 | Datenbank |
| Voice Processing | 8001 | STT/TTS API |

### Datenstruktur
```
kirobi-core/          # Supervisor, Policies, Events
experiences/family/   # Interview-Transkripte
canon/family/         # Familien-Profile
data/conversations/   # Voice-Sessions
data/supervisor/      # Task-Datenbank
```

---

## 🎓 Best Practices

### Für das erste Interview:
1. **Nimm dir Zeit** (30-60 Minuten)
2. **Sei ehrlich und offen** (das System ist nur für dich)
3. **Sprich natürlich** wie mit einem Freund
4. **Pausiere wenn nötig** (einfach "Pause" sagen)
5. **Stelle auch Gegenfragen** an Kirobi

### Für die Familie:
1. **Jedes Mitglied sollte ein eigenes Interview haben**
2. **Kinder kindgerecht ansprechen lassen** (Sineo bekommt altersgerechte Fragen)
3. **SACRED-Bereiche respektieren** (explizit markieren)
4. **Regelmäßige Updates** (alle paar Monate nachfassen)

---

## 🔐 Sicherheit & Privatsphäre

### Was du wissen solltest:
- ✅ **Alle Daten bleiben lokal** auf deinem Rechner
- ✅ **Keine Cloud-Uploads** ohne deine explizite Freigabe
- ✅ **FAMILY_PRIVATE Zone** für alle Interviews
- ✅ **SACRED-Inhalte** maximal geschützt
- ✅ **Verschlüsselte Vector-DB** für sensible Daten
- ✅ **Audit-Logs** in `/kirobi-core/core-events.log`

### Backup-Strategie:
```bash
# Manuelles Backup
make backup

# Automatisches Backup (täglich via Cron)
crontab -e
# Füge hinzu:
0 2 * * * cd /path/to/OpenDisruption && make backup
```

---

## 📞 Support & Feedback

### Logs prüfen:
```bash
make logs              # Alle Services
make supervisor-logs   # Supervisor
make voice-logs        # Voice Service
```

### Events prüfen:
```bash
cat kirobi-core/core-events.log
```

### Neustart bei Problemen:
```bash
make down
make up
```

### Vollständiger Reset (VORSICHT!):
```bash
make reset  # Löscht ALLE Daten!
```

---

## 🎉 Fertig!

**Gratulation! Kirobi läuft jetzt und ist bereit, deine Familie zu unterstützen.**

Das System wird:
- 📚 Kontinuierlich aus euren Gesprächen lernen
- 🤖 Autonom Tasks priorisieren und ausführen
- 🔄 Sich selbst weiterentwickeln
- ❤️ Eure Familie respektvoll begleiten

**Viel Freude mit Kirobi – deinem intelligenten, empathischen Familien-Partner!**

---

## 📚 Weitere Dokumentation

- [README.md](../README.md) – Projekt-Übersicht
- [PROJECT-CHARTER.md](../PROJECT-CHARTER.md) – Vision & Mission
- [ARCHITECTURE.md](../ARCHITECTURE.md) – Technische Architektur
- [CLAUDE.md](../CLAUDE.md) – AI-Agent Richtlinien
- [DEVELOPER-RUNBOOK.md](../DEVELOPER-RUNBOOK.md) – Entwickler-Dokumentation

---

**Version:** 1.0
**Letzte Aktualisierung:** 2026-05-05
**Autor:** Claude Opus 4.7 (via claude-code)
**Status:** ✅ Production Ready
