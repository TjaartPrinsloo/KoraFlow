
import frappe
from frappe.utils import set_request
from koraflow_core.www.billing import get_context

def test_billing_context():
    if not frappe.conf:
        frappe.init(site="koraflow-site", sites_path="sites")
        frappe.connect()

    # Mock Session
    test_user_email = "lezel@koraflow.com"
    frappe.set_user(test_user_email)
    
    # Mock Roles
    original_get_roles = frappe.get_roles
    frappe.get_roles = lambda x=None: ["Patient"]
    
    # Mock Request/Context
    class Context(dict):
        def __init__(self):
            self.no_cache = 0

    context = Context()
    
    # Run get_context
    try:
        get_context(context)
        print("\n--- BILLING CONTEST TEST ---")
        if hasattr(context, "quotations"):
            print(f"Quotations found: {len(context.quotations)}")
            for q in context.quotations:
                print(f"- {q.name}: {q.grand_total} ({q.status}) - {q.title}")
        else:
            print("No quotations found in context.")
            
        if "invoices" in context:
             print(f"Invoices found: {len(context.invoices)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_billing_context()
