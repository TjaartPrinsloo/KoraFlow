#!/bin/bash
###############################################################################
# KoraFlow Oracle Cloud Auto-Setup Wizard
# Automatically discovers Oracle Cloud resources and configures deployment
# Usage: ./auto-setup-wizard.sh
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Progress spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

log_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
}

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo -e "${BLUE}▶${NC} $1"
}

log_question() {
    echo -e "${CYAN}?${NC} $1"
}

###############################################################################
# Welcome Screen
###############################################################################

clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗  ██╗ ██████╗ ██████╗  █████╗ ███████╗██╗      ██████╗ ██╗ ║
║   ██║ ██╔╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔═══██╗██║ ║
║   █████╔╝ ██║   ██║██████╔╝███████║█████╗  ██║     ██║   ██║██║ ║
║   ██╔═██╗ ██║   ██║██╔══██╗██╔══██║██╔══╝  ██║     ██║   ██║██║ ║
║   ██║  ██╗╚██████╔╝██║  ██║██║  ██║██║     ███████╗╚██████╔╝██║ ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝ ║
║                                                                  ║
║           Oracle Cloud Auto-Setup & Deployment Wizard           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

EOF

echo -e "${CYAN}This wizard will:${NC}"
echo "  1. Auto-discover your Oracle Cloud instances"
echo "  2. Detect existing configurations"
echo "  3. Generate deployment scripts"
echo "  4. Setup automated CI/CD"
echo "  5. Configure everything automatically"
echo ""
read -p "Press Enter to continue..."

###############################################################################
# Check Prerequisites
###############################################################################

log_header "Checking Prerequisites"

# Check OCI CLI
if ! command -v oci &> /dev/null; then
    log_warn "OCI CLI not found. Installing..."
    
    # Install OCI CLI
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    
    # Add to PATH for current session
    export PATH="$HOME/bin:$PATH"
    
    if command -v oci &> /dev/null; then
        log_info "OCI CLI installed successfully"
    else
        log_error "Failed to install OCI CLI. Please install manually."
        exit 1
    fi
else
    log_info "OCI CLI is installed"
fi

# Check if OCI is configured
if [ ! -f "$HOME/.oci/config" ]; then
    log_warn "OCI CLI not configured. Let's set it up..."
    echo ""
    echo "You'll need:"
    echo "  - Your Oracle Cloud user OCID"
    echo "  - Your tenancy OCID"
    echo "  - Your home region"
    echo ""
    echo "Get these from: Oracle Cloud Console → Profile Icon → Tenancy"
    echo ""
    read -p "Press Enter to start OCI configuration..."
    
    oci setup config
    
    if [ ! -f "$HOME/.oci/config" ]; then
        log_error "OCI configuration failed. Please run 'oci setup config' manually."
        exit 1
    fi
    log_info "OCI CLI configured"
else
    log_info "OCI CLI is configured"
fi

# Check git
if ! command -v git &> /dev/null; then
    log_error "Git is not installed. Please install git first."
    exit 1
fi
log_info "Git is installed"

# Check jq for JSON parsing
if ! command -v jq &> /dev/null; then
    log_step "Installing jq for JSON parsing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y jq
    fi
fi
log_info "All prerequisites installed"

###############################################################################
# Discover Oracle Cloud Resources
###############################################################################

log_header "Discovering Oracle Cloud Resources"

# Get compartment ID
log_step "Detecting your tenancy and compartment..."
TENANCY_ID=$(oci iam compartment list --all --compartment-id-in-subtree true --query "data[0].\"compartment-id\"" --raw-output 2>/dev/null || echo "")

if [ -z "$TENANCY_ID" ]; then
    # Try getting tenancy from config
    TENANCY_ID=$(grep tenancy ~/.oci/config | cut -d'=' -f2 | tr -d ' ')
fi

log_info "Tenancy ID: ${TENANCY_ID:0:20}..."

# List all compute instances
log_step "Scanning for compute instances..."
INSTANCES_JSON=$(oci compute instance list --compartment-id "$TENANCY_ID" --all 2>/dev/null || echo "[]")

# Count instances
INSTANCE_COUNT=$(echo "$INSTANCES_JSON" | jq -r '.data | length')

