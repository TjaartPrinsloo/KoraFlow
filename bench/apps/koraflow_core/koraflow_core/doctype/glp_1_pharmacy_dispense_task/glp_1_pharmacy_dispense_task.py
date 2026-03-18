# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class GLP1PharmacyDispenseTask(Document):
	def validate(self):
		"""Validate task prerequisites"""
		if not self.prescription:
			frappe.throw(_("Prescription is required"))
		if not self.patient:
			frappe.throw(_("Patient is required"))

	def on_update(self):
		"""Update batch availability when task is opened"""
		if self.status == "Pending" and not self.batch_availability:
			self.populate_batch_availability()

	@frappe.whitelist()
	def dispense_and_ship(self):
		"""Pharmacist's action to dispense medication and trigger shipping"""
		from koraflow_core.api.dispensing import dispense_and_ship
		return dispense_and_ship(self.name)

	def populate_batch_availability(self):
		"""Populate available batches for this medication"""
		if not self.prescription:
			return

		prescription = frappe.get_doc("GLP-1 Patient Prescription", self.prescription)
		if not prescription.medication:
			return

		# Get item from medication linked items
		linked_item = frappe.get_all("Medication Linked Item",
			filters={"parent": prescription.medication},
			fields=["item"], limit=1)

		if not linked_item:
			return

		medication_item = linked_item[0].item

		# Get available batches from PHARM-CENTRAL-COLD
		pharm_warehouse = frappe.db.get_value(
			"Pharmacy Warehouse",
			{"warehouse_name": "PHARM-CENTRAL-COLD"},
			"erpnext_warehouse"
		)

		if not pharm_warehouse:
			return

		batches = frappe.db.sql("""
			SELECT
				b.name as batch,
				b.expiry_date,
				SUM(sle.actual_qty) as available_qty
			FROM `tabBatch` b
			INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
			WHERE sle.item_code = %s
			AND sle.warehouse = %s
			AND sle.is_cancelled = 0
			AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
			GROUP BY b.name, b.expiry_date
			HAVING available_qty > 0
			ORDER BY b.expiry_date ASC
		""", (medication_item, pharm_warehouse), as_dict=True)

		for batch in batches:
			self.append("batch_availability", {
				"batch": batch.batch,
				"expiry_date": batch.expiry_date,
				"available_quantity": batch.available_qty
			})
