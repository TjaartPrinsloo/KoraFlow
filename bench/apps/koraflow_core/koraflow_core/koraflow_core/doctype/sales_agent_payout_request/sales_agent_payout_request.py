import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class SalesAgentPayoutRequest(Document):
	def validate(self):
		if self.amount <= 0:
			frappe.throw("Amount must be greater than 0")
			
		# Snapshot bank details if not present
		if not self.bank_details_snapshot:
			agent = frappe.get_doc("Sales Agent", self.sales_agent)
			self.bank_details_snapshot = agent.bank_details

	def on_submit(self):
		# Auto-create Purchase Invoice on submit
		self.create_purchase_invoice()

	def create_purchase_invoice(self):
		if self.generated_invoice:
			return

		agent = frappe.get_doc("Sales Agent", self.sales_agent)
		
		# Find or Create Supplier for this Agent
		supplier_name = f"SA-{agent.first_name}-{agent.last_name}"
		if not frappe.db.exists("Supplier", supplier_name):
			supplier = frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": supplier_name,
				"supplier_group": "Services", # Assuming exists
				"supplier_type": "Individual",
			})
			supplier.insert(ignore_permissions=True)
		
		# Create Purchase Invoice
		pi = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"supplier": supplier_name,
			"rating_status": "Not Applicable", # Avoid validation errors if any
			"bill_date": getdate(),
			"items": [{
				"item_code": "Marketing Services", # Ensure this exists or use a generic service item
				"qty": 1,
				"rate": self.amount,
				"description": f"Payout Request {self.name} for {agent.first_name} {agent.last_name}"
			}],
			"is_paid": 0,
			"set_posting_time": 1
		})
		
		# If "Marketing Services" item doesn't exist, create it or fallback to description only if allowed
		# Best practice: Check validity first. For now assuming "Marketing Services" exists or we should create it.
		if not frappe.db.exists("Item", "Marketing Services"):
			# Create service item
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": "Marketing Services",
				"item_name": "Marketing Services",
				"item_group": "Services",
				"is_stock_item": 0,
				"is_sales_item": 0,
				"is_purchase_item": 1,
				"include_item_in_manufacturing": 0
			})
			item.insert(ignore_permissions=True)

		pi.insert(ignore_permissions=True)
		
		self.db_set("generated_invoice", pi.name)
		self.db_set("status", "Approved") # Auto-approve if invoice created successfully? Or keep Pending until Paid?
		# User request: "invoice from sales agent ... we can then pay". 
		# So status should probably track the Invoice status. 
		# For now, let's set to Approved indicating it's processed into an invoice.
