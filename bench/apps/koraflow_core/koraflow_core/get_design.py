import frappe
def get_design_tokens():
    pf_names = ['Sales Invoice', 'Quotation', 'GLP-1 Patient Prescription']
    pfs = frappe.get_all("Print Format", filters={"name": ["in", pf_names]}, fields=["name", "html", "css", "custom_format"])
    for pf in pfs:
        print(f"--- {pf.name} ---")
        print(f"Custom Format: {pf.custom_format}")
        print("HTML Snippet:")
        print((pf.html or "")[:1000])
        print("CSS Snippet:")
        print((pf.css or "")[:1000])
        print("\n")
