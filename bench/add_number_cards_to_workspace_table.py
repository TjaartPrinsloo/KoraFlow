#!/usr/bin/env python3
"""
Add Number Cards to Workspace Number Cards Child Table

The workspace content JSON references Number Cards, but they also need to be
in the workspace's number_cards child table for get_number_cards() to find them.
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
    print("Adding Number Cards to Workspace child table...")
    print()
    
    workspace = frappe.get_doc("Workspace", "Sales Partner Dashboard")
    
    # Get Number Cards from content
    content = json.loads(workspace.content or "[]")
    card_names = set()
    
    for item in content:
        if item.get("type") == "number_card":
            card_name = item.get("data", {}).get("number_card_name")
            if card_name:
                card_names.add(card_name)
    
    print(f"Found {len(card_names)} Number Cards in content:")
    for name in card_names:
        print(f"  - {name}")
    print()
    
    # Check existing child table entries
    existing_names = {row.number_card_name for row in workspace.number_cards}
    print(f"Existing in child table: {len(existing_names)}")
    print()
    
    # Add missing cards
    added = 0
    for card_name in card_names:
        if card_name not in existing_names:
            if frappe.db.exists("Number Card", card_name):
                # Get the Number Card to get its label
                card_doc = frappe.get_doc("Number Card", card_name)
                workspace.append("number_cards", {
                    "number_card_name": card_name,
                    "label": card_doc.label or card_name
                })
                added += 1
                print(f"  ✓ Added: {card_name}")
            else:
                print(f"  ⚠️  Card '{card_name}' does not exist, skipping")
    
    if added > 0:
        workspace.flags.ignore_permissions = True
        workspace.save()
        frappe.db.commit()
        print()
        print(f"✓ Added {added} Number Cards to workspace child table")
    else:
        print("✓ All Number Cards already in child table")
    
    print()
    print(f"Total Number Cards in workspace: {len(workspace.number_cards)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

