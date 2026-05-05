#!/bin/bash
# Kirobi Family Profiles - Schnellstart Setup Script
# Dieses Script richtet das Family Profiles System ein

set -e

echo "🎉 Willkommen beim Kirobi Family Profiles Setup!"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker läuft nicht. Bitte starte Docker und versuche es erneut."
    exit 1
fi

echo "✅ Docker ist aktiv"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Erstelle .env aus .env.example..."
    cp .env.example .env
    echo "⚠️  WICHTIG: Bitte .env bearbeiten und Secrets ändern!"
    echo "   Besonders: POSTGRES_PASSWORD, JWT_SECRET_KEY, OPENWEBUI_SECRET_KEY"
    read -p "   Drücke Enter wenn du bereit bist..."
fi

echo ""
echo "🚀 Starte PostgreSQL..."
docker-compose up -d postgres

echo "⏳ Warte auf PostgreSQL (15 Sekunden)..."
sleep 15

echo ""
echo "📊 Initialisiere Datenbank-Schema..."
docker-compose exec -T postgres psql -U kirobi -d kirobi < infra/db/schema/001_family_profiles.sql

if [ $? -eq 0 ]; then
    echo "✅ Datenbank-Schema erfolgreich erstellt!"
else
    echo "❌ Fehler beim Erstellen des Schemas. Bitte Logs prüfen."
    exit 1
fi

echo ""
echo "🔐 Erstelle Standard-Benutzer mit Passwort-Hashes..."

# Generate password hashes using Python
docker run --rm python:3.11-slim bash -c "
pip install passlib[bcrypt] -q && python3 << 'EOF'
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
password = 'kirobi2024'
print(pwd_context.hash(password))
EOF
" > /tmp/kirobi_hash.txt

HASH=$(cat /tmp/kirobi_hash.txt)
rm /tmp/kirobi_hash.txt

# Update passwords in database
docker-compose exec -T postgres psql -U kirobi -d kirobi << EOF
UPDATE users SET password_hash = '$HASH' WHERE username = 'sven';
UPDATE users SET password_hash = '$HASH' WHERE username = 'samira';
UPDATE users SET password_hash = '$HASH' WHERE username = 'sineo';
EOF

echo "✅ Standard-Passwort 'kirobi2024' gesetzt für alle Benutzer"
echo "⚠️  WICHTIG: Passwörter nach dem ersten Login ändern!"

echo ""
echo "🏗️  Baue Services..."
docker-compose build auth api web

echo ""
echo "🚀 Starte alle Services..."
docker-compose up -d auth api web

echo ""
echo "⏳ Warte auf Service-Start (10 Sekunden)..."
sleep 10

echo ""
echo "🔍 Service-Status:"
docker-compose ps auth api web

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "📱 Nächste Schritte:"
echo ""
echo "1. Öffne die PWA im Browser:"
echo "   → http://localhost:3002"
echo ""
echo "2. Melde dich an:"
echo "   - Sven:   sven / kirobi2024"
echo "   - Samira: samira / kirobi2024"
echo "   - Sineo:  sineo / kirobi2024"
echo ""
echo "3. Passwörter sofort ändern! (TODO: UI noch nicht fertig)"
echo ""
echo "4. Mobile Zugriff (finde deine IP mit 'ip addr'):"
echo "   → http://[DEINE-IP]:3002"
echo ""
echo "📚 Dokumentation:"
echo "   - docs/FAMILY-PROFILES-SYSTEM.md"
echo "   - docs/QUICKSTART-FAMILY.md"
echo ""
echo "🐛 Bei Problemen:"
echo "   docker-compose logs -f auth api web"
echo ""
echo "🎊 Viel Spaß mit Kirobi!"
