import frappe
from koraflow_core.api.courier_guy_dashboard import get_courier_guy_dashboard_data
import json

def verify_dashboard():
    frappe.init(site='koraflow-site', sites_path='sites')
    frappe.connect()
    
    print("\n--- Testing get_courier_guy_dashboard_data Jan 2026 ---")
    resp = get_courier_guy_dashboard_data(from_date="2026-01-01", to_date="2026-01-13")
    
    if resp.get("success"):
        data = resp.get("data", {})
        print(f"Success! Source: {data.get('source')}")
        print(f"Total Shipments in List: {len(data.get('shipments', []))}")
        if data.get('shipments'):
            s = data.get('shipments')[0]
            print(f"Raw first shipment keys: {list(s.keys())}")
            print(f"Raw first shipment values: {s}")
    else:
        print(f"Failed! Error: {resp.get('error')}")

if __name__ == "__main__":
    verify_dashboard()
