#!/bin/bash
# Script to fix database user for koraflow-site
# This script will attempt to create the database user using different methods

echo "=========================================="
echo "Fixing Database User for koraflow-site"
echo "=========================================="
echo ""

DB_USER="_64e6cfac4c3befcd"
DB_PASSWORD="NQtKKkmaNvAEsbNd"
DB_NAME="_64e6cfac4c3befcd"

# Method 1: Try with sudo mysql (works on macOS with Homebrew MariaDB)
echo "Attempting Method 1: sudo mysql..."
if sudo mysql < fix_database_user.sql 2>/dev/null; then
    echo "✓ Successfully created database user using sudo mysql"
    exit 0
fi

# Method 2: Try with mysql -u root -p (requires password)
echo ""
echo "Method 1 failed. Please run manually:"
echo "  Option A: sudo mysql < fix_database_user.sql"
echo "  Option B: mysql -u root -p < fix_database_user.sql"
echo ""
echo "Or run these SQL commands manually:"
echo ""
echo "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
echo "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;"
echo "GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';"
echo "FLUSH PRIVILEGES;"
echo ""
echo "After running the SQL commands, test the connection:"
echo "  mysql -u '${DB_USER}' -p'${DB_PASSWORD}' -e \"SELECT 1;\""
echo ""
echo "Then restart the Frappe server:"
echo "  cd /Users/tjaartprinsloo/Documents/KoraFlow/bench"
echo "  kill \$(lsof -ti:8000) 2>/dev/null"
echo "  source env/bin/activate"
echo "  export PYTHONPATH=\"/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps:\$PYTHONPATH\""
echo "  cd sites"
echo "  python3 -m frappe.utils.bench_helper frappe serve --port 8000"

