
import frappe
from koraflow_core.api.sales_agent_dashboard import get_dashboard_data

def execute():
    try:
        # Switch to the test user context
        user = "test_sales_agent@koraflow.io"
        frappe.set_user(user)
        
        data = get_dashboard_data()
        print("API Success!")
        print(f"Keys: {list(data.keys())}")
        print(f"Commission History Type: {type(data.get('commission_history'))}")
        if 'commission_history' in data:
            print("Commission History field present.")
        else:
            print("ERROR: commission_history missing!")
            
    except Exception as e:
        import traceback
        print(f"API Error: {e}")
        print(traceback.format_exc())
