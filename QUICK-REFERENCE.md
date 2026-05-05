# 🚀 Kirobi Quick Reference – Voice & Interview

**Schnellstart für das Voice-First Family Interaction System**

---

## 🎯 Erstes Mal (nach Clone)

```bash
./infra/scripts/detect-gpu.sh    # GPU optimieren
make init                         # System initialisieren
make up                           # Starten
make start-interview              # LOSLEGEN!
```

---

## 🎤 Voice Commands

| Befehl | Was passiert |
|--------|--------------|
| `make voice-test` | TTS testen |
| `make start-interview` | Interview starten |
| `make voice-logs` | Voice Logs anzeigen |
| `make voice-restart` | Voice Services neu starten |

---

## 🤖 System Commands

| Befehl | Was passiert |
|--------|--------------|
| `make status` | Status aller Services |
| `make logs` | Alle Logs (live) |
| `make supervisor-logs` | Supervisor Logs |
| `make restart` | Alles neu starten |
| `make down` | Services stoppen |
| `make backup` | Backup erstellen |

---

## 🎙️ Im Interview

**Spreche natürlich wie mit einem Freund!**

- ✅ Ehrlich und offen sein
- ✅ Nachfragen wenn unklar
- ✅ Pause jederzeit möglich ("Pause")
- ✅ Beenden mit "Tschüss" oder "Stopp"

**Kirobi fragt nach:**
- Vision & Träume
- Werte & Prinzipien
- Alltag & Herausforderungen
- Familie & Beziehungen
- Business & Kreativität
- Wie das System helfen soll

---

## 🔧 Troubleshooting

### GPU Problem
```bash
sudo systemctl restart docker
./infra/scripts/detect-gpu.sh
```

### Voice reagiert nicht
```bash
make voice-restart
make voice-logs
```

### Mikrofon Problem
```bash
arecord -l              # Devices anzeigen
arecord -d 5 test.wav   # Aufnahme testen
aplay test.wav          # Abspielen
```

---

## 📁 Wo finde ich was?

| Pfad | Inhalt |
|------|--------|
| `/experiences/family/interviews/` | Interview-Transkripte |
| `/canon/family/` | Familien-Profile |
| `/data/conversations/` | Voice Sessions |
| `/kirobi-core/core-events.log` | System-Events |

---

## 🌐 Web-Interfaces

- **Open WebUI:** http://localhost:3000
- **Flowise:** http://localhost:3001
- **Qdrant:** http://localhost:6333/dashboard
- **Voice API:** http://localhost:8001/docs

---

## 🔐 Sicherheit

- ✅ Alles lokal, keine Cloud
- ✅ FAMILY_PRIVATE Zone
- ✅ SACRED maximal geschützt
- ✅ Audit-Log aktiv
- ✅ Verschlüsselte Vector-DB

---

## 📞 Hilfe

```bash
make help               # Alle Commands
cat POST-CLONE-SETUP.md # Ausführliche Anleitung
make logs               # Logs prüfen
```

---

**Happy Talking! 🎊**

*Kirobi ist dein intelligenter, empathischer Familien-Partner.*
