"""
Admin utilities for User management.
Allows Administrator to change a user's email/login and cascade
the change to all linked records.
"""
import frappe
from frappe import _


@frappe.whitelist()
def change_user_email(old_email, new_email):
	"""
	Change a user's email address (which is also their login/name in Frappe).
	Only Administrator can do this. Cascades the change to linked records.
	"""
	if frappe.session.user != "Administrator":
		frappe.throw(_("Only Administrator can change user emails."))

	if not old_email or not new_email:
		frappe.throw(_("Both old and new email are required."))

	new_email = new_email.strip().lower()
	old_email = old_email.strip()

	if old_email == new_email:
		frappe.throw(_("New email is the same as the current one."))

	if not frappe.db.exists("User", old_email):
		frappe.throw(_("User {0} does not exist.").format(old_email))

	if frappe.db.exists("User", new_email):
		frappe.throw(_("A user with email {0} already exists.").format(new_email))

	if old_email in ("Administrator", "Guest"):
		frappe.throw(_("Cannot rename system users."))

	# Step 1: Rename the User document (this changes name + email field)
	frappe.rename_doc("User", old_email, new_email, force=True)

	# Step 2: Update the email field explicitly (rename_doc handles name but not always email)
	frappe.db.set_value("User", new_email, "email", new_email, update_modified=False)

	# Step 3: Cascade to linked records
	updates = _cascade_email_change(old_email, new_email)

	frappe.db.commit()

	update_summary = ", ".join(updates) if updates else "no linked records"
	return {
		"success": True,
		"message": _("Email changed from {0} to {1}. Updated: {2}").format(
			old_email, new_email, update_summary
		)
	}


def _cascade_email_change(old_email, new_email):
	"""Update all records that reference the old email."""
	updates = []

	# --- Sales Agent (user field is Link to User) ---
	agents = frappe.get_all("Sales Agent", filters={"user": old_email}, pluck="name")
	for agent in agents:
		frappe.db.set_value("Sales Agent", agent, "user", new_email)
	if agents:
		updates.append(f"{len(agents)} Sales Agent(s)")

	# --- Patient Referral (sales_agent field stores user email) ---
	referrals = frappe.get_all("Patient Referral", filters={"sales_agent": old_email}, pluck="name")
	for ref in referrals:
		frappe.db.set_value("Patient Referral", ref, "sales_agent", new_email)
	if referrals:
		updates.append(f"{len(referrals)} Patient Referral(s)")

	# --- Sales Agent Bank Details (sales_agent field stores user email) ---
	if frappe.db.exists("DocType", "Sales Agent Bank Details"):
		bank_docs = frappe.get_all("Sales Agent Bank Details", filters={"sales_agent": old_email}, pluck="name")
		for bd in bank_docs:
			frappe.db.set_value("Sales Agent Bank Details", bd, "sales_agent", new_email)
		if bank_docs:
			updates.append(f"{len(bank_docs)} Bank Detail(s)")

	# --- Patient (email field) ---
	patients = frappe.get_all("Patient", filters={"email": old_email}, pluck="name")
	for patient in patients:
		frappe.db.set_value("Patient", patient, "email", new_email)
	if patients:
		updates.append(f"{len(patients)} Patient(s)")

	# --- Contact (email_id field) ---
	contacts = frappe.get_all("Contact", filters={"email_id": old_email}, pluck="name")
	for contact in contacts:
		frappe.db.set_value("Contact", contact, "email_id", new_email)
	if contacts:
		updates.append(f"{len(contacts)} Contact(s)")

	# --- Contact Email (child table rows) ---
	contact_emails = frappe.db.sql(
		"SELECT name FROM `tabContact Email` WHERE email_id = %s", old_email, as_dict=True
	)
	for ce in contact_emails:
		frappe.db.set_value("Contact Email", ce.name, "email_id", new_email)
	if contact_emails:
		updates.append(f"{len(contact_emails)} Contact Email(s)")

	# --- Healthcare Practitioner (user_id field) ---
	if frappe.db.exists("DocType", "Healthcare Practitioner"):
		practitioners = frappe.get_all("Healthcare Practitioner", filters={"user_id": old_email}, pluck="name")
		for hp in practitioners:
			frappe.db.set_value("Healthcare Practitioner", hp, "user_id", new_email)
		if practitioners:
			updates.append(f"{len(practitioners)} Practitioner(s)")

	# --- Employee (user_id field) ---
	if frappe.db.exists("DocType", "Employee"):
		employees = frappe.get_all("Employee", filters={"user_id": old_email}, pluck="name")
		for emp in employees:
			frappe.db.set_value("Employee", emp, "user_id", new_email)
		if employees:
			updates.append(f"{len(employees)} Employee(s)")

	# --- Custom field: custom_assigned_nurse on Patient ---
	if frappe.db.has_column("Patient", "custom_assigned_nurse"):
		nurse_patients = frappe.get_all("Patient", filters={"custom_assigned_nurse": old_email}, pluck="name")
		for np in nurse_patients:
			frappe.db.set_value("Patient", np, "custom_assigned_nurse", new_email)
		if nurse_patients:
			updates.append(f"{len(nurse_patients)} Nurse Assignment(s)")

	return updates
