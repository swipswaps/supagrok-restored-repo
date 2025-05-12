#!/usr/bin/env bash
# Script to download the official Supabase docker-compose.yml

set -euo pipefail

echo "🔍 Downloading official Supabase docker-compose.yml..."

# Backup existing docker-compose.yml
if [ -f "docker-compose.yml" ]; then
  cp docker-compose.yml docker-compose.yml.backup
  echo "💾 Backed up existing docker-compose.yml to docker-compose.yml.backup"
fi

# Download the official docker-compose.yml
curl -s https://raw.githubusercontent.com/supabase/supabase/master/docker/docker-compose.yml > docker-compose.yml.official

echo "✅ Downloaded official docker-compose.yml to docker-compose.yml.official"
echo ""
echo "🔄 To use the official file:"
echo "1. Rename it: mv docker-compose.yml.official docker-compose.yml"
echo "2. Apply our fixes with: ./fix_supabase_complete.sh"
echo "3. Start the services: docker-compose up -d"