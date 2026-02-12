
import frappe

def check_prescription_data():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    print("\n--- CHECKING PRESCRIPTION METADATA ---")
    
    print("\nDosage Forms:")
    forms = frappe.get_all("Dosage Form", limit=5)
    for f in forms:
        print(f"- {f.name}")
        
    print("\nPrescription Dosages:")
    dosages = frappe.get_all("Prescription Dosage", limit=5)
    for d in dosages:
        print(f"- {d.name}")
        
    print("\nPrescription Durations:")
    durations = frappe.get_all("Prescription Duration", limit=5)
    for d in durations:
        print(f"- {d.name}")

if __name__ == "__main__":
    check_prescription_data()
