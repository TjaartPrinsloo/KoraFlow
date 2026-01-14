#!/usr/bin/env python3
"""
Check Number Card Data and Configuration

Verify if Number Cards have data and are configured correctly.
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
    print("Checking Number Cards...")
    print()
    
    card_names = [
        "SP Total Commission This Month",
        "SP Total Commission All Time",
        "SP Total Invoiced This Month",
        "SP Invoice Count This Month",
        "SP Total Invoiced All Time"
    ]
    
    for card_name in card_names:
        if frappe.db.exists("Number Card", card_name):
            card = frappe.get_doc("Number Card", card_name)
            print(f"Card: {card_name}")
            print(f"  Label: {card.label}")
            print(f"  Type: {card.type}")
            print(f"  Document Type: {card.document_type}")
            print(f"  Function: {card.function}")
            print(f"  Aggregate Field: {card.aggregate_function_based_on}")
            print(f"  Filters: {card.filters_json}")
            print(f"  Is Public: {card.is_public}")
            print()
            
            # Check if there's any data
            if card.document_type == "Sales Invoice":
                filters = json.loads(card.filters_json or "[]")
                # Build query to check data
                from frappe.query_builder import DocType
                si = DocType("Sales Invoice")
                query = frappe.qb.from_(si).select(frappe.qb.functions.Count("*"))
                
                for filter_item in filters:
                    if len(filter_item) >= 4:
                        field, operator, value = filter_item[1], filter_item[2], filter_item[3]
                        if operator == "=":
                            query = query.where(si[field] == value)
                        elif operator == "is" and value == "set":
                            query = query.where(si[field].isnotnull())
                
                count = query.run()[0][0]
                print(f"  Records matching filters: {count}")
        else:
            print(f"❌ Card '{card_name}' does NOT exist!")
        print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

