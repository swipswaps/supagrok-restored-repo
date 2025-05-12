#!/usr/bin/env bash
# Step-by-step solution to fix Supabase Docker Compose issues

set -e

echo "🔧 Executing step-by-step Supabase fix..."

echo "Step 1: Stopping all containers and cleaning up volumes"
docker-compose down -v --remove-orphans

echo "Step 2: Cleaning Docker environment"
docker volume prune -f

echo "Step 3: Running improved fix script to ensure correct configuration"
./fix_docker_compose_issues_improved.sh

echo "Step 4: Starting only the database container first"
docker-compose up -d db

echo "Step 5: Waiting for database to be healthy (15 seconds)..."
for i in {1..15}; do
  echo -n "."
  sleep 1
done
echo ""

echo "Step 6: Checking database status"
docker-compose ps db

echo "Step 7: Starting vector service"
docker-compose up -d vector

echo "Step 8: Waiting for vector to start (10 seconds)..."
for i in {1..10}; do
  echo -n "."
  sleep 1
done
echo ""

echo "Step 9: Starting remaining services"
docker-compose up -d

echo "✅ All services have been started!"
echo "Check status with: docker-compose ps"
echo "If any services are still unhealthy, check their logs with:"
echo "docker logs supabase-db"
echo "docker logs supabase-vector"
echo "docker logs supabase-auth"