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
    echo "ERPNext already installed"
fi

# Install ERPNext Healthcare (KoraFlow Healthcare)
echo ""
echo "Installing ERPNext Healthcare (KoraFlow Healthcare)..."
if [ ! -d "apps/healthcare" ]; then
    bench get-app healthcare --branch version-15
    bench --site "$SITE_NAME" install-app healthcare
else
    echo "Healthcare already installed"
fi

# Install Frappe HRMS (KoraFlow Workforce)
echo ""
echo "Installing Frappe HRMS (KoraFlow Workforce)..."
if [ ! -d "apps/hrms" ]; then
    bench get-app hrms --branch version-15
    bench --site "$SITE_NAME" install-app hrms
else
    echo "HRMS already installed"
fi

# Install ERPNext CRM (KoraFlow CRM)
echo ""
echo "Installing ERPNext CRM (KoraFlow CRM)..."
if [ ! -d "apps/crm" ]; then
    bench get-app crm --branch version-15
    bench --site "$SITE_NAME" install-app crm
else
    echo "CRM already installed"
fi

# Install Frappe Insights (KoraFlow Insights)
echo ""
echo "Installing Frappe Insights (KoraFlow Insights)..."
if [ ! -d "apps/insights" ]; then
    bench get-app insights --branch develop
    bench --site "$SITE_NAME" install-app insights
else
    echo "Insights already installed"
fi

# Install Frappe Drive (KoraFlow Drive)
echo ""
echo "Installing Frappe Drive (KoraFlow Drive)..."
if [ ! -d "apps/drive" ]; then
    bench get-app drive --branch version-15
    bench --site "$SITE_NAME" install-app drive
else
    echo "Drive already installed"
fi

# Install Frappe Gameplan (KoraFlow Gameplan)
echo ""
echo "Installing Frappe Gameplan (KoraFlow Gameplan)..."
if [ ! -d "apps/gameplan" ]; then
    bench get-app gameplan --branch version-15
    bench --site "$SITE_NAME" install-app gameplan
else
    echo "Gameplan already installed"
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

