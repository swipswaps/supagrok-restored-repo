# Supagrok Deployment Guide

This guide explains how to deploy the Supagrok services using our modular deployment approach, which includes pushing to GitHub and deploying to the IONOS server.

## Deployment Architecture

Our deployment consists of two main parts:

1. **Local Environment** - Your development machine where you make changes
2. **IONOS Server** - Production server (67.217.243.191) where services run

The deployment flow:
- Changes are committed to Git locally
- Changes are pushed to GitHub
- GitHub repository is cloned/pulled on the IONOS server
- Supabase services are deployed on IONOS in a modular fashion

## Prerequisites

- Git installed and configured with GitHub access
- SSH access to the IONOS server (SSH keys already in place)
- Docker and Docker Compose installed locally

## Deployment Scripts

We've created several scripts to make deployment modular and reliable:

### Core Scripts (Modular Services)

1. `add_core_services.sh` - Deploys essential database, storage, auth, REST, and functions services
2. `add_gateway_services.sh` - Deploys API gateway and realtime services
3. `add_ui_services.sh` - Deploys Supabase Studio UI
4. `add_performance_services.sh` - Deploys connection pooling and secrets management
5. `add_custom_services.sh` - Deploys TimescaleDB and custom services
6. `deploy_all.sh` - Orchestrates the deployment of all services in the correct order

### GitHub and IONOS Deployment

- `deploy_to_github_and_ionos.sh` - Master script that:
  - Commits and pushes changes to GitHub
  - Updates code on the IONOS server
  - Transfers all deployment scripts to IONOS
  - Creates required directories on IONOS
  - Transfers configuration files
  - Deploys all services on IONOS

## How to Deploy

1. Make your changes locally
2. Run the combined deployment script:

```bash
./deploy_to_github_and_ionos.sh
```

This will:
- Push all changes to GitHub
- Deploy to the IONOS server at `supagrok@67.217.243.191:~/supagrok-tipiservice/`
- Set up and start all required services

## Accessing Services

After deployment, you can access:

- Supabase Studio: http://67.217.243.191:8000
- REST API: http://67.217.243.191:8000/rest/v1
- Auth API: http://67.217.243.191:8000/auth/v1
- Storage API: http://67.217.243.191:8000/storage/v1
- TimescaleDB: 67.217.243.191:5435
- TIPI Service: http://67.217.243.191:7000

## Troubleshooting

If you encounter issues during deployment:

1. **Local Git Issues**:
   - Check your GitHub authentication
   - Make sure you have write access to the repository

2. **SSH Connection Issues**:
   - Verify SSH keys are correctly set up
   - Check that the IONOS server is reachable

3. **Service Startup Issues**:
   - SSH into the IONOS server and check Docker logs:
     ```bash
     ssh supagrok@67.217.243.191
     cd ~/supagrok-tipiservice
     docker-compose ps
     docker-compose logs [service-name]
     ```

4. **Circular Dependencies**:
   - If services fail to start due to circular dependencies, use the modular scripts to start services in the correct order:
     ```bash
     ./add_core_services.sh
     ./add_gateway_services.sh
     ./add_ui_services.sh
     ./add_performance_services.sh
     ./add_custom_services.sh
     ```

5. **Environment Variables**:
   - Make sure the `.env` file on the IONOS server contains all the required environment variables
   - Check `MODULAR_SETUP_README.md` for a list of required variables

## Maintenance

### Backups

To backup the PostgreSQL database:
```bash
ssh supagrok@67.217.243.191
docker exec -t supabase-db pg_dumpall -c -U postgres > ~/supagrok_backup_$(date +%Y%m%d).sql
```

### Updating Services

To update individual services:
```bash
ssh supagrok@67.217.243.191
cd ~/supagrok-tipiservice
# Update just one service group
./add_ui_services.sh
```

## Manual Operations (if needed)

If you need to manually deploy without going through GitHub:

```bash
# SSH into IONOS
ssh supagrok@67.217.243.191

# Go to supagrok-tipiservice directory
cd ~/supagrok-tipiservice

# Pull latest changes directly (if needed)
git pull origin main

# Deploy all services
./deploy_all.sh

# Or deploy specific service groups
./add_core_services.sh
./add_gateway_services.sh
# etc.