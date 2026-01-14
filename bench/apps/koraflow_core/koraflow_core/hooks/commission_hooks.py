# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Commission Calculation Hooks
Calculates item-wise commission on Sales Invoice submission
"""

import frappe
from frappe import _


def calculate_commission_on_invoice(doc, method=None):
	"""
	Calculate commission on Sales Invoice submission
	- Commission calculated only after invoice submission
	- No commission if invoice cancelled
	- Commission independent of discounting
	- Item-wise commission from Sales Partner Commission Rule
	"""
	
	if doc.doctype != "Sales Invoice" or doc.docstatus != 1:
		return
	
	# Also call existing referral update
	try:
		from koraflow_core.doctype.patient_referral.patient_referral import update_referral_on_invoice_paid
		update_referral_on_invoice_paid(doc, method)
	except:
		pass
	
	# Get sales partner from invoice
	sales_partner = doc.sales_partner if hasattr(doc, 'sales_partner') else None
	
	if not sales_partner:
		return  # No sales partner, no commission
	
	# Check if commission already calculated
	if frappe.db.exists("Sales Partner Commission", {"sales_invoice": doc.name}):
		return  # Already calculated
	
	# Calculate commission for each item
	total_commission = 0
	commission_items = []
	
	for item in doc.items:
		# Get commission rule for this item and sales partner
		commission_rule = frappe.db.get_value(
			"Sales Partner Commission Rule",
			{
				"sales_partner": sales_partner,
				"item": item.item_code,
				"enabled": 1
			},
			"commission_amount"
		)
		
		if commission_rule:
			item_commission = commission_rule * item.qty
			total_commission += item_commission
			commission_items.append({
				"item": item.item_code,
				"qty": item.qty,
				"commission_per_item": commission_rule,
				"total_commission": item_commission
			})
	
	if total_commission > 0:
		# Create commission record
		create_commission_record(doc, sales_partner, total_commission, commission_items)


def create_commission_record(invoice, sales_partner, total_commission, commission_items):
	"""Create Sales Partner Commission record"""
	
	# Check if Commission DocType exists, otherwise create a simple record
	if frappe.db.exists("DocType", "Sales Partner Commission"):
		commission = frappe.get_doc({
			"doctype": "Sales Partner Commission",
			"sales_invoice": invoice.name,
			"sales_partner": sales_partner,
			"commission_amount": total_commission,
			"status": "Unpaid"
		})
		commission.insert(ignore_permissions=True)
		frappe.db.commit()
	else:
		# Create custom commission log
		commission_log = frappe.get_doc({
			"doctype": "Custom Commission Log",
			"sales_invoice": invoice.name,
			"sales_partner": sales_partner,
			"total_commission": total_commission,
			"commission_items": str(commission_items)
		})
		commission_log.insert(ignore_permissions=True)
		frappe.db.commit()
	
	frappe.msgprint(_("Commission of {0} calculated for {1}").format(
		frappe.utils.fmt_money(total_commission, currency="ZAR"),
		sales_partner
	))


def cancel_commission_on_invoice_cancel(doc, method=None):
	"""Cancel commission if invoice is cancelled"""
	
	if doc.doctype != "Sales Invoice" or doc.docstatus != 2:
		return
	
	# Cancel commission records
	if frappe.db.exists("DocType", "Sales Partner Commission"):
		commissions = frappe.get_all(
			"Sales Partner Commission",
			filters={"sales_invoice": doc.name},
			fields=["name"]
		)
		for comm in commissions:
			frappe.db.set_value("Sales Partner Commission", comm.name, "status", "Cancelled")
		frappe.db.commit()
