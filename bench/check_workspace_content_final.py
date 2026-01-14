#!/usr/bin/env python3
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

ws = frappe.get_doc('Workspace', 'Sales Partner Dashboard')
print('Workspace:', ws.name)
print('Content length:', len(ws.content or ''))
content = json.loads(ws.content or '[]')
print(f'\nNumber of items: {len(content)}')
print('\nContent:')
for i, item in enumerate(content):
    print(f'{i+1}. Type: {item.get("type")}')
    if item.get('type') == 'number_card':
        print(f'   Card: {item.get("data", {}).get("number_card_name")}')
        card_name = item.get("data", {}).get("number_card_name")
        if card_name and frappe.db.exists('Number Card', card_name):
            print(f'   ✓ Card exists')
        else:
            print(f'   ❌ Card does NOT exist!')
    elif item.get('type') == 'shortcut':
        print(f'   Shortcut: {item.get("data", {}).get("label")} -> {item.get("data", {}).get("link_to")}')

frappe.destroy()

