import frappe
import json
from koraflow_core.api.courier_guy_tracking import get_historical_shipments
from koraflow_core.api.courier_guy_dashboard import format_shipments_for_display, get_waybill_details
from koraflow_core.utils.courier_guy_api import CourierGuyAPI

def execute():
    print("\n================================================")
    print("DEEP TESTING COURIER GUY DASHBOARD FIXES")
    print("================================================\n")

    print("[1] Testing Filters (Contact Info & Status Mapping)...")
    try:
        res = get_historical_shipments(limit=5)
        if res.get("success"):
            shipments = res.get("shipments", [])
            print(f"-> Fetched {len(shipments)} shipments.")
            if shipments:
                s = shipments[0]
                print(f"-> Raw Data Sample Status: '{s.get('raw_data', {}).get('status')}'")
                print(f"-> Formatted Status: '{s.get('status')}'")
                print(f"-> Coll Contact: '{s.get('collection_contact_name')}'")
                print(f"-> Del Contact: '{s.get('delivery_contact_name')}'")
                
                if s.get('collection_contact_name'):
                    print("✅ SUCCESS: Contact details are being populated.")
                else:
                    print("⚠️ WARNING: Contact details still None. Check raw keys.")
            else:
                print("No shipments found.")
    except Exception as e:
        print(f"Error in Filter test: {e}")

    print("\n[2] Deep Search for Waybill KC7N8P...")
    try:
        api = CourierGuyAPI()
        # Search limit 500 to avoid timeout
        res = api.get_shipments(limit=500)
        if res.get("success"):
            shipments = res.get("shipments", [])
            print(f"-> Searching in {len(shipments)} shipments...")
            found = False
            for s in shipments:
                refs = [
                    str(s.get("short_tracking_reference") or "").strip(),
                    str(s.get("id") or "").strip(),
                    str(s.get("waybill_number") or "").strip()
                ]
                if "KC7N8P" in refs:
                    print("✅ FOUND KC7N8P in shipment list!")
                    print(json.dumps(s, indent=2))
                    found = True
                    break
            if not found:
                print("❌ KC7N8P not found in shipments list (limit 500).")
        else:
            print(f"API Error: {res.get('error')}")
    except Exception as e:
        print(f"Error in search: {e}")

    print("\n[3] Testing get_waybill_details(KC7N8P)...")
    try:
        res = get_waybill_details("KC7N8P")
        if res.get("success"):
            print("✅ SUCCESS: get_waybill_details found the waybill!")
            print(f"   Status: {res.get('data', {}).get('status')}")
            print(f"   Contact Name: {res.get('data', {}).get('collection_contact_name')}")
        else:
            print(f"❌ FAIL: get_waybill_details error: {res.get('error')}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n================================================\n")
if __name__ == "__main__":
    execute()
