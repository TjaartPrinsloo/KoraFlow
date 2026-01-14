#!/usr/bin/env python3
"""Run Frappe migration to apply patches"""
import sys
import os

# Change to bench directory
bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

# Add apps to path
apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

# Change to sites directory for frappe.init
sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe
from frappe.commands.site import migrate
from frappe.migrate import SiteMigration

# Initialize and connect
frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Running migration for site: koraflow-site")
    print("=" * 50)
    
    # Create migration instance and run
    migration = SiteMigration(skip_failing=False, skip_search_index=False)
    migration.run(site='koraflow-site')
    
    print("=" * 50)
    print("✓ Migration completed successfully!")
    
except Exception as e:
    print(f"✗ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

