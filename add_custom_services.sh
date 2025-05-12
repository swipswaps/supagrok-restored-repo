#!/usr/bin/env bash
# Script to integrate custom services with Supabase

set -euo pipefail

echo "🔧 Adding custom services integration..."

# Check if the core Supabase services are running
db_running=$(docker-compose ps db | grep "Up" || echo "")
kong_running=$(docker-compose ps kong | grep "Up" || echo "")

if [ -z "$db_running" ] || [ -z "$kong_running" ]; then
  echo "❌ Error: Core Supabase services must be running first."
  echo "Please run these scripts in order:"
  echo "  ./add_core_services.sh"
  echo "  ./add_gateway_services.sh"
  echo "  ./add_ui_services.sh"
  exit 1
fi

# Make a backup of the current working docker-compose.yml
cp docker-compose.yml docker-compose.yml.before_custom

# Add TimescaleDB service
echo "📄 Adding TimescaleDB service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  timescaledb:
    container_name: supabase-timescaledb
    image: timescale/timescaledb:latest-pg15
    restart: unless-stopped
    volumes:
      - ./volumes/timescaledb/data:/var/lib/postgresql/data:Z
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 10
    environment:
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_USER: postgres
      POSTGRES_DB: timescaledb
    ports:
      - 5435:5432
EOF

echo "✅ Added TimescaleDB service to docker-compose.yml"
echo ""

# Create necessary directories
echo "Creating required directories..."
mkdir -p ./volumes/timescaledb/data
mkdir -p ./volumes/d3_plotter
mkdir -p ./volumes/tipiservice

# Copy d3_plotter configurations
echo "Setting up d3_plotter service..."

# d3_plotter service
echo "📄 Adding d3_plotter service to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  d3_plotter:
    container_name: supagrok-d3-plotter
    image: python:3.11-slim
    restart: unless-stopped
    depends_on:
      timescaledb:
        condition: service_healthy
    volumes:
      - ./app4/d3_plotter:/app
      - ./volumes/d3_plotter:/data
    working_dir: /app
    command: bash -c "pip install psycopg2-binary pandas requests schedule && python supagrok_logger_daemon.py"
    environment:
      TIMESCALE_HOST: timescaledb
      TIMESCALE_PORT: 5432
      TIMESCALE_USER: postgres
      TIMESCALE_PASSWORD: \${POSTGRES_PASSWORD}
      TIMESCALE_DB: timescaledb
      SUPABASE_URL: \${SUPABASE_PUBLIC_URL}
      SUPABASE_KEY: \${ANON_KEY}
EOF

echo "✅ Added d3_plotter service to docker-compose.yml"
echo ""

# tipiservice
echo "📄 Adding tipiservice to docker-compose.yml..."
cat >> docker-compose.yml <<EOF

  tipiservice:
    container_name: supagrok-tipiservice
    image: python:3.11-slim
    restart: unless-stopped
    ports:
      - 7000:7000
    volumes:
      - ./supagrok-tipiservice:/app
      - ./volumes/tipiservice:/data
    working_dir: /app
    command: bash -c "pip install flask requests python-dotenv psycopg2-binary && python main.py"
    environment:
      FLASK_PORT: 7000
      SUPABASE_URL: \${SUPABASE_PUBLIC_URL}
      SUPABASE_KEY: \${SERVICE_ROLE_KEY}
      TIMESCALE_HOST: timescaledb
      TIMESCALE_PORT: 5432
      TIMESCALE_USER: postgres
      TIMESCALE_PASSWORD: \${POSTGRES_PASSWORD}
      TIMESCALE_DB: timescaledb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
EOF

echo "✅ Added tipiservice to docker-compose.yml"
echo ""

# Create a simple TimescaleDB initialization script
echo "Creating TimescaleDB initialization script..."
cat > ./volumes/timescaledb/init.sql <<EOF
-- Create hypertables for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create schema for supagrok data
CREATE SCHEMA IF NOT EXISTS supagrok;

-- Create logs table
CREATE TABLE IF NOT EXISTS supagrok.logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB
);

-- Convert to hypertable
SELECT create_hypertable('supagrok.logs', 'timestamp', if_not_exists => TRUE);

-- Create metrics table
CREATE TABLE IF NOT EXISTS supagrok.metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB
);

-- Convert to hypertable
SELECT create_hypertable('supagrok.metrics', 'timestamp', if_not_exists => TRUE);

-- Create retention policy (keep 30 days of data)
SELECT add_retention_policy('supagrok.logs', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('supagrok.metrics', INTERVAL '30 days', if_not_exists => TRUE);
EOF

echo "✅ Created TimescaleDB initialization script"
echo ""

# Create a basic health check endpoint for tipiservice
echo "Creating main.py for tipiservice if it doesn't exist..."
if [ ! -f ./supagrok-tipiservice/main.py ]; then
  cat > ./supagrok-tipiservice/main.py <<EOF
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "supagrok-tipiservice"})

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 7000))
    app.run(host="0.0.0.0", port=port)
EOF
fi

echo "Starting TimescaleDB service..."
docker-compose up -d timescaledb

echo "Waiting for TimescaleDB to become healthy (20 seconds)..."
sleep 20

# Initialize TimescaleDB with our schema
echo "Initializing TimescaleDB with schema..."
docker exec -i supabase-timescaledb psql -U postgres -d timescaledb < ./volumes/timescaledb/init.sql

echo "Starting custom services..."
docker-compose up -d d3_plotter tipiservice

echo "Waiting for services to start (15 seconds)..."
sleep 15

echo ""
echo "✅ Custom services added and integrated with Supabase!"
echo ""
echo "You can access the services at:"
echo "  - TimescaleDB: localhost:5435 (user: postgres, password: from .env)"
echo "  - TIPI Service API: http://localhost:7000"
echo ""
echo "To view all running services:"
echo "docker-compose ps"
echo ""
echo "Would you like to check the status of all services? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  docker-compose ps
fi