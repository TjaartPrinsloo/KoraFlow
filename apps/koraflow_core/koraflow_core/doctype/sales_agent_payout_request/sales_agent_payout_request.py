import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class SalesAgentPayoutRequest(Document):
	def validate(self):
		if self.amount <= 0:
			frappe.throw("Amount must be greater than 0")

		# Snapshot bank details if not present
		if not self.bank_details_snapshot:
			agent = frappe.get_doc("Sales Agent", self.sales_agent)
			# Try structured bank details first, then legacy text
			bank_doc = frappe.db.get_value(
				"Sales Agent Bank Details",
				{"sales_agent": agent.user},
				["bank_name", "account_holder_name", "branch_code", "account_type"],
				as_dict=True
			)
			if bank_doc:
				self.bank_details_snapshot = (
					f"Bank: {bank_doc.bank_name}\n"
					f"Account Holder: {bank_doc.account_holder_name}\n"
					f"Branch: {bank_doc.branch_code}\n"
					f"Type: {bank_doc.account_type}"
				)
			elif agent.bank_details:
				self.bank_details_snapshot = agent.bank_details

	def on_submit(self):
		self.create_purchase_invoice()

	def create_purchase_invoice(self):
		if self.generated_invoice:
			return

		agent = frappe.get_doc("Sales Agent", self.sales_agent)

		# Ensure "Marketing Services" item exists
		if not frappe.db.exists("Item", "Marketing Services"):
			# Find a valid item group — prefer "Services", fall back to "All Item Groups"
			item_group = "Services"
			if not frappe.db.exists("Item Group", "Services"):
				item_group = "All Item Groups"

			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": "Marketing Services",
				"item_name": "Marketing Services",
				"item_group": item_group,
				"is_stock_item": 0,
				"is_sales_item": 0,
				"is_purchase_item": 1,
				"include_item_in_manufacturing": 0
			})
			item.insert(ignore_permissions=True)

		# Find or create Supplier for this Agent
		supplier_name = f"SA-{agent.first_name}-{agent.last_name}"
		if not frappe.db.exists("Supplier", supplier_name):
			# Find a valid supplier group
			supplier_group = "Services"
			if not frappe.db.exists("Supplier Group", "Services"):
				supplier_group = frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups"

			supplier = frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": supplier_name,
				"supplier_group": supplier_group,
				"supplier_type": "Individual",
			})
			supplier.insert(ignore_permissions=True)

		# Determine the default expense account
		company = frappe.defaults.get_defaults().get("company")
		expense_account = None
		if company:
			expense_account = frappe.db.get_value(
				"Company", company, "default_expense_account"
			)

		# Create Purchase Invoice
		pi_data = {
			"doctype": "Purchase Invoice",
			"supplier": supplier_name,
			"bill_date": today(),
			"posting_date": today(),
			"due_date": today(),
			"is_paid": 0,
			"update_stock": 0,
			"items": [{
				"item_code": "Marketing Services",
				"qty": 1,
				"rate": self.amount,
				"description": f"Sales Agent Commission Payout - {self.name} ({agent.first_name} {agent.last_name})",
			}],
			"remarks": f"Auto-generated from Payout Request {self.name}"
		}

		if expense_account:
			pi_data["items"][0]["expense_account"] = expense_account

		pi = frappe.get_doc(pi_data)
		pi.insert(ignore_permissions=True)

		self.db_set("generated_invoice", pi.name)
		self.db_set("status", "Approved")

		frappe.msgprint(
			f"Purchase Invoice <b>{pi.name}</b> created for R {self.amount:,.2f}",
			indicator="green",
			alert=True
		)
