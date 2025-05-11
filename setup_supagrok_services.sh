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

# 4. Start Supabase (example, adjust as needed)
if [ ! -f docker-compose.yml ]; then
  curl -o docker-compose.yml https://raw.githubusercontent.com/supabase/supabase/master/docker/docker-compose.yml
fi
docker compose up -d

# 5. (Add Crawl4AI, Gemini, ChatGPT setup as needed)
# Example placeholder:
# ./install_crawl4ai.sh

echo "🎉 SUPAGROK core services setup complete. Please configure API keys and test integrations."