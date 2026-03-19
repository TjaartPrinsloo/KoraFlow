import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_nurses(doctype, txt, searchfield, start, page_len, filters):
	"""Return users who have the Nurse role, for Link field queries."""
	return frappe.db.sql(
		"""
		SELECT DISTINCT u.name, u.full_name
		FROM `tabUser` u
		JOIN `tabHas Role` hr ON hr.parent = u.name
		WHERE hr.role = 'Nurse'
		  AND u.enabled = 1
		  AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
		ORDER BY u.full_name
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{"txt": f"%{txt}%", "start": start, "page_len": page_len},
	)
