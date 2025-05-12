#!/bin/bash

# PRF Compliant Script to check the availability of the supabase/postgrest-analytics image locally

IMAGE_NAME="supabase/postgrest-analytics:v0.1.0"

echo "Attempting to pull Docker image: ${IMAGE_NAME} locally..."

# Attempt to pull the image
docker pull ${IMAGE_NAME}

PULL_STATUS=$?

if [ ${PULL_STATUS} -eq 0 ]; then
    echo ""
    echo "✅ Successfully pulled the image ${IMAGE_NAME} locally."
    echo "This suggests the image is generally available from Docker Hub."
    echo "The issue on the IONOS server might be related to its specific Docker configuration, network, or temporary registry issues."
else
    echo ""
    echo "❌ Failed to pull the image ${IMAGE_NAME} locally."
    echo "This indicates the image may not exist, the name/tag is incorrect, or there's a general issue accessing the Docker registry."
    echo "Please verify the image name and tag for Supabase analytics."
fi

exit ${PULL_STATUS}