#!/usr/bin/env python3
"""
Fix Workspace Name/Title Mismatch

The workspace name is "Commission Dashboard" but title is "Sales Partner Dashboard".
The router uses the name slug, so we should either:
1. Change the name to match the title, OR
2. Change the title to match the name

Let's change the name to "Sales Partner Dashboard" so it matches the title.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.desk.utils import slug

WORKSPACE_NAME = "Commission Dashboard"

frappe.init(site='koraflow-site')
frappe.connect()

# Switch to Administrator
frappe.set_user("Administrator")

try:
    print("Fixing workspace name/title mismatch...")
    print()
    
    ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    print(f"Current name: {ws.name}")
    print(f"Current title: {ws.title}")
    print()
    
    # Rename workspace to match title
    new_name = "Sales Partner Dashboard"
    
    print(f"Renaming workspace from '{ws.name}' to '{new_name}'...")
    frappe.rename_doc("Workspace", ws.name, new_name, force=1)
    frappe.db.commit()
    
    # Verify
    ws_new = frappe.get_doc("Workspace", new_name)
    print(f"✓ Renamed successfully")
    print(f"  New name: {ws_new.name}")
    print(f"  Title: {ws_new.title}")
    print()
    
    # Calculate slugs
    name_slug = slug(ws_new.name.lower())
    print(f"Workspace slug: {name_slug}")
    print()
    print(f"Workspace should now be accessible at:")
    print(f"  /app/{name_slug}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

