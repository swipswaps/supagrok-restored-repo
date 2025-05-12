#!/usr/bin/env bash
# Fix for Supabase Docker Compose circular dependency issues
# Takes a more careful approach to modifying the docker-compose.yml

set -euo pipefail

echo "🔧 Fixing circular dependencies in docker-compose.yml..."

# Make a backup of the original docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml.original" ]; then
  cp docker-compose.yml docker-compose.yml.original
  echo "✅ Created backup at docker-compose.yml.original"
fi

# Reset from backup to ensure a clean start
cp docker-compose.yml.original docker-compose.yml

# Create a temporary file for the new docker-compose.yml
temp_file=$(mktemp)

# Read docker-compose.yml line by line
in_db_section=false
in_studio_section=false
in_analytics_section=false
in_depends_on=false
skip_lines=false

while IFS= read -r line; do
  # Check if we're entering specific sections
  if [[ "$line" =~ ^[[:space:]]*db: ]]; then
    in_db_section=true
    in_studio_section=false
    in_analytics_section=false
  elif [[ "$line" =~ ^[[:space:]]*studio: ]]; then
    in_db_section=false
    in_studio_section=true
    in_analytics_section=false
  elif [[ "$line" =~ ^[[:space:]]*analytics: ]]; then
    in_db_section=false
    in_studio_section=false
    in_analytics_section=true
  elif [[ "$line" =~ ^[[:space:]]*[a-zA-Z0-9_-]+: ]] && [[ ! "$line" =~ depends_on: ]]; then
    in_db_section=false
    in_studio_section=false
    in_analytics_section=false
    in_depends_on=false
    skip_lines=false
  fi

  # Check if we're entering a depends_on section
  if [[ "$line" =~ depends_on: ]]; then
    in_depends_on=true
    
    # If in the studio section, replace the whole depends_on block
    if [ "$in_studio_section" = true ]; then
      echo "      depends_on:" >> "$temp_file"
      echo "        db:" >> "$temp_file"
      echo "          condition: service_healthy" >> "$temp_file"
      skip_lines=true
      continue
    fi
    
    # If in the analytics section, modify to only depend on db
    if [ "$in_analytics_section" = true ]; then
      echo "      depends_on:" >> "$temp_file"
      echo "        db:" >> "$temp_file"
      echo "          condition: service_healthy" >> "$temp_file"
      skip_lines=true
      continue
    fi
    
    # For db section, remove depends_on completely
    if [ "$in_db_section" = true ]; then
      skip_lines=true
      continue
    fi
  fi

  # Stop skipping lines when we exit the depends_on section
  if [ "$skip_lines" = true ] && [[ "$line" =~ ^[[:space:]]*[a-zA-Z0-9_-]+: ]]; then
    if [ "$in_depends_on" = true ]; then
      in_depends_on=false
      skip_lines=false
    fi
  fi

  # If not skipping, write the line to the output file
  if [ "$skip_lines" = false ]; then
    echo "$line" >> "$temp_file"
  fi
done < docker-compose.yml

# Replace the original file with our modified version
mv "$temp_file" docker-compose.yml

echo "✅ Fixed circular dependencies in docker-compose.yml"
echo ""
echo "To start the services in the correct order, run:"
echo ""
echo "1. docker-compose down -v --remove-orphans"
echo "2. docker-compose up -d db"
echo "3. Wait ~15 seconds for the database to initialize"
echo "4. docker-compose up -d vector"
echo "5. Wait ~5 seconds"
echo "6. docker-compose up -d analytics"
echo "7. Wait ~5 seconds"
echo "8. docker-compose up -d"
echo ""
echo "Would you like to execute these steps now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  echo "Starting services in the correct sequence..."
  
  echo "Stopping all services..."
  docker-compose down -v --remove-orphans
  
  echo "Starting database..."
  docker-compose up -d db
  
  echo "Waiting for database to initialize (15 seconds)..."
  sleep 15
  
  echo "Starting vector service..."
  docker-compose up -d vector
  
  echo "Waiting for vector to initialize (5 seconds)..."
  sleep 5
  
  echo "Starting analytics service..."
  docker-compose up -d analytics
  
  echo "Waiting for analytics to initialize (5 seconds)..."
  sleep 5
  
  echo "Starting all remaining services..."
  docker-compose up -d
  
  echo "All services started. Check status with: docker-compose ps"
else
  echo "Please follow the steps above manually to start services in the correct order."
fi