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

  echo "--- Running migrations..."
  bench --site portal.slim2well.com migrate || echo "WARNING: migrate had errors, continuing..."

  echo "--- Building assets..."
  bench build

  echo "--- Restarting services..."
  sudo supervisorctl restart frappe-bench-web:frappe-bench-frappe-web
  sudo supervisorctl restart frappe-bench-workers:

  echo "--- Done."
ENDSSH

echo ""
echo "Deploy complete. https://portal.slim2well.com"
