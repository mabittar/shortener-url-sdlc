#!/bin/bash
set -e

DB_URL="${DATABASE_URL:-postgresql://shortener_user:shortener_password@localhost:5432/shortener_url}"

echo "🔄 Running migrations..."
psql "$DB_URL" -f sql/schema/001_initial_schema.sql

echo "✅ Migrations complete"
