#!/bin/bash
set -e

SERVER="frappe@156.38.193.194"
KEY="$HOME/.ssh/koraflow_deploy"
APP_DIR="bench/apps/koraflow_core"
REMOTE_DIR="/home/frappe/frappe-bench/apps/koraflow_core"

echo "==> Syncing koraflow_core to server..."
rsync -az --delete \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='*.egg-info' \
  -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  $APP_DIR/ \
  $SERVER:$REMOTE_DIR/

echo "==> Running post-deploy steps on server..."
ssh -i "$KEY" -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
  set -e
  export PATH=/home/frappe/.local/bin:/usr/local/bin:$PATH
  cd /home/frappe/frappe-bench

  echo "--- Reinstalling python package..."
  ./env/bin/pip install -e apps/koraflow_core --quiet

  echo "--- Ensuring koraflow_core.pth is correct (fixes namespace package issue)..."
  echo "/home/frappe/frappe-bench/apps/koraflow_core" > env/lib/python3.11/site-packages/koraflow_core.pth

  echo "--- Fixing asset symlink (ensure it points to deployed path)..."
  rm -f sites/assets/koraflow_core
  ln -s /home/frappe/frappe-bench/apps/koraflow_core/koraflow_core/public sites/assets/koraflow_core

  echo "--- Running migrations..."
  bench --site portal.slim2well.com migrate || echo "WARNING: migrate had errors, continuing..."

  echo "--- Building all app assets (frappe + erpnext + koraflow_core)..."
  cd apps/frappe && yarn run production 2>&1 | tail -30
  cd /home/frappe/frappe-bench

  echo "--- Ensuring branding settings (favicon, logo, login page)..."
  bench --site portal.slim2well.com execute frappe.db.set_value \
    --args '["Website Settings", "Website Settings", "favicon", "/assets/koraflow_core/images/s2w-favicon.svg"]'
  bench --site portal.slim2well.com execute frappe.db.set_value \
    --args '["Website Settings", "Website Settings", "app_logo_url", "/assets/koraflow_core/images/s2w_logo.png"]'
  bench --site portal.slim2well.com execute frappe.db.set_value \
    --args '["Website Settings", "Website Settings", "login_page", "s2w_login"]'
  bench --site portal.slim2well.com execute frappe.db.set_value \
    --args '["Navbar Settings", "Navbar Settings", "app_logo", "/assets/koraflow_core/images/s2w_logo.png"]'

  echo "--- Clearing caches..."
  bench --site portal.slim2well.com clear-cache
  bench --site portal.slim2well.com clear-website-cache

  echo "--- Turning off maintenance mode..."
  bench --site portal.slim2well.com set-maintenance-mode off

  echo "--- Restarting services..."
  sudo supervisorctl restart frappe-bench-web:frappe-bench-frappe-web
  sudo supervisorctl restart frappe-bench-workers:

  echo "--- Done."
ENDSSH

echo ""
echo "Deploy complete. https://portal.slim2well.com"
