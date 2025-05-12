#!/bin/bash

# PRF Compliant Script to help restore key-based SSH authentication on the IONOS server

# Define server details
IONOS_USER="supagrok"
IONOS_HOST="67.217.243.191"
IONOS_SSH_TARGET="${IONOS_USER}@${IONOS_HOST}"

echo "Attempting to restore key-based SSH authentication for ${IONOS_SSH_TARGET}"

# --- Step 1: Get the local public key ---
# Try to find a common public key file
LOCAL_PUB_KEY=""
if [ -f "$HOME/.ssh/id_rsa.pub" ]; then
    LOCAL_PUB_KEY="$HOME/.ssh/id_rsa.pub"
elif [ -f "$HOME/.ssh/id_ed25519.pub" ]; then
    LOCAL_PUB_KEY="$HOME/.ssh/id_ed25519.pub"
else
    echo "Error: No standard SSH public key found in $HOME/.ssh/"
    echo "Please ensure you have an SSH key pair. You can generate one using: ssh-keygen"
    exit 1
fi

echo "Using local public key: ${LOCAL_PUB_KEY}"

# --- Step 2: Attempt to use ssh-copy-id ---
# ssh-copy-id is the standard tool for this and handles permissions automatically
if command -v ssh-copy-id &> /dev/null; then
    echo "Using ssh-copy-id to copy the public key to the server."
    echo "You may be prompted for the password for ${IONOS_SSH_TARGET}."
    ssh-copy-id -i ${LOCAL_PUB_KEY} ${IONOS_SSH_TARGET}
    SSH_COPY_STATUS=$?

    if [ ${SSH_COPY_STATUS} -eq 0 ]; then
        echo "ssh-copy-id completed successfully."
        echo "Attempting to test key-based authentication..."
        ssh -o PreferredAuthentications=publickey -o BatchMode=yes ${IONOS_SSH_TARGET} exit
        TEST_STATUS=$?
        if [ ${TEST_STATUS} -eq 0 ]; then
            echo "Key-based authentication is now working."
            echo "You should now be able to run ./deploy_to_github_and_ionos.sh"
            exit 0
        else
            echo "ssh-copy-id ran, but key-based authentication test failed."
            echo "Proceeding with manual instructions..."
        fi
    else
        echo "ssh-copy-id failed (exit code ${SSH_COPY_STATUS})."
        echo "Proceeding with manual instructions..."
    fi
else
    echo "ssh-copy-id not found. Proceeding with manual instructions."
fi

# --- Step 3: Provide Manual Instructions if ssh-copy-id is not available or failed ---
echo ""
echo "--- Manual Steps to Restore Key-Based Authentication ---"
echo "ssh-copy-id was not available or failed. Please follow these manual steps:"
echo ""
echo "1. Copy your public key to your clipboard or a temporary file on your local machine:"
echo "   cat ${LOCAL_PUB_KEY}"
echo ""
echo "2. Log in to your IONOS server using your password:"
echo "   ssh ${IONOS_SSH_TARGET}"
echo ""
echo "3. On the server, create the .ssh directory if it doesn't exist and set permissions:"
echo "   mkdir -p ~/.ssh"
echo "   chmod 700 ~/.ssh"
echo ""
echo "4. Append your public key to the authorized_keys file. Replace 'PASTE_YOUR_PUBLIC_KEY_HERE' with the key you copied in step 1:"
echo "   echo 'PASTE_YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo ""
echo "5. Set the correct permissions for the authorized_keys file:"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "6. Exit the SSH session:"
echo "   exit"
echo ""
echo "7. On your local machine, test key-based authentication:"
echo "   ssh ${IONOS_SSH_TARGET}"
echo ""
echo "Once key-based authentication is working, you can run ./deploy_to_github_and_ionos.sh again."

exit 1 # Indicate that the script couldn't fully automate the process