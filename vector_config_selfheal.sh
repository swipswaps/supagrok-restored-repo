#!/bin/bash
set -e

CONTAINER=supabase-vector
LOCAL_CONFIG="./volumes/logs/vector.yml"
CONTAINER_CONFIG="/etc/vector/vector.yml"

# Copy the config from the running container for comparison
docker cp "$CONTAINER:$CONTAINER_CONFIG" ./_container_vector.yml

# Compare local and container configs, update if different
if ! diff -u "$LOCAL_CONFIG" ./_container_vector.yml; then
  echo "Config mismatch detected. Updating container config..."
  docker cp "$LOCAL_CONFIG" "$CONTAINER:$CONTAINER_CONFIG"
  docker restart "$CONTAINER"
  sleep 5
else
  echo "Config matches. Restarting container to ensure reload."
  docker restart "$CONTAINER"
  sleep 5
fi

# Test API endpoint
if curl -sf http://localhost:9001/health; then
  echo "Vector API is accessible."
else
  echo "Vector API is still not accessible. Check logs for errors."
  docker logs "$CONTAINER" | tail -40
fi

# Cleanup
rm -f ./_container_vector.yml