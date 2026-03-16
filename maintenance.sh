#!/bin/bash
# Usage: ./maintenance.sh on|off
KEY="$HOME/.ssh/koraflow_deploy"
SERVER="frappe@156.38.193.194"
MODE=${1:-on}

ssh -i "$KEY" -o StrictHostKeyChecking=no "$SERVER" << ENDSSH
  export PATH=/home/frappe/.local/bin:/usr/local/bin:\$PATH
  cd /home/frappe/frappe-bench
  bench --site portal.slim2well.com set-maintenance-mode $MODE
  echo "Maintenance mode: $MODE"
ENDSSH
