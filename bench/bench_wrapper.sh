#!/bin/bash
# Bench wrapper script to invoke Frappe commands through Python module

# Get the directory where this script is located
BENCH_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$BENCH_DIR/env/bin/activate"

# Set PYTHONPATH
export PYTHONPATH="$BENCH_DIR/apps:$PYTHONPATH"

# Change to sites directory for Frappe commands
cd "$BENCH_DIR/sites"

# Execute the frappe command through Python module
exec python -m frappe.utils.bench_helper frappe "$@"
