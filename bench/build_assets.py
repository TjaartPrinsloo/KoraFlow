#!/usr/bin/env python3
"""Build assets for koraflow_core app"""
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
from frappe.build import bundle
from frappe.commands import popen

# Initialize Frappe (no site needed for build)
frappe.init("")

# Make popen available to frappe.commands for build.py
if not hasattr(frappe, 'commands'):
    import frappe.commands
frappe.commands.popen = popen

try:
    print("Building assets for koraflow_core...")
    bundle(
        mode="build",
        apps="koraflow_core",
        verbose=True,
        skip_frappe=False
    )
    print("✓ Assets built successfully!")
except Exception as e:
    print(f"✗ Error building assets: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    frappe.destroy()

