#!/usr/bin/env bash
# Script to add API gateway and realtime services after the core services

set -euo pipefail

echo "🔧 Adding API gateway and realtime services..."

# Check if core services are running
rest_running=$(docker-compose ps rest | grep "Up" || echo "")
functions_running=$(docker-compose ps functions | grep "Up" || echo "")
storage_running=$(docker-compose ps storage | grep "Up" || echo "")
auth_running=$(docker-compose ps auth | grep "Up" || echo "")

if [ -z "$rest_running" ] || [ -z "$functions_running" ] || [ -z "$storage_running" ] || [ -z "$auth_running" ]; then
  echo "❌ Error: Core services (rest, functions, storage, auth) must be running first."
  echo "Please run this command first:"
  echo "  ./add_core_services.sh"
  exit 1
fi

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.with_core_services

# Add realtime service
echo "📄 Adding realtime service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  realtime:
    container_name: supabase-realtime
    image: supabase/realtime:v2.21.0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      PORT: 4000
      DB_HOST: \${POSTGRES_HOST}
      DB_PORT: \${POSTGRES_PORT}
      DB_USER: supabase_admin
      DB_PASSWORD: \${POSTGRES_PASSWORD}
      DB_NAME: postgres
      DB_AFTER_CONNECT_QUERY: 'SET search_path TO _realtime'
      DB_ENC_KEY: supabase_realtime_encryption_key
      API_JWT_SECRET: \${JWT_SECRET}
      FLY_ALLOC_ID: fly123
      FLY_APP_NAME: realtime
      SECRET_KEY_BASE: \${SECRET_KEY_BASE}
      ERL_AFLAGS: -proto_dist inet_tcp
      ENABLE_TAILSCALE: "false"
      DNS_NODES: "''"
    command:
      - "sh"
      - "-c"
      - "sleep 5 && /app/bin/migrate && /app/bin/realtime eval 'Realtime.Release.seeds(Realtime.Repo)' && /app/bin/server"
    ports:
      - 4000:4000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 5s
      timeout: 5s
      retries: 10
EOF

echo "✅ Added realtime service to docker-compose.yml"
echo ""
echo "Starting realtime service..."
docker-compose up -d realtime

echo "Waiting for realtime to become healthy (15 seconds)..."
sleep 15

# Add meta service
echo "📄 Adding meta service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  meta:
    container_name: supabase-meta
    image: supabase/postgres-meta:v0.69.0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      PG_META_PORT: 8080
      PG_META_DB_HOST: \${POSTGRES_HOST}
      PG_META_DB_PORT: \${POSTGRES_PORT}
      PG_META_DB_NAME: postgres
      PG_META_DB_USER: supabase_admin
      PG_META_DB_PASSWORD: \${POSTGRES_PASSWORD}
    ports:
      - 8080:8080
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 5s
      timeout: 5s
      retries: 6
EOF

echo "✅ Added meta service to docker-compose.yml"
echo ""
echo "Starting meta service..."
docker-compose up -d meta

echo "Waiting for meta to become healthy (15 seconds)..."
sleep 15

# Add kong service
echo "📄 Adding kong service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  kong:
    container_name: supabase-kong
    image: kong:2.8.1
    restart: unless-stopped
    ports:
      - 8000:8000/tcp
      - 8443:8443/tcp
    depends_on:
      db:
        condition: service_healthy
      auth:
        condition: service_healthy
      rest:
        condition: service_healthy
      realtime:
        condition: service_healthy
      storage:
        condition: service_healthy
      meta:
        condition: service_healthy
      functions:
        condition: service_healthy
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /var/lib/kong/kong.yml
      KONG_DNS_ORDER: LAST,A,CNAME
      KONG_PLUGINS: request-transformer,cors,key-auth,acl
    volumes:
      - ./volumes/kong/kong.yml:/var/lib/kong/kong.yml:ro,z
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 5s
      timeout: 5s
      retries: 10
EOF

echo "✅ Added kong service to docker-compose.yml"
echo ""

# Create required directory for Kong
echo "Creating kong configuration directory if it doesn't exist..."
mkdir -p ./volumes/kong

# Create basic Kong configuration
echo "Creating basic Kong configuration file..."
cat > ./volumes/kong/kong.yml <<EOF
_format_version: "3.0"
_transform: true

services:
  - name: auth-service
    url: http://auth:9999
    routes:
      - name: auth-route
        paths:
          - /auth
    plugins:
      - name: cors
  - name: rest-service
    url: http://rest:3000
    routes:
      - name: rest-route
        paths:
          - /rest
    plugins:
      - name: cors
  - name: realtime-service
    url: http://realtime:4000
    routes:
      - name: realtime-route
        paths:
          - /realtime
    plugins:
      - name: cors
  - name: storage-service
    url: http://storage:5000
    routes:
      - name: storage-route
        paths:
          - /storage
    plugins:
      - name: cors
  - name: meta-service
    url: http://meta:8080
    routes:
      - name: meta-route
        paths:
          - /meta
    plugins:
      - name: cors
  - name: functions-service
    url: http://functions:9090
    routes:
      - name: functions-route
        paths:
          - /functions
    plugins:
      - name: cors
EOF

echo "✅ Created Kong configuration"
echo ""
echo "Starting kong service..."
docker-compose up -d kong

echo "Waiting for kong to become healthy (15 seconds)..."
sleep 15

echo ""
echo "You can now check the status of all gateway services with:"
echo "docker-compose ps"
echo ""
echo "If all services are healthy, you can continue adding the remaining services like:"
echo "- studio"
echo "- imgproxy"
echo "- pgbouncer"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi