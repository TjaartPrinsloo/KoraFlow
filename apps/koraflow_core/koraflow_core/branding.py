"""
KoraFlow Branding Adapter
Central branding system for frontend-only rebranding.
"""

import frappe
from koraflow_core.koraflow_core.hooks import get_branding_map, get_branded_name


def apply_branding(text, context=None):
    """
    Apply KoraFlow branding to text.
    
    Args:
        text: Original text to brand
        context: Optional context (e.g., 'workspace', 'sidebar', 'title')
    
    Returns:
        Branded text
    """
    if not text:
        return text
    
    branding_map = get_branding_map()
    
    # Direct mapping
    if text in branding_map:
        return branding_map[text]
    
    # Replace in text
    branded_text = text
    for original, branded in branding_map.items():
        branded_text = branded_text.replace(original, branded)
    
    return branded_text


def get_branded_app_title(app_name):
    """
    Get branded app title for a given app name.
    """
    branding_map = get_branding_map()
    
    # Check direct mapping
    if app_name in branding_map:
        return branding_map[app_name]
    
    # Check case-insensitive
    app_name_lower = app_name.lower()
    for original, branded in branding_map.items():
        if original.lower() == app_name_lower:
            return branded
    
    return app_name


def get_module_display_name(module_name):
    """
    Get display name for a module.
    Used in workspaces and UI.
    """
    module_display_names = {
        'healthcare': 'KoraFlow Healthcare',
        'hr': 'KoraFlow Workforce',
        'crm': 'KoraFlow CRM',
        'helpdesk': 'KoraFlow Support',
        'insights': 'KoraFlow Insights',
        'erpnext': 'KoraFlow ERP',
        'frappe': 'KoraFlow Core',
    }
    
    return module_display_names.get(module_name.lower(), module_name)


@frappe.whitelist()
def get_branding_info():
    """
    API endpoint to get branding information.
    Used by frontend to apply branding dynamically.
    """
    return {
        'branding_map': get_branding_map(),
        'app_title': 'KoraFlow',
        'platform_name': 'KoraFlow'
    }

