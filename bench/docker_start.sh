#!/bin/bash
# Script to start Frappe in Docker with proper configuration

cd /workspace/bench

# Update site config for Docker network (if running in Docker)
if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "127.0.0.1" ]; then
    SITE_CONFIG="/workspace/bench/sites/koraflow-site/site_config.json"
    if [ -f "$SITE_CONFIG" ]; then
        # Backup original
        cp "$SITE_CONFIG" "${SITE_CONFIG}.bak"
        
        # Update for Docker
        python3 << EOF
import json
import os

config_path = "$SITE_CONFIG"
with open(config_path, 'r') as f:
    config = json.load(f)

# Update database connection for Docker
config['db_host'] = os.getenv('DB_HOST', 'mariadb')
config['db_port'] = int(os.getenv('DB_PORT', '3306'))

# Update Redis for Docker
redis_host = os.getenv('REDIS_CACHE', 'redis://redis:6379').replace('redis://', '').split(':')[0]
redis_port = os.getenv('REDIS_CACHE', 'redis://redis:6379').replace('redis://', '').split(':')[1] if ':' in os.getenv('REDIS_CACHE', 'redis://redis:6379').replace('redis://', '') else '6379'
config['redis_cache'] = f"redis://{redis_host}:{redis_port}"
config['redis_queue'] = f"redis://{redis_host}:{redis_port}"
config['redis_socketio'] = f"redis://{redis_host}:{redis_port}"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=1)
EOF
    fi
fi

# Set up environment - critical for finding frappe
export PYTHONPATH="/workspace/bench/apps:$PYTHONPATH"

# Change to sites directory (required for frappe)
cd /workspace/bench/sites

# Use Python to import and run frappe directly
exec python3 << 'PYTHON_SCRIPT'
import sys
import os

# Ensure apps are in path
sys.path.insert(0, '/workspace/bench/apps')
os.chdir('/workspace/bench/sites')

# Now import frappe - it should be found
import frappe.utils.bench_helper as bench_helper

# Run the serve command
import sys as _sys
_sys.argv = ['frappe', 'serve', '--host', '0.0.0.0', '--port', '8080', '--site', 'koraflow-site']
bench_helper.main()
PYTHON_SCRIPT
