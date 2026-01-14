#!/usr/bin/env python3
"""
Test Number Card Creation to identify the issue
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
    print("Testing Number Card Creation...")
    print("=" * 80)
    
    # Test 1: Check if total_commission field exists
    print("\n1. Checking Sales Invoice fields...")
    meta = frappe.get_meta("Sales Invoice")
    invoice_fields = [f.fieldname for f in meta.fields]
    if "total_commission" in invoice_fields:
        print("   ✓ Field 'total_commission' exists")
    else:
        print("   ❌ Field 'total_commission' does NOT exist!")
        commission_fields = [f for f in invoice_fields if 'commission' in f.lower()]
        print(f"   Available fields containing 'commission': {commission_fields}")
    
    # Test 2: Try creating a simple Number Card
    print("\n2. Testing Number Card creation...")
    test_card_name = "SP Test Card"
    
    # Delete if exists
    if frappe.db.exists("Number Card", test_card_name):
        frappe.delete_doc("Number Card", test_card_name, force=1)
        frappe.db.commit()
        print(f"   Deleted existing test card")
    
    try:
        card = frappe.get_doc({
            "doctype": "Number Card",
            "name": test_card_name,
            "label": "Test Card",
            "type": "Document Type",
            "document_type": "Sales Invoice",
            "function": "Sum",
            "aggregate_function_based_on": "base_net_total",  # Use a field we know exists
            "is_public": 1,
            "is_standard": 0,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "color": "#5e64ff",
            "module": "Selling",
        })
        
        # Set filters
        card.filters_json = json.dumps([
            ["Sales Invoice", "docstatus", "=", "1"]
        ])
        
        card.flags.ignore_permissions = True
        card.insert()
        print(f"   Card inserted, name: {card.name}")
        
        # Check before commit
        if frappe.db.exists("Number Card", card.name):
            print(f"   ✓ Card exists before commit: {card.name}")
        else:
            print(f"   ❌ Card NOT found before commit!")
        
        frappe.db.commit()
        print(f"   ✓ Committed to database")
        
        # Verify it exists after commit
        if frappe.db.exists("Number Card", card.name):
            print(f"   ✓ Card verified in database: {card.name}")
            card_doc = frappe.get_doc("Number Card", card.name)
            print(f"   ✓ Card loaded: {card_doc.label}")
        else:
            print(f"   ❌ Card NOT found in database after commit!")
            print(f"   Checking with original name: {test_card_name}")
            if frappe.db.exists("Number Card", test_card_name):
                print(f"   ✓ Found with original name: {test_card_name}")
            
    except Exception as e:
        print(f"   ❌ Error creating test card: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Try creating with total_commission
    print("\n3. Testing Number Card with total_commission field...")
    test_card_name2 = "SP Test Commission Card"
    
    if frappe.db.exists("Number Card", test_card_name2):
        frappe.delete_doc("Number Card", test_card_name2, force=1)
        frappe.db.commit()
    
    try:
        card2 = frappe.get_doc({
            "doctype": "Number Card",
            "name": test_card_name2,
            "label": "Test Commission Card",
            "type": "Document Type",
            "document_type": "Sales Invoice",
            "function": "Sum",
            "aggregate_function_based_on": "total_commission",
            "is_public": 1,
            "is_standard": 0,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "color": "#5e64ff",
            "module": "Selling",
        })
        
        card2.filters_json = json.dumps([
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ])
        
        card2.flags.ignore_permissions = True
        card2.insert()
        frappe.db.commit()
        
        print(f"   ✓ Commission card created successfully: {test_card_name2}")
        
        if frappe.db.exists("Number Card", test_card_name2):
            print(f"   ✓ Commission card verified in database")
        else:
            print(f"   ❌ Commission card NOT found in database!")
            
    except Exception as e:
        print(f"   ❌ Error creating commission card: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check existing SP cards
    print("\n4. Checking existing SP Number Cards...")
    existing = frappe.get_all("Number Card", filters={"name": ["like", "SP%"]}, fields=["name", "label", "document_type", "aggregate_function_based_on"])
    if existing:
        print(f"   Found {len(existing)} SP cards:")
        for card in existing:
            print(f"     • {card.name}: {card.label} ({card.aggregate_function_based_on})")
    else:
        print("   No SP cards found")
    
    # Test 5: Check ALL number cards with "Commission" in label
    print("\n5. Checking ALL Number Cards with 'Commission' in label...")
    all_commission = frappe.get_all("Number Card", filters={"label": ["like", "%Commission%"]}, fields=["name", "label"])
    if all_commission:
        print(f"   Found {len(all_commission)} cards:")
        for card in all_commission:
            print(f"     • {card.name}: {card.label}")
    else:
        print("   No commission cards found")
    
    # Test 6: Try creating the actual card from the script
    print("\n6. Testing actual card creation from script...")
    actual_card_name = "SP Total Commission This Month"
    
    # Delete if exists (with any suffix)
    existing_variants = frappe.get_all("Number Card", filters={"name": ["like", f"{actual_card_name}%"]}, fields=["name"])
    for variant in existing_variants:
        frappe.delete_doc("Number Card", variant.name, force=1)
    frappe.db.commit()
    
    try:
        card_actual = frappe.get_doc({
            "doctype": "Number Card",
            "name": actual_card_name,
            "label": "Total Commission (This Month)",
            "type": "Document Type",
            "document_type": "Sales Invoice",
            "function": "Sum",
            "aggregate_function_based_on": "total_commission",
            "is_public": 1,
            "is_standard": 0,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "color": "#5e64ff",
            "module": "Selling",
        })
        
        card_actual.filters_json = json.dumps([
            ["Sales Invoice", "docstatus", "=", "1"],
            ["Sales Invoice", "posting_date", "Timespan", "this month"],
            ["Sales Invoice", "sales_partner", "is", "set"]
        ])
        
        card_actual.flags.ignore_permissions = True
        card_actual.insert()
        print(f"   Card inserted with name: {card_actual.name}")
        
        frappe.db.commit()
        print(f"   ✓ Committed")
        
        # Check if it exists with the exact name
        if frappe.db.exists("Number Card", actual_card_name):
            print(f"   ✓ Card exists with exact name: {actual_card_name}")
        else:
            print(f"   ❌ Card NOT found with exact name: {actual_card_name}")
            # Check for variants
            variants = frappe.get_all("Number Card", filters={"name": ["like", f"{actual_card_name}%"]}, fields=["name"])
            if variants:
                print(f"   But found variants: {[v.name for v in variants]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

