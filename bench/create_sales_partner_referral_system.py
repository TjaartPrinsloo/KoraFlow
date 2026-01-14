#!/usr/bin/env python3
"""
Create Sales Partner Referral Tracking System

This script creates:
1. Sales Partner Referral DocType (safe projection of patient data)
2. Sales Partner Query DocType (commenting system)
3. Portal page for /my-referrals
4. Server-side hooks to sync status
5. Permissions setup
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

ROLE_NAME = "Sales Partner Portal"

def create_sales_partner_referral_doctype():
    """Create Sales Partner Referral DocType"""
    print("Creating Sales Partner Referral DocType...")
    
    if frappe.db.exists("DocType", "Sales Partner Referral"):
        print("  ✓ Sales Partner Referral DocType already exists")
        return
    
    doctype = {
        "doctype": "DocType",
        "name": "Sales Partner Referral",
        "module": "Selling",
        "custom": 0,
        "is_submittable": 0,
        "istable": 0,
        "issingle": 0,
        "autoname": "hash",
        "title_field": "full_name",
        "search_fields": "full_name,referral_status",
        "track_changes": 1,
        "track_views": 1,
        "fields": [
            {
                "fieldname": "sales_partner",
                "fieldtype": "Link",
                "options": "Sales Partner",
                "label": "Sales Partner",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "idx": 1
            },
            {
                "fieldname": "patient",
                "fieldtype": "Link",
                "options": "Patient",
                "label": "Patient",
                "reqd": 0,  # Not reqd in form, but validated in Python
                "hidden": 1,  # Hidden from portal users
                "idx": 2
            },
            {
                "fieldname": "first_name",
                "fieldtype": "Data",
                "label": "First Name",
                "reqd": 1,
                "in_list_view": 1,
                "idx": 3
            },
            {
                "fieldname": "last_name",
                "fieldtype": "Data",
                "label": "Last Name",
                "reqd": 1,
                "in_list_view": 1,
                "idx": 4
            },
            {
                "fieldname": "full_name",
                "fieldtype": "Data",
                "label": "Full Name",
                "read_only": 1,
                "in_list_view": 1,
                "idx": 5
            },
            {
                "fieldname": "referral_date",
                "fieldtype": "Date",
                "label": "Referral Date",
                "reqd": 1,
                "default": "Today",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "idx": 6
            },
            {
                "fieldname": "referral_status",
                "fieldtype": "Select",
                "label": "Status",
                "reqd": 1,
                "options": "\nQuotation Pending\nQuotation Sent\nOrder Confirmed\nPacking\nDispatched\nInvoiced\nPaid",
                "default": "Quotation Pending",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "idx": 7
            },
            {
                "fieldname": "last_updated",
                "fieldtype": "Datetime",
                "label": "Last Updated",
                "read_only": 1,
                "in_list_view": 1,
                "idx": 8
            },
            {
                "fieldname": "quotation",
                "fieldtype": "Link",
                "options": "Quotation",
                "label": "Quotation",
                "hidden": 1,  # Hidden from portal
                "idx": 9
            },
            {
                "fieldname": "sales_order",
                "fieldtype": "Link",
                "options": "Sales Order",
                "label": "Sales Order",
                "hidden": 1,  # Hidden from portal
                "idx": 10
            },
            {
                "fieldname": "delivery_note",
                "fieldtype": "Link",
                "options": "Delivery Note",
                "label": "Delivery Note",
                "hidden": 1,  # Hidden from portal
                "idx": 11
            },
            {
                "fieldname": "sales_invoice",
                "fieldtype": "Link",
                "options": "Sales Invoice",
                "label": "Sales Invoice",
                "hidden": 1,  # Hidden from portal
                "idx": 12
            },
            {
                "fieldname": "payment_entry",
                "fieldtype": "Link",
                "options": "Payment Entry",
                "label": "Payment Entry",
                "hidden": 1,  # Hidden from portal
                "idx": 13
            },
            {
                "fieldname": "commission_earned",
                "fieldtype": "Currency",
                "label": "Commission Earned",
                "read_only": 1,
                "hidden": 1,  # Will be shown via link to commission report
                "idx": 14
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 1,
                "print": 1,
                "email": 1,
                "export": 1
            },
            {
                "role": ROLE_NAME,
                "read": 1,
                "write": 0,
                "create": 0,
                "delete": 0,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 0,
                "print": 0,
                "email": 0,
                "export": 0
            }
        ]
    }
    
    doc = frappe.get_doc(doctype)
    doc.flags.ignore_permissions = True
    doc.insert()
    frappe.db.commit()
    print("  ✓ Created Sales Partner Referral DocType")


def create_sales_partner_query_doctype():
    """Create Sales Partner Query DocType for commenting"""
    print("Creating Sales Partner Query DocType...")
    
    if frappe.db.exists("DocType", "Sales Partner Query"):
        print("  ✓ Sales Partner Query DocType already exists")
        return
    
    doctype = {
        "doctype": "DocType",
        "name": "Sales Partner Query",
        "module": "Selling",
        "custom": 0,
        "is_submittable": 0,
        "istable": 0,
        "issingle": 0,
        "autoname": "hash",
        "title_field": "subject",
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "sales_partner",
                "fieldtype": "Link",
                "options": "Sales Partner",
                "label": "Sales Partner",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "idx": 1
            },
            {
                "fieldname": "referral",
                "fieldtype": "Link",
                "options": "Sales Partner Referral",
                "label": "Referral",
                "reqd": 1,
                "in_list_view": 1,
                "idx": 2
            },
            {
                "fieldname": "subject",
                "fieldtype": "Data",
                "label": "Subject",
                "reqd": 1,
                "in_list_view": 1,
                "idx": 3
            },
            {
                "fieldname": "message",
                "fieldtype": "Text Editor",
                "label": "Message",
                "reqd": 1,
                "idx": 4
            },
            {
                "fieldname": "status",
                "fieldtype": "Select",
                "label": "Status",
                "options": "\nOpen\nResponded\nClosed",
                "default": "Open",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "idx": 5
            },
            {
                "fieldname": "assigned_to",
                "fieldtype": "Link",
                "options": "User",
                "label": "Assigned To",
                "idx": 6
            },
            {
                "fieldname": "response",
                "fieldtype": "Text Editor",
                "label": "Response",
                "read_only": 1,
                "depends_on": "eval:doc.status == 'Responded'",
                "idx": 7
            },
            {
                "fieldname": "created_on",
                "fieldtype": "Datetime",
                "label": "Created On",
                "read_only": 1,
                "default": "Now",
                "in_list_view": 1,
                "idx": 8
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 1,
                "print": 1,
                "email": 1,
                "export": 1
            },
            {
                "role": ROLE_NAME,
                "read": 1,
                "write": 0,
                "create": 1,
                "delete": 0,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "report": 0,
                "print": 0,
                "email": 0,
                "export": 0
            }
        ]
    }
    
    doc = frappe.get_doc(doctype)
    doc.flags.ignore_permissions = True
    doc.insert()
    frappe.db.commit()
    print("  ✓ Created Sales Partner Query DocType")


def setup_permissions():
    """Set up User Permissions and DocType permissions"""
    print("Setting up permissions...")
    
    # Ensure Sales Partner Portal role has read access to Sales Partner Referral
    # (already set in DocType creation, but verify)
    print("  ✓ Permissions configured in DocType creation")


def main():
    try:
        print("Creating Sales Partner Referral System...")
        print()
        
        create_sales_partner_referral_doctype()
        create_sales_partner_query_doctype()
        setup_permissions()
        
        print()
        print("✅ Sales Partner Referral System created successfully!")
        print()
        print("Next steps:")
        print("1. Create server-side hooks to sync referral status")
        print("2. Create portal page /my-referrals")
        print("3. Set up User Permissions for data isolation")
        print("4. Test with a sales partner user")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()