if [ "$INSTANCE_COUNT" -eq 0 ]; then
    log_error "No compute instances found in your tenancy."
    echo ""
    echo "Please create an Oracle Cloud compute instance first:"
    echo "  1. Go to Oracle Cloud Console"
    echo "  2. Navigate to Compute → Instances"
    echo "  3. Create a new VM.Standard.A1.Flex instance"
    echo "  4. Use Ubuntu 22.04 image"
    echo "  5. Allocate 4 OCPUs and 24GB RAM (free tier)"
    echo ""
    exit 1
fi

log_info "Found $INSTANCE_COUNT compute instance(s)"

# Select instance
if [ "$INSTANCE_COUNT" -eq 1 ]; then
    SELECTED_INSTANCE=0
    INSTANCE_NAME=$(echo "$INSTANCES_JSON" | jq -r '.data[0]."display-name"')
    log_info "Auto-selected instance: $INSTANCE_NAME"
else
    echo ""
    log_question "Multiple instances found. Please select one:"
    echo ""
    
    # Display instances
    for i in $(seq 0 $((INSTANCE_COUNT - 1))); do
        NAME=$(echo "$INSTANCES_JSON" | jq -r ".data[$i].\"display-name\"")
        STATE=$(echo "$INSTANCES_JSON" | jq -r ".data[$i].\"lifecycle-state\"")
        SHAPE=$(echo "$INSTANCES_JSON" | jq -r ".data[$i].shape")
        
        STATUS_COLOR=$GREEN
        if [ "$STATE" != "RUNNING" ]; then
            STATUS_COLOR=$YELLOW
        fi
        
        echo -e "  [$((i + 1))] ${CYAN}$NAME${NC} - $SHAPE - ${STATUS_COLOR}$STATE${NC}"
    done
    
    echo ""
    read -p "Select instance number [1]: " INSTANCE_NUM
    INSTANCE_NUM=${INSTANCE_NUM:-1}
    SELECTED_INSTANCE=$((INSTANCE_NUM - 1))
    
    INSTANCE_NAME=$(echo "$INSTANCES_JSON" | jq -r ".data[$SELECTED_INSTANCE].\"display-name\"")
fi

# Get instance details
INSTANCE_ID=$(echo "$INSTANCES_JSON" | jq -r ".data[$SELECTED_INSTANCE].id")
INSTANCE_STATE=$(echo "$INSTANCES_JSON" | jq -r ".data[$SELECTED_INSTANCE].\"lifecycle-state\"")
INSTANCE_SHAPE=$(echo "$INSTANCES_JSON" | jq -r ".data[$SELECTED_INSTANCE].shape")

log_info "Selected: $INSTANCE_NAME ($INSTANCE_SHAPE)"

# Check if instance is running
if [ "$INSTANCE_STATE" != "RUNNING" ]; then
    log_warn "Instance is not running (state: $INSTANCE_STATE)"
    read -p "Start this instance? (yes/no): " START_INSTANCE
    
    if [ "$START_INSTANCE" == "yes" ]; then
        log_step "Starting instance..."
        oci compute instance action --action START --instance-id "$INSTANCE_ID" --wait-for-state RUNNING
        log_info "Instance started"
    else
        log_error "Instance must be running to continue"
        exit 1
    fi
fi

# Get public IP
log_step "Retrieving public IP address..."
VNIC_ATTACHMENTS=$(oci compute instance list-vnics --instance-id "$INSTANCE_ID" 2>/dev/null)
PUBLIC_IP=$(echo "$VNIC_ATTACHMENTS" | jq -r '.data[0]."public-ip"')

