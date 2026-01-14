#!/usr/bin/env python3
"""
Verify HR child workspaces are being returned correctly
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
    from frappe.desk.desktop import get_workspace_sidebar_items
    
    result = get_workspace_sidebar_items()
    pages = result.get('pages', [])
    
    print('=' * 80)
    print('VERIFYING HR CHILD WORKSPACES IN API RESPONSE')
    print('=' * 80)
    print()
    
    # Find HR workspace
    hr_workspace = None
    hr_children = []
    
    for page in pages:
        if page.get('name') == 'HR' or page.get('title') == 'HR':
            hr_workspace = page
        elif page.get('parent_page') == 'HR':
            hr_children.append(page)
    
    if hr_workspace:
        print('✅ HR Workspace Found:')
        print(f'   Name: {hr_workspace.get("name")}')
        print(f'   Title: {hr_workspace.get("title")}')
        print(f'   Is Hidden: {hr_workspace.get("is_hidden")}')
        print(f'   Public: {hr_workspace.get("public")}')
        print()
    else:
        print('❌ HR Workspace not found in pages')
        print()
    
    print(f'HR Child Workspaces Found: {len(hr_children)}')
    print('-' * 80)
    
    expected_children = ['Recruitment', 'Employee Lifecycle', 'Shift & Attendance', 'Performance']
    
    for child in hr_children:
        name = child.get('name')
        title = child.get('title')
        is_hidden = child.get('is_hidden')
        public = child.get('public')
        
        status = '✅' if not is_hidden and public else '⚠️'
        print(f'{status} {title} ({name})')
        print(f'   Is Hidden: {is_hidden}, Public: {public}')
    
    print()
    print('Expected children:')
    for expected in expected_children:
        found = any(c.get('name') == expected or c.get('title') == expected for c in hr_children)
        status = '✅' if found else '❌'
        print(f'{status} {expected}')
    
    print()
    print('=' * 80)
    
    if len(hr_children) >= 4:
        print('✅ All child workspaces are being returned by the API')
        print('   They should appear in the sidebar after browser refresh')
    else:
        print('⚠️  Some child workspaces may be missing')
        print('   Check if they are hidden or have permission issues')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

