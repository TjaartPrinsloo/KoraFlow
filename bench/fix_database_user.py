#!/usr/bin/env python3
"""
Fix database user for koraflow-site
This script recreates the database user with the correct password
"""
import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, os.path.join(bench_dir, 'apps'))

import frappe
from frappe.database.db_manager import DbManager
from frappe.database.mariadb.setup_db import get_root_connection

# Initialize Frappe
sites_path = os.path.join(bench_dir, 'sites')
frappe.init(site='koraflow-site', sites_path=sites_path)
frappe.local.session = frappe._dict({'user': 'Administrator'})

db_name = frappe.conf.db_name
db_password = frappe.conf.db_password

print(f"Attempting to fix database user: {db_name}")
print(f"Password from config: {'*' * len(db_password)}")

# Try to get root connection
# Common root passwords to try
root_passwords = ['', 'root', 'frappe', None]

root_conn = None
for pwd in root_passwords:
    try:
        root_conn = get_root_connection('root', pwd)
        print(f"✓ Connected to MariaDB as root")
        break
    except Exception as e:
        continue

if not root_conn:
    print("\n✗ Could not connect to MariaDB as root.")
    print("\nPlease run the following SQL commands manually:")
    print(f"  mysql -u root -p")
    print(f"  CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_password}';")
    print(f"  CREATE DATABASE IF NOT EXISTS `{db_name}`;")
    print(f"  GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_name}'@'localhost';")
    print(f"  FLUSH PRIVILEGES;")
    sys.exit(1)

# Create database manager
dbman = DbManager(root_conn)

try:
    # Delete existing user if exists
    try:
        dbman.delete_user(db_name)
        print(f"✓ Deleted existing user {db_name}")
    except:
        print(f"  (User {db_name} didn't exist, creating new one)")

    # Create user
    dbman.create_user(db_name, db_password)
    print(f"✓ Created user {db_name}")

    # Create database if not exists
    if db_name not in dbman.get_database_list():
        dbman.create_database(db_name)
        print(f"✓ Created database {db_name}")
    else:
        print(f"✓ Database {db_name} already exists")

    # Grant privileges
    dbman.grant_all_privileges(db_name, db_name)
    dbman.flush_privileges()
    print(f"✓ Granted privileges to user {db_name}")

    root_conn.close()
    print("\n✓ Database user setup complete!")
    print("\nYou can now start the server with:")
    print("  cd /Users/tjaartprinsloo/Documents/KoraFlow/bench")
    print("  source env/bin/activate")
    print("  export PYTHONPATH=\"/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps:$PYTHONPATH\"")
    print("  cd sites")
    print("  python3 -m frappe.utils.bench_helper frappe serve --port 8000")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

