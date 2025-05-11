#!/usr/bin/env bash
# PRF-compliant SUPAGROK service setup on IONOS

set -euo pipefail

# 1. Install Docker if not present
if ! command -v docker &>/dev/null; then
  sudo apt update
  sudo apt install -y docker.io
  sudo systemctl enable --now docker
fi

# 2. Stop and remove existing n8n container if it exists
if docker ps -a --format '{{.Names}}' | grep -Eq '^n8n$'; then
  docker stop n8n || true
  docker rm n8n || true
fi

# 3. Start n8n
docker run -d --name n8n -p 5678:5678 -v ~/n8n_data:/home/node/.n8n n8nio/n8n

# 4. Download Supabase docker-compose.yml if not present
if [ ! -f docker-compose.yml ]; then
  curl -o docker-compose.yml https://raw.githubusercontent.com/supabase/supabase/master/docker/docker-compose.yml
fi

# 5. Create .env file with required variables if not present
if [ ! -f .env ]; then
  cat > .env <<EOF
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
fi

# 6. Patch docker-compose.yml for valid docker.sock volume (if needed)
if grep -q ':/var/run/docker.sock' docker-compose.yml; then
  sed -i 's|:/var/run/docker.sock|/var/run/docker.sock:/var/run/docker.sock|g' docker-compose.yml
  echo "✅ Patched docker-compose.yml for valid Docker socket volume."
fi

# 7. Start Supabase
docker compose up -d

echo "🎉 SUPAGROK core services setup complete. Please configure API keys and test integrations."