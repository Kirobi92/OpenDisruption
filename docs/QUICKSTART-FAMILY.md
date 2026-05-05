# Kirobi Family Profiles - Schnellstart-Anleitung

## 🚀 In 5 Minuten startklar!

Diese Anleitung bringt das Kirobi Family Profiles System zum Laufen.

### Schritt 1: Voraussetzungen prüfen

```bash
# Docker & Docker Compose installiert?
docker --version
docker-compose --version

# Ports frei?
# 3002 (Web PWA), 8002 (Auth), 8003 (API), 5432 (PostgreSQL)
```

### Schritt 2: Umgebungsvariablen konfigurieren

```bash
# .env Datei erstellen
cp .env.example .env

# WICHTIG: Sichere Secrets setzen!
nano .env

# Mindestens diese Werte ändern:
# - POSTGRES_PASSWORD
# - JWT_SECRET_KEY
# - OPENWEBUI_SECRET_KEY
# - FLOWISE_SECRET_KEY
```

### Schritt 3: Services starten

```bash
# PostgreSQL zuerst starten (wenn noch nicht läuft)
docker-compose up -d postgres

# Auf Bereitschaft warten
sleep 10

# Datenbank-Schema initialisieren
docker-compose exec -T postgres psql -U kirobi -d kirobi < infra/db/schema/001_family_profiles.sql

# Alle neuen Services starten
docker-compose up -d auth api web

# Status prüfen
docker-compose ps
```

### Schritt 4: Passwörter für Familie setzen

```bash
# In Python Container (oder lokal)
python3 << 'EOF'
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sichere Passwörter generieren
sven_pw = "IhrSicheresPasswort123!"  # ÄNDERN!
samira_pw = "IhrSicheresPasswort123!"  # ÄNDERN!
sineo_pw = "IhrSicheresPasswort123!"  # ÄNDERN!

print(f"Sven: {pwd_context.hash(sven_pw)}")
print(f"Samira: {pwd_context.hash(samira_pw)}")
print(f"Sineo: {pwd_context.hash(sineo_pw)}")
EOF
```

Dann in PostgreSQL:

```bash
docker-compose exec postgres psql -U kirobi -d kirobi

UPDATE users SET password_hash = 'HASH_HIER' WHERE username = 'sven';
UPDATE users SET password_hash = 'HASH_HIER' WHERE username = 'samira';
UPDATE users SET password_hash = 'HASH_HIER' WHERE username = 'sineo';
\q
```

### Schritt 5: PWA öffnen!

**Desktop:**
- Browser: http://localhost:3002
- Login mit: `sven` / (dein Passwort)

**Mobile:**
- Finde deine lokale IP: `ip addr show` oder `ifconfig`
- Browser: http://[DEINE-IP]:3002
- Login und "Zum Startbildschirm hinzufügen"

## ✅ System testen

### Test 1: Anmeldung

```bash
# Auth Service testen
curl -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "sven", "password": "IhrPasswort"}'

# Erwartete Antwort:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer"
# }
```

### Test 2: Konversation erstellen

```bash
# Token aus Schritt 1 verwenden
TOKEN="eyJ..."

curl -X POST http://localhost:8003/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Gespräch", "zone": "FAMILY_PRIVATE"}'
```

### Test 3: Nachricht senden

```bash
CONV_ID="uuid-hier"

curl -X POST http://localhost:8003/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hallo Kirobi!"}'
```

## 📱 Familie onboarden

### Für Samira:
1. PWA öffnen: http://[IP]:3002
2. Login: `samira` / (Passwort)
3. Kurze Einführung geben
4. Erstes Gespräch starten: "Hallo, ich bin Samira!"

### Für Sineo:
1. PWA öffnen (am besten auf Smartphone)
2. Login: `sineo` / (Passwort)
3. "Zum Startbildschirm hinzufügen"
4. Erstes Gespräch: "Hey Kirobi, ich brauche Content-Ideen!"

## 🔧 Troubleshooting

### Services starten nicht?

```bash
# Logs ansehen
docker-compose logs auth
docker-compose logs api
docker-compose logs web

# Container neu bauen
docker-compose build --no-cache auth api web
docker-compose up -d
```

### Datenbank-Fehler?

```bash
# Schema-Status prüfen
docker-compose exec postgres psql -U kirobi -d kirobi -c "\dt"

# Sollte zeigen:
# - users
# - zone_permissions
# - conversations
# - messages
# - file_uploads
# - etc.

# Wenn nicht, Schema erneut laden:
docker-compose exec -T postgres psql -U kirobi -d kirobi < infra/db/schema/001_family_profiles.sql
```

### PWA installiert sich nicht?

1. HTTPS verwenden (oder localhost)
2. Manifest.json erreichbar? → http://localhost:3002/manifest.json
3. Service Worker registriert? → DevTools → Application → Service Workers
4. Browser unterstützt PWA? (Chrome, Edge, Safari, Firefox)

### Mobile zeigt "Verbindungsfehler"?

```bash
# Firewall-Regel prüfen
sudo ufw allow 3002/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 8003/tcp

# Oder alle Docker-Ports
sudo ufw allow from 192.168.0.0/16
```

## 🎉 Erfolg!

Wenn alles funktioniert, solltest du:

- ✅ PWA im Browser geöffnet haben
- ✅ Anmeldung erfolgreich
- ✅ Erste Nachricht an Kirobi gesendet
- ✅ Antwort von Kirobi erhalten
- ✅ Datei-Upload funktioniert
- ✅ Mobile Geräte können sich verbinden

## 📞 Support

Bei Problemen:
1. Logs prüfen: `docker-compose logs -f`
2. README lesen: `docs/FAMILY-PROFILES-SYSTEM.md`
3. Issue erstellen: GitHub Issues

---

**Viel Erfolg und eine tolle erste Familieninteraktion mit Kirobi! 🎊**
