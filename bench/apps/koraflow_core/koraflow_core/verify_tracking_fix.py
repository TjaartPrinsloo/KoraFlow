
import frappe
from koraflow_core.api.courier_guy_tracking import get_patient_tracking

def test_tracking():
    print("Testing get_patient_tracking API...")
    try:
        # We know "Test Patient" exists from our setup script
        result = get_patient_tracking("Test Patient")
        print("SUCCESS: API call completed.")
        print(f"Found {len(result.get('waybills', []))} waybills.")
    except Exception as e:
        print(f"FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tracking()
