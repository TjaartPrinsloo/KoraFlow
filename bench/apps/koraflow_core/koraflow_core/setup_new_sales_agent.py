import frappe

def setup():
	"""
	Creates Sales Agent Portal role with no desk access.
	"""
	if not frappe.db.exists("Role", "Sales Agent Portal"):
		role = frappe.new_doc("Role")
		role.role_name = "Sales Agent Portal"
		role.desk_access = 0
		role.is_custom = 1
		role.save(ignore_permissions=True)
		frappe.db.commit()
		print("Created Role: Sales Agent Portal")
	else:
		print("Role Sales Agent Portal already exists.")
