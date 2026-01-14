#!/usr/bin/env python3
"""
Verify Workspace Slug Calculation

Check what slug Frappe will use for the workspace in client-side JavaScript.
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

try:
    ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    
    # Frappe uses slug(page.name) in client-side JavaScript
    # See: frappe.workspaces[frappe.router.slug(page.name)] = page;
    name_slug = slug(ws.name.lower())
    title_slug = slug(ws.title.lower())
    
    print("Workspace slug calculation:")
    print(f"  Name: {ws.name}")
    print(f"  Title: {ws.title}")
    print()
    print(f"  Slug from name: {name_slug}")
    print(f"  Slug from title: {title_slug}")
    print()
    print("Client-side JavaScript will use:")
    print(f"  frappe.workspaces['{name_slug}']")
    print()
    print("So the route should be:")
    print(f"  /app/{name_slug}")
    print()
    print("Current URL being accessed:")
    print(f"  /app/commission-dashboard")
    print()
    
    if name_slug == "commission-dashboard":
        print("✓ Slug matches!")
    else:
        print(f"❌ Slug mismatch! Expected '{name_slug}' but URL uses 'commission-dashboard'")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

