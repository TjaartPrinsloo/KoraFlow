"""
Post-Payment Fulfilment Hooks
When invoice is paid → Draft DN → Draft Waybill → Pharmacy Dispense Task

Flow:
1. Payment Entry submitted → invoice marked as Paid
2. This hook detects paid invoice
3. Creates draft Delivery Note (NO stock movement yet)
4. Creates draft Waybill (NOT booked with courier yet)
5. Creates Pharmacy Dispense Task with links to DN, waybill, SO
6. Prescription status → "Dispense Queued"

The pharmacist then:
- Prints pick slip → picker gathers items → hands to pharmacist
- Pharmacist reviews and clicks "Dispense & Ship"
- That submits the DN (stock deducted), books the waybill with TCG, and completes the cycle
"""
import frappe
from frappe import _


def on_payment_received(doc, method):
	"""
	Triggered when a Payment Entry is submitted.
	For each referenced Sales Invoice that is now fully paid,
	trigger the fulfilment chain.
	"""
	if doc.payment_type != "Receive":
		return

	for ref in doc.references:
		if ref.reference_doctype != "Sales Invoice":
			continue

		try:
			invoice = frappe.get_doc("Sales Invoice", ref.reference_name)

			# Check if fully paid
			if invoice.outstanding_amount > 0:
				continue

			# Check if this is a GLP-1 related invoice
			patient = getattr(invoice, 'patient', None) or frappe.db.get_value("Patient", {"customer": invoice.customer}, "name")
			if not patient:
				continue

			# Don't process twice
			existing_task = frappe.db.exists("GLP-1 Pharmacy Dispense Task", {"invoice": invoice.name})
			if existing_task:
				continue

			frappe.logger().info(f"Fulfilment: Invoice {invoice.name} paid for patient {patient}")

			# Run fulfilment as background job
			frappe.enqueue(
				"koraflow_core.hooks.fulfilment_hooks.process_fulfilment",
				invoice_name=invoice.name,
				queue="short",
				timeout=300
			)

		except Exception as e:
			frappe.log_error(title="Fulfilment Hook Error", message=f"Error processing payment for {ref.reference_name}: {str(e)}")


def process_fulfilment(invoice_name):
	"""
	Fulfilment chain for a paid invoice — creates draft documents only.
	The pharmacist's "Dispense & Ship" action finalises everything.
	"""
	try:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		patient = getattr(invoice, 'patient', None) or frappe.db.get_value("Patient", {"customer": invoice.customer}, "name")

		frappe.logger().info(f"Fulfilment: Processing {invoice_name} for {patient}")

		# 1. Find the Sales Order
		sales_order_name = None
		for item in invoice.items:
			if item.sales_order:
				sales_order_name = item.sales_order
				break

		if not sales_order_name:
			frappe.logger().warning(f"Fulfilment: No Sales Order found for invoice {invoice_name}")
			return

		sales_order = frappe.get_doc("Sales Order", sales_order_name)

		# 2. Create draft Delivery Note (NOT submitted — no stock movement yet)
		delivery_note_name = create_draft_delivery_note(sales_order)

		# 3. Create draft Waybill (NOT booked with courier)
		waybill_name = None
		if delivery_note_name:
			waybill_name = create_draft_waybill(delivery_note_name, patient)

		# 4. Find prescription
		prescription_name = getattr(invoice, 'custom_prescription', None) or getattr(sales_order, 'custom_prescription', None)
		if not prescription_name:
			prescription_name = frappe.db.get_value("GLP-1 Patient Prescription",
				{"patient": patient, "status": ["in", ["Doctor Approved", "Quoted", "Dispense Queued"]]},
				"name", order_by="creation desc")

		# 5. Create Pharmacy Dispense Task (with all links)
		dispense_task_name = create_dispense_task(
			patient=patient,
			prescription_name=prescription_name,
			invoice_name=invoice_name,
			delivery_note_name=delivery_note_name,
			waybill_name=waybill_name,
			sales_order_name=sales_order_name,
		)

		# 6. Update prescription status
		if prescription_name:
			try:
				frappe.db.set_value("GLP-1 Patient Prescription", prescription_name, "status", "Dispense Queued")
			except Exception:
				pass

		# 7. Update referral status
		try:
			referral = frappe.db.get_value("Patient Referral",
				{"patient": patient, "current_journey_status": ["!=", "Cancelled"]}, "name")
			if referral:
				frappe.db.set_value("Patient Referral", referral, {
					"current_journey_status": "Invoice Paid",
					"last_status_update": frappe.utils.now_datetime()
				})
		except Exception:
			pass

		frappe.db.commit()
		frappe.logger().info(
			f"Fulfilment ready for {invoice_name}: "
			f"DN={delivery_note_name} (draft), Waybill={waybill_name} (draft), "
			f"Dispense Task={dispense_task_name} (pending)"
		)

	except Exception as e:
		frappe.log_error(title="Fulfilment Processing Error", message=f"Error processing fulfilment for {invoice_name}: {str(e)}")


