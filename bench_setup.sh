#!/bin/bash
# KoraFlow Bench Setup Script
# Installs Bench, Frappe Framework, and all required modules

set -e

echo "=========================================="
echo "KoraFlow Bench Setup"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 is required"; exit 1; }

# Check if Python 3.10+
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "Python version: $PYTHON_VERSION ✓"

# Install Bench CLI
echo ""
echo "Installing Bench CLI..."
if ! command -v bench &> /dev/null; then
    # Try user install first (no sudo required)
    pip3 install --user frappe-bench
    # Add user bin to PATH if not already there
    export PATH="$HOME/Library/Python/3.9/bin:$PATH"
    # If still not found, try with sudo (will prompt)
    if ! command -v bench &> /dev/null; then
        echo "Attempting sudo install (you may be prompted for password)..."
        sudo pip3 install frappe-bench
    fi
else
    echo "Bench CLI already installed"
fi

# Initialize Bench
echo ""
echo "Initializing Bench..."
BENCH_DIR="${BENCH_DIR:-$(pwd)/bench}"
if [ ! -d "$BENCH_DIR" ]; then
    bench init --frappe-branch version-15 --skip-redis-config-generation "$BENCH_DIR"
else
    echo "Bench directory already exists: $BENCH_DIR"
fi

cd "$BENCH_DIR"

# Helper function to check if app is installed on site
check_app_installed() {
    local app_name=$1
    python3 -c "
import sys
sys.path.insert(0, 'apps')
import os
os.chdir('sites')
import frappe
frappe.init(site='$SITE_NAME')
frappe.connect()
apps = frappe.get_installed_apps()
result = '$app_name' in apps
frappe.destroy()
sys.exit(0 if result else 1)
" 2>/dev/null
}

# Create site
echo ""
echo "Creating site..."
SITE_NAME="${SITE_NAME:-koraflow-site}"
if [ ! -d "sites/$SITE_NAME" ]; then
    bench new-site "$SITE_NAME" --mariadb-root-password admin --admin-password admin --mariadb-user-host-login-scope='%'
else
    echo "Site already exists: $SITE_NAME"
fi

# Install Frappe Framework (already installed with bench init)
echo ""
echo "Frappe Framework installed ✓"

# Install ERPNext
echo ""
echo "Installing ERPNext..."
if [ ! -d "apps/erpnext" ]; then
    bench get-app erpnext --branch version-15
    bench --site "$SITE_NAME" install-app erpnext
else
    if check_app_installed "erpnext"; then
        echo "ERPNext already installed on site"
    else
        echo "ERPNext app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app erpnext
    fi
fi

# Install ERPNext Healthcare (KoraFlow Healthcare)
echo ""
echo "Installing ERPNext Healthcare (KoraFlow Healthcare)..."
if [ ! -d "apps/healthcare" ]; then
    bench get-app healthcare --branch version-15
    bench --site "$SITE_NAME" install-app healthcare
else
    if check_app_installed "healthcare"; then
        echo "Healthcare already installed on site"
    else
        echo "Healthcare app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app healthcare
    fi
fi

# Install Frappe HRMS (KoraFlow Workforce)
echo ""
echo "Installing Frappe HRMS (KoraFlow Workforce)..."
if [ ! -d "apps/hrms" ]; then
    bench get-app hrms --branch version-15
    bench --site "$SITE_NAME" install-app hrms
else
    if check_app_installed "hrms"; then
        echo "HRMS already installed on site"
    else
        echo "HRMS app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app hrms
    fi
fi

# Install ERPNext CRM (KoraFlow CRM)
echo ""
echo "Installing ERPNext CRM (KoraFlow CRM)..."
if [ ! -d "apps/crm" ]; then
    bench get-app crm --branch version-15
    bench --site "$SITE_NAME" install-app crm
else
    if check_app_installed "crm"; then
        echo "CRM already installed on site"
    else
        echo "CRM app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app crm
    fi
fi

# Install Frappe Insights (KoraFlow Insights)
echo ""
echo "Installing Frappe Insights (KoraFlow Insights)..."
if [ ! -d "apps/insights" ]; then
    bench get-app insights --branch develop
    bench --site "$SITE_NAME" install-app insights
else
    if check_app_installed "insights"; then
        echo "Insights already installed on site"
    else
        echo "Insights app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app insights
    fi
fi

# Install Frappe Drive (KoraFlow Drive)
echo ""
echo "Installing Frappe Drive (KoraFlow Drive)..."
if [ ! -d "apps/drive" ]; then
    bench get-app drive --branch version-15
    bench --site "$SITE_NAME" install-app drive
else
    if check_app_installed "drive"; then
        echo "Drive already installed on site"
    else
        echo "Drive app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app drive
    fi
fi

# Install Frappe Gameplan (KoraFlow Gameplan)
echo ""
echo "Installing Frappe Gameplan (KoraFlow Gameplan)..."
if [ ! -d "apps/gameplan" ]; then
    bench get-app gameplan --branch version-15
    bench --site "$SITE_NAME" install-app gameplan
else
    if check_app_installed "gameplan"; then
        echo "Gameplan already installed on site"
    else
        echo "Gameplan app directory exists but not installed on site. Installing now..."
        bench --site "$SITE_NAME" install-app gameplan
    fi
fi

echo ""
echo "=========================================="
echo "Bench setup complete!"
echo "=========================================="
echo ""
echo "To start the development server:"
echo "  cd $BENCH_DIR"
echo "  bench start"
echo ""
echo "Site URL: http://localhost:8000"
echo "Site name: $SITE_NAME"
echo ""

