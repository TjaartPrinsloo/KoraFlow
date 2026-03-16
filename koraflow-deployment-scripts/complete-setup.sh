#!/bin/bash
###############################################################################
# KoraFlow Oracle Cloud Complete Setup (Manual)
# Full server configuration and application deployment
###############################################################################

set -e

# Configuration
CONFIG_FILE="$HOME/.koraflow-config/deployment.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at $CONFIG_FILE"
    echo "Please run the auto-setup-wizard.sh first."
    exit 1
fi

source "$CONFIG_FILE"

echo "--------------------------------------------------------"
echo "KoraFlow Complete Setup - Oracle Cloud"
echo "Target IP: $ORACLE_IP"
echo "--------------------------------------------------------"

# 1. System Preparation
echo "Step 1: Preparing system..."
ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" "sudo apt update && sudo apt upgrade -y"

# 2. Install Dependencies
echo "Step 2: Installing dependencies..."
if [ -f "$HOME/.koraflow-config/install-on-oracle.sh" ]; then
    scp -i "$SSH_KEY_PATH" "$HOME/.koraflow-config/install-on-oracle.sh" "${SSH_USER}@${ORACLE_IP}:/tmp/"
    ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" "bash /tmp/install-on-oracle.sh"
else
    echo "Error: Installation script not found. Regeneration required."
    exit 1
fi

# 3. Deploy Application
echo "Step 3: Deploying application..."
if [ -f "$HOME/.koraflow-config/deploy-app.sh" ]; then
    bash "$HOME/.koraflow-config/deploy-app.sh"
else
    echo "Error: Deployment script not found. Regeneration required."
    exit 1
fi

# 4. Final Verification
echo "Step 4: Verifying installation..."
ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" "sudo supervisorctl status"

echo "--------------------------------------------------------"
echo "Setup Complete! Access your app at: http://$ORACLE_IP"
echo "--------------------------------------------------------"
