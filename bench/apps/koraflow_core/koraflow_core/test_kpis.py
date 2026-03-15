import frappe
from koraflow_core.api.courier_guy_dashboard import get_courier_guy_dashboard_data

def test_kpis():
    frappe.init(site="koraflow-site")
    frappe.connect()
    
    res = get_courier_guy_dashboard_data(from_date="2024-09-01", to_date="2026-12-31")
    
    if res.get("success"):
        kpis = res["data"]["kpis"]
        print("KPIs:", kpis)
        shipments = res["data"]["shipments"]
        print("Shipments count:", len(shipments))
        if shipments:
            s0 = shipments[0]
            print(f"First shipment keys: {list(shipments[0].keys())}")
            print(f"First shipment rate/value: {shipments[0].get('total_value')} {shipments[0].get('total_weight')} {shipments[0].get('parcel_count')}")
            print(f"First shipment contact info: {shipments[0].get('sender_contact_name')} {shipments[0].get('receiver_contact_name')}")
    else:
        print("Failed:", res)

test_kpis()
