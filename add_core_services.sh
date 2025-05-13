#!/usr/bin/env bash
# Script to incrementally add the core Supabase services after db, vector, and analytics

set -euo pipefail

echo "🔧 Adding remaining core Supabase services incrementally..."

# Check if db and analytics are running
db_running=$(docker-compose ps db | grep "Up" || echo "")
# analytics_running=$(docker-compose ps analytics | grep "Up" || echo "") # Analytics is commented out in docker-compose.yml

if [ -z "$db_running" ]; then # Only check if db is running
  echo "❌ Error: Database must be running first."
  echo "Please run this command first:"
  echo "  docker-compose up -d db"
  exit 1
fi
# Check for analytics is removed as it's commented out in docker-compose.yml

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.with_analytics

# Add storage service
echo "📄 Adding storage service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  storage:
    container_name: supabase-storage
    image: supabase/storage-api:v0.40.4
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      ANON_KEY: \${ANON_KEY}
      SERVICE_ROLE_KEY: \${SERVICE_ROLE_KEY}
      POSTGREST_URL: http://rest:3000
      PGRST_JWT_SECRET: \${JWT_SECRET}
      DATABASE_URL: postgresql://supabase_storage_admin:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/postgres
      FILE_SIZE_LIMIT: 52428800
      STORAGE_BACKEND: file
      FILE_STORAGE_BACKEND_PATH: /var/lib/storage
      TENANT_ID: 00000000-0000-0000-0000-000000000000
      REGION: auto
      GLOBAL_S3_BUCKET: storage
      ENABLE_IMAGE_TRANSFORMATION: "true"
      IMGPROXY_URL: http://imgproxy:5001
    volumes:
      - ./volumes/storage:/var/lib/storage
    ports:
      - 5000:5000
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:5000/status"]
      timeout: 5s
      interval: 5s
      retries: 3
EOF

echo "✅ Added storage service to docker-compose.yml"
echo ""
echo "Starting storage service..."
docker-compose up -d storage

echo "Waiting for storage to become healthy (10 seconds)..."
sleep 10

# Add auth service
echo "📄 Adding auth service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  auth:
    container_name: supabase-auth
    image: supabase/gotrue:v2.132.3
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      GOTRUE_API_HOST: 0.0.0.0
      GOTRUE_API_PORT: 9999
      API_EXTERNAL_URL: \${API_EXTERNAL_URL}
      GOTRUE_DB_DRIVER: postgres
      GOTRUE_DB_DATABASE_URL: postgresql://supabase_auth_admin:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/postgres
      GOTRUE_SITE_URL: \${SITE_URL}
      GOTRUE_URI_ALLOW_LIST: \${ADDITIONAL_REDIRECT_URLS}
      GOTRUE_DISABLE_SIGNUP: \${DISABLE_SIGNUP}
      GOTRUE_JWT_SECRET: \${JWT_SECRET}
      GOTRUE_JWT_EXP: \${JWT_EXPIRY}
      GOTRUE_JWT_DEFAULT_GROUP_NAME: authenticated
      GOTRUE_EXTERNAL_EMAIL_ENABLED: \${ENABLE_EMAIL_SIGNUP}
      GOTRUE_MAILER_AUTOCONFIRM: \${ENABLE_EMAIL_AUTOCONFIRM}
      GOTRUE_SMTP_ADMIN_EMAIL: \${SMTP_ADMIN_EMAIL}
      GOTRUE_SMTP_HOST: \${SMTP_HOST}
      GOTRUE_SMTP_PORT: \${SMTP_PORT}
      GOTRUE_SMTP_USER: \${SMTP_USER}
      GOTRUE_SMTP_PASS: \${SMTP_PASS}
      GOTRUE_SMTP_SENDER_NAME: \${SMTP_SENDER_NAME}
      GOTRUE_MAILER_URLPATHS_INVITE: \${MAILER_URLPATHS_INVITE}
      GOTRUE_MAILER_URLPATHS_CONFIRMATION: \${MAILER_URLPATHS_CONFIRMATION}
      GOTRUE_MAILER_URLPATHS_RECOVERY: \${MAILER_URLPATHS_RECOVERY}
      GOTRUE_MAILER_URLPATHS_EMAIL_CHANGE: \${MAILER_URLPATHS_EMAIL_CHANGE}
      GOTRUE_EXTERNAL_PHONE_ENABLED: \${ENABLE_PHONE_SIGNUP}
      GOTRUE_SMS_AUTOCONFIRM: \${ENABLE_PHONE_AUTOCONFIRM}
    ports:
      - 9999:9999
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9999/health"]
      timeout: 5s
      interval: 5s
      retries: 3
EOF

echo "✅ Added auth service to docker-compose.yml"
echo ""
echo "Starting auth service..."
docker-compose up -d auth

echo "Waiting for auth to become healthy (10 seconds)..."
sleep 10

# Add rest service
echo "📄 Adding rest service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  rest:
    container_name: supabase-rest
    image: postgrest/postgrest:v11.2.2
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      PGRST_DB_URI: postgresql://authenticator:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/postgres
      PGRST_DB_SCHEMAS: \${PGRST_DB_SCHEMAS}
      PGRST_DB_ANON_ROLE: anon
      PGRST_JWT_SECRET: \${JWT_SECRET}
      PGRST_DB_USE_LEGACY_GUCS: "false"
    ports:
      - 3000:3000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      timeout: 5s
      interval: 5s
      retries: 10
EOF

echo "✅ Added rest service to docker-compose.yml"
echo ""
echo "Starting rest service..."
docker-compose up -d rest

echo "Waiting for rest to become healthy (10 seconds)..."
sleep 10

# Add functions service
echo "📄 Adding functions service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  functions:
    container_name: supabase-functions
    image: supabase/functions-js:v1.6.0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      JWT_SECRET: \${JWT_SECRET}
      DB_URL: postgresql://postgres:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/postgres
      VERIFY_JWT: \${FUNCTIONS_VERIFY_JWT}
    volumes:
      - ./volumes/functions:/home/deno/functions
    ports:
      - 9090:9090
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090"]
      timeout: 10s
      interval: 5s
      retries: 3
EOF

echo "✅ Added functions service to docker-compose.yml"
echo ""
echo "Starting functions service..."
docker-compose up -d functions

echo "Waiting for functions to become healthy (10 seconds)..."
sleep 10

echo ""
echo "You can now check the status of all services with:"
echo "docker-compose ps"
echo ""
echo "If all services are healthy, you can continue adding the remaining services like:"
echo "- meta"
echo "- realtime"
echo "- kong"
echo "- studio"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi