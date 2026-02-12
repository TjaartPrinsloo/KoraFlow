import frappe
import json
import os

def update_doctype():
    json_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps/koraflow_core/koraflow_core/doctype/google_settings/google_settings.json"
    
    with open(json_path, 'r') as f:
        doc_data = json.load(f)
        
    # Remove standard fields that cause conflicts
    for field in ['modified', 'creation', 'owner', 'modified_by', 'idx', 'autoname', 'naming_rule']:
        if field in doc_data:
            del doc_data[field]


    # doc_data is the DocType definition
    # Check if exists
    if frappe.db.exists("DocType", "Google Settings"):
        print("DocType exists, updating...")
        doc = frappe.get_doc("DocType", "Google Settings")
        doc.reload() # Ensure latest
        doc.update(doc_data)
        doc.save()
    else:
        print("Creating DocType...")
        doc = frappe.get_doc(doc_data)
        doc.insert()

    print("Google Settings DocType updated successfully.")
    
    # Verify field
    fields = frappe.get_all('DocField', filters={'parent': 'Google Settings', 'fieldname': 'maps_api_key'})
    print(f"Fields found: {fields}")

    # Set dummy value again to be sure
    if not frappe.db.get_single_value("Google Settings", "maps_api_key"):
        s = frappe.get_doc("Google Settings")
        s.maps_api_key = "TEST_KEY_FROM_DB_MANUAL_UPDATE"
        s.save()
        print("Updated dummy key.")

update_doctype()
