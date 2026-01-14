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

ws = frappe.get_doc('Workspace', 'Commission Dashboard')
print('Workspace:', ws.name)
print('Title:', ws.title)
print('Public:', ws.public)
print('\nContent:')
content = json.loads(ws.content or '[]')
print(json.dumps(content, indent=2))

print('\nNumber Cards referenced:')
for item in content:
    if item.get('type') == 'number_card':
        card_name = item.get('data', {}).get('number_card_name')
        print(f'  - {card_name}')
        if card_name and frappe.db.exists('Number Card', card_name):
            card = frappe.get_doc('Number Card', card_name)
            print(f'    ✓ Exists: {card.label} (public: {card.is_public})')
        else:
            print(f'    ❌ Does not exist!')

frappe.destroy()

