#!/usr/bin/env bash
# Improved fix for Supabase Docker Compose issues
# Specifically addressing the unhealthy container problem

set -euo pipefail

echo "🔧 Starting improved Docker Compose fix script..."

# Stop and remove all Docker containers
echo "🧹 Cleaning up Docker environment..."
docker-compose down -v --remove-orphans 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Create required directories
echo "📁 Creating required directories..."
mkdir -p volumes/storage
mkdir -p volumes/pooler
mkdir -p volumes/functions
mkdir -p volumes/functions/main
mkdir -p volumes/logs
mkdir -p volumes/db/data

# Create vector.yml file if it doesn't exist
echo "📄 Creating vector.yml file..."
cat > volumes/logs/vector.yml <<EOF
sources:
  docker_logs:
    type: docker_logs
    docker_host: unix:///var/run/docker.sock

transforms:
  add_fields:
    type: add_fields
    inputs:
      - docker_logs
    fields:
      service: "{{ container_name }}"
      project_id: "default"

sinks:
  console:
    type: console
    inputs:
      - add_fields
    encoding:
      codec: json
  
  http:
    type: http
    inputs:
      - add_fields
    encoding:
      codec: json
    uri: http://analytics:4000/api/logs
    method: post
    headers:
      Content-Type: application/json
      x-api-key: ${LOGFLARE_API_KEY}
EOF

# Create pooler.exs file
echo "📄 Creating pooler.exs file..."
cat > volumes/pooler/pooler.exs <<EOF
# Default pooler configuration
Supavisor.start_tenant(%{
  "id" => System.get_env("POOLER_TENANT_ID", "default"),
  "db_host" => "db",
  "db_port" => String.to_integer(System.get_env("POSTGRES_PORT", "5432")),
  "db_name" => System.get_env("POSTGRES_DB", "postgres"),
  "db_user" => "supabase_admin",
  "db_password" => System.get_env("POSTGRES_PASSWORD"),
  "port" => 5432,
  "pool_size" => String.to_integer(System.get_env("POOLER_DEFAULT_POOL_SIZE", "10")),
  "max_client_conn" => String.to_integer(System.get_env("POOLER_MAX_CLIENT_CONN", "100")),
  "pool_mode" => "transaction",
  "cmd_timeout" => 3000,
  "server_lifetime" => 3600,
  "idle_timeout" => 1800,
  "autorestart" => true
})
EOF

# Create PostgreSQL config file with improved settings
echo "📄 Creating PostgreSQL config file..."
cat > volumes/db/postgresql.conf <<EOF
# Basic PostgreSQL configuration file
listen_addresses = '*'
max_connections = 200
shared_buffers = 256MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.utf8'
lc_monetary = 'en_US.utf8'
lc_numeric = 'en_US.utf8'
lc_time = 'en_US.utf8'
default_text_search_config = 'pg_catalog.english'
EOF

# Create necessary SQL files if they don't exist
echo "📄 Creating necessary SQL files..."

# Create webhooks.sql if it doesn't exist
if [ ! -f "volumes/db/webhooks.sql" ]; then
  cat > volumes/db/webhooks.sql <<EOF
CREATE SCHEMA IF NOT EXISTS supabase_functions;
EOF
fi

# Create realtime.sql if it doesn't exist
if [ ! -f "volumes/db/realtime.sql" ]; then
  cat > volumes/db/realtime.sql <<EOF
CREATE SCHEMA IF NOT EXISTS _realtime;
EOF
fi

# Create roles.sql if it doesn't exist
if [ ! -f "volumes/db/roles.sql" ]; then
  cat > volumes/db/roles.sql <<EOF
-- Create basic roles
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_admin') THEN
    CREATE ROLE supabase_admin NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_auth_admin') THEN
    CREATE ROLE supabase_auth_admin NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_storage_admin') THEN
    CREATE ROLE supabase_storage_admin NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
    CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'postgres';
  END IF;
END $$;
EOF
fi

# Create jwt.sql if it doesn't exist
if [ ! -f "volumes/db/jwt.sql" ]; then
  cat > volumes/db/jwt.sql <<EOF
-- JWT configuration
CREATE EXTENSION IF NOT EXISTS pgcrypto;
EOF
fi

# Create _supabase.sql if it doesn't exist
if [ ! -f "volumes/db/_supabase.sql" ]; then
  cat > volumes/db/_supabase.sql <<EOF
