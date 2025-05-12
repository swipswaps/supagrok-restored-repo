#!/usr/bin/env bash
# Comprehensive Supabase Docker Compose fix script
# This script resolves common issues with Supabase Docker Compose setup

set -euo pipefail

echo "🚀 Starting Supabase Docker Compose fix script..."

# Stop and remove all existing containers
echo "🧹 Cleaning up Docker environment..."
docker-compose down -v --remove-orphans 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Create required directories
echo "📁 Creating required directories..."
mkdir -p volumes/storage
mkdir -p volumes/pooler
mkdir -p volumes/functions
mkdir -p volumes/functions/main

# Create PostgreSQL config file
echo "📄 Creating PostgreSQL config file..."
cat > volumes/db/postgresql.conf <<EOF
# Basic PostgreSQL configuration file
listen_addresses = '*'
max_connections = 100
shared_buffers = 128MB
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

# Create a basic Edge Function main file
echo "📄 Creating a basic Edge Function main file..."
cat > volumes/functions/main/index.ts <<EOF
// Basic Edge Function
export const handler = async (req: Request) => {
  return new Response(JSON.stringify({ message: "Hello from Edge Functions!" }), {
    headers: { "Content-Type": "application/json" }
  });
};
EOF

# Backup original files
echo "💾 Backing up original files..."
if [ ! -f docker-compose.yml.original ]; then
  cp docker-compose.yml docker-compose.yml.original
fi
if [ ! -f .env.original ]; then
  cp .env .env.original
fi

# Update .env file with correct values
echo "🔑 Updating environment variables..."
sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env
sed -i 's/your_logflare_api_key/logflare_api_key_placeholder/g' .env
sed -i 's/your_vault_enc_key/vault_enc_key_placeholder/g' .env
sed -i 's/your_tenant_id/default/g' .env

# Fix docker.sock volume mount in docker-compose.yml
echo "🔧 Fixing docker.sock volume mount..."
sed -i 's|.*- .*docker\.sock.*docker\.sock.*|      - /var/run/docker.sock:/var/run/docker.sock:ro,z|g' docker-compose.yml

# Add postgresql.conf mount to docker-compose.yml if not already present
echo "🔧 Adding postgresql.conf mount to docker-compose.yml..."
if ! grep -q "postgresql.conf:/etc/postgresql/postgresql.conf" docker-compose.yml; then
  sed -i '/db-config:/i\      - ./volumes/db/postgresql.conf:/etc/postgresql/postgresql.conf:Z' docker-compose.yml
fi

# Remove dependency on vector container to avoid circular dependency
echo "🔧 Removing circular dependency in docker-compose.yml..."
sed -i '/depends_on:/,/condition: service_healthy/d' docker-compose.yml

# Set proper permissions on newly created directories
echo "🔒 Setting proper permissions on directories..."
chmod 755 volumes/storage volumes/pooler volumes/functions 2>/dev/null || true

# Start the services
echo "🚀 Starting Supabase services..."
docker-compose up -d db

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Create database roles
echo "🔧 Creating PostgreSQL roles..."
docker exec -i supabase-db psql -U postgres <<EOF
-- Create supabase_admin role
CREATE ROLE supabase_admin WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';
ALTER ROLE supabase_admin WITH SUPERUSER;

-- Create authenticator role
CREATE ROLE authenticator WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';

-- Create supabase_storage_admin role
CREATE ROLE supabase_storage_admin WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';

-- Create other required roles
CREATE ROLE anon;
CREATE ROLE authenticated;
CREATE ROLE service_role;

-- Grant permissions
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;
GRANT service_role TO supabase_admin;
EOF

# Start the remaining services
echo "🚀 Starting remaining services..."
docker-compose up -d

echo "✅ Fix completed! Supabase services should now be running."
echo "🔍 Check container status with: docker ps"
echo "🌐 Access Supabase Studio at: http://localhost:8000"
echo "📊 Access Analytics at: http://localhost:4000"