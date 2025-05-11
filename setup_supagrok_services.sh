#!/usr/bin/env bash
# PRF-compliant SUPAGROK service setup on IONOS

set -euo pipefail

# 1. Install Docker if not present
if ! command -v docker &>/dev/null; then
  sudo apt update
  sudo apt install -y docker.io
  sudo systemctl enable --now docker
fi

# 2. Start n8n (example, adjust as needed)
docker run -d --name n8n -p 5678:5678 -v ~/n8n_data:/home/node/.n8n n8nio/n8n

# 3. Start Supabase (example, adjust as needed)
if [ ! -f docker-compose.yml ]; then
  curl -o docker-compose.yml https://raw.githubusercontent.com/supabase/supabase/develop/docker/docker-compose.yml
fi
docker compose up -d

# 4. (Add Crawl4AI, Gemini, ChatGPT setup as needed)
# Example placeholder:
# ./install_crawl4ai.sh
# ./configure_gemini.sh
# ./configure_chatgpt.sh

echo "🎉 SUPAGROK core services setup complete. Please configure API keys and test integrations."