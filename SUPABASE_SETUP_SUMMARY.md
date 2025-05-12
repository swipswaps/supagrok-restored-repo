# Supabase Docker Compose Setup and Troubleshooting

This document provides a comprehensive summary of the issues identified with the Supabase Docker Compose setup and their solutions.

## Key Issues Identified

1. **Missing Directories**: Required directories for volumes were missing
   - `volumes/storage`
   - `volumes/pooler`
   - `volumes/functions`

2. **Missing Configuration Files**:
   - PostgreSQL configuration file (`postgresql.conf`)
   - Pooler configuration file (`pooler.exs`)

3. **Docker Socket Mount Issue**: Malformed docker.sock mount path in docker-compose.yml

4. **Circular Dependency**: The database service depending on the vector service, which might have been causing startup order issues

5. **Database Connection Issues**: Services trying to connect to the database at "localhost" instead of "db"

6. **PostgreSQL User Authentication**: Issues with the "supabase_admin" user authentication

## Complete Solution

To resolve these issues, follow these steps:

1. **Run the Complete Fix Script**:

```bash
./fix_supabase_complete.sh
```

This script performs the following:

- Creates all required directories
- Creates necessary configuration files
- Updates environment variables
- Fixes docker.sock mount paths
- Resolves circular dependencies
- Ensures proper database connections

2. **Restart Docker Compose**:

```bash
docker-compose down -v && docker-compose up -d
```

## Manual Steps (if needed)

If you prefer to fix issues manually:

1. **Create Required Directories**:
```bash
mkdir -p volumes/storage
mkdir -p volumes/pooler
mkdir -p volumes/functions/main
```

2. **Create PostgreSQL Configuration**:
```bash
cat > volumes/db/postgresql.conf <<EOF
# Basic PostgreSQL configuration file
listen_addresses = '*'
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.utf8'
lc_monetary = 'en_US.utf8'
lc_numeric = 'en_US.utf8'
lc_time = 'en_US.utf8'
default_text_search_config = 'pg_catalog.english'
EOF
```

3. **Create Pooler Configuration**:
```bash
cat > volumes/pooler/pooler.exs <<EOF
# Default pooler configuration
Supavisor.start_tenant(%{
  "id" => System.get_env("POOLER_TENANT_ID", "default"),
  "db_host" => "db",
  "db_port" => String.to_integer(System.get_env("POSTGRES_PORT", "5432")),
  "db_name" => System.get_env("POSTGRES_DB", "postgres"),
  "db_user" => "supabase_admin",
  "db_password" => System.get_env("POSTGRES_PASSWORD"),
  "port" => 5432,
  "pool_size" => String.to_integer(System.get_env("POOLER_DEFAULT_POOL_SIZE", "10")),
  "max_client_conn" => String.to_integer(System.get_env("POOLER_MAX_CLIENT_CONN", "100")),
  "pool_mode" => "transaction",
  "cmd_timeout" => 3000,
  "server_lifetime" => 3600,
  "idle_timeout" => 1800,
  "autorestart" => true
})
EOF
```

4. **Update Environment Variables**:
```bash
sed -i 's/POSTGRES_HOST=localhost/POSTGRES_HOST=db/g' .env
```

5. **Fix Docker Socket Mount**:
```bash
sed -i 's|.*- .*docker\.sock.*docker\.sock.*|      - /var/run/docker.sock:/var/run/docker.sock:ro,z|g' docker-compose.yml
```

6. **Remove Circular Dependencies**:
```bash
sed -i '/depends_on:/,/condition: service_healthy/d' docker-compose.yml
```

7. **Add PostgreSQL Config Mount**:
```bash
sed -i '/db-config:/i\      - ./volumes/db/postgresql.conf:/etc/postgresql/postgresql.conf:Z' docker-compose.yml
```

## Common Issues and Solutions

### 1. Database Connection Issues

If you see errors like "connection refused" in the logs:

- Verify that `POSTGRES_HOST=db` is set in `.env`
- Make sure the database container is running with `docker ps`
- Check database logs with `docker logs supabase-db`

### 2. Authentication Failed Errors

If you see "password authentication failed for user" errors:

- Check that the database initialization scripts are present in `volumes/db/`
- Verify the `POSTGRES_PASSWORD` value in `.env` matches what services are using
- You may need to manually create the role with:
  ```sql
  CREATE ROLE supabase_admin WITH LOGIN PASSWORD 'your_password';
  ```

### 3. Missing Volumes

If containers fail to start due to missing volumes:

- Check that all required directories exist
- Verify permissions are set correctly
- Run `docker-compose down -v` to clean up any orphaned volumes before trying again

## Verification

To verify that Supabase is working correctly:

1. Check that all containers are running:
```bash
docker ps
```

2. Access the Supabase Studio at http://localhost:8000

3. Connect to the database with:
```bash
docker exec -it supabase-db psql -U postgres
```

## References

- [Supabase Self-hosting Docs](https://supabase.com/docs/guides/hosting/docker)
- [PostgreSQL Configuration Docs](https://www.postgresql.org/docs/current/runtime-config.html)