#!/usr/bin/env bash
# Script to incrementally add the remaining Supabase services
# Run this after db and vector are running successfully

set -euo pipefail

echo "🔧 Adding remaining Supabase services incrementally..."

# Check if db and vector are running
db_running=$(docker-compose ps db | grep "Up" || echo "")
vector_running=$(docker-compose ps vector | grep "Up" || echo "")

if [ -z "$db_running" ] || [ -z "$vector_running" ]; then
  echo "❌ Error: Database and vector must be running first."
  echo "Please run these commands first:"
  echo "  docker-compose up -d db"
  echo "  docker-compose up -d vector"
  exit 1
fi

# Create a more complete docker-compose.yml with analytics service
echo "📄 Adding analytics service to docker-compose.yml..."

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.working

# Update docker-compose.yml to include analytics service
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
    ports:
      - "9001:9001"

  analytics:
    container_name: supabase-analytics
    image: supabase/logflare:1.12.0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    ports:
      - 4000:4000
    healthcheck:
      test:
        [
          "CMD",
          "curl",
          "http://localhost:4000/health"
        ]
      timeout: 5s
      interval: 5s
      retries: 10
    environment:
      LOGFLARE_NODE_HOST: 127.0.0.1
      DB_USERNAME: supabase_admin
      DB_DATABASE: _supabase
      DB_HOSTNAME: \${POSTGRES_HOST}
      DB_PORT: \${POSTGRES_PORT}
      DB_PASSWORD: \${POSTGRES_PASSWORD}
      DB_SCHEMA: _analytics
      LOGFLARE_API_KEY: \${LOGFLARE_API_KEY}
      LOGFLARE_SINGLE_TENANT: "true"
      LOGFLARE_SUPABASE_MODE: "true"
      LOGFLARE_MIN_CLUSTER_SIZE: 1
      POSTGRES_BACKEND_URL: postgresql://supabase_admin:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/_supabase
      POSTGRES_BACKEND_SCHEMA: _analytics
      LOGFLARE_FEATURE_FLAG_OVERRIDE: multibackend=true

volumes:
  db-config:
EOF

echo "✅ Updated docker-compose.yml with analytics service"
echo ""
echo "Starting analytics service..."
docker-compose up -d analytics

echo "Waiting for analytics to become healthy (10 seconds)..."
sleep 10

# Check if analytics is running
analytics_running=$(docker-compose ps analytics | grep "Up" || echo "")
if [ -z "$analytics_running" ]; then
  echo "⚠️ Analytics service may not be fully healthy yet. You can check logs with:"
  echo "  docker logs supabase-analytics"
else
  echo "✅ Analytics service is running"
fi

echo ""
echo "You can now add more services incrementally, for example:"
echo ""
echo "# To add auth service:"
echo "docker-compose -f docker-compose.yml.original -p supabase_auth up -d auth"
echo ""
echo "# To add rest service:"
echo "docker-compose -f docker-compose.yml.original -p supabase_rest up -d rest"
echo ""
echo "# Etc."
echo ""
echo "This approach lets you add services one by one to identify any issues."
echo "When all essential services are running, you can restore the full docker-compose.yml"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi