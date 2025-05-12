 #!/usr/bin/env bash
# Script to add the Studio UI service after the gateway services

set -euo pipefail

echo "🔧 Adding Supabase Studio UI service..."

# Check if gateway services are running
kong_running=$(docker-compose ps kong | grep "Up" || echo "")
meta_running=$(docker-compose ps meta | grep "Up" || echo "")
realtime_running=$(docker-compose ps realtime | grep "Up" || echo "")

if [ -z "$kong_running" ] || [ -z "$meta_running" ] || [ -z "$realtime_running" ]; then
  echo "❌ Error: Gateway services (kong, meta, realtime) must be running first."
  echo "Please run these scripts first:"
  echo "  ./add_core_services.sh"
  echo "  ./add_gateway_services.sh"
  exit 1
fi

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.with_gateway_services

# Add imgproxy service first (required for Studio image transformations)
echo "📄 Adding imgproxy service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  imgproxy:
    container_name: supabase-imgproxy
    image: darthsim/imgproxy:v3.8.0
    restart: unless-stopped
    environment:
      IMGPROXY_BIND: :5001
      IMGPROXY_LOCAL_FILESYSTEM_ROOT: /
      IMGPROXY_USE_ETAG: "true"
      IMGPROXY_ENABLE_WEBP_DETECTION: \${IMGPROXY_ENABLE_WEBP_DETECTION}
    ports:
      - 5001:5001
    healthcheck:
      test: ["CMD", "imgproxy", "health"]
      interval: 5s
      timeout: 5s
      retries: 3
EOF

echo "✅ Added imgproxy service to docker-compose.yml"
echo ""
echo "Starting imgproxy service..."
docker-compose up -d imgproxy

echo "Waiting for imgproxy to become healthy (10 seconds)..."
sleep 10

# Add studio service
echo "📄 Adding studio service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  studio:
    container_name: supabase-studio
    image: supabase/studio:20240212-4c7e9d0
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      kong:
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
      imgproxy:
        condition: service_healthy
    ports:
      - 8000:3000
    environment:
      STUDIO_PG_META_URL: http://meta:8080
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      DEFAULT_ORGANIZATION_NAME: \${STUDIO_DEFAULT_ORGANIZATION}
      DEFAULT_PROJECT_NAME: \${STUDIO_DEFAULT_PROJECT}
      SUPABASE_URL: \${SUPABASE_PUBLIC_URL}
      SUPABASE_REST_URL: \${API_EXTERNAL_URL}/rest/v1/
      SUPABASE_ANON_KEY: \${ANON_KEY}
      SUPABASE_SERVICE_KEY: \${SERVICE_ROLE_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 5s
      timeout: 5s
      retries: 10
EOF

echo "✅ Added studio service to docker-compose.yml"
echo ""
echo "Starting studio service..."
docker-compose up -d studio

echo "Waiting for studio to become healthy (20 seconds)..."
sleep 20

echo ""
echo "✅ Supabase Studio should now be accessible at: http://localhost:8000"
echo ""
echo "You can now check the status of all UI services with:"
echo "docker-compose ps"
echo ""
echo "If all services are healthy, you have a complete Supabase stack ready to use!"
echo "To authenticate in the Studio, use these settings:"
echo "  URL: http://localhost:8000"
echo "  API Key: ${ANON_KEY} (from .env file)"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi