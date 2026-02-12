#!/bin/bash
# Startup script for Frappe services

cd /Users/tjaartprinsloo/Documents/KoraFlow/bench

# Activate virtual environment
source env/bin/activate

# Note: Do NOT set PYTHONPATH to apps/ directory as it causes koraflow_core
# to be imported as a namespace package with __file__=None, breaking Frappe's
# www page resolution. The editable pip install handles module discovery.

# Change to sites directory (required for Frappe)
cd sites

# Start Frappe web server
echo "Starting Frappe web server on port 8080..."
python -m frappe.utils.bench_helper frappe --site koraflow-site serve --port 8080 >> ../logs/web.log 2>&1 &
WEB_PID=$!

# Go back to bench directory for other services
cd ..

# Start socketio server
echo "Starting SocketIO server on port 9000..."
/Users/tjaartprinsloo/.nvm/versions/node/v18.20.8/bin/node apps/frappe/socketio.js &
SOCKETIO_PID=$!

# Start worker
echo "Starting Frappe worker..."
cd sites
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES NO_PROXY=* python -m frappe.utils.bench_helper frappe --site koraflow-site worker >> ../logs/worker.log 2>> ../logs/worker.error.log &
WORKER_PID=$!
cd ..

# Start scheduler
echo "Starting Frappe scheduler..."
cd sites
python -m frappe.utils.bench_helper frappe --site koraflow-site schedule &
SCHEDULE_PID=$!
cd ..

echo "All Frappe services started!"
echo "Web server PID: $WEB_PID (port 8080)"
echo "SocketIO PID: $SOCKETIO_PID (port 9000)"
echo "Worker PID: $WORKER_PID"
echo "Scheduler PID: $SCHEDULE_PID"

# Wait for all processes
wait
