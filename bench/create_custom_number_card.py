#!/usr/bin/env python3
"""Create a custom copy of a standard Number Card that can be edited"""
import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)

apps_dir = os.path.join(bench_dir, 'apps')
sys.path.insert(0, apps_dir)

sites_dir = os.path.join(bench_dir, 'sites')
os.chdir(sites_dir)

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

card_name = 'Total Patients Admitted'

# Get the standard card
if frappe.db.exists('Number Card', card_name):
    original_card = frappe.get_doc('Number Card', card_name)
    
    print(f'Found original card: {original_card.name}')
    print(f'  Is Standard: {original_card.is_standard}')
    print(f'  Label: {original_card.label}')
    print(f'  Document Type: {original_card.document_type}')
    print(f'  Function: {original_card.function}')
    
    # Check filters
    if hasattr(original_card, 'filters_json') and original_card.filters_json:
        filters = json.loads(original_card.filters_json)
        print(f'\n  Current Filters: {filters}')
    
    # Create a custom copy
    new_card_name = 'Total Patients Under Review'
    
    # Check if custom card already exists
    if frappe.db.exists('Number Card', new_card_name):
        print(f'\nCustom card "{new_card_name}" already exists. Updating...')
        new_card = frappe.get_doc('Number Card', new_card_name)
    else:
        print(f'\nCreating custom card "{new_card_name}"...')
        # Create new card based on original - don't set name, let Frappe auto-generate
        new_card = frappe.get_doc({
            'doctype': 'Number Card',
            'label': 'Total Patients Under Review',
            'type': original_card.type if hasattr(original_card, 'type') else 'Document Type',
            'document_type': original_card.document_type,
            'function': original_card.function,
            'is_standard': 0,  # Make it custom/editable
        })
        new_card.insert()
        # Now rename it to the desired name
        if new_card.name != new_card_name:
            new_card.rename(new_card_name)
            new_card.reload()
    
    # Copy settings from original
    if hasattr(original_card, 'is_public'):
        new_card.is_public = original_card.is_public
    if hasattr(original_card, 'show_percentage_stats'):
        new_card.show_percentage_stats = original_card.show_percentage_stats
    if hasattr(original_card, 'stats_time_interval'):
        new_card.stats_time_interval = original_card.stats_time_interval
    if hasattr(original_card, 'color'):
        new_card.color = original_card.color
    if hasattr(original_card, 'background_color'):
        new_card.background_color = original_card.background_color
    if hasattr(original_card, 'show_full_number'):
        new_card.show_full_number = original_card.show_full_number
    if hasattr(original_card, 'currency'):
        new_card.currency = original_card.currency
    
    # Set filters to "Under Review"
    filters = [['status', '=', 'Under Review']]
    new_card.filters_json = json.dumps(filters)
    
    new_card.flags.ignore_permissions = True
    new_card.save()
    frappe.db.commit()
    
    print(f'\n✅ Created/Updated custom card: {new_card_name}')
    print(f'   Filter: status = "Under Review"')
    print(f'   Is Standard: {new_card.is_standard} (editable)')
    print(f'\nYou can now edit this card at:')
    print(f'   http://localhost:8000/app/number-card/{new_card_name}')
    
else:
    print(f'Card "{card_name}" not found')
    # List available cards
    cards = frappe.get_all('Number Card', filters={'document_type': 'Patient'}, fields=['name', 'is_standard', 'label'], limit=10)
    print(f'\nAvailable Patient Number Cards:')
    for c in cards:
        print(f'  - {c.name} (Standard: {c.is_standard}, Label: {c.label})')

frappe.destroy()

