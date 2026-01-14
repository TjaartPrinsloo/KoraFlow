#!/usr/bin/env python3
"""
Show all submenu items under HR workspace
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
    # Get HR workspace
    workspace = frappe.get_doc('Workspace', 'HR')
    
    print('=' * 80)
    print('HR WORKSPACE SUBMENU ITEMS')
    print('=' * 80)
    print()
    
    # Extract shortcuts
    print('SHORTCUTS:')
    print('-' * 80)
    for shortcut in workspace.shortcuts:
        print(f'  • {shortcut.label} ({shortcut.type})')
    print()
    
    # Extract links (submenu items)
    print('SUBMENU ITEMS (Links):')
    print('-' * 80)
    
    current_section = None
    for link in workspace.links:
        if link.type == 'Card Break':
            if current_section:
                print()
            current_section = link.label
            print(f'\n[{current_section}]')
        elif link.type == 'Link':
            link_type = link.link_type or 'DocType'
            link_to = link.link_to or link.label
            print(f'  • {link.label} ({link_type}: {link_to})')
    
    print()
    print('=' * 80)
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

