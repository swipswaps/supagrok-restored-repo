#!/usr/bin/env bash
# PRF-compliant SUPAGROK service setup on IONOS or Fedora

set -euo pipefail

# 1. Install Docker if not present (with OS detection)
if ! command -v docker &>/dev/null; then
  if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    sudo /usr/bin/apt update
    sudo /usr/bin/apt install -y docker.io
    sudo /usr/bin/systemctl enable --now docker
  elif [ -f /etc/redhat-release ] || [ -f /etc/fedora-release ]; then
    # RHEL/CentOS/Fedora
    if command -v dnf &>/dev/null; then
      sudo /usr/bin/dnf install -y docker
    else
      sudo /usr/bin/yum install -y docker
    fi
    sudo /usr/bin/systemctl enable --now docker
  else
    echo "Unsupported OS. Please install Docker manually."
    exit 1
  fi
fi

# 2. Stop and remove existing n8n container if it exists
if /usr/bin/docker ps -a --format '{{.Names}}' | grep -Eq '^n8n$'; then
  /usr/bin/docker stop n8n || true
  /usr/bin/docker rm n8n || true
fi

# 3. Start n8n
/usr/bin/docker run -d --name n8n -p 5678:5678 -v /home/owner/n8n_data:/home/node/.n8n n8nio/n8n

# 4. Download Supabase docker-compose.yml if not present
if [ ! -f /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml ]; then
  /usr/bin/curl -o /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml https://raw.githubusercontent.com/supabase/supabase/master/docker/docker-compose.yml
fi

# 5. Create .env file with required variables if not present
if [ ! -f /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/.env ]; then
  cat > /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/.env <<EOF
# Fill in all required secrets before first use!
POSTGRES_PASSWORD=
JWT_SECRET=
ANON_KEY=
SERVICE_ROLE_KEY=
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# Add other required variables here
EOF
  echo "✅ .env file created. Please edit and fill in all secrets before first deploy."
fi

# 6. # Patch vector Docker socket mount to be correct and idempotent
sed -i '/supabase-vector/,/volumes:/!b;:a;n;/docker\.sock/!ba;s|.*docker\.sock.*|      - /var/run/docker.sock:/var/run/docker.sock:ro,z|' /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml
echo "✅ Patched docker-compose.yml for valid Docker socket volume."

# 7. Patch vector config mount to use a file, not a directory
if grep -q './vector:/etc/vector/vector.yml' /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml; then
  /usr/bin/sed -i 's|./vector:/etc/vector/vector.yml|./vector.yml:/etc/vector/vector.yml|g' /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml
  echo "✅ Patched docker-compose.yml to mount vector.yml as a file."
fi

# 8. Create minimal vector.yml config if not present
if [ ! -f /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/vector.yml ]; then
  cat > /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/vector.yml <<EOF
sources: {}
sinks: {}
EOF
  echo "✅ Created minimal vector.yml config."
fi

# 9. Ensure docker-compose.yml is compatible with classic docker-compose
/usr/bin/sed -i 's/: true/: "true"/g; s/: false/: "false"/g' /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml
/usr/bin/sed -i 's/"\([0-9]\+\)"/\1/g' /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml

# 10. Pull all required Docker images (PRF-compliant dependency management)
/usr/bin/docker pull supabase/studio:2025.04.21-sha-173cc56
/usr/bin/docker pull kong:2.8.1
/usr/bin/docker pull supabase/gotrue:v2.171.0
/usr/bin/docker pull postgrest/postgrest:v12.2.11
/usr/bin/docker pull supabase/realtime:v2.34.47
/usr/bin/docker pull supabase/storage-api:v1.22.7
/usr/bin/docker pull darthsim/imgproxy:v3.8.0
/usr/bin/docker pull supabase/postgres-meta:v0.88.9
/usr/bin/docker pull supabase/edge-runtime:v1.67.4
/usr/bin/docker pull supabase/logflare:1.12.0
/usr/bin/docker pull supabase/postgres:15.8.1.060
/usr/bin/docker pull timberio/vector:0.28.1-alpine
/usr/bin/docker pull supabase/supavisor:2.5.1

# 11. Start Supabase
/usr/bin/docker-compose -f /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca.new/app/supagrok_restored_repo/docker-compose.yml up -d

echo "🎉 SUPAGROK core services setup complete. Please configure API keys and test integrations."