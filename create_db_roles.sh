#!/usr/bin/env bash
# Script to create required database roles for Supabase

set -euo pipefail

echo "🔧 Creating PostgreSQL roles for Supabase..."

# Connect to PostgreSQL as postgres user and create the required roles
docker exec -it supabase-db psql -U postgres -c "
-- Create supabase_admin role
CREATE ROLE supabase_admin WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';
ALTER ROLE supabase_admin WITH SUPERUSER;

-- Create authenticator role
CREATE ROLE authenticator WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';

-- Create supabase_storage_admin role
CREATE ROLE supabase_storage_admin WITH LOGIN PASSWORD 'V3ryS3cur3P@ssw0rd';

-- Create other required roles
CREATE ROLE anon;
CREATE ROLE authenticated;
CREATE ROLE service_role;

-- Grant permissions
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;
GRANT service_role TO supabase_admin;
"

echo "✅ Database roles created successfully!"
echo "🔄 You may need to restart the services with: docker-compose restart"