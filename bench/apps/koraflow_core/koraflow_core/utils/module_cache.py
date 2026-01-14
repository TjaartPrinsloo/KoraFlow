# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.modules.utils import scrub


def populate_module_cache():
	"""Populate frappe.local.module_app from database if not already populated"""
	if not hasattr(frappe.local, 'module_app') or not frappe.local.module_app:
		frappe.local.module_app = {}
	
	# Get all modules from database
	modules = frappe.get_all('Module Def', fields=['name', 'app_name'], filters={'disabled': 0})
	
	for module in modules:
		scrubbed_name = scrub(module.name)
		# Only add if not already present (to avoid overwriting)
		if scrubbed_name not in frappe.local.module_app:
			frappe.local.module_app[scrubbed_name] = module.app_name
	
	frappe.cache().set_value('module_app_populated', True)

