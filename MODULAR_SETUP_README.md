# Modular Supabase Stack Setup

This guide provides a modular approach to building and deploying the Supabase stack using Docker Compose. By breaking down the deployment into manageable projects, we can better isolate issues and ensure a stable setup.

## Project Structure

We've broken down the Supabase deployment into five distinct projects:

1. **Core Services** - Essential database and logging functionality
2. **API Gateway Services** - API routing and management
3. **UI Services** - Supabase Studio interface
4. **Performance Services** - Connection pooling and secrets management
5. **Custom Services** - Integration with TimescaleDB and application-specific services

## Prerequisites

- Docker and Docker Compose installed
- User added to the docker group (`sudo usermod -aG docker $USER`)
- Sufficient disk space for Docker images and volumes
- The `.env` file with all required variables properly configured

## Deployment Instructions

### 1. Core Services

First, deploy the essential database, vector, analytics, storage, auth, REST, and functions services:

```bash
# This starts db, vector, and analytics
docker-compose up -d db vector analytics

# Or to start everything in the core services group
./add_core_services.sh
```

This script will:
- Deploy the PostgreSQL database
- Add the vector service for logging
- Add the analytics service
- Add the storage service
- Add the authentication service
- Add the REST API service
- Add the serverless functions service

### 2. API Gateway Services

Once the core services are operational, deploy the API gateway and related services:

```bash
./add_gateway_services.sh
```

This script will:
- Deploy the realtime service for WebSocket connections
- Add the meta service for database metadata
- Add the Kong API gateway for routing and proxy

### 3. UI Services

Next, add the Supabase Studio interface:

```bash
./add_ui_services.sh
```

This script will:
- Deploy the imgproxy service for image transformations
- Add the Studio UI service

After this step, you should be able to access the Supabase dashboard at: http://localhost:8000

### 4. Performance Services

Add connection pooling and secrets management:

```bash
./add_performance_services.sh
```

This script will:
- Deploy the pgbouncer service for connection pooling
- Add the vault service for secrets management

### 5. Custom Services

Finally, integrate TimescaleDB and application-specific services:

```bash
./add_custom_services.sh
```

This script will:
- Deploy TimescaleDB for time-series data
- Add the d3_plotter service
- Add the tipiservice API
- Configure necessary schemas and connections

## Service Access URLs

After completing all steps, you can access the following services:

- **Supabase Studio**: http://localhost:8000
- **PostgreSQL**: localhost:5433 (supabase-db)
- **TimescaleDB**: localhost:5435
- **PgBouncer**: localhost:6432
- **Analytics**: http://localhost:4000
- **TIPI Service API**: http://localhost:7000

## Troubleshooting

If you encounter issues:

1. Check service status:
   ```bash
   docker-compose ps
   ```

2. View service logs:
   ```bash
   docker logs [container-name]
   ```

3. Restart specific services:
   ```bash
   docker-compose restart [service-name]
   ```

4. If a particular service group is failing, try deploying them in sequence:
   ```bash
   ./add_core_services.sh
   ./add_gateway_services.sh
   ./add_ui_services.sh
   ./add_performance_services.sh
   ./add_custom_services.sh
   ```

5. For persistent issues, check the Supabase Docker Compose troubleshooting guides:
   - SUPABASE_TROUBLESHOOTING.md
   - DOCKER_SETUP.md
   - CIRCULAR_DEPENDENCY_FIX.md

## Maintenance

### Backing Up

To backup your data:
```bash
docker exec -t supabase-db pg_dumpall -c -U postgres > supabase_backup.sql
```

### Updating

To update the stack:
1. Stop all services:
   ```bash
   docker-compose down
   ```

2. Pull the latest images:
   ```bash
   docker-compose pull
   ```

3. Redeploy the services in sequence using the scripts.

## Complete Reset

To completely reset the environment:
```bash
docker-compose down -v --remove-orphans
rm -rf volumes/db/data/* volumes/storage/* volumes/functions/* volumes/pooler/* volumes/timescaledb/data/*
./fix_docker_compose_issues_improved.sh
```

Then start again with the modular deployment approach.