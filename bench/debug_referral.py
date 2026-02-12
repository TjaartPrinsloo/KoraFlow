import frappe
import traceback
from koraflow_core.api.sales_agent_dashboard import create_referral

try:
    frappe.connect("koraflow-site")
    # Mock 'Administrator'
    frappe.session.user = "Administrator"
    
    print("Attempting to create referral as Administrator...")
    res = create_referral('John', 'Debug', 'john.debug@example.com', '0825550001')
    print("Success:", res)

except Exception:
    traceback.print_exc()
finally:
    frappe.db.rollback()
    frappe.destroy()
