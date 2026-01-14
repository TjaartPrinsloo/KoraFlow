#!/usr/bin/env python3
"""
Link a Sales Invoice to a Sales Partner for Testing

This script will:
1. Find or create a Sales Invoice
2. Link it to a Sales Partner
3. Submit it so Number Cards can display data
"""

import sys
import os
from datetime import datetime

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

try:
    print("=" * 80)
    print("LINKING SALES INVOICE TO SALES PARTNER")
    print("=" * 80)
    print()
    
    # Find a Sales Partner
    sales_partners = frappe.get_all("Sales Partner", fields=["name"], limit=1)
    if not sales_partners:
        print("❌ No Sales Partners found!")
        print("   Please create sales partners first using create_sales_partners.py")
        exit(1)
    
    sales_partner = sales_partners[0].name
    print(f"Using Sales Partner: {sales_partner}")
    print()
    
    # Find an existing Sales Invoice (draft or submitted)
    invoices = frappe.get_all("Sales Invoice", 
        fields=["name", "docstatus", "sales_partner", "posting_date", "grand_total"],
        limit=10,
        order_by="creation desc"
    )
    
    invoice_to_update = None
    
    if invoices:
        print(f"Found {len(invoices)} Sales Invoices")
        # Try to find one that's not submitted and doesn't have a sales partner
        for inv in invoices:
            if inv.docstatus == 0 and not inv.sales_partner:
                invoice_to_update = inv.name
                print(f"  ✓ Found draft invoice: {inv.name} (no sales partner)")
                break
        
        # If none found, use the first one
        if not invoice_to_update:
            invoice_to_update = invoices[0].name
            print(f"  Using invoice: {invoice_to_update} (docstatus: {invoices[0].docstatus})")
    else:
        print("No Sales Invoices found. Creating a test invoice...")
        # Create a simple test invoice
        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": frappe.get_all("Customer", limit=1)[0].name if frappe.get_all("Customer") else None,
            "posting_date": datetime.now().date(),
            "due_date": datetime.now().date(),
            "company": frappe.get_all("Company", limit=1)[0].name if frappe.get_all("Company") else None,
        })
        
        if not invoice.customer:
            print("❌ No Customer found. Cannot create invoice.")
            print("   Please create a Customer first or use an existing invoice.")
            exit(1)
        
        if not invoice.company:
            print("❌ No Company found. Cannot create invoice.")
            print("   Please create a Company first or use an existing invoice.")
            exit(1)
        
        invoice.insert()
        invoice_to_update = invoice.name
        print(f"  ✓ Created test invoice: {invoice_to_update}")
    
    print()
    
    # Update the invoice with sales partner
    invoice_doc = frappe.get_doc("Sales Invoice", invoice_to_update)
    print(f"Updating invoice: {invoice_doc.name}")
    print(f"  Current docstatus: {invoice_doc.docstatus}")
    print(f"  Current sales_partner: {invoice_doc.sales_partner}")
    print(f"  Posting date: {invoice_doc.posting_date}")
    print(f"  Due date: {invoice_doc.due_date}")
    print()
    
    # Fix due date using db_set to bypass validation
    from frappe.utils import add_days, today
    posting_date = invoice_doc.posting_date or today()
    
    # Ensure due date is AFTER posting date
    if not invoice_doc.due_date or invoice_doc.due_date <= posting_date:
        new_due_date = add_days(posting_date, 30)
        frappe.db.set_value("Sales Invoice", invoice_to_update, "due_date", new_due_date)
        print(f"  Fixed due date: {new_due_date}")
    
    # Set sales partner using db_set
    frappe.db.set_value("Sales Invoice", invoice_to_update, "sales_partner", sales_partner)
    print(f"  Set sales partner: {sales_partner}")
    
    # Calculate and set commission
    frappe.db.commit()  # Commit the changes so we can reload
    invoice_doc.reload()
    
    if invoice_doc.base_net_total and not invoice_doc.total_commission:
        commission_rate = 0.05
        total_commission = invoice_doc.base_net_total * commission_rate
        frappe.db.set_value("Sales Invoice", invoice_to_update, "commission_rate", commission_rate)
        frappe.db.set_value("Sales Invoice", invoice_to_update, "total_commission", total_commission)
        print(f"  Set commission rate: {commission_rate * 100}%")
        print(f"  Calculated commission: {total_commission}")
    
    frappe.db.commit()
    invoice_doc.reload()
    frappe.db.commit()
    print(f"  ✓ Updated invoice with sales partner: {sales_partner}")
    print()
    
    # Submit the invoice if it's draft
    if invoice_doc.docstatus == 0:
        print("Submitting invoice...")
        try:
            invoice_doc.flags.ignore_permissions = True
            invoice_doc.submit()
            frappe.db.commit()
            print(f"  ✓ Invoice submitted successfully!")
            print(f"  Docstatus is now: {invoice_doc.docstatus}")
        except Exception as e:
            print(f"  ⚠️  Could not submit invoice: {e}")
            print(f"  Invoice is saved but not submitted.")
            print(f"  You may need to submit it manually or fix validation errors.")
    else:
        print(f"  Invoice is already submitted (docstatus: {invoice_doc.docstatus})")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Sales Partner: {sales_partner}")
    print(f"Invoice: {invoice_doc.name}")
    print(f"Docstatus: {invoice_doc.docstatus}")
    print(f"Sales Partner: {invoice_doc.sales_partner}")
    print(f"Total Commission: {invoice_doc.total_commission or 0}")
    print(f"Base Net Total: {invoice_doc.base_net_total or 0}")
    print()
    print("Next steps:")
    print("  1. Refresh the Sales Partner Dashboard")
    print("  2. Number Cards should now display data")
    print("  3. If logged in as the sales partner user, you should see filtered data")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    frappe.destroy()

