import frappe
from koraflow_core.utils.courier_guy_api import CourierGuyAPI
from datetime import datetime

def probe_2026():
    frappe.init(site='koraflow-site', sites_path='sites')
    frappe.connect()
    api = CourierGuyAPI()

    print("\n--- Probing January 2026 Shipments ---")
    
    # 1. Broad probe for Jan 2026
    params = {
        "date_filter": "time_created",
        "start_date": "2026-01-01 00:00:00Z",
        "end_date": "2026-01-14 23:59:59Z",
        "limit": 100
    }
    resp = api._make_request("GET", "/shipments", params)
    if resp.get("success"):
        data = resp.get("data", [])
        shipments = data if isinstance(data, list) else data.get("shipments", [])
        print(f"Found {len(shipments)} shipments for Jan 1-14 2026.")
        for i, s in enumerate(shipments[:10]):
            print(f"  {i+1}. ID: {s.get('id')}, Created: {s.get('time_created')}, Ref: {s.get('short_tracking_reference')}")
    else:
        print(f"API Error: {resp.get('error')}")

    # 2. Check for even more recent (today/yesterday)
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n--- Checking for shipments today ({today}) ---")
    resp_today = api.get_shipments(from_date=today, limit=50)
    print(f"Today success: {resp_today.get('success')}, Count: {len(resp_today.get('shipments', []))}")

if __name__ == "__main__":
    probe_2026()
