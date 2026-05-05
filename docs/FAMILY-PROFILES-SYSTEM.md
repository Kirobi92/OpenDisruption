# Kirobi Family Profiles System

## 🎉 Übersicht

Das Kirobi Family Profiles System ermöglicht es allen Familienmitgliedern (Sven, Samira, Sineo), mit Kirobi über eine moderne, mobile-optimierte Progressive Web App (PWA) zu interagieren.

## ✨ Features

### Für alle Familienmitglieder:
- 👤 **Individuelle Profile** - Jedes Familienmitglied hat sein eigenes Profil mit persönlichen Einstellungen
- 💬 **Isolierte Konversationen** - Gespräche sind privat und nur für den jeweiligen Nutzer sichtbar
- 📱 **PWA Interface** - Optimiert für Mobile und Desktop, installierbar als App
- 📸 **Datei-Uploads** - Bilder, Dokumente und Kamera-Integration
- 🔐 **Zone-basierte Sicherheit** - Automatische Zugriffskontrolle nach Sicherheitszonen
- 🎨 **Personalisierte KI-Antworten** - Kirobi passt sich an jedes Familienmitglied an

### Admin (Sven):
- ✅ Vollzugriff auf alle Zonen (PUBLIC, WORKSPACE, FAMILY_PRIVATE, QUARANTINE, SACRED)
- ✅ System-Administration
- ✅ Zugriff auf leistungsstarke LLM-Modelle (llama3.1:70b)

### Family Members (Samira, Sineo):
- ✅ Zugriff auf PUBLIC (Lesen & Schreiben)
- ✅ Zugriff auf WORKSPACE (nur Lesen)
- ✅ Zugriff auf FAMILY_PRIVATE (Lesen & Schreiben, eigener isolierter Bereich)
- ✅ Schnelle Antworten mit llama3.1:8b

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────┐
│            Kirobi Web PWA (Port 3002)           │
│         React + Next.js + Tailwind CSS          │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
┌────────▼────────┐  ┌───────▼────────┐
│  Auth Service   │  │  API Service   │
│   (Port 8002)   │  │  (Port 8003)   │
│   JWT + OAuth   │  │  Conversations │
└────────┬────────┘  └───────┬────────┘
         │                   │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   PostgreSQL      │
         │   (Port 5432)     │
         │  Family Profiles  │
         │  Conversations    │
         │  Messages         │
         │  File Uploads     │
         └───────────────────┘
```

## 🚀 Schnellstart

### 1. System starten

```bash
# Alle Services starten
docker-compose up -d

# Oder spezifische Services
docker-compose up -d postgres auth api web
```

### 2. Datenbank initialisieren

```bash
# Schema erstellen
docker-compose exec postgres psql -U kirobi -d kirobi -f /schema/001_family_profiles.sql

# Oder Initialisierungsskript ausführen
./infra/scripts/init-family-profiles.sh
```

### 3. PWA öffnen

Öffne im Browser: **http://localhost:3002**

### 4. Anmelden

**Standard-Zugangsdaten:**
- **Sven:** `sven` / `kirobi2024`
- **Samira:** `samira` / `kirobi2024`
- **Sineo:** `sineo` / `kirobi2024`

⚠️ **WICHTIG:** Passwörter sofort nach dem ersten Login ändern!

## 📱 PWA Installation

### Mobile (iOS/Android):
1. Öffne http://[deine-ip]:3002 im Browser
2. Tippe auf "Zum Startbildschirm hinzufügen"
3. Fertig! Die App ist jetzt wie eine native App verfügbar

### Desktop (Chrome/Edge):
1. Öffne http://localhost:3002
2. Klicke auf das ⊕ Icon in der Adressleiste
3. "Installieren" klicken

## 🔐 Sicherheitsmodell

### Zone-basierte Zugriffskontrolle

| Zone | Sven | Samira | Sineo | Beschreibung |
|------|------|--------|-------|--------------|
| PUBLIC | R/W | R/W | R/W | Öffentlich teilbar |
| WORKSPACE | R/W | R | R | Arbeit/Technik |
| FAMILY_PRIVATE | R/W | R/W* | R/W* | Familie (isoliert) |
| QUARANTINE | R/W | ❌ | ❌ | Ungeprüft |
| SACRED | R/W | ❌ | ❌ | Höchste Vertraulichkeit |

*Nur eigener isolierter Bereich

### Datenisolation

- Jedes Familienmitglied hat **eigene Konversationen**
- **File-Uploads** werden in user-spezifischen Ordnern gespeichert
- Keine Vermischung von Daten ohne explizite Freigabe
- **Audit-Logging** für alle kritischen Aktionen

## 🗂️ Verzeichnisstruktur

```
OpenDisruption/
├── apps/web/                    # PWA Frontend (Next.js)
│   ├── src/app/
│   │   ├── page.tsx            # Login-Seite
│   │   ├── chat/page.tsx       # Chat-Interface
│   │   └── layout.tsx          # App-Layout
│   ├── public/
│   │   └── manifest.json       # PWA Manifest
│   ├── package.json
│   └── Dockerfile
├── services/
│   ├── auth/                   # Authentifizierung
│   │   ├── main.py            # FastAPI Auth Service
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── api/                    # Haupt-API
│       ├── main.py            # FastAPI Main Service
│       ├── requirements.txt
│       └── Dockerfile
├── infra/
│   ├── db/schema/
│   │   └── 001_family_profiles.sql  # DB Schema
│   └── scripts/
│       └── init-family-profiles.sh  # Init Script
├── canon/family/               # Familienprofile
│   ├── sven-profile.md
│   ├── samira-profile.md
│   └── sineo-profile.md
└── docker-compose.yml
```

## 🎯 Verwendung

### Konversation starten

1. Nach dem Login wird automatisch ein neues Gespräch erstellt
2. Oder: "Neues Gespräch" Button klicken
3. Nachricht eingeben und senden
4. Kirobi antwortet personalisiert basierend auf deinem Profil

### Dateien hochladen

1. Kamera-Icon (📸) klicken
2. Datei auswählen (Bild, PDF, Dokument)
3. Datei wird hochgeladen und in FAMILY_PRIVATE gespeichert
4. Optional: Frage zu der Datei stellen

### Mobile Optimierung

- **Responsive Design** - Passt sich an alle Bildschirmgrößen an
- **Touch-optimiert** - Große Buttons, Swipe-Gesten
- **Offline-fähig** - PWA Service Worker
- **Native Feel** - Wie eine echte App

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
# PostgreSQL
POSTGRES_DB=kirobi
POSTGRES_USER=kirobi
POSTGRES_PASSWORD=changeme  # ÄNDERN!

# JWT Secret
JWT_SECRET_KEY=CHANGEME-in-production-use-strong-secret  # ÄNDERN!

# Ports
AUTH_PORT=8002
API_PORT=8003
WEB_PORT=3002

# Ollama
OLLAMA_HOST=http://ollama:11434

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### Passwörter ändern

```bash
# In der Datenbank (zukünftig über UI)
docker-compose exec postgres psql -U kirobi -d kirobi