if [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" == "null" ]; then
    log_error "No public IP found for this instance"
    exit 1
fi

log_info "Public IP: $PUBLIC_IP"

###############################################################################
# Detect SSH Configuration
###############################################################################

log_header "Configuring SSH Access"

# Check for existing SSH key
SSH_KEY_PATH="$HOME/.ssh/koraflow_oracle"

if [ -f "$SSH_KEY_PATH" ]; then
    log_info "Found existing SSH key: $SSH_KEY_PATH"
else
    log_step "Generating new SSH key..."
    ssh-keygen -t ed25519 -C "koraflow-oracle-auto" -f "$SSH_KEY_PATH" -N ""
    log_info "SSH key generated: $SSH_KEY_PATH"
    
    log_warn "You need to add this public key to your Oracle instance"
    echo ""
    echo "Public key:"
    cat "${SSH_KEY_PATH}.pub"
    echo ""
    echo "To add it:"
    echo "  1. Go to Oracle Cloud Console → Compute → Instances"
    echo "  2. Click on $INSTANCE_NAME"
    echo "  3. Scroll to 'Resources' → 'Attached VNICs'"
    echo "  4. Click on the VNIC → 'Resources' → 'Instance Access'"
    echo "  5. Add SSH Keys → Paste the key above"
    echo ""
    read -p "Press Enter after adding the key..."
fi

# Test SSH connection
log_step "Testing SSH connection..."
SSH_USER="ubuntu"  # Default for Ubuntu images

if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "${SSH_USER}@${PUBLIC_IP}" "echo 'SSH test successful'" &>/dev/null; then
    log_info "SSH connection successful"
else
    # Try with opc user (Oracle Linux default)
    SSH_USER="opc"
    if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "${SSH_USER}@${PUBLIC_IP}" "echo 'SSH test successful'" &>/dev/null; then
        log_info "SSH connection successful (using user: opc)"
    else
        log_error "Cannot connect via SSH. Please check:"
        echo "  1. Instance is running"
        echo "  2. Security list allows port 22"
        echo "  3. SSH key is added to instance"
        exit 1
    fi
fi

###############################################################################
# Detect Existing Installation
###############################################################################

log_header "Checking for Existing Installation"

log_step "Scanning for Frappe installation..."

# Check if Frappe is already installed
FRAPPE_EXISTS=$(ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${PUBLIC_IP}" "[ -d /home/frappe/frappe-bench ] && echo 'yes' || echo 'no'" 2>/dev/null)

if [ "$FRAPPE_EXISTS" == "yes" ]; then
    log_info "Frappe installation detected"
    
    # Get site name
    EXISTING_SITE=$(ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${PUBLIC_IP}" "ls /home/frappe/frappe-bench/sites/ 2>/dev/null | grep -v 'assets\|apps.txt\|common_site_config.json' | head -1" 2>/dev/null || echo "")
    
    if [ -n "$EXISTING_SITE" ]; then
        log_info "Found existing site: $EXISTING_SITE"
        
        read -p "Use existing installation? (yes/no) [yes]: " USE_EXISTING
        USE_EXISTING=${USE_EXISTING:-yes}
        
        if [ "$USE_EXISTING" == "yes" ]; then
            SITE_NAME="$EXISTING_SITE"
            FRESH_INSTALL=false
        else
            FRESH_INSTALL=true
        fi
    else
        FRESH_INSTALL=true
    fi
else
    log_info "No existing Frappe installation found"
    FRESH_INSTALL=true
fi

###############################################################################
# Gather Configuration
###############################################################################

log_header "Configuration Setup"

# Get GitHub repository
log_question "Enter your KoraFlow custom app GitHub repository URL:"
echo "  Example: https://github.com/username/koraflow_core.git"
read -p "Repository URL: " GITHUB_REPO

if [ -z "$GITHUB_REPO" ]; then
    log_warn "No custom app repository provided. Using default apps only."
    GITHUB_REPO=""
fi

# Get branch
read -p "Git branch to deploy [main]: " GIT_BRANCH
GIT_BRANCH=${GIT_BRANCH:-main}

# Get domain/site name
if [ "$FRESH_INSTALL" == true ]; then
    log_question "Enter your domain name (or use IP for testing):"
    read -p "Domain/Site name [$PUBLIC_IP]: " SITE_NAME
    SITE_NAME=${SITE_NAME:-$PUBLIC_IP}
fi

log_info "Site name: $SITE_NAME"

# Generate secure passwords
log_step "Generating secure passwords..."
ADMIN_PASSWORD=$(openssl rand -base64 16)
DB_PASSWORD=$(openssl rand -base64 16)
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 16)

# Get API keys (optional)
echo ""
log_question "Do you want to configure API keys now? (optional)"
read -p "Configure API keys? (yes/no) [no]: " CONFIGURE_APIS
CONFIGURE_APIS=${CONFIGURE_APIS:-no}

XERO_CLIENT_ID=""
XERO_CLIENT_SECRET=""
TCG_API_KEY=""
GOOGLE_MAPS_KEY=""

if [ "$CONFIGURE_APIS" == "yes" ]; then
    read -p "Xero Client ID: " XERO_CLIENT_ID
    read -p "Xero Client Secret: " XERO_CLIENT_SECRET
    read -p "The Courier Guy API Key: " TCG_API_KEY
    read -p "Google Maps API Key: " GOOGLE_MAPS_KEY
fi

###############################################################################
# Generate Configuration Files
###############################################################################

log_header "Generating Configuration Files"

CONFIG_DIR="$HOME/.koraflow-config"
mkdir -p "$CONFIG_DIR"

# Save configuration
cat > "$CONFIG_DIR/deployment.conf" <<EOF
# KoraFlow Deployment Configuration
# Generated: $(date)

# Oracle Cloud
ORACLE_IP="$PUBLIC_IP"
ORACLE_INSTANCE_ID="$INSTANCE_ID"
ORACLE_INSTANCE_NAME="$INSTANCE_NAME"
SSH_USER="$SSH_USER"
SSH_KEY_PATH="$SSH_KEY_PATH"

# Application
SITE_NAME="$SITE_NAME"
GITHUB_REPO="$GITHUB_REPO"
GIT_BRANCH="$GIT_BRANCH"

# Credentials
ADMIN_PASSWORD="$ADMIN_PASSWORD"
DB_PASSWORD="$DB_PASSWORD"
MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD"

# API Keys
XERO_CLIENT_ID="$XERO_CLIENT_ID"
XERO_CLIENT_SECRET="$XERO_CLIENT_SECRET"
TCG_API_KEY="$TCG_API_KEY"
GOOGLE_MAPS_KEY="$GOOGLE_MAPS_KEY"

# Flags
FRESH_INSTALL=$FRESH_INSTALL
EOF

chmod 600 "$CONFIG_DIR/deployment.conf"
log_info "Configuration saved to: $CONFIG_DIR/deployment.conf"

# Generate installation script
log_step "Generating installation script..."

cat > "$CONFIG_DIR/install-on-oracle.sh" <<'INSTALL_SCRIPT'
#!/bin/bash
set -e

# Source configuration
source ~/.koraflow-config/deployment.conf

echo "Installing KoraFlow on Oracle Cloud instance..."

# System update
sudo apt update && sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y

# Install prerequisites
sudo apt install -y curl wget git vim htop build-essential pkg-config

# Configure firewall
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp

# Create swap
if [ ! -f /swapfile ]; then
    sudo fallocate -l 8G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
python3 -m pip install --upgrade pip

# Install MariaDB
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash -s -- --mariadb-server-version=10.11
sudo DEBIAN_FRONTEND=noninteractive apt install -y mariadb-server mariadb-client libmariadb-dev

# Secure MariaDB
sudo mysql <<MYSQL_EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
FLUSH PRIVILEGES;
MYSQL_EOF

# Configure MariaDB
sudo tee /etc/mysql/mariadb.conf.d/99-frappe.cnf > /dev/null <<MARIADB_CONF
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
max_connections = 200
max_allowed_packet = 256M
innodb_buffer_pool_size = 4G
MARIADB_CONF

sudo systemctl restart mariadb

# Install Redis
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server

# Install Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 18
npm install -g yarn

# Install other dependencies
sudo apt install -y nginx supervisor wkhtmltopdf libmagic1

# Create frappe user if doesn't exist
if ! id frappe &>/dev/null; then
    sudo useradd -m -s /bin/bash frappe
    echo "frappe ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/frappe
fi

echo "✓ Installation complete!"
INSTALL_SCRIPT

chmod +x "$CONFIG_DIR/install-on-oracle.sh"

# Generate deployment script
cat > "$CONFIG_DIR/deploy-app.sh" <<'DEPLOY_SCRIPT'
#!/bin/bash
set -e

# Source configuration
source $HOME/.koraflow-config/deployment.conf

ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" bash <<'REMOTE'
set -e

# Switch to frappe user
sudo -u frappe bash <<'FRAPPE_SCRIPT'
cd ~

# Install bench if not exists
if ! command -v bench &> /dev/null; then
    pip3 install frappe-bench
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Initialize bench if doesn't exist
if [ ! -d frappe-bench ]; then
    bench init frappe-bench --frappe-branch version-15 --python python3.11
fi

cd frappe-bench

# Create database user
sudo mysql -u root -pMYSQL_ROOT_PASSWORD_PLACEHOLDER <<MYSQL_EOF
CREATE USER IF NOT EXISTS 'koraflow'@'localhost' IDENTIFIED BY 'DB_PASSWORD_PLACEHOLDER';
GRANT ALL PRIVILEGES ON koraflow.* TO 'koraflow'@'localhost';
FLUSH PRIVILEGES;
MYSQL_EOF

# Create site if doesn't exist
if [ ! -d sites/SITE_NAME_PLACEHOLDER ]; then
    bench new-site SITE_NAME_PLACEHOLDER \
        --db-name koraflow \
        --db-password "DB_PASSWORD_PLACEHOLDER" \
        --admin-password "ADMIN_PASSWORD_PLACEHOLDER"
fi

# Get apps
bench get-app erpnext --branch version-15 || true
bench get-app healthcare --branch version-15 || true
bench get-app hrms --branch version-15 || true

# Get custom app if provided
if [ -n "GITHUB_REPO_PLACEHOLDER" ]; then
    bench get-app koraflow_core GITHUB_REPO_PLACEHOLDER --branch GIT_BRANCH_PLACEHOLDER || true
fi

# Install apps
bench --site SITE_NAME_PLACEHOLDER install-app erpnext || true
bench --site SITE_NAME_PLACEHOLDER install-app healthcare || true
bench --site SITE_NAME_PLACEHOLDER install-app hrms || true

if [ -n "GITHUB_REPO_PLACEHOLDER" ]; then
    bench --site SITE_NAME_PLACEHOLDER install-app koraflow_core || true
fi

# Build assets
bench build

echo "✓ Deployment complete!"
FRAPPE_SCRIPT
REMOTE

echo "✓ Remote deployment complete!"
DEPLOY_SCRIPT

# Replace placeholders
sed -i "s|MYSQL_ROOT_PASSWORD_PLACEHOLDER|$MYSQL_ROOT_PASSWORD|g" "$CONFIG_DIR/deploy-app.sh"
sed -i "s|DB_PASSWORD_PLACEHOLDER|$DB_PASSWORD|g" "$CONFIG_DIR/deploy-app.sh"
sed -i "s|ADMIN_PASSWORD_PLACEHOLDER|$ADMIN_PASSWORD|g" "$CONFIG_DIR/deploy-app.sh"
sed -i "s|SITE_NAME_PLACEHOLDER|$SITE_NAME|g" "$CONFIG_DIR/deploy-app.sh"
sed -i "s|GITHUB_REPO_PLACEHOLDER|$GITHUB_REPO|g" "$CONFIG_DIR/deploy-app.sh"
sed -i "s|GIT_BRANCH_PLACEHOLDER|$GIT_BRANCH|g" "$CONFIG_DIR/deploy-app.sh"

chmod +x "$CONFIG_DIR/deploy-app.sh"

log_info "Scripts generated successfully"

###############################################################################
# Execute Installation
###############################################################################

log_header "Installation"

if [ "$FRESH_INSTALL" == true ]; then
    read -p "Ready to install KoraFlow on Oracle Cloud? (yes/no) [yes]: " PROCEED
    PROCEED=${PROCEED:-yes}
    
    if [ "$PROCEED" == "yes" ]; then
        log_step "Uploading installation script..."
        scp -i "$SSH_KEY_PATH" "$CONFIG_DIR/install-on-oracle.sh" "${SSH_USER}@${PUBLIC_IP}:/tmp/"
        
        log_step "Running installation (this may take 30-45 minutes)..."
        ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${PUBLIC_IP}" "bash /tmp/install-on-oracle.sh"
        
        log_info "System installation complete!"
        
        log_step "Deploying application..."
        bash "$CONFIG_DIR/deploy-app.sh"
        
        log_info "Application deployed!"
    fi
else
    log_info "Skipping fresh install (using existing installation)"
fi

###############################################################################
# Setup GitHub Actions
###############################################################################

log_header "GitHub Actions CI/CD Setup"

if [ -n "$GITHUB_REPO" ]; then
    read -p "Setup automated deployments with GitHub Actions? (yes/no) [yes]: " SETUP_GITHUB
    SETUP_GITHUB=${SETUP_GITHUB:-yes}
    
    if [ "$SETUP_GITHUB" == "yes" ]; then
        log_step "To complete GitHub Actions setup:"
        echo ""
        echo "1. Go to your repository: $GITHUB_REPO"
        echo "2. Navigate to Settings → Secrets and variables → Actions"
        echo "3. Add these secrets:"
        echo ""
        echo "   Name: ORACLE_HOST"
        echo "   Value: $PUBLIC_IP"
        echo ""
        echo "   Name: SSH_PRIVATE_KEY"
        echo "   Value: (paste content below)"
        echo ""
        cat "$SSH_KEY_PATH"
        echo ""
        echo "4. Copy the workflow file from koraflow-deployment-scripts/github-actions-deploy.yml"
        echo "   to .github/workflows/ in your repository"
        echo ""
        read -p "Press Enter after setting up GitHub secrets..."
    fi
fi

###############################################################################
# Summary
###############################################################################

log_header "Setup Complete!"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    🎉 SUCCESS! 🎉"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}Instance Information:${NC}"
echo "  Public IP:     $PUBLIC_IP"
echo "  Instance Name: $INSTANCE_NAME"
echo "  SSH User:      $SSH_USER"
echo "  SSH Key:       $SSH_KEY_PATH"
echo ""
echo -e "${CYAN}Application:${NC}"
echo "  Site URL:      http://$PUBLIC_IP"
echo "  Site Name:     $SITE_NAME"
echo "  Admin User:    Administrator"
echo "  Admin Pass:    $ADMIN_PASSWORD"
echo ""
echo -e "${CYAN}Database:${NC}"
echo "  Root Password: $MYSQL_ROOT_PASSWORD"
echo "  User Password: $DB_PASSWORD"
echo ""
echo -e "${CYAN}Configuration:${NC}"
echo "  Config file:   $CONFIG_DIR/deployment.conf"
echo "  Install script: $CONFIG_DIR/install-on-oracle.sh"
echo "  Deploy script:  $CONFIG_DIR/deploy-app.sh"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Save these credentials securely!${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo "1. Access your application:"
echo "   → Open browser: http://$PUBLIC_IP"
echo ""
echo "2. SSH to your server:"
echo "   → ssh -i $SSH_KEY_PATH ${SSH_USER}@${PUBLIC_IP}"
echo ""
echo "3. Enable SSL (after DNS is pointed):"
echo "   → sudo certbot --nginx -d $SITE_NAME"
echo ""
echo "4. View logs:"
echo "   → ssh ... 'tail -f /home/frappe/frappe-bench/logs/web.log'"
echo ""
echo "5. Deploy updates:"
echo "   → Just push to GitHub (if Actions configured)"
echo "   → Or run: bash $CONFIG_DIR/deploy-app.sh"
echo ""
echo "═══════════════════════════════════════════════════════════════"

# Save credentials to file
CREDS_FILE="$CONFIG_DIR/CREDENTIALS.txt"
cat > "$CREDS_FILE" <<EOF
KoraFlow Oracle Cloud Credentials
Generated: $(date)

Instance Information:
  Public IP:     $PUBLIC_IP
  Instance ID:   $INSTANCE_ID
  Instance Name: $INSTANCE_NAME
  SSH User:      $SSH_USER
  SSH Key:       $SSH_KEY_PATH

Application:
  Site URL:      http://$PUBLIC_IP
  Site Name:     $SITE_NAME
  Admin User:    Administrator
  Admin Pass:    $ADMIN_PASSWORD

Database:
  Root Password: $MYSQL_ROOT_PASSWORD
  User Password: $DB_PASSWORD

GitHub:
  Repository:    $GITHUB_REPO
  Branch:        $GIT_BRANCH

API Keys:
  Xero Client ID:     $XERO_CLIENT_ID
  Xero Client Secret: $XERO_CLIENT_SECRET
  TCG API Key:        $TCG_API_KEY
  Google Maps Key:    $GOOGLE_MAPS_KEY

Configuration Files:
  Main Config:   $CONFIG_DIR/deployment.conf
  Install Script: $CONFIG_DIR/install-on-oracle.sh
  Deploy Script:  $CONFIG_DIR/deploy-app.sh

EOF

chmod 600 "$CREDS_FILE"

echo ""
log_info "Credentials saved to: $CREDS_FILE"
echo ""
echo "🚀 Your KoraFlow application is ready!"
