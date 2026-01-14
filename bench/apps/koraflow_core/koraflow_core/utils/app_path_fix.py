# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Fix for frappe.get_app_path to return correct app root for koraflow_core
TemplatePage needs app root, not module path
"""

import frappe
import os


def fix_app_path():
	"""Patch frappe.get_app_path to return app root for koraflow_core"""
	# Check if frappe.get_app_path exists
	if not hasattr(frappe, 'get_app_path'):
		# Frappe not initialized yet, return and try again later
		return
	
	# Always reapply the patch (frappe.init(force=True) resets it)
	# Store original if not already stored
	if not hasattr(fix_app_path, '_original_get_app_path'):
		fix_app_path._original_get_app_path = frappe.get_app_path
	
	original_get_app_path = fix_app_path._original_get_app_path
	
	def patched_get_app_path(app_name, *joins):
		if app_name == "koraflow_core":
			# get_app_path should return the app root directory
			# For koraflow_core, that's bench/apps/koraflow_core
			# The issue is that get_pymodule_path is broken for koraflow_core (namespace package)
			# So we manually calculate the correct path
			try:
				import importlib
				module = importlib.import_module(app_name)
				# Get the first path from the namespace
				if hasattr(module, '__path__') and module.__path__:
					module_path = module.__path__[0]
					# module_path is something like: /path/to/bench/sites/../apps/koraflow_core
					# Resolve it to get the actual path
					resolved_path = os.path.abspath(module_path)
					# The resolved path IS the app root (bench/apps/koraflow_core)
					# NOT the module directory (bench/apps/koraflow_core/koraflow_core)
					# So we use it directly as the app root
					app_root = resolved_path
					
					if joins:
						return os.path.join(app_root, *joins)
					return app_root
			except Exception as e:
				import frappe
				frappe.log_error(f"Error in app_path_fix: {e}", "App Path Fix Error")
				# Fallback: calculate from bench path
				try:
					bench_path = frappe.get_bench_path()
					# bench_path is bench/sites, so go up to bench, then to apps
					bench_root = os.path.dirname(bench_path)
					app_root = os.path.join(bench_root, "apps", "koraflow_core")
					if joins:
						return os.path.join(app_root, *joins)
					return app_root
				except Exception:
					# Last resort: hardcoded relative to sites
					sites_path = frappe.local.site_path if hasattr(frappe, 'local') and hasattr(frappe.local, 'site_path') else None
					if sites_path:
						# sites_path is bench/sites, go up to bench, then to apps
						bench_root = os.path.dirname(sites_path)
						app_root = os.path.join(bench_root, "apps", "koraflow_core")
						if joins:
							return os.path.join(app_root, *joins)
						return app_root
					# Ultimate fallback
					return original_get_app_path(app_name, *joins)
		return original_get_app_path(app_name, *joins)
	
	frappe.get_app_path = patched_get_app_path
	# Mark as patched
	frappe.get_app_path._koraflow_patched = True


# Apply the fix when module is imported
fix_app_path()