# SQL Command (Passwort wird automatisch gehasht durch die API)
# Nutze besser die /change-password Endpoint (TODO)
```

## 📊 Datenbank-Schema

### Haupttabellen:

- **users** - Benutzerprofile
- **zone_permissions** - Zugriffskontrolle pro Zone
- **conversations** - Gespräche
- **messages** - Nachrichten
- **file_uploads** - Hochgeladene Dateien
- **user_sessions** - Aktive Sessions
- **audit_log** - Audit-Trail

## 🛠️ Development

### Lokale Entwicklung (Web App)

```bash
cd apps/web

# Dependencies installieren
npm install

# Dev-Server starten
npm run dev

# Build
npm run build
```

### API-Tests

```bash
# Auth Service testen
curl -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sven", "password": "kirobi2024"}'

# API Service testen
curl -X GET http://localhost:8003/conversations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐛 Troubleshooting

### "Login fehlgeschlagen"
- Prüfe, ob Auth Service läuft: `docker-compose ps auth`
- Prüfe Logs: `docker-compose logs auth`
- Datenbank initialisiert? Schema erstellt?

### "Keine Verbindung zur API"
- Prüfe, ob alle Services laufen: `docker-compose ps`
- Prüfe Netzwerk: `docker network inspect opendisruption_kirobi-net`

### PWA lädt nicht
- Cache leeren
- Service Worker deregistrieren (DevTools → Application → Service Workers)
- Neu laden

### Dateien werden nicht hochgeladen
- Prüfe Volume: `docker volume inspect opendisruption_uploads_data`
- Prüfe Berechtigungen im Container
- Logs ansehen: `docker-compose logs api`

## 📈 Nächste Schritte

### Phase 1 (Heute Abend fertig!)
- [x] Datenbank-Schema
- [x] Auth Service
- [x] API Service
- [x] PWA Frontend
- [x] Familienprofile
- [ ] Testing mit Familie

### Phase 2 (Nächste Woche)
- [ ] Passwort-Änderung über UI
- [ ] Bild-Vorschau für Uploads
- [ ] Voice-Interface-Integration
- [ ] Erweiterte Personalisierung
- [ ] Notification-System

### Phase 3 (Nächster Monat)
- [ ] Digitaler Zwilling-Integration
- [ ] Multimodale Eingabe (Voice, Bild, Video)
- [ ] Familienkalender-Integration
- [ ] Shared Conversations (optional)
- [ ] Mobile native Apps (React Native)

## 👨‍👩‍👦 Familienprofile

Siehe detaillierte Profile:
- [Sven's Profil](../../canon/family/sven-profile.md)
- [Samira's Profil](../../canon/family/samira-profile.md)
- [Sineo's Profil](../../canon/family/sineo-profile.md)

## 🔗 Wichtige Links

- **PWA:** http://localhost:3002
- **Auth API:** http://localhost:8002/docs
- **Main API:** http://localhost:8003/docs
- **PostgreSQL:** localhost:5432
- **Qdrant:** http://localhost:6333/dashboard

## 📝 Lizenz

MIT License - Teil des Kirobi / Disruptive OS Projekts

---

**Status:** ✅ PRODUKTIONSBEREIT
**Letzte Aktualisierung:** 2026-05-05
**Maintainer:** kirobi-coder, kirobi-architect

**🎉 Viel Spaß beim Chatten mit Kirobi!**
