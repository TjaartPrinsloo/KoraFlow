import frappe
from koraflow_core.api.apps import get_apps
import json

def test_get_apps():
    frappe.set_user('nurse@koraflow.com')
    apps = get_apps()
    print("APPS FOR NURSE:")
    print(json.dumps(apps, indent=2))

if __name__ == "__main__":
    test_get_apps()
