#!/usr/bin/env python3
import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

# Check workspace
workspaces = frappe.get_all('Workspace', filters={'title': ['like', '%Sales Partner%']}, fields=['name', 'title', 'public'])
print('Sales Partner Workspaces:')
for ws in workspaces:
    print(f'  {ws.name}: {ws.title} (public: {ws.public})')
    roles = frappe.get_all('Has Role', filters={'parent': ws.name, 'parenttype': 'Workspace'}, fields=['role'])
    print(f'    Roles: {[r.role for r in roles]}')

# Check Commission Dashboard
comm_ws = frappe.get_all('Workspace', filters={'name': 'Commission Dashboard'}, fields=['name', 'title', 'public'])
if comm_ws:
    ws = comm_ws[0]
    print(f'\nCommission Dashboard: {ws.name} (public: {ws.public})')
    roles = frappe.get_all('Has Role', filters={'parent': ws.name, 'parenttype': 'Workspace'}, fields=['role'])
    print(f'  Roles: {[r.role for r in roles]}')
    
    # Check content
    ws_doc = frappe.get_doc('Workspace', ws.name)
    print(f'  Content length: {len(ws_doc.content or [])}')

frappe.destroy()

