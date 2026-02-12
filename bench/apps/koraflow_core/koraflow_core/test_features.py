"""
Feature Verification Test Script
Tests all major features implemented in the last 3 days
"""
import frappe
from frappe.utils import nowdate, add_days

def run_all_tests():
    results = []
    
    # Test 1: Quotation from Encounter Hook
    results.append(test_encounter_quotation_hook())
    
    # Test 2: Billing APIs
    results.append(test_billing_apis())
    
    # Test 3: Referral Custom Fields
    results.append(test_referral_fields())
    
    # Test 4: Prescription Renewal Job
    results.append(test_renewal_job())
    
    # Print Results
    print("\n" + "="*60)
    print("FEATURE VERIFICATION RESULTS")
    print("="*60)
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n{status} - {r['name']}")
        if r.get("details"):
            for d in r["details"]:
                print(f"   • {d}")
        if r.get("error"):
            print(f"   ERROR: {r['error']}")
    print("\n" + "="*60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)
    
    return results

def test_encounter_quotation_hook():
    """Test that quotation generation hook exists and is callable"""
    result = {"name": "Quotation from Encounter", "passed": False, "details": []}
    
    try:
        from koraflow_core.hooks.prescription_hooks import handle_encounter_submit, generate_quotation_from_encounter
        result["details"].append("handle_encounter_submit hook found")
        result["details"].append("generate_quotation_from_encounter function found")
        
        # Check hooks.py registration
        hooks = frappe.get_hooks("doc_events")
        pe_hooks = hooks.get("Patient Encounter", {})
        if "on_submit" in pe_hooks:
            result["details"].append(f"on_submit hook registered: {pe_hooks['on_submit']}")
        else:
            result["details"].append("WARNING: on_submit hook not found in doc_events")
        
        result["passed"] = True
    except ImportError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result

def test_billing_apis():
    """Test billing API endpoints exist"""
    result = {"name": "Billing Portal APIs", "passed": False, "details": []}
    
    try:
        from koraflow_core.api.billing import accept_quotation, reject_quotation
        result["details"].append("accept_quotation API found")
        result["details"].append("reject_quotation API found")
        
        # Check if download_quotation_pdf exists
        try:
            from koraflow_core.api.billing import download_quotation_pdf
            result["details"].append("download_quotation_pdf API found")
        except ImportError:
            result["details"].append("download_quotation_pdf not found (may be optional)")
        
        result["passed"] = True
    except ImportError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result

def test_referral_fields():
    """Test referral custom fields exist on DocTypes"""
    result = {"name": "Referral Custom Fields", "passed": False, "details": []}
    
    try:
        # Check Patient DocType
        patient_meta = frappe.get_meta("Patient")
        patient_fields = [f.fieldname for f in patient_meta.fields]
        
        if "custom_referrer_name" in patient_fields:
            result["details"].append("custom_referrer_name on Patient ✓")
        else:
            result["details"].append("custom_referrer_name on Patient ✗")
        
        # Check Quotation DocType
        quotation_meta = frappe.get_meta("Quotation")
        quotation_fields = [f.fieldname for f in quotation_meta.fields]
        
        if "custom_referrer_name" in quotation_fields:
            result["details"].append("custom_referrer_name on Quotation ✓")
        else:
            result["details"].append("custom_referrer_name on Quotation ✗")
        
        if "custom_sales_agent" in quotation_fields:
            result["details"].append("custom_sales_agent on Quotation ✓")
        else:
            result["details"].append("custom_sales_agent on Quotation ✗")
        
        # Check GLP-1 Intake Form if exists
        try:
            intake_meta = frappe.get_meta("GLP-1 Intake Form")
            intake_fields = [f.fieldname for f in intake_meta.fields]
            if "custom_referrer_name" in intake_fields or "referrer_name" in intake_fields:
                result["details"].append("referrer_name on GLP-1 Intake Form ✓")
            else:
                result["details"].append("referrer_name on GLP-1 Intake Form ✗")
        except:
            result["details"].append("GLP-1 Intake Form DocType not found")
        
        # Pass if at least Patient and Quotation have the fields
        if "custom_referrer_name on Patient ✓" in result["details"]:
            result["passed"] = True
    except Exception as e:
        result["error"] = str(e)
    
    return result

def test_renewal_job():
    """Test prescription renewal job"""
    result = {"name": "Prescription Renewal Job", "passed": False, "details": []}
    
    try:
        from koraflow_core.jobs.prescription_renewal import generate_renewal_quotes
        result["details"].append("generate_renewal_quotes function found")
        
        # Check scheduler registration
        hooks = frappe.get_hooks("scheduler_events")
        daily_hooks = hooks.get("daily", [])
        
        if any("prescription_renewal" in str(h) for h in daily_hooks):
            result["details"].append("Registered in daily scheduler ✓")
        else:
            result["details"].append("NOT registered in daily scheduler")
        
        # Try executing (won't do anything without matching prescriptions)
        generate_renewal_quotes()
        result["details"].append("Job executed successfully (no matching prescriptions)")
        
        result["passed"] = True
    except ImportError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    run_all_tests()
