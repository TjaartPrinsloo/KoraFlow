import frappe
from frappe import _


def get_context(context):
	"""Public page shown after intake form submission - no login required"""
	context.no_cache = 1
	context.title = "Profile Under Review"
	context.show_sidebar = False

