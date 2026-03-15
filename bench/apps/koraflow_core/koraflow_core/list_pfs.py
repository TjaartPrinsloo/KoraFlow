import frappe
def list_pfs():
    pfs = frappe.get_all("Print Format", fields=["name", "doc_type"])
    for p in pfs:
        print(f"{p.name} ({p.doc_type})")
