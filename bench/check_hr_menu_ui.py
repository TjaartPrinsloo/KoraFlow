#!/usr/bin/env python3
"""
Check HR menu items in UI
"""

import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

try:
    # Check if there's a custom override affecting HR menu
    from frappe.desk.desktop import get_workspace_sidebar_items
    items = get_workspace_sidebar_items()
    
    print('=' * 80)
    print('HR MENU ITEMS IN UI')
    print('=' * 80)
    print()
    print(f'Items type: {type(items)}')
    print()
    
    # Handle dict structure
    if isinstance(items, dict):
        print('Items structure:')
        for key in items.keys():
            print(f'  - {key}')
        print()
        
        # Look for HR in all values
        hr_item = None
        for key, value in items.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if item.get('name') == 'HR' or item.get('label') == 'HR':
                            hr_item = item
                            break
            elif isinstance(value, dict):
                if value.get('name') == 'HR' or value.get('label') == 'HR':
                    hr_item = value
                    break
            
            if hr_item:
                break
        
        if hr_item:
            print('✅ HR Workspace Found:')
            print(f'  Name: {hr_item.get("name")}')
            print(f'  Label: {hr_item.get("label")}')
            print(f'  Type: {hr_item.get("type")}')
            print(f'  Has Children: {"children" in hr_item}')
            print()
            
            if 'children' in hr_item and hr_item['children']:
                print(f'  Children Count: {len(hr_item["children"])}')
                print('  Children (Submenu Items):')
                for child in hr_item['children']:
                    if isinstance(child, dict):
                        print(f'    - {child.get("label", child.get("name"))} ({child.get("type", "unknown")})')
                    else:
                        print(f'    - {child}')
            else:
                print('  ⚠️  No children found - submenu items may not be showing')
                print()
                print('  This could mean:')
                print('    1. Workspace links are not being converted to children')
                print('    2. There\'s a custom override hiding them')
                print('    3. Browser cache needs to be cleared')
        else:
            print('❌ HR workspace not found')
            print()
            print('Full items structure:')
            print(json.dumps(items, indent=2, default=str))
    else:
        print('Unexpected items structure')
        print(json.dumps(items, indent=2, default=str))
    
    print()
    print('=' * 80)
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

