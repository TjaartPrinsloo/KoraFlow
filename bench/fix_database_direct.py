#!/usr/bin/env python3
"""
Fix database user for koraflow-site using direct SQL
"""
import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, os.path.join(bench_dir, 'apps'))

import frappe
from frappe.database.mariadb.setup_db import get_root_connection

# Initialize Frappe
sites_path = os.path.join(bench_dir, 'sites')
frappe.init(site='koraflow-site', sites_path=sites_path)
frappe.local.session = frappe._dict({'user': 'Administrator'})

db_name = frappe.conf.db_name
db_password = frappe.conf.db_password

print(f"Attempting to fix database user: {db_name}")

# Try to get root connection
root_password = frappe.conf.get("root_password")
root_login = frappe.conf.get("root_login", "root")

# Try common passwords and socket connection
root_passwords = [root_password, '', 'root', 'frappe', None]

root_conn = None
for pwd in root_passwords:
    try:
        frappe.flags.root_login = root_login
        frappe.flags.root_password = pwd
        root_conn = get_root_connection(root_login, pwd)
        print(f"✓ Connected to MariaDB as root")
        break
    except Exception as e:
        continue

if not root_conn:
    print("\n✗ Could not connect to MariaDB as root.")
    print("Please run manually: sudo mysql < fix_database_user.sql")
    sys.exit(1)

try:
    # Use root connection to execute SQL directly
    print(f"\nCreating user and database...")
    
    # Delete existing user if exists
    try:
        root_conn.sql(f"DROP USER IF EXISTS '{db_name}'@'localhost'")
        print(f"✓ Deleted existing user {db_name} (if existed)")
    except:
        pass

    # Create user
    root_conn.sql(f"CREATE USER '{db_name}'@'localhost' IDENTIFIED BY '{db_password}'")
    print(f"✓ Created user {db_name}")

    # Create database if not exists
    root_conn.sql(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    print(f"✓ Created/verified database {db_name}")

    # Grant privileges
    root_conn.sql(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_name}'@'localhost'")
    root_conn.sql("FLUSH PRIVILEGES")
    print(f"✓ Granted privileges to user {db_name}")

    root_conn.close()
    print("\n✓ Database user setup complete!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

