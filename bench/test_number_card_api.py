#!/usr/bin/env python3
"""
Test Number Card API Endpoint

Test if the get_result API returns data for our Number Cards.
"""

import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.desk.doctype.number_card.number_card import get_result

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Testing Number Card API...")
    print()
    
    # Test card 1: Total Commission This Month
    card1 = frappe.get_doc("Number Card", "SP Total Commission This Month")
    print(f"Card: {card1.name}")
    print(f"  Type: {card1.type}")
    print(f"  Document Type: {card1.document_type}")
    print(f"  Function: {card1.function}")
    print(f"  Aggregate Field: {card1.aggregate_function_based_on}")
    print(f"  Filters: {card1.filters_json}")
    print()
    
    # Convert card to dict for API
    card_dict = card1.as_dict()
    filters = json.loads(card1.filters_json or "[]")
    
    print("Calling get_result API...")
    try:
        result = get_result(card_dict, filters)
        print(f"  ✓ API Result: {result}")
        print(f"  ✓ Type: {type(result)}")
    except Exception as e:
        print(f"  ❌ API Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test manually with frappe.get_list
    print("Testing manual query...")
    from frappe.query_builder import DocType, functions
    si = DocType("Sales Invoice")
    
    # Build query based on card filters
    query = frappe.qb.from_(si).select(functions.Sum(si.total_commission))
    
    # Apply filters
    for filter_item in filters:
        if len(filter_item) >= 4:
            field, operator, value = filter_item[1], filter_item[2], filter_item[3]
            if operator == "=":
                query = query.where(si[field] == value)
            elif operator == "is" and value == "set":
                query = query.where(si[field].isnotnull())
            elif operator == "Timespan" and value == "this month":
                from frappe.utils import get_first_day, get_last_day, today
                first_day = get_first_day(today())
                last_day = get_last_day(today())
                query = query.where(si.posting_date >= first_day).where(si.posting_date <= last_day)
    
    manual_result = query.run()[0][0] or 0
    print(f"  Manual query result: {manual_result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

