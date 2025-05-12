# Docker Setup for Supabase

This document provides instructions for setting up and troubleshooting the Docker Compose environment for Supabase.

## Prerequisites

- Docker and Docker Compose installed
- User added to the docker group (`sudo usermod -aG docker $USER`)
- Sufficient disk space for Docker images and volumes

## Getting Started

1. Make sure you have the necessary files and directories:
   - `docker-compose.yml` - The main Docker Compose configuration
   - `.env` - Environment variables for the Docker Compose setup
   - `volumes/` - Directory containing required files for the services

2. Run the fix script to ensure all required directories and files exist:
   ```bash
   ./fix_docker_compose_issues.sh
   ```

3. Start the Docker Compose services:
   ```bash
   docker-compose down -v && docker-compose up -d
   ```

4. Check the status of the services:
   ```bash
   docker-compose ps
   ```

5. Access the Supabase Studio at http://localhost:8000

## Common Issues and Solutions

### Missing Directories or Files

If you encounter errors about missing files or directories, run the fix script:
```bash
./fix_docker_compose_issues.sh
```

### Permission Issues

If you encounter permission issues, make sure your user is in the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker  # Apply the new group without logging out
```

### Database Connection Issues

If services can't connect to the database:

1. Check if the database container is running:
   ```bash
   docker logs supabase-db
   ```

2. Verify the database environment variables in the `.env` file:
   ```
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_HOST=db  # Must be "db", not "localhost"
   POSTGRES_PORT=5432
   ```

   **Important**: The `POSTGRES_HOST` must be set to `db` (the service name in docker-compose.yml), not `localhost`.
   Services in Docker Compose reference each other by their service names, not by localhost.

### Vector Service Issues

If the vector service fails to start:

1. Check the vector logs:
   ```bash
   docker logs supabase-vector
   ```

2. Verify the vector.yml file exists:
   ```bash
   ls -l volumes/logs/vector.yml
   ```

### Cleaning Up

To completely reset the Docker Compose setup:
```bash
docker-compose down -v --remove-orphans
rm -rf volumes/storage/* volumes/functions/* volumes/pooler/*
./fix_docker_compose_issues.sh
docker-compose up -d
```

## Service URLs

- Supabase Studio: http://localhost:8000
- PostgreSQL: localhost:5432
- Analytics: http://localhost:4000

## Environment Variables

Key environment variables in the `.env` file:

- `POSTGRES_PASSWORD`: Password for the PostgreSQL database
- `JWT_SECRET`: Secret for JWT token generation
- `ANON_KEY`: Anonymous API key
- `SERVICE_ROLE_KEY`: Service role API key
- `SUPABASE_PUBLIC_URL`: Public URL for Supabase