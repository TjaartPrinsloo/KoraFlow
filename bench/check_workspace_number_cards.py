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

workspace = frappe.get_doc('Workspace', 'Sales Partner Dashboard')
print('Number Cards in workspace child table:')
print(f'Total: {len(workspace.number_cards)}')
for i, row in enumerate(workspace.number_cards, 1):
    print(f'{i}. {row.number_card_name} (label: {row.label})')
    if not frappe.db.exists('Number Card', row.number_card_name):
        print(f'    ⚠️  Card does NOT exist!')
    else:
        card = frappe.get_doc('Number Card', row.number_card_name)
        print(f'    ✓ Card exists, label: {card.label}')

frappe.destroy()

