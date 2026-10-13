#!/bin/bash
set -e

DB_URL="${DATABASE_URL:-postgresql://shortener_user:shortener_password@localhost:5432/shortener_url}"

echo "⚠️  Dropping all tables..."
psql "$DB_URL" << EOF
DROP TABLE IF EXISTS url_creation_throttle CASCADE;
DROP TABLE IF EXISTS failed_login_attempts CASCADE;
DROP TABLE IF EXISTS short_urls CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
EOF

echo "✅ All tables dropped"
