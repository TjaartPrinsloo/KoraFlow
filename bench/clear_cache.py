#!/usr/bin/env python3
"""
Clear Frappe cache
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
    frappe.clear_cache()
    print('✅ Cache cleared successfully')
    print()
    print('Next steps:')
    print('1. Hard refresh your browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)')
    print('2. Or clear browser cache completely')
    print('3. Check if HR submenu items appear')
except Exception as e:
    print(f'Error: {e}')
finally:
    frappe.destroy()

