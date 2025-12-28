"""
KoraFlow Module Registry
Manages module activation/deactivation and visibility.
"""

import frappe
from frappe import _


class ModuleRegistry:
    """Registry for managing KoraFlow modules"""
    
    MODULE_CONFIG_KEY = 'koraflow_modules'
    
    @staticmethod
    def get_enabled_modules():
        """
        Get list of enabled modules.
        Returns list of module names.
        """
        site_config = frappe.get_site_config()
        enabled_modules = site_config.get(ModuleRegistry.MODULE_CONFIG_KEY, {})
        
        # Return only enabled modules
        return [name for name, enabled in enabled_modules.items() if enabled]
    
    @staticmethod
    def is_module_enabled(module_name):
        """
        Check if a module is enabled.
        
        Args:
            module_name: Name of the module (e.g., 'healthcare', 'hr')
        
        Returns:
            bool: True if module is enabled
        """
        site_config = frappe.get_site_config()
        enabled_modules = site_config.get(ModuleRegistry.MODULE_CONFIG_KEY, {})
        return enabled_modules.get(module_name, True)  # Default to enabled
    
    @staticmethod
    def enable_module(module_name):
        """
        Enable a module.
        
        Args:
            module_name: Name of the module to enable
        """
        site_config = frappe.get_site_config()
        enabled_modules = site_config.get(ModuleRegistry.MODULE_CONFIG_KEY, {})
        enabled_modules[module_name] = True
        
        frappe.conf.update({
            ModuleRegistry.MODULE_CONFIG_KEY: enabled_modules
        })
        frappe.db.commit()
    
    @staticmethod
    def disable_module(module_name):
        """
        Disable a module.
        
        Args:
            module_name: Name of the module to disable
        """
        site_config = frappe.get_site_config()
        enabled_modules = site_config.get(ModuleRegistry.MODULE_CONFIG_KEY, {})
        enabled_modules[module_name] = False
        
        frappe.conf.update({
            ModuleRegistry.MODULE_CONFIG_KEY: enabled_modules
        })
        frappe.db.commit()
    
    @staticmethod
    def get_all_modules():
        """
        Get all available modules with their status.
        
        Returns:
            dict: Module name -> enabled status
        """
        available_modules = {
            'erpnext': {'name': 'KoraFlow ERP', 'default': True},
            'healthcare': {'name': 'KoraFlow Healthcare', 'default': True},
            'hr': {'name': 'KoraFlow Workforce', 'default': True},
            'crm': {'name': 'KoraFlow CRM', 'default': True},
            'helpdesk': {'name': 'KoraFlow Support', 'default': True},
            'insights': {'name': 'KoraFlow Insights', 'default': True},
        }
        
        site_config = frappe.get_site_config()
        enabled_modules = site_config.get(ModuleRegistry.MODULE_CONFIG_KEY, {})
        
        result = {}
        for module_key, module_info in available_modules.items():
            result[module_key] = {
                'name': module_info['name'],
                'enabled': enabled_modules.get(module_key, module_info['default'])
            }
        
        return result
    
    @staticmethod
    def should_show_module(module_name):
        """
        Check if module should be shown in UI.
        Used by workspace and sidebar visibility rules.
        
        Args:
            module_name: Name of the module
        
        Returns:
            bool: True if module should be visible
        """
        return ModuleRegistry.is_module_enabled(module_name)


@frappe.whitelist()
def get_module_status(module_name):
    """
    API endpoint to get module status.
    """
    return {
        'enabled': ModuleRegistry.is_module_enabled(module_name),
        'visible': ModuleRegistry.should_show_module(module_name)
    }


@frappe.whitelist()
def toggle_module(module_name, enable=True):
    """
    API endpoint to toggle module on/off.
    
    Args:
        module_name: Name of the module
        enable: True to enable, False to disable
    """
    if enable:
        ModuleRegistry.enable_module(module_name)
    else:
        ModuleRegistry.disable_module(module_name)
    
    return {
        'module': module_name,
        'enabled': enable,
        'status': 'success'
    }


@frappe.whitelist()
def get_all_modules_status():
    """
    API endpoint to get status of all modules.
    """
    return ModuleRegistry.get_all_modules()

