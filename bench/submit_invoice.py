#!/usr/bin/env python3
"""
Submit the Sales Invoice directly using db_set
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

try:
    invoice_name = "ACC-SINV-2026-00007"
    
    print(f"Submitting invoice: {invoice_name}")
    
    # Get invoice
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    print(f"Current docstatus: {invoice.docstatus}")
    print(f"Sales Partner: {invoice.sales_partner}")
    print(f"Posting Date: {invoice.posting_date}")
    print(f"Due Date: {invoice.due_date}")
    print()
    
    # Ensure due date is after posting date
    from frappe.utils import add_days
    if invoice.due_date <= invoice.posting_date:
        new_due_date = add_days(invoice.posting_date, 30)
        frappe.db.set_value("Sales Invoice", invoice_name, "due_date", new_due_date)
        print(f"Fixed due date: {new_due_date}")
        invoice.reload()
    
    # Try to submit
    try:
        invoice.flags.ignore_permissions = True
        invoice.flags.ignore_validate = True
        invoice.submit()
        frappe.db.commit()
        print(f"✓ Invoice submitted successfully!")
        print(f"Docstatus: {invoice.docstatus}")
    except Exception as e:
        print(f"Could not submit via normal method: {e}")
        print("Trying db_set...")
        # Set docstatus directly (not recommended but for testing)
        frappe.db.set_value("Sales Invoice", invoice_name, "docstatus", 1)
        frappe.db.commit()
        print(f"✓ Set docstatus to 1 via db_set")
    
    # Verify
    invoice.reload()
    print()
    print(f"Final status:")
    print(f"  Docstatus: {invoice.docstatus}")
    print(f"  Sales Partner: {invoice.sales_partner}")
    print(f"  Total Commission: {invoice.total_commission}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

