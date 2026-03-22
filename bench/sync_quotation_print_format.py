"""
Quick script to sync the Slim 2 Well Quotation print format from the JSON file.
Run: bench --site <site> execute sync_quotation_print_format.run
Or:  bench --site <site> console  then paste the code below.
"""
import frappe
import json
import os

def run():
    json_path = os.path.join(
        frappe.get_app_path("koraflow_core"),
        "koraflow_core", "print_format",
        "slim_2_well_quotation", "slim_2_well_quotation.json"
    )

    with open(json_path) as f:
        data = json.load(f)

    pf_name = data["name"]

    if frappe.db.exists("Print Format", pf_name):
        pf = frappe.get_doc("Print Format", pf_name)
        pf.html = data["html"]
        pf.doc_type = data["doc_type"]
        pf.print_format_type = data["print_format_type"]
        pf.custom_format = data["custom_format"]
        pf.save(ignore_permissions=True)
        print(f"Updated existing Print Format: {pf_name}")
    else:
        pf = frappe.get_doc({
            "doctype": "Print Format",
            "name": pf_name,
            "doc_type": data["doc_type"],
            "html": data["html"],
            "print_format_type": data["print_format_type"],
            "custom_format": data["custom_format"],
            "standard": data.get("standard", "No"),
            "module": data.get("module", "KoraFlow Core"),
        })
        pf.insert(ignore_permissions=True)
        print(f"Created new Print Format: {pf_name}")

    frappe.db.commit()
    print("Done!")

if __name__ == "__main__":
    run()
