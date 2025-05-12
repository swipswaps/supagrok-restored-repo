# Step-by-Step Supabase Docker Compose Fix

This guide breaks down the fix process into smaller, manageable steps to resolve the Supabase Docker Compose issues.

## Problem Description

The error message:
```
ERROR: The Compose file './docker-compose.yml' is invalid because:
services.studio.depends_on contains an invalid type, it should be an array, or an object
```

This indicates two issues:
1. YAML structure issues in docker-compose.yml (incorrect format for depends_on)
2. Circular dependencies between services

## Step 1: Ensure Required Directories and Files Exist

First, make sure all necessary directories and configuration files are present:

```bash
./fix_directories.sh
```

This script will:
- Create all required directories (volumes/storage, volumes/pooler, etc.)
- Create essential configuration files like vector.yml
- Ensure database SQL init files exist

## Step 2: Fix YAML Structure Issues

We have two options for fixing the YAML structure:

### Option A: Use the simplified approach
```bash
./fix_yaml_structure.sh
```
This creates a minimal docker-compose.yml with just the essential services (db and vector) using proper YAML formatting.

### Option B: Use the dependency-chain fix
```bash
./fix_circular_deps.sh
```
This attempts to fix the original docker-compose.yml by breaking circular dependencies, but may still have YAML structure issues.

**We recommend Option A (fix_yaml_structure.sh) for most cases** as it's simpler and more reliable.

## Step 3: Start Services Incrementally

Regardless of which fix you chose in Step 2, follow these steps:

```bash
# First, bring down any running services
docker-compose down -v --remove-orphans

# Start only the database
docker-compose up -d db

# Wait ~15 seconds for the database to initialize
sleep 15

# Check the database status
docker-compose ps db

# If the database is healthy, start vector
docker-compose up -d vector

# Wait ~5 seconds
sleep 5

# If vector is healthy, start analytics
docker-compose up -d analytics

# Wait ~5 seconds
sleep 5

# Finally, start all remaining services
docker-compose up -d
```

## Step 4: Verify Services

Check the status of all services:

```bash
docker-compose ps
```

If any services are unhealthy, check their logs:

```bash
docker logs supabase-db
docker logs supabase-vector
# etc.
```

## Complete Fix Script

For convenience, you can use the combined fix script that runs the recommended steps:

```bash
./fix_supabase_complete.sh
```

This script will:
1. Run fix_directories.sh to ensure all files exist
2. Run fix_yaml_structure.sh to fix the YAML structure
3. Guide you through the incremental service startup process

## Why This Approach Works

Breaking down the solution into smaller steps helps:
1. Identify exactly where the problem occurs
2. Fix issues one at a time
3. Build a working system incrementally
4. Avoid complex circular dependencies

This is a proven strategy for handling complex Docker Compose setups with multiple interdependent services.