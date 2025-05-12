#!/usr/bin/env bash
# Script to deploy the entire Supabase stack in the correct sequence

set -euo pipefail

echo "🚀 Starting full Supabase stack deployment..."
echo "This script will run all the modular scripts in sequence."
echo ""

# Check if scripts exist and have execute permissions
for script in add_core_services.sh add_gateway_services.sh add_ui_services.sh add_performance_services.sh add_custom_services.sh; do
  if [ ! -f "./$script" ]; then
    echo "❌ Error: Required script $script not found."
    exit 1
  fi
  
  if [ ! -x "./$script" ]; then
    echo "Setting execute permission on $script..."
    chmod +x "./$script"
  fi
done

echo "1️⃣ Deploying Core Services (DB, Vector, Analytics, Storage, Auth, REST, Functions)..."
./add_core_services.sh

echo ""
echo "2️⃣ Deploying API Gateway Services (Realtime, Meta, Kong)..."
./add_gateway_services.sh

echo ""
echo "3️⃣ Deploying UI Services (Imgproxy, Studio)..."
./add_ui_services.sh

echo ""
echo "4️⃣ Deploying Performance Services (PgBouncer, Vault)..."
./add_performance_services.sh

echo ""
echo "5️⃣ Deploying Custom Services (TimescaleDB, d3_plotter, tipiservice)..."
./add_custom_services.sh

echo ""
echo "✅ Full Supabase stack deployment complete!"
echo ""
echo "Access your services at:"
echo "- Supabase Studio: http://localhost:8000"
echo "- REST API: http://localhost:8000/rest/v1"
echo "- Auth API: http://localhost:8000/auth/v1"
echo "- Storage API: http://localhost:8000/storage/v1"
echo "- TimescaleDB: localhost:5435"
echo "- TIPI Service: http://localhost:7000"
echo ""
echo "For more information, please see MODULAR_SETUP_README.md"