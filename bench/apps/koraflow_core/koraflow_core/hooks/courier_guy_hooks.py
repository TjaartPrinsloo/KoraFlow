"""
Courier Guy Hooks
Hooks for integrating Courier Guy with the sales workflow:
- DN Submit: Create draft waybill (no API call)
- Payment Entry Submit: Book waybill via TCG API when invoice is paid
"""
import frappe
from frappe import _


def create_waybill_on_delivery_note_submit(doc, method):
	"""
	On Delivery Note submit: Create a DRAFT waybill only (no TCG API call).
	The waybill will be booked when the linked invoice is paid.
	"""
	# Check if Courier Guy is enabled
	try:
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return
	except Exception:
		return

	# Check if waybill already exists
	existing_waybill = frappe.db.exists("Courier Guy Waybill", {"delivery_note": doc.name})
	if existing_waybill:
		return

	try:
		# Trace back to quotation for rate metadata
		quotation_name = get_quotation_from_delivery_note(doc)
		service_level_code = ""

		if quotation_name:
			service_level_code = frappe.db.get_value(
				"Quotation", quotation_name, "custom_courier_service_level"
			) or ""

		# Create draft waybill (insert triggers before_save which populates addresses)
		waybill = frappe.get_doc({
			"doctype": "Courier Guy Waybill",
			"delivery_note": doc.name,
			"customer": doc.customer,
			"status": "Draft",
			"quotation": quotation_name,
			"service_level_code": service_level_code
		})
		waybill.insert(ignore_permissions=True)

		# Link waybill to delivery note (if custom field exists)
		if frappe.db.has_column("Delivery Note", "courier_guy_waybill"):
			frappe.db.set_value("Delivery Note", doc.name, "courier_guy_waybill", waybill.name)
		frappe.db.commit()

		frappe.msgprint(
			_("Draft waybill {0} created. Shipment will be booked when invoice is paid.").format(waybill.name),
			indicator="blue"
		)

	except Exception as e:
		frappe.log_error(title="Courier Guy Integration", message=f"Error creating draft waybill: {str(e)}")
		frappe.msgprint(
			_("Warning: Could not create draft waybill: {0}").format(str(e)),
			indicator="orange"
		)


def on_payment_entry_submit(doc, method):
	"""
	On Payment Entry submit — waybill booking is now handled by the pharmacist
	dispense action, not on payment. This hook is kept as a no-op for backward
	compatibility with the hook registration.
	"""
	pass


def book_waybill_for_invoice(invoice):
	"""
	Find the draft waybill linked to this invoice's delivery note and book it via TCG API.
	Traces: Invoice items → Delivery Note → Courier Guy Waybill
	Also tries: Invoice items → Sales Order → DN items → Delivery Note → Waybill
	"""
	waybill_names = set()

	# Method 1: Direct DN reference on invoice items
	for item in invoice.items:
		if item.delivery_note:
			wn = frappe.db.get_value(
				"Courier Guy Waybill",
				{"delivery_note": item.delivery_note, "status": "Draft"},
				"name"
			)
			if wn:
				waybill_names.add(wn)

	# Method 2: Via Sales Order → Delivery Note
	if not waybill_names:
		for item in invoice.items:
			if item.sales_order:
				dn_names = frappe.get_all(
					"Delivery Note Item",
					filters={"against_sales_order": item.sales_order, "docstatus": 1},
					fields=["parent"],
					distinct=True
				)
				for dn in dn_names:
					wn = frappe.db.get_value(
						"Courier Guy Waybill",
						{"delivery_note": dn.parent, "status": "Draft"},
						"name"
					)
					if wn:
						waybill_names.add(wn)

	# Method 3: Check custom courier_guy_waybill field on DN
	if not waybill_names:
		linked_dns = set()
		for item in invoice.items:
			if item.delivery_note:
				linked_dns.add(item.delivery_note)
		for dn_name in linked_dns:
			wn = frappe.db.get_value("Delivery Note", dn_name, "courier_guy_waybill")
			if wn:
				status = frappe.db.get_value("Courier Guy Waybill", wn, "status")
				if status == "Draft":
					waybill_names.add(wn)

	# Book each draft waybill
	for waybill_name in waybill_names:
		frappe.enqueue(
			"koraflow_core.hooks.courier_guy_hooks.book_waybill_async",
			waybill_name=waybill_name,
			invoice_name=invoice.name,
			queue="short"
		)


def book_waybill_async(waybill_name, invoice_name):
	"""
	Background job: Book a draft waybill via the TCG API.
	Called when the linked invoice is fully paid.
	"""
	try:
		waybill = frappe.get_doc("Courier Guy Waybill", waybill_name)

		if waybill.status != "Draft":
			frappe.logger().info(f"Waybill {waybill_name} is not in Draft status ({waybill.status}), skipping booking")
			return

		# Link the invoice
		waybill.sales_invoice = invoice_name
		waybill.save(ignore_permissions=True)

		# Book via TCG API
		waybill.create_waybill()

		frappe.logger().info(f"Waybill {waybill_name} booked successfully for invoice {invoice_name}")

	except Exception as e:
		frappe.log_error(
			title="Courier Guy Waybill Booking",
			message=f"Error booking waybill {waybill_name} for invoice {invoice_name}: {str(e)}"
		)


# =====================
# Helpers
# =====================

def get_quotation_from_delivery_note(dn_doc):
	"""
	Trace Delivery Note → Sales Order → Quotation.
	Returns the quotation name or None.
	"""
	# Try to get Sales Order from DN items
	for item in dn_doc.items:
		so_name = item.against_sales_order
		if so_name:
			# Get quotation from Sales Order items
			quotation = frappe.db.get_value(
				"Sales Order Item",
				{"parent": so_name, "prevdoc_docname": ["is", "set"]},
				"prevdoc_docname"
			)
			if quotation:
				return quotation

	return None
