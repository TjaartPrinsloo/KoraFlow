
import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
import requests
import json
import sys

# Initialize Frappe
frappe.init(site="koraflow-site")
frappe.connect()

def test_submission():
    # Simulate a guest or logged-in user?
    # The API requires login.
    # We can use Frappe's test client or just call the python function directly to test the LOGIC first.
    # Calling directly bypasses the network/server layer (WSGI), so it tests if the code works with the DB.
    
    print("Testing create_intake_submission logic directly...")
    
    try:
        from koraflow_core.api.intake_review import create_intake_submission
        
        # Mock session user (the API checks frappe.session.user)
        # We need to pick a valid user. Let's create one or use Administrator?
        # The API says: if frappe.session.user == "Guest": frappe.throw...
        
        frappe.session.user = "Administrator" # masquerade as admin for test
        
        test_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "email": "test.patient.api@example.com",
            "mobile": "+27630000000",
            "date_of_birth": "1990-01-01",
            "biological_sex": "Male",
            "height_unit": "cm",
            "height_cm": 180,
            "weight_unit": "kg",
            "weight_kg": 80,
            "id_number": "9001015000080"
        }
        
        print(f"Submitting data: {test_data}")
        result = create_intake_submission(test_data)
        print("Result:", result)
        
    except Exception as e:
        print("Error during direct execution:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_submission()
