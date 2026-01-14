#!/usr/bin/env python3
"""
Fix Child Table Labels to Match Card Names

The child table entries have old labels that don't match the card names.
Update them to match so the make() method can find the cards.
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

workspace = frappe.get_doc('Workspace', 'Sales Partner Dashboard')
print('Updating child table labels to match card names...')
print()

updated = 0
for row in workspace.number_cards:
    card = frappe.get_doc('Number Card', row.number_card_name)
    if row.label != card.name:
        print(f'  Updating {row.number_card_name}:')
        print(f'    Old label: {row.label}')
        print(f'    New label: {card.name}')
        row.label = card.name
        updated += 1
    else:
        print(f'  ✓ {row.number_card_name} already matches')

if updated > 0:
    workspace.flags.ignore_permissions = True
    workspace.save()
    frappe.db.commit()
    print()
    print(f'✓ Updated {updated} child table labels')
else:
    print()
    print('✓ All labels already match')

frappe.destroy()

