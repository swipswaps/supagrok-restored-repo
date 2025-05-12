#!/usr/bin/env bash
# Complete Supabase Docker Compose Issue Fix
# This script orchestrates the full repair process by running the specialized fix scripts

set -euo pipefail

echo "🔧 Starting Supabase Docker Compose Issue Fix"
echo "==============================================="
echo ""

# Step 1: Ensure all required directories and files exist
echo "Step 1: Creating required directories and files..."
./fix_directories.sh

# Step 2: Fix circular dependencies in docker-compose.yml
echo ""
echo "Step 2: Fixing circular dependencies in docker-compose.yml..."
./fix_circular_deps.sh

# Note: fix_circular_deps.sh already handles starting the services in the correct order
# so we don't need to add that step here.

echo ""
echo "🎉 Fix process completed!"
echo ""
echo "If you chose not to start the services automatically, remember to start them in this order:"
echo "1. docker-compose down -v --remove-orphans"
echo "2. docker-compose up -d db"
echo "3. Wait ~15 seconds for the database to initialize"
echo "4. docker-compose up -d vector"
echo "5. Wait ~5 seconds"
echo "6. docker-compose up -d analytics"
echo "7. Wait ~5 seconds"
echo "8. docker-compose up -d"
echo ""
echo "Check service status with: docker-compose ps"
echo "Access Supabase Studio at: http://localhost:8000"