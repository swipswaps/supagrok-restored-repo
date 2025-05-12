#!/usr/bin/env bash
# PRF-compliant one-shot fix for Supabase Docker Compose env and volume issues

set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# 1. Generate .env file with required variables (add more as needed)
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
POSTGRES_PASSWORD=changeme
JWT_SECRET=changeme
ANON_KEY=changeme
SERVICE_ROLE_KEY=changeme
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# Add other required variables here
EOF

  echo "✅ .env file created with placeholder values. Please update with secure secrets after first deploy."
else
  echo "✅ .env file already exists. Skipping creation."
fi

# 2. Patch docker-compose.yml for valid docker.sock volume (if needed)
if grep -q ':/var/run/docker.sock' "$COMPOSE_FILE"; then
  sed -i 's|:/var/run/docker.sock|/var/run/docker.sock:/var/run/docker.sock|g' "$COMPOSE_FILE"
  echo "✅ Patched docker-compose.yml for valid Docker socket volume."
else
  echo "ℹ️  No docker.sock volume issue found in docker-compose.yml."
fi

echo "🎉 One-shot fix complete. Re-run ./supagrok_deploy.sh for a clean deployment."