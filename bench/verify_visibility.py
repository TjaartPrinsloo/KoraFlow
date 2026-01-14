import frappe
from koraflow_core.utils.courier_guy_api import CourierGuyAPI
import json
from datetime import datetime, date

def verify_visibility():
    frappe.init(site='koraflow-site', sites_path='sites')
    frappe.connect()
    
    api = CourierGuyAPI()
    
    # Current date is 2026-01-13
    # User says "last two weeks", so from 2025-12-30 to 2026-01-13
    
    test_ranges = [
        ("2025-12-01", "2026-01-31", "Wide Range Jan 2026"),
        ("2024-09-01", "2024-09-30", "Known Working 2024"),
    ]
    
    # Also test the base request with just limit to see if ANYTHING new comes back
    print("\n--- Testing base request (limit 10) ---")
    resp_base = api._make_request("GET", "/shipments", {"limit": 10})
    if resp_base.get("success"):
        data = resp_base.get("data", [])
        shipments = data if isinstance(data, list) else data.get("shipments", [])
        print(f"Found {len(shipments)} shipments total.")
        for i, s in enumerate(shipments[:5]):
            print(f"  {i+1}. ID: {s.get('id')}, Created: {s.get('time_created')}, Ref: {s.get('short_tracking_reference')}")
    else:
        print(f"Base request failed: {resp_base.get('error')}")

    for start, end, label in test_ranges:
        print(f"\n--- Testing Range: {label} ({start} to {end}) ---")
        # Try both our new utility method and direct request with different formats if needed
        
        # 1. Using utility method (which uses +02:00)
        resp_util = api.get_shipments(from_date=start, to_date=end, limit=50)
        print(f"Util Method Success: {resp_util.get('success')}, Count: {len(resp_util.get('shipments', []))}")
        if resp_util.get('shipments'):
            for s in resp_util.get('shipments')[:3]:
                print(f"  - {s.get('time_created')} ({s.get('short_tracking_reference')})")
        
        # 2. Try raw request with UTC (Z) just in case
        params_utc = {
            "date_filter": "time_created",
            "start_date": f"{start} 00:00:00Z",
            "end_date": f"{end} 23:59:59Z",
            "limit": 50
        }
        resp_raw_utc = api._make_request("GET", "/shipments", params_utc)
        shipments_utc = []
        if resp_raw_utc.get("success"):
            data = resp_raw_utc.get("data", [])
            shipments_utc = data if isinstance(data, list) else data.get("shipments", [])
        print(f"Raw UTC Request Success: {resp_raw_utc.get('success')}, Count: {len(shipments_utc)}")

if __name__ == "__main__":
    verify_visibility()