def create_draft_delivery_note(sales_order):
	"""Create a draft Delivery Note from Sales Order — do NOT submit."""
	# Check for existing draft DN
	existing_dn = frappe.db.get_value("Delivery Note Item",
		{"against_sales_order": sales_order.name, "docstatus": 0}, "parent")
	if existing_dn:
		frappe.logger().info(f"Fulfilment: Draft DN already exists: {existing_dn}")
		return existing_dn

	# Check for already submitted DN (from a previous run)
	submitted_dn = frappe.db.get_value("Delivery Note Item",
		{"against_sales_order": sales_order.name, "docstatus": 1}, "parent")
	if submitted_dn:
		return submitted_dn

	# Create new draft DN
	try:
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		dn = make_delivery_note(sales_order.name)
		dn.flags.ignore_permissions = True
		dn.insert(ignore_permissions=True)
		# Do NOT submit — pharmacist will submit during dispense
		frappe.db.commit()
		frappe.logger().info(f"Fulfilment: Created draft DN: {dn.name}")
		return dn.name

	except Exception as e:
		frappe.log_error(title="DN Creation Error", message=f"Error creating DN for SO {sales_order.name}: {str(e)}")
		return None


def create_draft_waybill(delivery_note_name, patient_name):
	"""Create a draft Courier Guy Waybill — do NOT book with TCG API."""
	# Check if waybill already exists
	existing = frappe.db.exists("Courier Guy Waybill", {"delivery_note": delivery_note_name})
	if existing:
		frappe.logger().info(f"Fulfilment: Waybill already exists: {existing}")
		return existing

	try:
		settings = frappe.get_single("Courier Guy Settings")
		if not settings.enabled:
			return None

		dn = frappe.get_doc("Delivery Note", delivery_note_name)

		waybill = frappe.get_doc({
			"doctype": "Courier Guy Waybill",
			"delivery_note": delivery_note_name,
			"customer": dn.customer,
			"patient": patient_name,
			"status": "Draft",
			"service_type": getattr(settings, 'default_service_type', 'Economy') or "Economy",
		})
		waybill.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"Fulfilment: Created draft waybill: {waybill.name}")
		return waybill.name

	except Exception as e:
		frappe.log_error(title="Waybill Creation Error", message=f"Error creating waybill for DN {delivery_note_name}: {str(e)}")
		return None


def create_dispense_task(patient, prescription_name, invoice_name,
						 delivery_note_name=None, waybill_name=None, sales_order_name=None):
	"""Create Pharmacy Dispense Task with all linked documents."""
	# Check if already exists
	existing = frappe.db.exists("GLP-1 Pharmacy Dispense Task", {"invoice": invoice_name})
	if existing:
		return existing

	if not prescription_name:
		frappe.logger().warning(f"Fulfilment: No prescription found for dispense task (patient: {patient})")
		return None

	try:
		task_data = {
			"doctype": "GLP-1 Pharmacy Dispense Task",
			"patient": patient,
			"prescription": prescription_name,
			"invoice": invoice_name,
			"status": "Pending",
		}

		# Add linked documents if fields exist
		if delivery_note_name:
			task_data["delivery_note"] = delivery_note_name
		if waybill_name:
			task_data["waybill"] = waybill_name
		if sales_order_name:
			task_data["sales_order"] = sales_order_name

		task = frappe.get_doc(task_data)
		task.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"Fulfilment: Dispense Task created: {task.name}")
		return task.name

	except Exception as e:
		frappe.log_error(title="Dispense Task Error", message=f"Error creating dispense task: {str(e)}")
		return None
