#!/usr/bin/env python3
"""
Setup Sales Agent System
Run from bench directory: python3 setup_sales_agent_system.py
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("=" * 80)
    print("SETTING UP SALES AGENT SYSTEM")
    print("=" * 80)
    print()
    
    from koraflow_core.koraflow_core.setup_sales_agent import setup_sales_agent_system
    setup_sales_agent_system()
    
    print()
    print("=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    
    frappe.db.commit()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    frappe.db.rollback()
finally:
    frappe.destroy()

