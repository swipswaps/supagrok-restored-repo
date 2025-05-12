#!/usr/bin/env bash
# Script to use the official Supabase docker-compose.yml with our fixes

set -euo pipefail

echo "🔄 Using official Supabase docker-compose.yml..."

# Stop all running containers
echo "🧹 Cleaning up Docker environment..."
docker-compose down -v --remove-orphans 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Save our current docker-compose.yml as a backup
mv docker-compose.yml docker-compose.yml.bak

# Use the official docker-compose.yml
cp docker-compose.yml.official docker-compose.yml
echo "✅ Using official docker-compose.yml"

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

# Update .env file with correct values
echo "🔑 Updating environment variables..."
sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env
sed -i 's/your_logflare_api_key/logflare_api_key_placeholder/g' .env
sed -i 's/your_vault_enc_key/vault_enc_key_placeholder/g' .env
sed -i 's/your_tenant_id/default/g' .env

# Fix docker.sock volume mount in docker-compose.yml if needed
echo "🔧 Fixing docker.sock volume mount if needed..."
if grep -q ':/var/run/docker.sock' docker-compose.yml; then
  sed -i 's|:/var/run/docker.sock|/var/run/docker.sock:/var/run/docker.sock|g' docker-compose.yml
fi

# Add postgresql.conf mount to docker-compose.yml if needed
echo "🔧 Adding postgresql.conf mount if needed..."
if ! grep -q "postgresql.conf:/etc/postgresql/postgresql.conf" docker-compose.yml; then
  sed -i '/db-config:/i\      - ./volumes/db/postgresql.conf:/etc/postgresql/postgresql.conf:Z' docker-compose.yml
fi

# Remove circular dependency in docker-compose.yml if it exists
echo "🔧 Removing any circular dependencies..."
if grep -q 'depends_on:.*vector.*condition: service_healthy' docker-compose.yml; then
  sed -i '/depends_on:/,/condition: service_healthy/d' docker-compose.yml
fi

# Set proper permissions on newly created directories
echo "🔒 Setting proper permissions on directories..."
chmod 755 volumes/storage volumes/pooler volumes/functions 2>/dev/null || true

echo "✅ Preparations complete!"
echo ""
echo "🚀 To start all services, run:"
echo "  docker-compose up -d"
echo ""
echo "⚠️ After the services start, run the following command to create database roles:"
echo "  ./create_db_roles.sh"
echo ""
echo "🌐 When all services are running, you can access:"
echo "  - Supabase Studio: http://localhost:8000"
echo "  - Analytics: http://localhost:4000"