#!/bin/bash
# Kirobi Family Profiles - Database Initialization Script
# Zone: WORKSPACE
# Purpose: Initialize database schema and create default family profiles

set -e

echo "🚀 Initializing Kirobi Family Profiles Database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-kirobi}; do
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run database schema
echo "📊 Creating database schema..."
PGPASSWORD=${POSTGRES_PASSWORD:-changeme} psql -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-kirobi} -d ${POSTGRES_DB:-kirobi} -f /schema/001_family_profiles.sql

echo "👥 Creating default family member accounts..."

# Create default passwords (should be changed on first login)
DEFAULT_PASSWORD="kirobi2024"  # This will be hashed

# Note: The SQL schema already creates the users with INSERT ON CONFLICT DO NOTHING
# So we just need to update passwords if needed

echo "✅ Database initialization complete!"
echo ""
echo "📝 Default accounts created:"
echo "   - Username: sven (Admin)"
echo "   - Username: samira (Family Member)"
echo "   - Username: sineo (Family Member)"
echo ""
echo "⚠️  IMPORTANT: Default password for all accounts: $DEFAULT_PASSWORD"
echo "   Please change passwords immediately after first login!"
echo ""
echo "🎉 Family profiles are ready to use!"