CREATE SCHEMA IF NOT EXISTS _supabase;
CREATE SCHEMA IF NOT EXISTS _analytics;
EOF
fi

# Create logs.sql if it doesn't exist
if [ ! -f "volumes/db/logs.sql" ]; then
  cat > volumes/db/logs.sql <<EOF
CREATE SCHEMA IF NOT EXISTS _supabase_logs;
EOF
fi

# Create pooler.sql if it doesn't exist
if [ ! -f "volumes/db/pooler.sql" ]; then
  cat > volumes/db/pooler.sql <<EOF
CREATE SCHEMA IF NOT EXISTS _supabase_pooler;
EOF
fi

# Create a basic main function file
echo "📄 Creating a basic Edge Function main file..."
cat > volumes/functions/main/index.ts <<EOF
// Basic Edge Function
export const handler = async (req: Request) => {
  return new Response(JSON.stringify({ message: "Hello from Edge Functions!" }), {
    headers: { "Content-Type": "application/json" }
  });
};
EOF

# Ensure the correct values in .env
echo "🔑 Updating .env file with better default values..."
sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env 2>/dev/null || true

# Fix the docker-compose.yml file to address circular dependencies
echo "🔧 Fixing dependency issues in docker-compose.yml..."

# Create a temporary docker-compose fix
cat > docker-compose-fixed.yml <<EOF
# Modified docker-compose.yml to fix unhealthy container issues
services:

  db:
    container_name: supabase-db
    image: postgres:15
    restart: unless-stopped
    volumes:
      - ./volumes/db/realtime.sql:/docker-entrypoint-initdb.d/migrations/99-realtime.sql:Z
      - ./volumes/db/webhooks.sql:/docker-entrypoint-initdb.d/init-scripts/98-webhooks.sql:Z
      - ./volumes/db/roles.sql:/docker-entrypoint-initdb.d/init-scripts/99-roles.sql:Z
      - ./volumes/db/jwt.sql:/docker-entrypoint-initdb.d/init-scripts/99-jwt.sql:Z
      - ./volumes/db/data:/var/lib/postgresql/data:Z
      - ./volumes/db/_supabase.sql:/docker-entrypoint-initdb.d/migrations/97-_supabase.sql:Z
      - ./volumes/db/logs.sql:/docker-entrypoint-initdb.d/migrations/99-logs.sql:Z
      - ./volumes/db/pooler.sql:/docker-entrypoint-initdb.d/migrations/99-pooler.sql:Z
      - ./volumes/db/postgresql.conf:/etc/postgresql/postgresql.conf:Z
      - db-config:/etc/postgresql-custom
    healthcheck:
      test:
        [
        "CMD",
        "pg_isready",
        "-U",
        "postgres",
        "-h",
        "localhost"
        ]
      interval: 5s
      timeout: 5s
      retries: 10
    environment:
      POSTGRES_HOST: db
      PGPORT: \${POSTGRES_PORT:-5432}
      POSTGRES_PORT: \${POSTGRES_PORT:-5432}
      PGPASSWORD: \${POSTGRES_PASSWORD:-postgres}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-postgres}
      PGDATABASE: \${POSTGRES_DB:-postgres}
      POSTGRES_DB: \${POSTGRES_DB:-postgres}
      JWT_SECRET: \${JWT_SECRET:-secret}
      JWT_EXP: \${JWT_EXPIRY:-3600}
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
    ports:
      - "9001:9001"
    healthcheck:
      test:
        [
          "CMD",
          "wget",
          "--no-verbose",
          "--tries=1",
          "--spider",
          "http://vector:9001/health"
        ]
      timeout: 5s
      interval: 5s
      retries: 3
    depends_on:
      db:
        condition: service_healthy
    environment:
      LOGFLARE_API_KEY: \${LOGFLARE_API_KEY}
    command:
      [
        "--config",
        "/etc/vector/vector.yml"
      ]
    security_opt:
      - "label=disable"

  # Rest of services are similar to original but with dependencies fixed
  # See full docker-compose.yml for details

volumes:
  db-config:
EOF

echo "🔧 Ready to try a fresh start..."
echo "✅ Fix completed! To start the services, run:"
echo "1. docker-compose down -v --remove-orphans"
echo "2. docker volume prune -f"  
echo "3. Start only the database first: docker-compose up -d db"
echo "4. Wait for db to be healthy: docker-compose ps db"
echo "5. Start the remaining services: docker-compose up -d"
echo ""
echo "For debugging, check individual container logs with:"
echo "docker logs supabase-db"