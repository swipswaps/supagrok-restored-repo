#!/usr/bin/env bash
# Script to add database performance services (connection pooling)

set -euo pipefail

echo "🔧 Adding database performance services..."

# Check if core services are running
db_running=$(docker-compose ps db | grep "Up" || echo "")

if [ -z "$db_running" ]; then
  echo "❌ Error: Database service must be running first."
  echo "Please run this command first:"
  echo "  docker-compose up -d db"
  exit 1
fi

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.before_performance

# Create required directory for pgbouncer
echo "Creating pgbouncer directory if it doesn't exist..."
mkdir -p ./volumes/pgbouncer

# Create basic PgBouncer configuration
echo "Creating basic PgBouncer configuration file..."
cat > ./volumes/pgbouncer/pgbouncer.ini <<EOF
[databases]
postgres = host=\${POSTGRES_HOST} port=\${POSTGRES_PORT} dbname=postgres user=postgres password=\${POSTGRES_PASSWORD}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
server_reset_query = DISCARD ALL
max_client_conn = \${POOLER_MAX_CLIENT_CONN}
default_pool_size = \${POOLER_DEFAULT_POOL_SIZE}
ignore_startup_parameters = extra_float_digits
EOF

# Create userlist file for pgbouncer authentication
echo "Creating user authentication list for PgBouncer..."
cat > ./volumes/pgbouncer/userlist.txt <<EOF
"postgres" "md5$(echo -n "md5\${POSTGRES_PASSWORD}postgres" | md5sum | cut -d ' ' -f 1)"
EOF

# Add pgbouncer service
echo "📄 Adding pgbouncer service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  pgbouncer:
    container_name: supabase-pgbouncer
    image: bitnami/pgbouncer:1.20.1
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      POSTGRESQL_HOST: \${POSTGRES_HOST}
      POSTGRESQL_PORT: \${POSTGRES_PORT}
      POSTGRESQL_USERNAME: postgres
      POSTGRESQL_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRESQL_DATABASE: postgres
      POSTGRESQL_MD5_PASSWORD_ENCODED: "false"
      PGBOUNCER_PORT: 6432
      PGBOUNCER_DATABASE: postgres
      PGBOUNCER_MAX_CLIENT_CONN: \${POOLER_MAX_CLIENT_CONN}
      PGBOUNCER_DEFAULT_POOL_SIZE: \${POOLER_DEFAULT_POOL_SIZE}
      PGBOUNCER_POOL_MODE: transaction
      PGBOUNCER_IGNORE_STARTUP_PARAMETERS: extra_float_digits
      PGBOUNCER_AUTH_TYPE: md5
      PGBOUNCER_ADMIN_USERS: postgres
      TENANT_ID: \${POOLER_TENANT_ID:-default}
    ports:
      - 6432:6432
    volumes:
      - ./volumes/pgbouncer/pgbouncer.ini:/bitnami/pgbouncer/conf/pgbouncer.ini:ro,z
      - ./volumes/pgbouncer/userlist.txt:/bitnami/pgbouncer/conf/userlist.txt:ro,z
    healthcheck:
      test: ["CMD-SHELL", "PGPASSWORD=\${POSTGRES_PASSWORD} psql -h 127.0.0.1 -p 6432 -U postgres -c '\\l'"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF

echo "✅ Added pgbouncer service to docker-compose.yml"
echo ""
echo "Starting pgbouncer service..."
docker-compose up -d pgbouncer

echo "Waiting for pgbouncer to become healthy (15 seconds)..."
sleep 15

# Add vault service
echo "📄 Adding vault service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  vault:
    container_name: supabase-vault
    image: supabase/vault:v0.1.0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    ports:
      - 8100:8100
    environment:
      VAULT_DB_ENCRYPTION_KEY: \${VAULT_ENC_KEY}
      VAULT_DB_URL: postgresql://supabase_admin:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/postgres
      VAULT_HTTP_HOST: 0.0.0.0
      VAULT_HTTP_PORT: 8100
      VAULT_JWT_CLAIM_NAMESPACE: vault
      VAULT_JWT_SECRET: \${JWT_SECRET}
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8100/health"]
      interval: 5s
      timeout: 5s
      retries: 3
EOF

echo "✅ Added vault service to docker-compose.yml"
echo ""
echo "Starting vault service..."
docker-compose up -d vault

echo "Waiting for vault to become healthy (15 seconds)..."
sleep 15

echo ""
echo "✅ Database performance services added successfully."
echo ""
echo "You can now check the status of all services with:"
echo "docker-compose ps"
echo ""
echo "To connect to the database through the connection pool:"
echo "  Host: localhost"
echo "  Port: 6432"
echo "  User: postgres"
echo "  Password: (from POSTGRES_PASSWORD in .env file)"
echo "  Database: postgres"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi