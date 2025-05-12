# Supabase Docker Compose Troubleshooting Guide

## Common "Container is unhealthy" Errors

If you're seeing errors like:
```
ERROR: for rest  Container "0a25aabed430" is unhealthy.
ERROR: for supavisor  Container "0a25aabed430" is unhealthy.
ERROR: for realtime  Container "0a25aabed430" is unhealthy.
ERROR: for kong  Container "0a25aabed430" is unhealthy.
ERROR: for studio  Container "0a25aabed430" is unhealthy.
ERROR: for auth  Container "0a25aabed430" is unhealthy.
ERROR: for functions  Container "0a25aabed430" is unhealthy.
ERROR: for meta  Container "0a25aabed430" is unhealthy.
```

This is a known issue with Supabase Docker Compose setups and indicates problems with either:

1. Circular dependencies between services
2. Core services failing to start properly
3. Missing configuration files or directories 
4. Database initialization issues

## Solution Steps

### 1. Clean Docker Environment

```bash
docker-compose down -v --remove-orphans
docker rm -f $(docker ps -aq)  # Optional: removes all containers
docker volume prune -f  # Optional: removes unused volumes
```

### 2. Start Services Sequentially

The most common solution is to start services in the correct order:

```bash
# Start only the database first
docker-compose up -d db

# Wait for the database to be fully healthy (check status)
docker-compose ps db

# Start vector service next
docker-compose up -d vector

# Start the remaining services
docker-compose up -d
```

### 3. Check Individual Service Logs

If issues persist, check logs for specific services:

```bash
docker logs supabase-db
docker logs supabase-vector
docker logs supabase-auth
```

### 4. Fix Common Configuration Issues

#### Vector Configuration

Ensure `vector.yml` exists and has proper permissions:
```bash
ls -l volumes/logs/vector.yml
chmod 644 volumes/logs/vector.yml
```

#### Database Connection Issues

Ensure your .env file has the correct database connection settings:
- `POSTGRES_HOST` should be set to `db` (service name), not `localhost`
- Ensure `POSTGRES_PASSWORD` is consistent

#### Volume Mount Issues

Many issues stem from incorrect volume mounts. Use the improved fix script:
```bash
./fix_docker_compose_issues_improved.sh
```

#### PostgreSQL Configuration

The `postgresql.conf` file should have proper permissions and settings:
```bash
chmod 644 volumes/db/postgresql.conf
```

### 5. Known Issues with Specific Versions

Some Supabase versions have known compatibility issues. If you continue to experience problems:

- Try using slightly older or newer image versions
- Check the [Supabase GitHub issues](https://github.com/supabase/supabase/issues) for your specific error
- Ensure Docker and Docker Compose are up to date

## Advanced Troubleshooting

### Inspecting Container Health

For more details on why containers are unhealthy:

```bash
docker inspect <container_id> | grep -A 10 "Health"
```

### Database Initialization Problems

If the database is failing to initialize properly:

```bash
# Check if required SQL init files exist
ls -la volumes/db/*.sql

# Manually connect to the database
docker exec -it supabase-db psql -U postgres
```

### Service Dependency Resolution

The order of service startup is important. If one service depends on another that's unhealthy, it will also fail to start. The correct startup sequence is:

1. Database (db)
2. Vector (vector)
3. Analytics (analytics)
4. Storage, Functions, REST, Auth
5. Kong and Studio

## When All Else Fails

If you've tried all the above solutions without success:

1. Use the improved fix script: `./fix_docker_compose_issues_improved.sh`
2. Start with a completely fresh setup:
   ```bash
   docker-compose down -v --remove-orphans
   rm -rf volumes/db/data/* volumes/storage/* volumes/functions/* volumes/pooler/*
   ./fix_docker_compose_issues_improved.sh
   ```
3. Restart your Docker daemon:
   ```bash
   sudo systemctl restart docker