#!/usr/bin/env bash
# PRF-compliant upload to IONOS server

IONOS_USER="supagrok"
IONOS_HOST="67.217.243.191"
IONOS_PATH="~/supagrok-tipiservice/"

# Adjust the local path as needed
LOCAL_PATH="./supagrok-tipiservice/"

rsync -avz --progress --partial --exclude 'large_files_backup' "$LOCAL_PATH" "${IONOS_USER}@${IONOS_HOST}:${IONOS_PATH}"