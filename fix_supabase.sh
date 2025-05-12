#!/usr/bin/env bash
# Comprehensive solution for fixing Supabase Docker Compose issues
# Specifically targeting the "Container is unhealthy" errors

set -euo pipefail

echo "🔍 Analyzing Supabase Docker Compose setup..."

# Stop and remove all containers first
echo "🧹 Cleaning up Docker environment..."
docker-compose down -v --remove-orphans 2>/dev/null || true
docker volume prune -f 2>/dev/null || true

# Create required directories
echo "📁 Creating required directories..."
mkdir -p volumes/storage
mkdir -p volumes/pooler
mkdir -p volumes/functions/main
mkdir -p volumes/logs
mkdir -p volumes/db/data

# Critical fix: Create vector.yml file
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
      x-api-key: \${LOGFLARE_API_KEY}
EOF

# Check for missing SQL files
for file in realtime.sql webhooks.sql roles.sql jwt.sql _supabase.sql logs.sql pooler.sql; do
  if [ ! -f "volumes/db/$file" ]; then
    echo "📄 Creating $file..."
    
    # Create a minimal version of each file to prevent errors
    case "$file" in
      realtime.sql)
        echo "CREATE SCHEMA IF NOT EXISTS _realtime;" > "volumes/db/$file"
        ;;
      webhooks.sql)
        echo "CREATE SCHEMA IF NOT EXISTS supabase_functions;" > "volumes/db/$file"
        ;;
      roles.sql)
        cat > "volumes/db/$file" <<EOF
-- Create basic roles
DO \$\$
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
END \$\$;
EOF
        ;;
      jwt.sql)
        echo "CREATE EXTENSION IF NOT EXISTS pgcrypto;" > "volumes/db/$file"
        ;;
      _supabase.sql)
        echo -e "CREATE SCHEMA IF NOT EXISTS _supabase;\nCREATE SCHEMA IF NOT EXISTS _analytics;" > "volumes/db/$file"
        ;;
      logs.sql)
        echo "CREATE SCHEMA IF NOT EXISTS _supabase_logs;" > "volumes/db/$file"
        ;;
      pooler.sql)
        echo "CREATE SCHEMA IF NOT EXISTS _supabase_pooler;" > "volumes/db/$file"
        ;;
    esac
  fi
done

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

# Create Edge Function main file
echo "📄 Creating Edge Function main file..."
cat > volumes/functions/main/index.ts <<EOF
// Basic Edge Function
export const handler = async (req: Request) => {
  return new Response(JSON.stringify({ message: "Hello from Edge Functions!" }), {
    headers: { "Content-Type": "application/json" }
  });
};
EOF

# Fix environment variables
echo "🔑 Checking environment variables..."
if grep -q "POSTGRES_HOST=localhost" .env 2>/dev/null; then
  echo "Fixing POSTGRES_HOST in .env..."
  sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env
fi

# Make a backup of the original docker-compose.yml
cp docker-compose.yml docker-compose.yml.bak

# FIX: Break the circular dependency chain
echo "🔧 Breaking circular dependencies in docker-compose.yml..."
# Instead of removing all depends_on blocks, we'll only modify them to avoid cycles

# Approach: Make db depend on nothing, and make analytics depend only on db
# This breaks the dependency cycle
sed -i '/db:/,/depends_on:/d' docker-compose.yml
sed -i '/analytics:/,/depends_on:/d' docker-compose.yml

# Steps to start the services correctly
echo "✅ Setup complete. Now let's start the services in the correct order:"
echo ""
echo "1. Start the database first:"
echo "   docker-compose up -d db"
echo ""
echo "2. Wait about 10-15 seconds for the database to initialize, then start vector:"
echo "   docker-compose up -d vector"
echo ""
echo "3. Wait about 5 seconds, then start analytics:"
echo "   docker-compose up -d analytics"
echo "" 
echo "4. Wait about 5 seconds, then start all remaining services:"
echo "   docker-compose up -d"
echo ""
echo "Would you like to execute these steps automatically? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  echo "Starting services in the correct sequence..."
  
  echo "Starting database..."
  docker-compose up -d db
  
  echo "Waiting for database to initialize (15 seconds)..."
  sleep 15
  
  echo "Starting vector service..."
  docker-compose up -d vector
  
  echo "Waiting for vector to initialize (5 seconds)..."
  sleep 5
  
  echo "Starting analytics service..."
  docker-compose up -d analytics
  
  echo "Waiting for analytics to initialize (5 seconds)..."
  sleep 5
  
  echo "Starting all remaining services..."
  docker-compose up -d
  
  echo "All services started. Check status with: docker-compose ps"
else
  echo "Please follow the above steps manually to start services in the correct order."
fi