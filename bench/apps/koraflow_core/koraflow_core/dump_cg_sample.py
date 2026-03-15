import frappe
from koraflow_core.utils.courier_guy_api import CourierGuyAPI
import json

def dump_sample():
    frappe.init(site="koraflow-site")
    frappe.connect()
    api = CourierGuyAPI()
    res = api.get_shipments(limit=3)
    if res.get("success"):
        shipments = res.get("shipments", [])
        if shipments:
            print(json.dumps(shipments[0], indent=2))
        else:
            print("No shipments found.")
    else:
        print("Error:", res.get("error"))

if __name__ == "__main__":
    dump_sample()
