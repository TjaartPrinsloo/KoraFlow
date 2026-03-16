#!/bin/bash
###############################################################################
# KoraFlow Quick Deploy Helper
# Fast updates for application code and migrations
###############################################################################

set -e

# Configuration
CONFIG_FILE="$HOME/.koraflow-config/deployment.conf"
source "$CONFIG_FILE"

TARGET=${1:-production}

echo "Deploying updates to $TARGET ($ORACLE_IP)..."

ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" <<'REMOTE'
    cd /home/frappe/frappe-bench
    
    echo "Pulling latest code..."
    bench update --pull --no-backup
    
    echo "Running migrations..."
    bench migrate
    
    echo "Building assets..."
    bench build
    
    echo "Restarting services..."
    sudo supervisorctl restart all
REMOTE

echo "Deployment finished!"
