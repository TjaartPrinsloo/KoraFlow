
import frappe
from frappe import _

def get_context(context):
    context.no_cache = 1
    
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to access this page"), frappe.PermissionError)
    
    if "Patient" not in frappe.get_roles():
        frappe.throw(_("Access denied"), frappe.PermissionError)
    
    patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
    
    if not patient_name:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/glp1-intake"
        return
    
    patient = frappe.get_doc("Patient", patient_name)
    context.patient = patient
    
    # Google Maps Settings
    google_settings = frappe.get_single("Google Settings")
    context.google_maps_api_key = google_settings.maps_api_key
    context.enable_google_maps = google_settings.enable_google_maps

@frappe.whitelist()
def update_profile(mobile, city, address_line1, state=None, zip_code=None):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to update profile"))
        
    patient_name = frappe.db.get_value("Patient", {"email": frappe.session.user}, "name")
    if not patient_name:
        frappe.throw(_("Patient record not found"))
        
    patient = frappe.get_doc("Patient", patient_name)
    patient.mobile = mobile
    patient.city = city
    patient.address_line1 = address_line1
    if state: patient.state = state
    if state: patient.state = state
    if zip_code: patient.zip_code = zip_code
    
    # Custom Fields
    if frappe.form_dict.get('billing_address'):
        patient.custom_billing_address = frappe.form_dict.get('billing_address')
    
    patient.custom_marketing_consent = 1 if frappe.form_dict.get('marketing_consent') == 'on' else 0
    
    patient.save(ignore_permissions=True)
    return True

@frappe.whitelist()
def update_password(new_password):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to change password"))
        
    from frappe.utils.password import update_password as _update_password
    _update_password(frappe.session.user, new_password)
    return True
