import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def reject_encounter(encounter, reason):
	"""
	Doctor rejects a draft Patient Encounter.

	Sets the encounter's custom status to "Not Approved", records the reason,
	rejecting doctor, and timestamp. Also flags the linked patient so the
	rejection is visible to all internal users on the Patient form.
	"""
	if not frappe.user.has_role("Physician") and not frappe.user.has_role("Administrator"):
		frappe.throw(_("Only a Doctor (Physician) can reject an encounter."))

	if not reason or not reason.strip():
		frappe.throw(_("A rejection reason is required."))

	enc = frappe.get_doc("Patient Encounter", encounter)

	if enc.docstatus != 0:
		frappe.throw(_("Only draft (unsaved/unsubmitted) encounters can be rejected."))

	# Update the encounter
	frappe.db.set_value(
		"Patient Encounter",
		encounter,
		{
			"custom_encounter_status": "Not Approved",
			"custom_rejection_reason": reason.strip(),
			"custom_rejected_by": frappe.session.user,
			"custom_rejected_on": now_datetime(),
		},
		update_modified=True,
	)

	# Flag the patient so the rejection banner appears on the Patient form
	if enc.patient and frappe.db.has_column("Patient", "custom_encounter_not_approved"):
		frappe.db.set_value(
			"Patient",
			enc.patient,
			{
				"custom_encounter_not_approved": 1,
				"custom_rejection_reason_display": reason.strip(),
				"custom_rejected_encounter": encounter,
			},
			update_modified=False,
		)

	# Log a timeline comment so the rejection is visible in the form timeline
	enc_doc = frappe.get_doc("Patient Encounter", encounter)
	enc_doc.add_comment(
		"Comment",
		text=f"<b>Encounter Rejected</b> by {frappe.session.user}<br>"
		     f"<b>Reason:</b> {frappe.utils.escape_html(reason.strip())}",
	)

	frappe.db.commit()
	return {"success": True, "message": _("Encounter rejected successfully.")}


@frappe.whitelist()
def delete_draft_encounter(encounter):
	"""
	Delete a draft (docstatus=0) Patient Encounter.

	Bypasses the block_delete audit hook by checking permission explicitly
	and doing a direct DB delete. Only Physicians, System Managers, and
	Administrators may do this.
	"""
	allowed_roles = {"Physician", "System Manager", "Administrator"}
	if not any(frappe.user.has_role(r) for r in allowed_roles):
		frappe.throw(_("Only a Doctor or Administrator can delete a draft encounter."))

	enc = frappe.get_doc("Patient Encounter", encounter)

	if enc.docstatus != 0:
		frappe.throw(_("Only draft (unsubmitted) encounters can be cancelled this way."))

	# Clear the patient rejection flag if this encounter was the flagged one
	if enc.patient and frappe.db.has_column("Patient", "custom_rejected_encounter"):
		rejected_enc = frappe.db.get_value("Patient", enc.patient, "custom_rejected_encounter")
		if rejected_enc == encounter:
			frappe.db.set_value(
				"Patient",
				enc.patient,
				{
					"custom_encounter_not_approved": 0,
					"custom_rejection_reason_display": "",
					"custom_rejected_encounter": None,
				},
				update_modified=False,
			)

	frappe.delete_doc("Patient Encounter", encounter, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"success": True, "message": _("Draft encounter deleted.")}


@frappe.whitelist()
def clear_patient_rejection(patient):
	"""
	Clear the 'Not Approved' flag on a patient, e.g. after a new encounter is
	submitted and approved by a doctor.
	"""
	if not frappe.user.has_role("Physician") and not frappe.user.has_role("Administrator"):
		frappe.throw(_("Only a Doctor or Administrator can clear a rejection flag."))

	if frappe.db.has_column("Patient", "custom_encounter_not_approved"):
		frappe.db.set_value(
			"Patient",
			patient,
			{
				"custom_encounter_not_approved": 0,
				"custom_rejection_reason_display": "",
				"custom_rejected_encounter": None,
			},
			update_modified=False,
		)
		frappe.db.commit()

	return {"success": True}
