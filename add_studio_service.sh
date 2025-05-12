#!/usr/bin/env bash
# Script to add the studio service to the current docker-compose.yml

set -euo pipefail

echo "🔧 Adding Studio service to docker-compose.yml..."

# Extract the studio service from the official docker-compose.yml
studio_service=$(sed -n '/^  studio:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')

# Add the studio service to our current docker-compose.yml
echo "" >> docker-compose.yml
echo "$studio_service" >> docker-compose.yml

echo "🔧 Adding Kong service (API Gateway)..."
kong_service=$(sed -n '/^  kong:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$kong_service" >> docker-compose.yml

echo "🔧 Adding REST service (PostgreSQL API)..."
rest_service=$(sed -n '/^  rest:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$rest_service" >> docker-compose.yml

echo "🔧 Adding Auth service..."
auth_service=$(sed -n '/^  auth:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$auth_service" >> docker-compose.yml

echo "🔧 Adding Storage service..."
storage_service=$(sed -n '/^  storage:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$storage_service" >> docker-compose.yml

echo "🔧 Adding Meta service..."
meta_service=$(sed -n '/^  meta:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$meta_service" >> docker-compose.yml

echo "🔧 Adding Functions service..."
functions_service=$(sed -n '/^  functions:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$functions_service" >> docker-compose.yml

echo "🔧 Adding ImgProxy service..."
imgproxy_service=$(sed -n '/^  imgproxy:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$imgproxy_service" >> docker-compose.yml

echo "🔧 Adding Realtime service..."
realtime_service=$(sed -n '/^  realtime:/,/^  [a-z]/p' docker-compose.yml.official | sed '$d')
echo "" >> docker-compose.yml
echo "$realtime_service" >> docker-compose.yml

echo "✅ Added all services to docker-compose.yml"
echo ""
echo "🔄 Now run these commands to apply your fixes and start all services:"
echo "1. ./fix_supabase_complete.sh"
echo "2. docker-compose down -v && docker-compose up -d"