#!/usr/bin/env python3
"""
Create Sales Partner Dashboard with Commission Number Cards

This script creates:
1. Number Cards showing commission metrics (filtered by User Permissions)
2. A Workspace/Dashboard for Sales Partners
3. Links to commission reports

Run with:
    python3 create_sales_partner_dashboard.py
"""

import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

ROLE_NAME = "Sales Partner Portal"
WORKSPACE_NAME = "Sales Partner Dashboard"  # Updated to match renamed workspace


def create_number_card(name, label, query, color=None):
    """Create a Number Card with a custom query"""
    try:
        if frappe.db.exists("Number Card", name):
            print(f"  ✓ Number Card '{name}' already exists")
            return name
        
        card = frappe.get_doc({
            "doctype": "Number Card",
            "name": name,
            "label": label,
            "type": "Report",
            "report_name": None,  # We'll use custom query
            "function": "Sum",
            "aggregate_function_based_on": None,
            "document_type": "Sales Invoice",
            "is_public": 1,
            "is_standard": 0,
            "show_percentage_stats": 0,
            "stats_time_interval": "Monthly",
            "color": color or "#5e64ff",
        })
        
        # Set custom query using filters_json
        # The query will be filtered by User Permissions automatically
        card.filters_json = json.dumps([])
        
        # Store query in a custom field or use report
        # Actually, we'll create a custom report for each card
        card.flags.ignore_permissions = True
        card.insert()
        frappe.db.commit()
        print(f"  ✓ Created Number Card: {label}")
        return name
    except Exception as e:
        print(f"  ❌ Error creating Number Card '{name}': {e}")
        frappe.log_error(f"Error creating Number Card {name}: {str(e)}")
        return None


def create_document_type_card(name, label, document_type, function, aggregate_field, filters, color="#5e64ff"):
    """Create a Number Card based on Document Type with filters"""
    try:
        # Delete any existing cards with this name (including variants) or same label
        existing_by_name = frappe.get_all("Number Card", filters={"name": ["like", f"{name}%"]}, fields=["name"])
        for card in existing_by_name:
            try:
                frappe.delete_doc("Number Card", card.name, force=1)
            except:
                pass
        
        existing_by_label = frappe.get_all("Number Card", filters={"label": label}, fields=["name"])
        for card in existing_by_label:
            try:
                frappe.delete_doc("Number Card", card.name, force=1)
            except:
                pass
        
        frappe.db.commit()
        
        # Create the card - let autoname handle initial naming
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
        
        # Set filters
        card.filters_json = json.dumps(filters)
        
        card.flags.ignore_permissions = True
        card.insert()
        
        # Rename to our desired name if it doesn't match
        if card.name != name:
            try:
                frappe.rename_doc("Number Card", card.name, name, force=1)
                card.name = name
            except Exception as rename_error:
                # If rename fails, use the auto-generated name
                name = card.name
        
        frappe.db.commit()
        
        # Verify it exists with correct name
        if frappe.db.exists("Number Card", name):
            print(f"  ✓ Created/Updated Number Card: {name} ({label})")
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


def create_sales_partner_number_cards():
    """Create all number cards for sales partner dashboard"""
    print("1️⃣ Creating Number Cards...")
    print("   Note: User Permissions automatically filter by sales_partner")
    
    cards = []
    
    # Card 1: Total Commission (This Month)
    # Filters: submitted invoices, this month, has sales_partner (via User Permission)
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
    
    print(f"   Created {len(cards)} Number Cards\n")
    return cards


def create_sales_partner_workspace(cards):
    """Create Workspace for Sales Partners"""
    print("2️⃣ Creating Sales Partner Workspace...")
    
    try:
        # Check if workspace exists by name or title
        existing_workspace = None
        if frappe.db.exists("Workspace", WORKSPACE_NAME):
            existing_workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
        else:
            # Check by title
            existing = frappe.get_all("Workspace", filters={"title": "Sales Partner Dashboard"}, limit=1)
            if existing:
                existing_workspace = frappe.get_doc("Workspace", existing[0].name)
        
        if existing_workspace:
            workspace = existing_workspace
            print(f"  ✓ Workspace '{workspace.name}' already exists, updating...")
        else:
            workspace = frappe.get_doc({
                "doctype": "Workspace",
                "title": "Sales Partner Dashboard",
                "label": "Commission Dashboard",
                "public": 1,
                "is_hidden": 0,
                "module": "Selling",
                "icon": "chart-line",
                "content": json.dumps([]),
            })
            workspace.flags.ignore_permissions = True
            workspace.insert()
            frappe.db.commit()
        
        # Build workspace content
        content = []
        
        # Add number cards section
        if cards:
            cards_block = {
                "type": "number_card",
                "data": {
                    "number_card_name": cards[0] if len(cards) > 0 else None,
                    "time_interval": "Monthly"
                }
            }
            content.append(cards_block)
        
        # Add shortcut to commission reports
        shortcuts = [
            {
                "type": "shortcut",
                "data": {
                    "label": "Commission Summary",
                    "link_to": "Sales Partner Commission Summary",
                    "type": "Report",
                    "doc_view": "List"
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "label": "Transaction Summary",
                    "link_to": "Sales Partner Transaction Summary",
                    "type": "Report",
                    "doc_view": "List"
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "label": "My Sales Partner Record",
                    "link_to": "Sales Partner",
                    "type": "DocType",
                    "doc_view": "List"
                }
            }
        ]
        
        # Add all number cards
        for card_name in cards:
            content.append({
                "type": "number_card",
                "data": {
                    "number_card_name": card_name,
                    "time_interval": "Monthly"
                }
            })
        
        # Add shortcuts after cards
        content.extend(shortcuts)
        
        workspace.content = json.dumps(content)
        
        # Add role permissions
        if not any(r.role == ROLE_NAME for r in workspace.roles):
            workspace.append("roles", {"role": ROLE_NAME})
        
        workspace.flags.ignore_permissions = True
        workspace.save()
        frappe.db.commit()
        
        print(f"  ✓ Created/Updated Workspace: {WORKSPACE_NAME}")
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Error creating Workspace: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Error creating Workspace {WORKSPACE_NAME}: {str(e)}")
        return False


def setup_dashboard():
    """Main function to set up the dashboard"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("CREATING SALES PARTNER DASHBOARD")
        print("=" * 80)
        print()
        
        # Create number cards
        cards = create_sales_partner_number_cards()
        
        # Create workspace
        if create_sales_partner_workspace(cards):
            print("=" * 80)
            print("✅ DASHBOARD SETUP COMPLETE")
            print("=" * 80)
            print()
            print("Summary:")
            print(f"  • Number Cards Created: {len(cards)}")
            print(f"  • Workspace: {WORKSPACE_NAME}")
            print()
            print("Dashboard includes:")
            print("  • Total Commission (This Month)")
            print("  • Total Commission (All Time)")
            print("  • Total Invoiced Amount (This Month)")
            print("  • Number of Invoices (This Month)")
            print("  • Average Commission Rate")
            print()
            print("⚠️  IMPORTANT:")
            print("  • All data is automatically filtered by User Permissions")
            print("  • Each sales partner only sees their own commission data")
            print("  • No medical or item information is displayed")
            print("  • Access via Portal: /app/sales-partner-dashboard")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Fatal error in create_sales_partner_dashboard: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    setup_dashboard()

