import frappe
from frappe.modules.utils import reload_doc

def reload():
    try:
        print("Reloading Google Settings...")
        # Trying with koraflow_core as the module (which maps to the app usually)
        # reload_doc(app, module, type, name) -> wait, reload_doc signature is (module, type, name, force=False)
        # where module is "app.module" usually?
        
        # Let's try passing 'koraflow_core' as module
        frappe.reload_doc("koraflow_core", "doctype", "Google Settings")
        print("Success with 'koraflow_core'")
        return
    except Exception as e:
        print(f"Failed with 'koraflow_core': {e}")

    try:
        # Trying 'KoraFlow Core'
        frappe.reload_doc("koraflow_core", "doctype", "Google Settings", force=True) 
        # Wait, if modules.txt defines mappings, frappe.reload_doc handles it?
        # reload_doc takes (module, type, name). 
        # If I pass the wrong module, it fails.
        pass
    except Exception as e:
        print(f"Failed again: {e}")

    # Let's check what modules are available
    # print(frappe.get_all("Module Def", fields=["name", "app_name"]))

reload()
