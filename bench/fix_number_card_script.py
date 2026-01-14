#!/usr/bin/env python3
"""
Fix Number Card Creation Script

The issue: Cards are being created but with auto-generated names instead of the specified names.
Solution: Ensure names are set correctly and handle name conflicts properly.
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

def create_document_type_card(name, label, document_type, function, aggregate_field, filters, color="#5e64ff"):
    """Create a Number Card based on Document Type with filters"""
    try:
        # First, delete any existing cards with this name (including variants)
        existing = frappe.get_all("Number Card", filters={"name": ["like", f"{name}%"]}, fields=["name"])
        for card in existing:
            try:
                frappe.delete_doc("Number Card", card.name, force=1)
            except:
                pass
        
        # Also delete by label if name doesn't match
        existing_by_label = frappe.get_all("Number Card", filters={"label": label}, fields=["name"])
        for card in existing_by_label:
            try:
                frappe.delete_doc("Number Card", card.name, force=1)
            except:
                pass
        
        frappe.db.commit()
        
        # Now create the card
        card = frappe.get_doc({
            "doctype": "Number Card",
            "label": label,
            "type": "Document Type",
            "document_type": document_type,
            "function": function,
            "aggregate_function_based_on": aggregate_field,
            "is_public": 1,
            "is_standard": 0,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "color": color,
            "module": "Selling",
        })
        
        # Set the name explicitly AFTER creating the doc but BEFORE insert
        # This ensures Frappe uses our name
        card.name = name
        
        # Set filters
        card.filters_json = json.dumps(filters)
        
        card.flags.ignore_permissions = True
        card.insert()
        
        # Verify the name was set correctly
        if card.name != name:
            print(f"   ⚠️  Name changed from '{name}' to '{card.name}'")
            # Try to rename it
            try:
                frappe.rename_doc("Number Card", card.name, name, force=1)
                card.name = name
                print(f"   ✓ Renamed to '{name}'")
            except Exception as rename_error:
                print(f"   ⚠️  Could not rename: {rename_error}")
                name = card.name  # Use the actual name
        
        frappe.db.commit()
        
        # Verify it exists
        if frappe.db.exists("Number Card", name):
            print(f"  ✓ Created Number Card: {name} ({label})")
            return name
        else:
            print(f"  ❌ Card '{name}' not found after creation!")
            return None
            
    except Exception as e:
        print(f"  ❌ Error creating Number Card '{name}': {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Error creating Number Card {name}: {str(e)}")
        return None


def create_all_cards():
    """Create all sales partner number cards"""
    print("=" * 80)
    print("CREATING SALES PARTNER NUMBER CARDS")
    print("=" * 80)
    print()
    
    cards = []
    
    # Card 1: Total Commission (This Month)
    card1 = create_document_type_card(
        "SP Total Commission This Month",
        "Total Commission (This Month)",
        "Sales Invoice",
        "Sum",
        "total_commission",
        [
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "posting_date", "Timespan", "this month"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ],
        color="#5e64ff"
    )
    if card1:
        cards.append(card1)
    
    # Card 2: Total Commission (All Time)
    card2 = create_document_type_card(
        "SP Total Commission All Time",
        "Total Commission (All Time)",
        "Sales Invoice",
        "Sum",
        "total_commission",
        [
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ],
        color="#28a745"
    )
    if card2:
        cards.append(card2)
    
    # Card 3: Total Invoiced Amount (This Month)
    card3 = create_document_type_card(
        "SP Total Invoiced This Month",
        "Total Invoiced (This Month)",
        "Sales Invoice",
        "Sum",
        "base_net_total",
        [
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "posting_date", "Timespan", "this month"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ],
        color="#ff9800"
    )
    if card3:
        cards.append(card3)
    
    # Card 4: Number of Invoices (This Month)
    card4 = create_document_type_card(
        "SP Invoice Count This Month",
        "Invoices (This Month)",
        "Sales Invoice",
        "Count",
        None,
        [
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "posting_date", "Timespan", "this month"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ],
        color="#9c27b0"
    )
    if card4:
        cards.append(card4)
    
    # Card 5: Total Invoiced Amount (All Time)
    card5 = create_document_type_card(
        "SP Total Invoiced All Time",
        "Total Invoiced (All Time)",
        "Sales Invoice",
        "Sum",
        "base_net_total",
        [
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ],
        color="#00bcd4"
    )
    if card5:
        cards.append(card5)
    
    print()
    print(f"Created {len(cards)} Number Cards")
    print()
    
    # Verify all cards exist
    print("Verifying cards...")
    for card_name in cards:
        if frappe.db.exists("Number Card", card_name):
            print(f"  ✓ {card_name}")
        else:
            print(f"  ❌ {card_name} - NOT FOUND!")
    
    return cards


if __name__ == "__main__":
    try:
        cards = create_all_cards()
        print("=" * 80)
        print("✅ COMPLETE")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frappe.destroy()

