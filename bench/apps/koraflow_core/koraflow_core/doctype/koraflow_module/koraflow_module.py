# Copyright (c) 2024, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from koraflow_core.module_registry import ModuleRegistry


class KoraFlowModule(Document):
    """KoraFlow Module DocType"""
    
    def validate(self):
        """Validate module configuration"""
        if not self.module_name:
            frappe.throw(_("Module Name is required"))
    
    def on_update(self):
        """Update module registry when DocType is updated"""
        # Sync with module registry
        if self.enabled:
            ModuleRegistry.enable_module(self.module_name)
        else:
            ModuleRegistry.disable_module(self.module_name)
    
    def after_insert(self):
        """Initialize module when created"""
        if self.enabled:
            ModuleRegistry.enable_module(self.module_name)

