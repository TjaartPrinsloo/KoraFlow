#!/usr/bin/env python3
"""
Check Sales Invoice Data for Number Cards

Verify if there's data matching the Number Card filters.
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe
from frappe.query_builder import DocType, functions

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("Checking Sales Invoice data...")
    print()
    
    si = DocType("Sales Invoice")
    
    # Check total invoices
    total_count = frappe.qb.from_(si).select(functions.Count("*")).run()[0][0]
    print(f"Total Sales Invoices: {total_count}")
    
    # Check submitted invoices
    submitted_count = frappe.qb.from_(si).select(functions.Count("*")).where(si.docstatus == 1).run()[0][0]
    print(f"Submitted Sales Invoices: {submitted_count}")
    
    # Check invoices with sales_partner
    with_sp_count = frappe.qb.from_(si).select(functions.Count("*")).where(
        si.docstatus == 1
    ).where(si.sales_partner.isnotnull()).run()[0][0]
    print(f"Submitted invoices with sales_partner: {with_sp_count}")
    
    # Check this month
    from frappe.utils import get_first_day, get_last_day, today
    first_day = get_first_day(today())
    last_day = get_last_day(today())
    
    this_month_count = frappe.qb.from_(si).select(functions.Count("*")).where(
        si.docstatus == 1
    ).where(si.sales_partner.isnotnull()).where(
        si.posting_date >= first_day
    ).where(si.posting_date <= last_day).run()[0][0]
    print(f"This month (submitted, with sales_partner): {this_month_count}")
    
    # Check total commission
    total_commission = frappe.qb.from_(si).select(functions.Sum(si.total_commission)).where(
        si.docstatus == 1
    ).where(si.sales_partner.isnotnull()).run()[0][0] or 0
    print(f"Total commission (all time): {total_commission}")
    
    # Check this month commission
    this_month_commission = frappe.qb.from_(si).select(functions.Sum(si.total_commission)).where(
        si.docstatus == 1
    ).where(si.sales_partner.isnotnull()).where(
        si.posting_date >= first_day
    ).where(si.posting_date <= last_day).run()[0][0] or 0
    print(f"This month commission: {this_month_commission}")
    
    print()
    print("Sample sales partners:")
    partners = frappe.get_all("Sales Invoice", 
        filters={"docstatus": 1, "sales_partner": ["is", "set"]},
        fields=["sales_partner", "total_commission", "posting_date"],
        limit=5
    )
    for p in partners:
        print(f"  {p.sales_partner}: {p.total_commission} on {p.posting_date}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

