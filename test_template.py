
import frappe
from frappe.utils.jinja import render_template
import os

# Explicitly set path to sites
sites_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench/sites"

def test_render():
    # Read the file
    with open("bench/apps/koraflow_core/koraflow_core/www/glp1_intake_wizard.html", "r") as f:
        content = f.read()

    # Mock context
    context = {
        "frappe": frappe,
        "_": frappe._,
        "intake_status": {"status": "pending"},
        "patient": None
    }
    
    # Mock session
    if not hasattr(frappe, 'session'):
        frappe.session = frappe._dict({'user': 'Patient0', 'csrf_token': 'dummy_token'})
    else:
        frappe.session.user = 'Patient0'
        frappe.session.csrf_token = 'dummy_token'

    print("Attempting to render full file after fix...")
    try:
        rendered = frappe.render_template(content, context, safe_render=True)
        print("PASS FULL FILE")
        print("Snippet with fix check:")
        frappe.render_template('window["__"] = function...', context, safe_render=True)
        print("PASS FIXED SNIPPET")
    except Exception as e:
        print(f"Render failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    frappe.init(site="koraflow-site", sites_path=sites_path)
    frappe.connect()
    test_render()
