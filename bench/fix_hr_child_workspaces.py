#!/usr/bin/env python3
"""
Fix HR child workspaces to show as submenu items
Sets parent_page for child workspaces so they appear in sidebar
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

# Map workspace names (as they appear in database) to their display names
WORKSPACE_MAP = {
    'Recruitment': 'Recruitment',
    'Employee Lifecycle': 'Employee Lifecycle',
    'Shift & Attendance': 'Shift & Attendance',
    'Performance': 'Performance',
    'Leaves': 'Leaves',
    'Expense Claims': 'Expense Claims'
}

PARENT_WORKSPACE = 'HR'

try:
    print('=' * 80)
    print('FIXING HR CHILD WORKSPACES')
    print('=' * 80)
    print()
    
    # First, check current state
    print('Current state:')
    print('-' * 80)
    for ws_name, display_name in WORKSPACE_MAP.items():
        if frappe.db.exists('Workspace', ws_name):
            ws = frappe.get_doc('Workspace', ws_name)
            print(f'{display_name}:')
            print(f'  Parent Page: {ws.parent_page or "None"}')
            print(f'  Is Hidden: {ws.is_hidden}')
            print(f'  Public: {ws.public}')
            print()
        else:
            print(f'{display_name}: ❌ Not found')
            print()
    
    print()
    print('Updating parent_page...')
    print('-' * 80)
    
    updated_count = 0
    for ws_name, display_name in WORKSPACE_MAP.items():
        if frappe.db.exists('Workspace', ws_name):
            ws = frappe.get_doc('Workspace', ws_name)
            
            needs_update = False
            
            # Check parent_page
            if ws.parent_page != PARENT_WORKSPACE:
                ws.parent_page = PARENT_WORKSPACE
                needs_update = True
            
            # Check if hidden - unhide child workspaces
            if ws.is_hidden:
                ws.is_hidden = 0
                needs_update = True
            
            if needs_update:
                ws.flags.ignore_permissions = True
                ws.save()
                frappe.db.commit()
                changes = []
                if ws.parent_page == PARENT_WORKSPACE and ws.parent_page != PARENT_WORKSPACE:
                    changes.append('parent_page')
                if not ws.is_hidden:
                    changes.append('unhidden')
                print(f'✅ {display_name}: Updated ({", ".join(changes)})')
                updated_count += 1
            else:
                print(f'✓ {display_name}: Already configured correctly')
        else:
            print(f'⚠️  {display_name}: Workspace not found')
    
    print()
    print('=' * 80)
    print(f'✅ Updated {updated_count} workspace(s)')
    print('=' * 80)
    print()
    print('Next steps:')
    print('1. Clear cache: bench clear-cache')
    print('2. Hard refresh browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)')
    print('3. Check sidebar - HR should now show expandable submenu items')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    frappe.db.rollback()
finally:
    frappe.destroy()

