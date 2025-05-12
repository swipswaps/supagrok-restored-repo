#!/usr/bin/env bash
# Fix YAML structure issues in docker-compose.yml
# This script handles the specific error with depends_on format

set -euo pipefail

echo "🔧 Fixing YAML structure in docker-compose.yml..."

# Make a backup of the original docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml.original" ]; then
  cp docker-compose.yml docker-compose.yml.original
  echo "✅ Created backup at docker-compose.yml.original"
fi

# Create a minimal docker-compose.yml that should work
cat > docker-compose.yml <<EOF
# Usage
#   Start:              docker compose up
#   With helpers:       docker compose -f docker-compose.yml -f ./dev/docker-compose.dev.yml up
#   Stop:               docker compose down
#   Destroy:            docker compose -f docker-compose.yml -f ./dev/docker-compose.dev.yml down -v --remove-orphans
#   Reset everything:  ./reset.sh

services:
  db:
    container_name: supabase-db
    image: postgres:15
    restart: unless-stopped
    volumes:
      - ./volumes/db/data:/var/lib/postgresql/data:Z
      - ./volumes/db/postgresql.conf:/etc/postgresql/postgresql.conf:Z
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 10
    environment:
      POSTGRES_HOST: db
      POSTGRES_PORT: \${POSTGRES_PORT:-5432}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: \${POSTGRES_DB:-postgres}
      JWT_SECRET: \${JWT_SECRET:-secret}
    command:
      [
        "postgres",
        "-c",
        "config_file=/etc/postgresql/postgresql.conf"
      ]
    ports:
      - 5433:5432

  vector:
    container_name: supabase-vector
    image: timberio/vector:0.28.1-alpine
    restart: unless-stopped
    volumes:
      - ./volumes/logs/vector.yml:/etc/vector/vector.yml:ro,z
      - /var/run/docker.sock:/var/run/docker.sock:ro,z
    depends_on:
      db:
        condition: service_healthy
    command:
      [
        "--config",
        "/etc/vector/vector.yml"
      ]

volumes:
  db-config:
EOF

echo "✅ Created simplified docker-compose.yml with correct structure"
echo ""
echo "To test the database connection, run:"
echo "docker-compose up -d db"
echo ""
echo "If the database starts successfully, you can continue with:"
echo "docker-compose up -d vector"
echo ""
echo "Would you like to start the database now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  echo "Starting database..."
  docker-compose down -v --remove-orphans
  docker-compose up -d db
  
  echo "Checking database status..."
  sleep 5
  docker-compose ps db
  
  echo ""
  echo "If the database is healthy, you can continue with vector:"
  echo "docker-compose up -d vector"
else
  echo "You can manually start the database with: docker-compose up -d db"
fi