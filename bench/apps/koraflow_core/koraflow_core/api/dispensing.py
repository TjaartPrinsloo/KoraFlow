"""
Dispensing API
- Pick Slip: printable document for warehouse picker
- Dispense & Ship: pharmacist action to finalise the order
"""
import frappe
from frappe import _


@frappe.whitelist()
def get_pick_slip(task_name):
	"""
	Generate a branded, printable pick slip for the warehouse picker.
	Returns HTML that can be opened in a new tab and printed.
	"""
	if "Pharmacist" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only Pharmacists can access pick slips"), frappe.PermissionError)

	task = frappe.get_doc("GLP-1 Pharmacy Dispense Task", task_name)
	patient = frappe.get_doc("Patient", task.patient)
	prescription = frappe.get_doc("GLP-1 Patient Prescription", task.prescription) if task.prescription else None

	# Get items from Sales Order or Delivery Note
	items = []
	warehouse = frappe.db.get_value("Pharmacy Warehouse",
		{"warehouse_name": "PHARM-CENTRAL-COLD"}, "erpnext_warehouse") or "PHARM-CENTRAL-COLD - S2W"

	so_name = getattr(task, 'sales_order', None)
	dn_name = getattr(task, 'delivery_note', None)

	source_doc = None
	if dn_name:
		source_doc = frappe.get_doc("Delivery Note", dn_name)
	elif so_name:
		source_doc = frappe.get_doc("Sales Order", so_name)

	if source_doc:
		for item in source_doc.items:
			if item.item_code == "COURIER-FEE":
				continue

			# Find batch for this item in the pharmacy warehouse
			batch_info = frappe.db.sql("""
				SELECT b.name as batch_no, b.expiry_date,
					SUM(sle.actual_qty) as available_qty
				FROM `tabBatch` b
				INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
				WHERE sle.item_code = %s AND sle.warehouse = %s AND sle.is_cancelled = 0
				AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
				GROUP BY b.name, b.expiry_date
				HAVING available_qty > 0
				ORDER BY b.expiry_date ASC
				LIMIT 1
			""", (item.item_code, warehouse), as_dict=True)

			items.append({
				"item_code": item.item_code,
				"item_name": item.item_name or item.item_code,
				"qty": item.qty,
				"uom": item.uom or item.stock_uom or "Nos",
				"batch_no": batch_info[0].batch_no if batch_info else "—",
				"expiry_date": frappe.utils.formatdate(batch_info[0].expiry_date) if batch_info and batch_info[0].expiry_date else "—",
				"available_qty": batch_info[0].available_qty if batch_info else 0,
				"warehouse": warehouse,
			})

	# Render template
	from jinja2 import Template
	template_path = frappe.get_app_path("koraflow_core", "templates", "pick_slip.html")
	with open(template_path) as f:
		template = Template(f.read())

	html = template.render(
		task=task,
		patient=patient,
		prescription=prescription,
		items=items,
		warehouse=warehouse,
		date=frappe.utils.formatdate(frappe.utils.nowdate(), "dd MMM yyyy"),
		time=frappe.utils.nowtime()[:5],
		frappe=frappe,
	)

	frappe.local.response.filename = f"PickSlip-{task_name}.html"
	frappe.local.response.filecontent = html
	frappe.local.response.type = "download"
	frappe.local.response.content_type = "text/html"
	frappe.local.response.display_content_as = "inline"


@frappe.whitelist()
def dispense_and_ship(task_name):
	"""
	Pharmacist's final action — dispense medication and trigger shipping.

	Steps:
	1. Submit the draft Delivery Note (stock deducted)
	2. Create Dispense Confirmation
	3. Book waybill with TCG API
	4. Update prescription → "Dispensed"
	5. Update task → "Dispensed"
	"""
	if "Pharmacist" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only Pharmacists can dispense"), frappe.PermissionError)

	task = frappe.get_doc("GLP-1 Pharmacy Dispense Task", task_name)

	if task.status not in ("Pending", "In Progress"):
		frappe.throw(_("Task is already {0}").format(task.status))

	errors = []

	# 1. Submit the Delivery Note (this deducts stock)
	dn_name = getattr(task, 'delivery_note', None)
	if dn_name:
		try:
			dn = frappe.get_doc("Delivery Note", dn_name)
			if dn.docstatus == 0:
				dn.flags.ignore_permissions = True
				dn.submit()
				frappe.db.commit()
				frappe.logger().info(f"Dispense: DN {dn_name} submitted")
		except Exception as e:
			errors.append(f"Delivery Note: {str(e)}")
			frappe.log_error(title="Dispense DN Error", message=str(e))

	# 2. Create Dispense Confirmation
	try:
		if not frappe.db.exists("GLP-1 Dispense Confirmation", {"prescription": task.prescription}):
			confirmation = frappe.get_doc({
				"doctype": "GLP-1 Dispense Confirmation",
				"prescription": task.prescription,
				"patient": task.patient,
				"pharmacist": frappe.session.user,
			})
			confirmation.insert(ignore_permissions=True)
			frappe.db.commit()
	except Exception as e:
		errors.append(f"Dispense Confirmation: {str(e)}")
		frappe.log_error(title="Dispense Confirmation Error", message=str(e))

	# 3. Book waybill with TCG API
	waybill_name = getattr(task, 'waybill', None)
	if waybill_name:
		try:
			waybill = frappe.get_doc("Courier Guy Waybill", waybill_name)
			if waybill.status == "Draft":
				frappe.enqueue(
					"koraflow_core.hooks.courier_guy_hooks.book_waybill_async",
					waybill_name=waybill_name,
					invoice_name=task.invoice,
					queue="short"
				)
				frappe.logger().info(f"Dispense: Waybill {waybill_name} booking enqueued")
		except Exception as e:
			errors.append(f"Waybill: {str(e)}")
			frappe.log_error(title="Dispense Waybill Error", message=str(e))

	# 4. Update prescription status
	if task.prescription:
		try:
			frappe.db.set_value("GLP-1 Patient Prescription", task.prescription, "status", "Dispensed")
			frappe.db.set_value("GLP-1 Patient Prescription", task.prescription, "last_dispense_date", frappe.utils.nowdate())
		except Exception:
			pass

	# 5. Update task status
	task.status = "Dispensed"
	task.dispensed_by = frappe.session.user
	task.dispensed_at = frappe.utils.now_datetime()
	task.save(ignore_permissions=True)
	frappe.db.commit()

	# 6. Update referral status
	try:
		referral = frappe.db.get_value("Patient Referral",
			{"patient": task.patient, "current_journey_status": ["!=", "Cancelled"]}, "name")
		if referral:
			frappe.db.set_value("Patient Referral", referral, {
				"current_journey_status": "Medication Dispatched",
				"last_status_update": frappe.utils.now_datetime()
			})
	except Exception:
		pass

	frappe.db.commit()

	if errors:
		return {
			"success": True,
			"message": _("Dispensed with warnings: {0}").format("; ".join(errors)),
			"task": task.name
		}

	return {
		"success": True,
		"message": _("Medication dispensed and shipping initiated!"),
		"task": task.name,
		"waybill": waybill_name
	}
