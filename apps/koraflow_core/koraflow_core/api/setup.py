import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ENCOUNTER_REJECTION_FIELDS = {
	"Patient Encounter": [
		{
			"fieldname": "custom_encounter_status",
			"label": "Encounter Status",
			"fieldtype": "Select",
			"options": "\nNot Approved",
			"insert_after": "encounter_date",
			"read_only": 1,
		},
		{
			"fieldname": "custom_rejection_reason",
			"label": "Rejection Reason",
			"fieldtype": "Small Text",
			"insert_after": "custom_encounter_status",
			"read_only": 1,
		},
		{
			"fieldname": "custom_rejected_by",
			"label": "Rejected By",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "custom_rejection_reason",
			"read_only": 1,
		},
		{
			"fieldname": "custom_rejected_on",
			"label": "Rejected On",
			"fieldtype": "Datetime",
			"insert_after": "custom_rejected_by",
			"read_only": 1,
		},
	],
	"Patient": [
		{
			"fieldname": "custom_encounter_not_approved",
			"label": "Encounter Not Approved",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "customer",
			"hidden": 1,
		},
		{
			"fieldname": "custom_rejection_reason_display",
			"label": "Rejection Reason",
			"fieldtype": "Small Text",
			"insert_after": "custom_encounter_not_approved",
			"hidden": 1,
			"read_only": 1,
		},
		{
			"fieldname": "custom_rejected_encounter",
			"label": "Rejected Encounter",
			"fieldtype": "Link",
			"options": "Patient Encounter",
			"insert_after": "custom_rejection_reason_display",
			"hidden": 1,
			"read_only": 1,
		},
	],
}


@frappe.whitelist()
def create_encounter_rejection_fields():
	"""Create custom fields required for the encounter rejection workflow."""
	create_custom_fields(ENCOUNTER_REJECTION_FIELDS, ignore_validate=True)
	frappe.db.commit()
	return {"success": True, "message": "Encounter rejection custom fields created."}
