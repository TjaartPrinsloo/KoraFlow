#!/usr/bin/env python3
"""
Fix Workspace Content to Use Number Card Labels Instead of Names

The make() method searches for Number Cards by label, but the workspace content
uses number_card_name. We need to update the content to use labels, OR update
the Number Card labels to match their names.

Actually, wait - let me check the child table entries. They should have the
correct label set. The issue might be that the make() method needs to search
by name as well as label.
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
    print("Checking Number Card labels vs names...")
    print()
    
    workspace = frappe.get_doc("Workspace", "Sales Partner Dashboard")
    content = json.loads(workspace.content or "[]")
    
    # Check child table entries
    print("Child table entries:")
    for row in workspace.number_cards:
        card = frappe.get_doc("Number Card", row.number_card_name)
        print(f"  Name: {row.number_card_name}")
        print(f"  Label in table: {row.label}")
        print(f"  Label in card: {card.label}")
        print()
    
    # The make() method searches by label, but content uses name
    # Solution: Update Number Card labels to match their names
    # OR update workspace content to use labels
    
    # Actually, let's check what the make method actually does
    # It searches page_data.number_cards.items for obj.label == block_name
    # block_name comes from this.data.number_card_name
    
    # So we need the card's label to match its name
    # OR we need to update the content to use labels
    
    # Let's update the Number Card labels to match their names for now
    print("Updating Number Card labels to match their names...")
    updated = 0
    
    for row in workspace.number_cards:
        card = frappe.get_doc("Number Card", row.number_card_name)
        if card.label != card.name:
            print(f"  Updating '{card.name}': '{card.label}' -> '{card.name}'")
            card.label = card.name
            card.flags.ignore_permissions = True
            card.save()
            updated += 1
    
    if updated > 0:
        frappe.db.commit()
        print(f"\n✓ Updated {updated} Number Card labels")
    else:
        print("\n✓ All labels already match names")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

