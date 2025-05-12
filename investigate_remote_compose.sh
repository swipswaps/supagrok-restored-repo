#!/bin/bash

# PRF Compliant Script to investigate the docker-compose.yml file on the IONOS server

# Define server details
IONOS_USER="supagrok"
IONOS_HOST="67.217.243.191"
IONOS_SSH_TARGET="${IONOS_USER}@${IONOS_HOST}"
REMOTE_COMPOSE_PATH="~/supagrok-tipiservice/docker-compose.yml"

echo "Attempting to read the docker-compose.yml file from ${IONOS_SSH_TARGET}:${REMOTE_COMPOSE_PATH}"
echo "You must have key-based SSH authentication working for this script to run without a password."

# Use SSH to read the remote file content
ssh ${IONOS_SSH_TARGET} "cat ${REMOTE_COMPOSE_PATH}"

SSH_STATUS=$?

if [ ${SSH_STATUS} -eq 0 ]; then
    echo ""
    echo "Successfully read the remote docker-compose.yml file."
    echo "Please examine the output above, paying close attention to the 'realtime' and 'vector' service definitions."
    echo "Look for any structural issues, incorrect indentation, or missing required fields that might cause validation errors."
else
    echo ""
    echo "Error: Failed to read the remote docker-compose.yml file."
    echo "Please ensure key-based SSH authentication is working and the file path is correct."
    exit 1
fi

exit 0