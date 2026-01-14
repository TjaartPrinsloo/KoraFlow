#!/usr/bin/env python3
"""
Script to setup Sales Agent system
Run from bench directory: python3 ../run_sales_agent_setup.py
"""

import sys
import os

# Add bench apps to path
bench_path = os.path.join(os.path.dirname(__file__), 'bench')
apps_path = os.path.join(bench_path, 'apps')
sites_path = os.path.join(bench_path, 'sites')

sys.path.insert(0, apps_path)
os.chdir(sites_path)

# Initialize Frappe
import frappe
frappe.init(site='koraflow-site', sites_path=sites_path)
frappe.connect()

# Run setup
from koraflow_core.koraflow_core.setup_sales_agent import setup_sales_agent_system
print("Setting up Sales Agent system...")
setup_sales_agent_system()
print("✓ Setup complete!")

frappe.db.commit()
frappe.destroy()

