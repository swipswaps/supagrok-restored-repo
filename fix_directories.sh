#!/usr/bin/env bash
# Ensure all required directories and files exist for Supabase Docker Compose
# This script focuses ONLY on creating necessary files and directories

set -euo pipefail

echo "📁 Creating required directories and files for Supabase..."

# Create required directories
echo "📁 Creating base directories..."
mkdir -p volumes/storage
mkdir -p volumes/pooler
mkdir -p volumes/functions/main
mkdir -p volumes/logs
mkdir -p volumes/db/data

# Create vector.yml file if it doesn't exist
if [ ! -f "volumes/logs/vector.yml" ]; then
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
  echo "✅ Created vector.yml"
fi

# Create pooler.exs file if it doesn't exist
if [ ! -f "volumes/pooler/pooler.exs" ]; then
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
  echo "✅ Created pooler.exs"
fi

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
    echo "✅ Created $file"
  fi
done

# Create a basic main function file for edge functions if it doesn't exist
if [ ! -f "volumes/functions/main/index.ts" ]; then
  echo "📄 Creating Edge Function main file..."
  cat > volumes/functions/main/index.ts <<EOF
// Basic Edge Function
export const handler = async (req: Request) => {
  return new Response(JSON.stringify({ message: "Hello from Edge Functions!" }), {
    headers: { "Content-Type": "application/json" }
  });
};
EOF
  echo "✅ Created Edge Function main file"
fi

# Fix environment variables if .env exists
if [ -f ".env" ]; then
  echo "🔑 Checking environment variables..."
  if grep -q "POSTGRES_HOST=localhost" .env; then
    echo "Fixing POSTGRES_HOST in .env..."
    sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env
    echo "✅ Updated POSTGRES_HOST in .env"
  fi
fi

echo "✅ All required directories and files have been created."
echo ""
echo "Now run ./fix_circular_deps.sh to fix the circular dependencies in docker-compose.yml"
echo "and start the services in the correct order."